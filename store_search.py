from __future__ import annotations

import difflib
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().with_name("store_test.db")
DB_PATH = Path(os.environ.get("STORE_DB_PATH", DEFAULT_DB_PATH))


CATEGORY_ALIASES = {
    "phone": "phones",
    "phones": "phones",
    "smartphone": "phones",
    "smartphones": "phones",
    "laptop": "laptops",
    "laptops": "laptops",
    "notebook": "laptops",
    "notebooks": "laptops",
    "earbud": "earbuds",
    "earbuds": "earbuds",
    "headphone": "headphones",
    "headphones": "headphones",
    "headset": "headphones",
    "headsets": "headphones",
    "monitor": "monitors",
    "monitors": "monitors",
    "tv": "tvs",
    "tvs": "tvs",
    "television": "tvs",
    "televisions": "tvs",
    "charger": "chargers",
    "chargers": "chargers",
    "adapter": "chargers",
    "adapters": "chargers",
    "cable": "cables",
    "cables": "cables",
    "smartwatch": "smartwatches",
    "smartwatches": "smartwatches",
    "watch": "smartwatches",
    "tablet": "tablets",
    "tablets": "tablets",
    "camera": "cameras",
    "cameras": "cameras",
    "printer": "printers",
    "printers": "printers",
    "router": "routers",
    "routers": "routers",
    "mouse": "gaming",
    "keyboard": "gaming",
    "console": "gaming",
    "software": "software",
    "os": "software",
}

# Common product families help category extraction and conservative typo handling.
# Keep this list narrow so fuzzy matching does not silently change identity.
PRODUCT_FAMILY_CATEGORY_ALIASES = {
    "iphone": "phones",
    "pixel": "phones",
    "oneplus": "phones",
    "macbook": "laptops",
    "thinkpad": "laptops",
    "ideapad": "laptops",
    "vivobook": "laptops",
    "zenbook": "laptops",
    "legion": "laptops",
    "airpods": "earbuds",
}

TYPO_MATCH_CUTOFF = 0.82

# These contain numbers but are normally specifications, not exact models.
NON_MODEL_IDENTITY_TOKENS = {
    "4g",
    "5g",
    "wifi",
    "wifi6",
    "wifi7",
    "bluetooth",
}

# These become exact requirements when used with a named product family.
# Example: iPhone 16 Pro Max.
EXACT_VARIANT_TOKENS = {
    "pro",
    "max",
    "plus",
    "ultra",
    "mini",
    "air",
    "se",
    "slim",
}


# Product-name clues are a second safety layer when catalogue category data is
# missing or incorrect. These are intentionally conservative: they only classify
# names with strong family words.
OBVIOUS_NAME_CATEGORY_PATTERNS = {
    "phones": (
        r"\biphone\b", r"\bgalaxy\s+(?:s|a|z|m|f)\d",
        r"\bpixel\s+\d", r"\bnova\s+\d", r"\bredmi\s+note\b",
        r"\boppo\s+(?:reno|find|a)\b", r"\boneplus\s+\d",
        r"\bxiaomi\s+\d", r"\bhonor\s+(?:magic|x)\d",

    ),
    "software": (
        r"\bwindows\s+(?:10|11)\b",
        r"\bwindows\s+(?:home|pro|professional|enterprise|education)\b",
        r"\boperating\s+systems?\b",
    ),
    "laptops": (
        r"\bmacbook\b", r"\bthinkpad\b", r"\bideapad\b",
        r"\bvivobook\b", r"\bzenbook\b", r"\bmatebook\b",
        r"\bchromebook\b", r"\baspire\b", r"\bswift\b",
        r"\bnitro\b", r"\bpredator\b", r"\bro[g]?\b",
        r"\bzephyrus\b", r"\btuf\b", r"\blegion\b",
        r"\bomen\b", r"\bvictus\b", r"\balienware\b",
        r"\brazer\s+blade\b", r"\bframework\s+laptop\b",
        r"\blaptop\b", r"\bnotebook\b",
    ),
    "tablets": (r"\bipad\b", r"\bgalaxy\s+tab\b", r"\bsurface\s+(?:go|pro)\b"),
    "tvs": (r"\b(?:oled|qled|mini\s*led)\s+tv\b", r"\btelevision\b", r"\bsmart\s+tv\b"),
    "headphones": (r"\bheadphones?\b", r"\bheadset\b", r"\bairpods\s+max\b"),
    "earbuds": (r"\bearbuds?\b", r"\bairpods(?:\s+pro)?\b", r"\bgalaxy\s+buds\b"),
}

GENERIC_IDENTITY_TOKENS = {
    "laptop", "notebook", "gaming", "student", "students", "edition",
    "series", "model", "inch", "inches", "fhd", "oled", "ai", "max",
    "pro", "plus", "ultra", "new", "2024", "2025", "2026",
    "software",
    "os",
    "operating",
    "system",
    "systems",
    "license",
    "licence",
}


GENERIC_QUERY_IDENTITY_TOKENS = {
    *GENERIC_IDENTITY_TOKENS,
    "phone", "phones", "smartphone", "smartphones",
    "laptop", "laptops", "notebook", "notebooks",
    "earbud", "earbuds", "headphone", "headphones",
    "monitor", "monitors", "tv", "tvs", "television",
    "charger", "chargers", "adapter", "adapters",
    "cable", "cables", "tablet", "tablets",
    "camera", "cameras", "printer", "printers",
    "router", "routers", "mouse", "keyboard", "console",
    "aed", "dhs", "dirham", "dirhams",
    "under", "below", "less", "than", "maximum", "max",
    "want", "need", "looking", "find", "show", "buy",
}


def _requested_product_identity_text(user_query: str) -> str:
    """Return the part of the query that names the product being purchased."""
    without_budget = BUDGET_PATTERN.sub(" ", user_query or "")
    tokens = tokenize(without_budget)

    if not tokens:
        return ""

    identity_anchors = (
        set(CATEGORY_ALIASES)
        | set(PRODUCT_FAMILY_CATEGORY_ALIASES)
    )

    anchor_indexes = [
        index
        for index, token in enumerate(tokens)
        if token in identity_anchors
    ]

    if not anchor_indexes:
        return " ".join(tokens)

    anchor_index = anchor_indexes[0]

    compatibility_sequences = (
        ("compatible", "with"),
        ("works", "with"),
        ("work", "with"),
        ("to", "use", "with"),
        ("for", "use", "with"),
    )

    for index in range(anchor_index + 1, len(tokens)):
        # "laptop for engineering" and
        # "monitor for MacBook Air"
        if tokens[index] == "for":
            return " ".join(tokens[:index])

        for sequence in compatibility_sequences:
            if tuple(tokens[index:index + len(sequence)]) == sequence:
                return " ".join(tokens[:index])

    return " ".join(tokens)

def infer_obvious_category_from_name(product_name: str) -> str | None:
    normalized = normalize_product_text(product_name)
    for category_name, patterns in OBVIOUS_NAME_CATEGORY_PATTERNS.items():
        if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns):
            return category_name
    return None


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "best",
    "buy",
    "can",
    "cheap",
    "for",
    "from",
    "good",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "please",
    "product",
    "products",
    "show",
    "suitable",
    "the",
    "to",
    "under",
    "want",
    "with",
}


BUDGET_PATTERN = re.compile(
    r"\b(?:under|below|less\s+than|max(?:imum)?|up\s+to)"
    r"\s*(?:aed|dhs)?\s*"
    r"([\d,]+(?:\.\d+)?)"
    r"\s*(?:aed|dhs)?\b",
    flags=re.IGNORECASE,
)


def normalize_product_text(text: str) -> str:
    """Normalize product text so names from the web and catalogue compare better."""
    normalized = (text or "").lower().strip()
    normalized = normalized.replace("usb-c", "usbc").replace("usb c", "usbc")
    normalized = re.sub(r"\b2\s*[- ]?\s*in\s*[- ]?\s*1\b", "2in1", normalized)
    normalized = re.sub(
        r"\b(\d+(?:\.\d+)?)\s*[- ]?\s*(gb|tb|mm|inches|inch|in|w|m)\b",
        lambda match: (
            f"{match.group(1)}"
            f"{'inch' if match.group(2) in {'in', 'inch', 'inches'} else match.group(2)}"
        ),
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"[^a-z0-9.]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def tokenize(text: str) -> list[str]:
    """Split text while preserving values such as 15.6inch and 512gb."""
    return re.findall(r"\d+(?:\.\d+)?[a-z]*|[a-z0-9]+", normalize_product_text(text))


def normalize_category(category: str | None) -> str | None:
    if not category:
        return None

    normalized = normalize_product_text(category)
    for word in tokenize(normalized):
        if word in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[word]

    return normalized or None


def extract_category_from_query(query: str) -> str | None:
    """
    Extract the product category while distinguishing software from
    hardware that merely uses that software.

    Examples:
        "Windows 11 Pro" -> software
        "operating system for my PC" -> software
        "Windows laptop" -> laptops
        "laptop with Windows 11" -> laptops
    """
    tokens = tokenize(query)

    combined_aliases = {
        **CATEGORY_ALIASES,
        **PRODUCT_FAMILY_CATEGORY_ALIASES,
    }

    category_candidates: list[tuple[int, str]] = []

    # Find normal product categories.
    for index, word in enumerate(tokens):
        category = combined_aliases.get(word)

        if category:
            category_candidates.append(
                (index, category)
            )

    # Recognize explicit operating-system shopping requests.
    software_edition_tokens = {
        "10",
        "11",
        "home",
        "pro",
        "professional",
        "enterprise",
        "education",
        "license",
        "licence",
        "key",
    }

    for index, word in enumerate(tokens):
        if word in {"software", "os"}:
            category_candidates.append(
                (index, "software")
            )

        if (
            word == "operating"
            and index + 1 < len(tokens)
            and tokens[index + 1] in {
                "system",
                "systems",
            }
        ):
            category_candidates.append(
                (index, "software")
            )

        # Do not treat bare "windows" as software. Require an edition,
        # version, licence, or key term.
        if (
            word == "windows"
            and index + 1 < len(tokens)
            and tokens[index + 1] in software_edition_tokens
        ):
            category_candidates.append(
                (index, "software")
            )

    if category_candidates:
        # The first product category mentioned is normally the item
        # being purchased.
        category_candidates.sort(
            key=lambda item: item[0]
        )
        return category_candidates[0][1]

    # Conservative spelling correction for existing categories.
    # Software-family words such as "windows" are intentionally excluded
    # so "window" cannot become a Windows software request.
    alias_words = tuple(
        word
        for word, category in combined_aliases.items()
        if category != "software"
    )

    for word in tokens:
        if len(word) < 4 or not word.isalpha():
            continue

        matches = difflib.get_close_matches(
            word,
            alias_words,
            n=1,
            cutoff=TYPO_MATCH_CUTOFF,
        )

        if matches:
            return combined_aliases[matches[0]]

    return None

def extract_max_price(query: str) -> float | None:
    matches = list(BUDGET_PATTERN.finditer(query or ""))
    if not matches:
        return None
    return float(matches[-1].group(1).replace(",", ""))


def _meaningful_tokens(text: str) -> set[str]:
    return {token for token in tokenize(text) if token not in STOPWORDS}


def _identifier_tokens(tokens: set[str]) -> set[str]:
    """Return model-like tokens such as X1504VA, A515, S24, or 3530."""
    identifiers: set[str] = set()
    for token in tokens:
        has_letter = any(character.isalpha() for character in token)
        has_digit = any(character.isdigit() for character in token)
        if has_letter and has_digit:
            identifiers.add(token)
        # Short numbers such as 14, 15, 16, 128, and 512 commonly describe
        # screen size or capacity. Treating them as model identifiers caused
        # unrelated products to match. Keep only longer numeric model codes.
        elif token.isdigit() and len(token) >= 4:
            identifiers.add(token)
    return identifiers


def _candidate_similarity(
    candidate_name: str,
    product_name: str,
    candidate_brand: str = "",
) -> float:
    candidate_normalized = normalize_product_text(candidate_name)
    product_normalized = normalize_product_text(product_name)

    if not candidate_normalized or not product_normalized:
        return 0.0

    if candidate_normalized == product_normalized:
        return 1.0

    candidate_tokens = _meaningful_tokens(candidate_normalized)
    product_tokens = _meaningful_tokens(product_normalized)

    if not candidate_tokens or not product_tokens:
        return 0.0

    overlap = candidate_tokens & product_tokens
    candidate_coverage = len(overlap) / len(candidate_tokens)
    balanced_coverage = len(overlap) / max(1, min(len(candidate_tokens), len(product_tokens)))
    sequence_ratio = difflib.SequenceMatcher(
        None, candidate_normalized, product_normalized
    ).ratio()

    candidate_identifiers = _identifier_tokens(candidate_tokens)
    product_identifiers = _identifier_tokens(product_tokens)
    identifier_overlap = candidate_identifiers & product_identifiers

    brand_tokens = _meaningful_tokens(candidate_brand)
    brand_matches = not brand_tokens or bool(brand_tokens & product_tokens)

    # Remove brand names and generic shopping/spec words. At least one meaningful
    # product-family token (for example macbook, ideapad, vivobook, nitro) must
    # overlap unless an exact model identifier overlaps. This blocks matches such
    # as Apple MacBook Air 15 -> iPhone 15 and HUAWEI MateBook D 15 -> nova 15.
    candidate_family = (
        candidate_tokens - brand_tokens - GENERIC_IDENTITY_TOKENS
    )
    product_family = product_tokens - brand_tokens - GENERIC_IDENTITY_TOKENS
    family_overlap = candidate_family & product_family

    identifier_bonus = 0.22 if identifier_overlap else 0.0
    identifier_penalty = (
        0.20
        if candidate_identifiers and product_identifiers and not identifier_overlap
        else 0.0
    )

    score = (
        0.44 * candidate_coverage
        + 0.24 * balanced_coverage
        + 0.32 * sequence_ratio
        + identifier_bonus
        - identifier_penalty
    )

    if not brand_matches:
        score = min(score, 0.45)
    if not family_overlap and not identifier_overlap:
        score = min(score, 0.55)

    return max(0.0, min(1.0, score))


def _requirements_similarity(
    product_text: str,
    product_category: str,
    requirement_terms: list[str],
) -> float:
    product_tokens = _meaningful_tokens(
        f"{product_text} {product_category}"
    )

    if not product_tokens:
        return 0.0

    scores: list[float] = []

    for term in requirement_terms:
        term_tokens = _meaningful_tokens(term)

        if not term_tokens:
            continue

        overlap = term_tokens & product_tokens
        scores.append(len(overlap) / len(term_tokens))

    if not scores:
        return 0.0

    # One easy requirement such as "Windows" should not make the
    # entire product a perfect requirements match.
    average_score = sum(scores) / len(scores)
    best_score = max(scores)

    return 0.70 * average_score + 0.30 * best_score

def _fuzzy_identity_overlap(
    query_tokens: set[str],
    identity_tokens: set[str],
) -> set[str]:
    """
    Return product identity tokens matched exactly or through one
    conservative spelling correction.
    """
    matched = query_tokens & identity_tokens

    alphabetic_identity = {
        token
        for token in identity_tokens
        if len(token) >= 4 and token.isalpha()
    }

    if not alphabetic_identity:
        return matched

    for query_token in query_tokens - matched:
        if len(query_token) < 4 or not query_token.isalpha():
            continue

        close_matches = difflib.get_close_matches(
            query_token,
            alphabetic_identity,
            n=1,
            cutoff=TYPO_MATCH_CUTOFF,
        )

        if close_matches:
            matched.add(close_matches[0])

    return matched

def _flatten_specifications_for_search(raw_json: str) -> str:
    """
    Convert specifications JSON into searchable text.

    False Boolean values are ignored so that:
        "dedicated_gpu": False

    does not accidentally match:
        "I need a dedicated GPU"
    """
    try:
        data = json.loads(raw_json or "{}")
    except (TypeError, json.JSONDecodeError):
        return ""

    parts: list[str] = []

    def visit(key: str, value: Any) -> None:
        label = key.replace("_", " ").strip()

        if isinstance(value, bool):
            if value and label:
                parts.append(label)
            return

        if isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(str(child_key), child_value)
            return

        if isinstance(value, list):
            for child_value in value:
                visit(key, child_value)
            return

        if value is None:
            return

        text_value = str(value).strip()

        if not text_value:
            return

        if key.endswith("_gb"):
            field_name = key[:-3].replace("_", " ")
            parts.append(f"{text_value} gb {field_name}")

        elif key.endswith("_w"):
            field_name = key[:-2].replace("_", " ")
            parts.append(f"{text_value} w {field_name}")

        else:
            parts.append(f"{label} {text_value}".strip())

    if isinstance(data, dict):
        for key, value in data.items():
            visit(str(key), value)

    return " ".join(parts)

def extract_explicit_model_tokens(user_query: str) -> set[str]:
    """
    Extract model, generation, capacity, and variant tokens.

    Examples:
        iPhone 22 under AED 5000
        -> {"22"}

        iPhone 16 Pro Max 256GB
        -> {"16", "pro", "max", "256gb"}

        MacBook Air M3
        -> {"air", "m3"}

    The maximum budget is removed first so AED 5000 is not mistaken
    for a model number.
    """
    tokens = tokenize(
        _requested_product_identity_text(user_query)
    )

    model_tokens: set[str] = set()

    for token in tokens:
        if token in NON_MODEL_IDENTITY_TOKENS:
            continue

        has_letter = any(character.isalpha() for character in token)
        has_digit = any(character.isdigit() for character in token)

        # Examples: S24, M3, 16IRX9, 256GB.
        if has_letter and has_digit:
            model_tokens.add(token)
            continue

        # Examples: iPhone 15, iPhone 16, iPhone 22.
        if token.isdigit():
            numeric_value = int(token)

            # A year is normally shopping context rather than a model.
            if 1900 <= numeric_value <= 2100:
                continue

            if len(token) <= 4:
                model_tokens.add(token)

            continue

        # Examples: Pro, Max, Ultra, Air.
        if token in EXACT_VARIANT_TOKENS:
            model_tokens.add(token)

    normalized_query = " ".join(
        tokenize(user_query)
    )

    # In these phrases, "pro" is part of the product family rather
    # than a separate variant requirement.
    family_phrases_using_pro = {
        "macbook pro",
        "airpods pro",
        "surface pro",
    }

    if any(
            phrase in normalized_query
            for phrase in family_phrases_using_pro
    ):
        model_tokens.discard("pro")

    return model_tokens


def _explicit_identity_constraint(
    *,
    user_query: str,
    product_name: str,
    brand: str = "",
    product_family: str = "",
    model_number: str = "",
    specifications_text: str = "",
) -> tuple[bool, str]:
    """
    Enforce exact model and generation constraints.

    This prevents:
        iPhone 22 -> iPhone 15
        MacBook M3 -> MacBook M2
        Galaxy S24 -> Galaxy S23

    A broad request such as "an iPhone under AED 5000" remains valid
    because it does not contain an exact generation.
    """
    identity_query = _requested_product_identity_text(user_query)
    query_tokens = _meaningful_tokens(identity_query)

    if not query_tokens:
        return True, ""

    brand_tokens = _meaningful_tokens(brand)

    family_tokens = (
        _meaningful_tokens(product_family)
        - GENERIC_IDENTITY_TOKENS
    )

    name_tokens = (
        _meaningful_tokens(product_name)
        - GENERIC_IDENTITY_TOKENS
    )

    identity_name_tokens = (
        brand_tokens
        | family_tokens
        | name_tokens
    )

    distinctive_identity_tokens = {
        token
        for token in identity_name_tokens
        if len(token) >= 3 and not token.isdigit()
    }

    identity_overlap = _fuzzy_identity_overlap(
        query_tokens,
        distinctive_identity_tokens,
    )

    # The customer did not explicitly name this brand or family.
    # Let normal web-candidate matching handle the product.
    if not identity_overlap:
        return True, ""

    requested_model_tokens = extract_explicit_model_tokens(
        user_query
    )

    # Broad family request such as "an iPhone".
    if not requested_model_tokens:
        return True, ""

    product_identity_text = " ".join(
        part
        for part in (
            product_name,
            brand,
            product_family,
            model_number,
            specifications_text,
        )
        if part
    )

    product_identity_tokens = set(
        tokenize(product_identity_text)
    )

    missing_tokens = (
        requested_model_tokens
        - product_identity_tokens
    )

    if missing_tokens:
        return (
            False,
            "Exact requested model or variant token(s) are absent: "
            + ", ".join(sorted(missing_tokens)),
        )

    return True, ""


def external_product_matches_query_identity(
    user_query: str,
    exact_product_name: str,
) -> bool:
    """
    Apply the same exact-model requirement to an external retailer product.
    """
    allowed, _ = _explicit_identity_constraint(
        user_query=user_query,
        product_name=exact_product_name,
    )

    return allowed

def _query_identity_match(
    *,
    user_query: str,
    product_name: str,
    brand: str,
    product_family: str,
    model_number: str,
) -> tuple[bool, float, str]:
    """
    Recognize a product explicitly requested by the customer.

    A broad request such as "an iPhone" may match any suitable iPhone.

    When a generation, model, capacity, or variant is supplied, it
    becomes a hard identity requirement.

    Conservative fuzzy matching handles spelling mistakes such as:
        iphnoe -> iphone

    Numbers and model identifiers are never autocorrected.
    """
    constraint_ok, _ = _explicit_identity_constraint(
        user_query=user_query,
        product_name=product_name,
        brand=brand,
        product_family=product_family,
        model_number=model_number,
    )

    if not constraint_ok:
        return False, 0.0, ""

    query_tokens = (
        _meaningful_tokens(user_query)
        - GENERIC_QUERY_IDENTITY_TOKENS
    )

    if not query_tokens:
        return False, 0.0, ""

    brand_tokens = _meaningful_tokens(brand)

    family_tokens = (
        _meaningful_tokens(product_family)
        - GENERIC_IDENTITY_TOKENS
    )

    model_tokens = (
        _meaningful_tokens(model_number)
        - GENERIC_IDENTITY_TOKENS
    )

    name_tokens = (
        _meaningful_tokens(product_name)
        - GENERIC_IDENTITY_TOKENS
    )

    distinctive_query_tokens = {
        token
        for token in query_tokens
        if len(token) >= 3 and not token.isdigit()
    }

    if not distinctive_query_tokens:
        return False, 0.0, ""

    model_overlap = _fuzzy_identity_overlap(
        distinctive_query_tokens,
        model_tokens,
    )

    family_overlap = _fuzzy_identity_overlap(
        distinctive_query_tokens,
        family_tokens,
    )

    brand_overlap = _fuzzy_identity_overlap(
        distinctive_query_tokens,
        brand_tokens,
    )

    name_overlap = _fuzzy_identity_overlap(
        distinctive_query_tokens,
        name_tokens,
    )

    requested_model_tokens = extract_explicit_model_tokens(
        user_query
    )

    exact_suffix = ""

    if requested_model_tokens:
        exact_suffix = (
            " Exact requested model or variant preserved: "
            + ", ".join(sorted(requested_model_tokens))
            + "."
        )

    if model_overlap:
        matched = sorted(model_overlap)

        return (
            True,
            0.97,
            f"Matches the requested model term(s): "
            f"{', '.join(matched)}."
            + exact_suffix,
        )

    if family_overlap:
        matched = sorted(family_overlap)

        return (
            True,
            0.93,
            f"Matches the requested product family: "
            f"{', '.join(matched)}."
            + exact_suffix,
        )

    if name_overlap:
        matched = sorted(name_overlap)

        return (
            True,
            0.90,
            f"Matches the requested product name term(s): "
            f"{', '.join(matched)}."
            + exact_suffix,
        )

    if brand_overlap:
        matched = sorted(brand_overlap)

        return (
            True,
            0.84,
            f"Matches the requested brand: "
            f"{', '.join(matched)}."
            + exact_suffix,
        )

    return False, 0.0, ""


def _fetch_catalogue_rows(
    *,
    category: str | None,
    max_price_aed: float | None,
    in_stock_only: bool,
) -> list[sqlite3.Row]:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Catalogue database was not found: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as schema_connection:
        available_columns = {
            str(row[1])
            for row in schema_connection.execute("PRAGMA table_info(products)").fetchall()
        }

    def optional_column(name: str) -> str:
        return name if name in available_columns else f"'' AS {name}"

    sql = f"""
        SELECT
            rowid AS catalogue_id,
            name,
            price_aed,
            in_stock,
            url,
            category,
            {optional_column('brand')},
            {optional_column('product_family')},
            {optional_column('model_number')},
            {optional_column('subcategory')},
            {optional_column('description')},
            {optional_column('specifications_json')},
            {optional_column('search_keywords')}
        FROM products
        WHERE 1 = 1
    """
    parameters: list[Any] = []

    # Do not filter categories with a raw SQL equality check. Catalogue data may
    # use labels such as "Laptop", "Laptops", or "Gaming Laptops". The requested
    # and stored categories are normalized consistently later in Python.

    if max_price_aed is not None and max_price_aed >= 0:
        sql += " AND price_aed <= ?"
        parameters.append(float(max_price_aed))

    if in_stock_only:
        sql += " AND in_stock = 1"

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(sql, parameters).fetchall()


def search_catalogue_for_candidates(
    *,
    candidate_products: list[dict[str, Any]],
    category: str | None,
    max_price_aed: float | None,
    requirement_terms: list[str],
    user_query: str = "",
    desired_results: int = 4,
    result_limit: int = 24,
    in_stock_only: bool = True,
) -> list[dict[str, Any]]:
    """
    Search the catalogue using both researched product names and broad requirements.

    The candidate list comes from the model's web research. The requirement search
    prevents the web shortlist from hiding a suitable product that happens to be less
    prominent online but is present in the store catalogue.
    """
    rows = _fetch_catalogue_rows(
        category=category,
        max_price_aed=max_price_aed,
        in_stock_only=in_stock_only,
    )

    prepared_candidates: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidate_products):
        name = str(candidate.get("name") or "").strip()
        if not name:
            continue
        prepared_candidates.append(
            {
                "name": name,
                "brand": str(candidate.get("brand") or "").strip(),
                "model_number": str(candidate.get("model_number") or "").strip(),
                "rank": int(candidate.get("rank") or index + 1),
                "why_fit": str(candidate.get("why_fit") or "").strip(),
            }
        )

    scored_products: list[dict[str, Any]] = []
    normalized_requested_category = normalize_category(category)

    for row in rows:
        product_name = str(row["name"])
        product_category = str(row["category"] or "")
        product_brand = str(row["brand"] or "")
        product_family = str(row["product_family"] or "")
        product_model_number = str(row["model_number"] or "")
        normalized_product_category = normalize_category(product_category)
        obvious_name_category = infer_obvious_category_from_name(product_name)

        # Category is a hard requirement once it is known. First reject an
        # obvious name-level contradiction even if the database category column
        # is wrong (for example iPhone labelled as a laptop).
        if (
            normalized_requested_category
            and obvious_name_category
            and obvious_name_category != normalized_requested_category
        ):
            continue

        # Then apply the authoritative normalized database category when present. A phone must never
        # appear in laptop results merely because both names contain a number.
        if (
            normalized_requested_category
            and normalized_product_category != normalized_requested_category
        ):
            continue

        exact_identity_ok, exact_identity_reason = (
            _explicit_identity_constraint(
                user_query=user_query,
                product_name=product_name,
                brand=product_brand,
                product_family=product_family,
                model_number=product_model_number,
                specifications_text=str(
                    row["specifications_json"] or ""
                ),
            )
        )

        if not exact_identity_ok:
            # Neither a researched web candidate nor a broad family match
            # may override the customer's exact generation or model.
            continue

        explicit_query_match, explicit_query_score, explicit_query_reason = (
            _query_identity_match(
                user_query=user_query,
                product_name=product_name,
                brand=product_brand,
                product_family=product_family,
                model_number=product_model_number,
            )
        )

        best_candidate: dict[str, Any] | None = None
        best_candidate_score = 0.0

        for candidate in prepared_candidates:
            candidate_identity = " ".join(
                part
                for part in (
                    candidate["brand"],
                    candidate["name"],
                    candidate["model_number"],
                )
                if part
            )
            similarity = _candidate_similarity(
                candidate_identity,
                product_name,
                candidate["brand"],
            )
            rank_bonus = max(0.0, 0.08 - (candidate["rank"] - 1) * 0.002)
            weighted_similarity = min(1.0, similarity + rank_bonus)

            if weighted_similarity > best_candidate_score:
                best_candidate_score = weighted_similarity
                best_candidate = candidate

        product_search_text = " ".join(
            part
            for part in (
                product_name,
                product_category,
                str(row["subcategory"] or ""),
                str(row["description"] or ""),
                _flatten_specifications_for_search(
                    str(row["specifications_json"] or "{}")
                ),
                str(row["search_keywords"] or ""),
            )
            if part
        )

        requirements_score = _requirements_similarity(
            product_search_text,
            product_category,
            requirement_terms,
        )

        category_match = bool(
            normalized_requested_category
            and normalized_product_category == normalized_requested_category
        )

        # A category match alone is not evidence that a product fits the use case.
        # Candidate identity is the primary signal. Requirement-only matching is
        # retained for richer catalogue names, but requires substantial overlap.
        catalogue_wide_score = 0.12 if category_match else 0.0
        final_score = max(
            best_candidate_score,
            explicit_query_score,
            0.76 * requirements_score + catalogue_wide_score,
        )

        if best_candidate_score >= 0.82:
            match_type = "strong_candidate_match"
        elif explicit_query_match:
            match_type = "explicit_query_match"
        elif best_candidate_score >= 0.68:
            match_type = "possible_candidate_match"
        else:
            match_type = "catalogue_requirement_match"

        should_include = (
            explicit_query_match
            or best_candidate_score >= 0.58
            or (category_match and requirements_score >= 0.60)
        )

        if not should_include:
            continue

        scored_products.append(
            {
                "catalogue_id": str(row["catalogue_id"]),
                "name": product_name,
                "price_aed": float(row["price_aed"]),
                "in_stock": bool(row["in_stock"]),
                "url": str(row["url"] or ""),
                "category": product_category,
                "subcategory": str(row["subcategory"] or ""),
                "brand": product_brand,
                "product_family": product_family,
                "model_number": product_model_number,
                "description": str(row["description"] or ""),
                "specifications_json": str(row["specifications_json"] or "{}"),
                "search_keywords": str(row["search_keywords"] or ""),
                "match_type": match_type,
                "match_score": round(final_score, 4),
                "matched_candidate": (
                    best_candidate["name"]
                    if best_candidate and best_candidate_score >= 0.68
                    else None
                ),
                "candidate_reason": (
                    explicit_query_reason
                    if explicit_query_match
                    else (
                        best_candidate["why_fit"]
                        if best_candidate and best_candidate_score >= 0.68
                        else ""
                    )
                ),
            }
        )

    scored_products.sort(
        key=lambda product: (
            -product["match_score"],
            not product["in_stock"],
            product["price_aed"],
        )
    )

    deduplicated: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for product in scored_products:
        key = (product["url"] or product["name"]).strip().lower()
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        deduplicated.append(product)
        if len(deduplicated) >= max(desired_results, result_limit):
            break

    return deduplicated


def search_store_inventory(
    query: str,
    min_match_ratio: float = 0.5,
) -> list[dict[str, Any]]:
    """Backward-compatible wrapper for older code and simple direct tests."""
    category = extract_category_from_query(query)
    max_price = extract_max_price(query)

    matches = search_catalogue_for_candidates(
        candidate_products=[
            {
                "name": query,
                "brand": "",
                "model_number": "",
                "rank": 1,
                "why_fit": "Direct catalogue query",
            }
        ],
        category=category,
        max_price_aed=max_price,
        requirement_terms=[query],
        user_query=query,
        desired_results=10,
        result_limit=40,
        in_stock_only=False,
    )

    return [
        product
        for product in matches
        if product["match_score"] >= min_match_ratio
        or product["match_type"] == "catalogue_requirement_match"
    ]