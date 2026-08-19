from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().with_name("store_test.db")


def create_product(
    *,
    sku: str,
    name: str,
    brand: str,
    product_family: str,
    model_number: str,
    price_aed: float,
    in_stock: bool,
    url: str,
    category: str,
    subcategory: str,
    description: str,
    specifications: dict[str, Any] | None = None,
    search_keywords: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build one product record in a consistent format.

    The specifications in this test database are sample data for development.
    Replace them with exact information from your real catalogue before using
    the database in production.
    """
    return {
        "sku": sku.strip(),
        "name": name.strip(),
        "brand": brand.strip(),
        "product_family": product_family.strip(),
        "model_number": model_number.strip(),
        "price_aed": float(price_aed),
        "in_stock": 1 if in_stock else 0,
        "url": url.strip(),
        "category": category.strip().lower(),
        "subcategory": subcategory.strip().lower(),
        "description": description.strip(),
        "specifications_json": json.dumps(
            specifications or {},
            ensure_ascii=False,
            sort_keys=True,
        ),
        "search_keywords": " ".join(search_keywords or []).strip().lower(),
    }


def create_test_database() -> None:
    """
    Recreate store_test.db with structured sample products.

    WARNING:
    This deletes the existing `products` table every time it runs.
    Use this only for a development or test database.
    """
    connection = sqlite3.connect(DB_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute("DROP TABLE IF EXISTS products")

        cursor.execute(
            """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                brand TEXT NOT NULL,
                product_family TEXT NOT NULL DEFAULT '',
                model_number TEXT NOT NULL DEFAULT '',

                price_aed REAL NOT NULL
                    CHECK (price_aed >= 0),

                in_stock INTEGER NOT NULL
                    CHECK (in_stock IN (0, 1)),

                url TEXT NOT NULL UNIQUE,

                category TEXT NOT NULL,
                subcategory TEXT NOT NULL DEFAULT '',

                description TEXT NOT NULL DEFAULT '',
                specifications_json TEXT NOT NULL DEFAULT '{}',
                search_keywords TEXT NOT NULL DEFAULT ''
            )
            """
        )

        sample_products = [
            # -----------------------------------------------------------------
            # Earbuds and headphones
            # -----------------------------------------------------------------
            create_product(
                sku="EAR-ANK-P40I-001",
                name="Soundcore P40i Wireless Earbuds",
                brand="Soundcore",
                product_family="P40i",
                model_number="P40i",
                price_aed=199.00,
                in_stock=True,
                url="https://yourstore.ae/products/soundcore-p40i",
                category="earbuds",
                subcategory="true-wireless-earbuds",
                description=(
                    "True-wireless earbuds intended for commuting, calls, "
                    "music, and everyday portable listening."
                ),
                specifications={
                    "form_factor": "true wireless",
                    "connection": "Bluetooth",
                    "active_noise_cancellation": True,
                },
                search_keywords=[
                    "wireless earbuds",
                    "commuting",
                    "calls",
                    "bluetooth",
                    "noise cancelling",
                ],
            ),
            create_product(
                sku="EAR-JBL-VBEAM-001",
                name="JBL Vibe Beam Wireless Earbuds",
                brand="JBL",
                product_family="Vibe Beam",
                model_number="Vibe Beam",
                price_aed=299.95,
                in_stock=True,
                url="https://yourstore.ae/products/jbl-vibe-beam",
                category="earbuds",
                subcategory="true-wireless-earbuds",
                description=(
                    "Compact true-wireless earbuds for music, calls, commuting, "
                    "and general everyday use."
                ),
                specifications={
                    "form_factor": "true wireless",
                    "connection": "Bluetooth",
                },
                search_keywords=[
                    "wireless earbuds",
                    "commuting",
                    "calls",
                    "bluetooth",
                ],
            ),
            create_product(
                sku="HDP-SON-WH1000XM5-001",
                name="Sony WH-1000XM5 Headphones",
                brand="Sony",
                product_family="WH-1000XM5",
                model_number="WH-1000XM5",
                price_aed=1399.00,
                in_stock=True,
                url="https://yourstore.ae/products/sony-wh1000xm5",
                category="headphones",
                subcategory="wireless-over-ear-headphones",
                description=(
                    "Premium wireless over-ear headphones intended for travel, "
                    "commuting, calls, and noise-isolated listening."
                ),
                specifications={
                    "form_factor": "over ear",
                    "connection": "Bluetooth",
                    "active_noise_cancellation": True,
                },
                search_keywords=[
                    "travel headphones",
                    "commuting",
                    "over ear",
                    "noise cancelling",
                    "bluetooth",
                ],
            ),
            create_product(
                sku="EAR-APL-APP2-001",
                name="Apple AirPods Pro 2",
                brand="Apple",
                product_family="AirPods Pro",
                model_number="2nd generation",
                price_aed=999.00,
                in_stock=False,
                url="https://yourstore.ae/products/airpods-pro-2",
                category="earbuds",
                subcategory="true-wireless-earbuds",
                description=(
                    "Apple true-wireless earbuds designed for portable listening, "
                    "calls, and integration with Apple devices."
                ),
                specifications={
                    "form_factor": "true wireless",
                    "connection": "Bluetooth",
                    "active_noise_cancellation": True,
                    "ecosystem": "Apple",
                },
                search_keywords=[
                    "airpods",
                    "iphone earbuds",
                    "apple earbuds",
                    "noise cancelling",
                ],
            ),
            create_product(
                sku="HDP-ANK-Q30-001",
                name="Anker Soundcore Life Q30",
                brand="Soundcore",
                product_family="Life Q30",
                model_number="Q30",
                price_aed=349.00,
                in_stock=True,
                url="https://yourstore.ae/products/soundcore-life-q30",
                category="headphones",
                subcategory="wireless-over-ear-headphones",
                description=(
                    "Affordable wireless over-ear headphones for travel, study, "
                    "commuting, and everyday listening."
                ),
                specifications={
                    "form_factor": "over ear",
                    "connection": "Bluetooth",
                    "active_noise_cancellation": True,
                },
                search_keywords=[
                    "budget headphones",
                    "study headphones",
                    "travel",
                    "noise cancelling",
                ],
            ),

            # -----------------------------------------------------------------
            # Phones
            # -----------------------------------------------------------------
            create_product(
                sku="PHN-SAM-S24-128-001",
                name="Samsung Galaxy S24 128GB",
                brand="Samsung",
                product_family="Galaxy S24",
                model_number="S24",
                price_aed=2899.00,
                in_stock=False,
                url="https://yourstore.ae/products/galaxy-s24",
                category="phones",
                subcategory="android-phones",
                description="Samsung Android smartphone with 128GB storage.",
                specifications={
                    "storage_gb": 128,
                    "operating_system": "Android",
                    "5g": True,
                },
                search_keywords=["android phone", "samsung smartphone", "5g phone"],
            ),
            create_product(
                sku="PHN-SAM-S24U-256-001",
                name="Samsung Galaxy S24 Ultra 256GB",
                brand="Samsung",
                product_family="Galaxy S24 Ultra",
                model_number="S24 Ultra",
                price_aed=4299.00,
                in_stock=True,
                url="https://yourstore.ae/products/galaxy-s24-ultra",
                category="phones",
                subcategory="android-phones",
                description="Premium Samsung Android smartphone with 256GB storage.",
                specifications={
                    "storage_gb": 256,
                    "operating_system": "Android",
                    "5g": True,
                },
                search_keywords=[
                    "premium android phone",
                    "samsung smartphone",
                    "5g phone",
                ],
            ),
            create_product(
                sku="PHN-APL-IP15-128-001",
                name="iPhone 15 128GB",
                brand="Apple",
                product_family="iPhone 15",
                model_number="iPhone 15",
                price_aed=3299.00,
                in_stock=True,
                url="https://yourstore.ae/products/iphone-15",
                category="phones",
                subcategory="ios-phones",
                description="Apple smartphone with 128GB storage.",
                specifications={
                    "storage_gb": 128,
                    "operating_system": "iOS",
                    "5g": True,
                },
                search_keywords=["iphone", "apple phone", "ios phone", "5g phone"],
            ),
            create_product(
                sku="PHN-GOO-PIX9-001",
                name="Google Pixel 9",
                brand="Google",
                product_family="Pixel 9",
                model_number="Pixel 9",
                price_aed=2799.00,
                in_stock=False,
                url="https://yourstore.ae/products/pixel-9",
                category="phones",
                subcategory="android-phones",
                description="Google Android smartphone from the Pixel 9 family.",
                specifications={
                    "operating_system": "Android",
                    "5g": True,
                },
                search_keywords=["google phone", "pixel phone", "android phone"],
            ),
            create_product(
                sku="PHN-HON-6005G-001",
                name="HONOR 600 5G",
                brand="HONOR",
                product_family="HONOR 600",
                model_number="600 5G",
                price_aed=1599.00,
                in_stock=True,
                url="https://yourstore.ae/products/honor-600-5g",
                category="phones",
                subcategory="android-phones",
                description="HONOR Android smartphone with 5G connectivity.",
                specifications={
                    "operating_system": "Android",
                    "5g": True,
                },
                search_keywords=["honor phone", "android phone", "5g phone"],
            ),
            create_product(
                sku="PHN-ONE-11-5G-001",
                name="OnePlus 11 5G",
                brand="OnePlus",
                product_family="OnePlus 11",
                model_number="11 5G",
                price_aed=1299.00,
                in_stock=True,
                url="https://yourstore.ae/products/oneplus-11-5g",
                category="phones",
                subcategory="android-phones",
                description="OnePlus Android smartphone with 5G connectivity.",
                specifications={
                    "operating_system": "Android",
                    "5g": True,
                },
                search_keywords=["oneplus phone", "android phone", "5g phone"],
            ),
            create_product(
                sku="PHN-HUA-NOVA15MAX-001",
                name="HUAWEI nova 15 Max",
                brand="HUAWEI",
                product_family="nova 15 Max",
                model_number="nova 15 Max",
                price_aed=1199.00,
                in_stock=True,
                url="https://yourstore.ae/products/huawei-nova-15-max",
                category="phones",
                subcategory="smartphones",
                description="HUAWEI smartphone from the nova family.",
                specifications={
                    "device_type": "smartphone",
                },
                search_keywords=["huawei phone", "nova phone", "smartphone"],
            ),

            # -----------------------------------------------------------------
            # General and student laptops
            # -----------------------------------------------------------------
            create_product(
                sku="LAP-FRW-L12DIY-001",
                name="Framework Laptop 12 DIY Edition",
                brand="Framework",
                product_family="Laptop 12",
                model_number="DIY Edition",
                price_aed=2015.00,
                in_stock=True,
                url="https://yourstore.ae/products/framework-laptop-12",
                category="laptops",
                subcategory="student-laptops",
                description=(
                    "Repairable and configurable laptop intended for study, "
                    "productivity, and general everyday computing."
                ),
                specifications={
                    "device_type": "laptop",
                    "intended_use": [
                        "school",
                        "productivity",
                        "general computing",
                    ],
                    "dedicated_gpu": False,
                },
                search_keywords=[
                    "student laptop",
                    "school laptop",
                    "repairable laptop",
                    "productivity",
                ],
            ),
            create_product(
                sku="LAP-DEL-XPS13-001",
                name="Dell XPS 13",
                brand="Dell",
                product_family="XPS 13",
                model_number="XPS 13",
                price_aed=4599.00,
                in_stock=True,
                url="https://yourstore.ae/products/dell-xps-13",
                category="laptops",
                subcategory="ultrabooks",
                description=(
                    "Compact premium Windows laptop intended for productivity, "
                    "study, travel, and everyday work."
                ),
                specifications={
                    "device_type": "laptop",
                    "screen_size_class": "13-inch",
                    "operating_system": "Windows",
                    "dedicated_gpu": False,
                    "intended_use": [
                        "productivity",
                        "study",
                        "travel",
                    ],
                },
                search_keywords=[
                    "ultrabook",
                    "portable laptop",
                    "student laptop",
                    "business laptop",
                ],
            ),
            create_product(
                sku="LAP-LEN-IPSLIM3-001",
                name="Lenovo IdeaPad Slim 3",
                brand="Lenovo",
                product_family="IdeaPad Slim 3",
                model_number="IdeaPad Slim 3",
                price_aed=1899.00,
                in_stock=True,
                url="https://yourstore.ae/products/lenovo-ideapad-slim-3",
                category="laptops",
                subcategory="student-laptops",
                description=(
                    "Affordable Windows laptop intended for schoolwork, documents, "
                    "presentations, browser research, video calls, and general use."
                ),
                specifications={
                    "device_type": "laptop",
                    "operating_system": "Windows",
                    "dedicated_gpu": False,
                    "intended_use": [
                        "school",
                        "productivity",
                        "general computing",
                    ],
                },
                search_keywords=[
                    "student laptop",
                    "school laptop",
                    "budget laptop",
                    "windows laptop",
                    "productivity",
                ],
            ),
            create_product(
                sku="LAP-APL-MBA-M3-13-001",
                name="MacBook Air M3 13-inch",
                brand="Apple",
                product_family="MacBook Air",
                model_number="M3 13-inch",
                price_aed=4799.00,
                in_stock=True,
                url="https://yourstore.ae/products/macbook-air-m3",
                category="laptops",
                subcategory="ultrabooks",
                description=(
                    "Portable Apple laptop intended for school, university, "
                    "productivity, travel, and general creative work."
                ),
                specifications={
                    "device_type": "laptop",
                    "processor_family": "Apple M3",
                    "screen_size_class": "13-inch",
                    "operating_system": "macOS",
                    "dedicated_gpu": False,
                    "intended_use": [
                        "school",
                        "university",
                        "productivity",
                        "light creative work",
                    ],
                },
                search_keywords=[
                    "mac laptop",
                    "macbook",
                    "student laptop",
                    "portable laptop",
                ],
            ),

            # -----------------------------------------------------------------
            # Gaming laptops
            # These are included so gaming-laptop queries have valid local data.
            # -----------------------------------------------------------------
            create_product(
                sku="LAP-ASU-TUFA15-001",
                name="ASUS TUF Gaming A15",
                brand="ASUS",
                product_family="TUF Gaming A15",
                model_number="FA507NV",
                price_aed=4499.00,
                in_stock=True,
                url="https://yourstore.ae/products/asus-tuf-gaming-a15",
                category="laptops",
                subcategory="gaming-laptops",
                description=(
                    "15.6-inch Windows gaming laptop with a dedicated NVIDIA GPU, "
                    "high-refresh display, and upgrade-friendly gaming design."
                ),
                specifications={
                    "device_type": "laptop",
                    "processor": "AMD Ryzen 7 7735HS",
                    "ram_gb": 16,
                    "storage_gb": 512,
                    "storage_type": "SSD",
                    "gpu": "NVIDIA GeForce RTX 4060",
                    "dedicated_gpu": True,
                    "screen_inches": 15.6,
                    "refresh_rate_hz": 144,
                    "operating_system": "Windows 11",
                    "intended_use": [
                        "gaming",
                        "school",
                        "content creation",
                        "university engineering",
                        "CAD",
                        "3D modelling",
                    ],
                    "test_configuration": True,
                },
                search_keywords=[
                    "gaming laptop",
                    "rtx 4060 laptop",
                    "asus gaming",
                    "high refresh rate",
                    "engineering student laptop",
                    "university engineering laptop",
                    "CAD laptop",
                ],
            ),
            create_product(
                sku="LAP-LEN-LEGION5-001",
                name="Lenovo Legion 5",
                brand="Lenovo",
                product_family="Legion 5",
                model_number="16IRX9",
                price_aed=5799.00,
                in_stock=True,
                url="https://yourstore.ae/products/lenovo-legion-5",
                category="laptops",
                subcategory="gaming-laptops",
                description=(
                    "16-inch Windows gaming laptop with a dedicated NVIDIA GPU, "
                    "high-refresh display, and strong gaming-oriented cooling."
                ),
                specifications={
                    "device_type": "laptop",
                    "processor": "Intel Core i7-14650HX",
                    "ram_gb": 16,
                    "storage_gb": 1000,
                    "storage_type": "SSD",
                    "gpu": "NVIDIA GeForce RTX 4060",
                    "dedicated_gpu": True,
                    "screen_inches": 16.0,
                    "refresh_rate_hz": 165,
                    "operating_system": "Windows 11",
                    "intended_use": [
                        "gaming",
                        "content creation",
                        "productivity",
                        "university engineering",
                        "CAD",
                        "3D modelling",
                    ],
                    "test_configuration": True,
                },
                search_keywords=[
                    "gaming laptop",
                    "rtx 4060 laptop",
                    "lenovo legion",
                    "high refresh rate",
                    "engineering student laptop",
                    "university engineering laptop",
                    "CAD laptop",
                ],
            ),

            # -----------------------------------------------------------------
            # TVs and monitors
            # -----------------------------------------------------------------
            create_product(
                sku="TV-TCL-65C645-001",
                name="TCL 65-Inch 4K QLED Smart TV",
                brand="TCL",
                product_family="65-Inch 4K QLED Smart TV",
                model_number="65C645",
                price_aed=1869.00,
                in_stock=True,
                url="https://yourstore.ae/products/tcl-65c645",
                category="tvs",
                subcategory="qled-tvs",
                description="Large 65-inch 4K QLED smart television.",
                specifications={
                    "screen_inches": 65,
                    "resolution": "4K",
                    "display_type": "QLED",
                    "smart_tv": True,
                },
                search_keywords=["65 inch tv", "4k tv", "qled tv", "smart tv"],
            ),
            create_product(
                sku="TV-SAM-65CUHD-001",
                name="Samsung 65-Inch Crystal UHD TV",
                brand="Samsung",
                product_family="Crystal UHD TV",
                model_number="65-inch",
                price_aed=1746.00,
                in_stock=True,
                url="https://yourstore.ae/products/samsung-65-crystal",
                category="tvs",
                subcategory="4k-tvs",
                description="Large 65-inch Samsung Crystal UHD television.",
                specifications={
                    "screen_inches": 65,
                    "resolution": "4K",
                    "display_type": "LED",
                    "smart_tv": True,
                },
                search_keywords=["65 inch tv", "4k tv", "samsung tv", "smart tv"],
            ),
            create_product(
                sku="MON-LG-27-4K-001",
                name="LG 27-Inch 4K Monitor",
                brand="LG",
                product_family="27-Inch 4K Monitor",
                model_number="27-inch 4K",
                price_aed=1099.00,
                in_stock=True,
                url="https://yourstore.ae/products/lg-27-4k-monitor",
                category="monitors",
                subcategory="4k-monitors",
                description=(
                    "27-inch 4K external monitor for productivity and detailed visual work. "
                    "Compatible with MacBook Air through a USB-C to HDMI adapter."
                ),
                specifications={
                    "screen_inches": 27,
                    "resolution": "4K",
                    "video_inputs": [
                        "HDMI",
                        "DisplayPort",
                    ],
                    "usb_c_video_input": False,
                    "macbook_air_compatibility": (
                        "USB-C to HDMI adapter required"
                    ),
                },
                search_keywords=[
                    "27 inch monitor",
                    "4k monitor",
                    "productivity monitor",
                    "external monitor for macbook air",
                    "mac compatible monitor",
                ],
            ),
            create_product(
                sku="MON-DEL-24-FHD-001",
                name="Dell 24-Inch FHD Monitor",
                brand="Dell",
                product_family="24-Inch FHD Monitor",
                model_number="24-inch FHD",
                price_aed=449.00,
                in_stock=False,
                url="https://yourstore.ae/products/dell-24-fhd-monitor",
                category="monitors",
                subcategory="full-hd-monitors",
                description="Affordable 24-inch Full HD monitor for everyday use.",
                specifications={
                    "screen_inches": 24,
                    "resolution": "Full HD",
                },
                search_keywords=["24 inch monitor", "full hd monitor", "budget monitor"],
            ),

            # -----------------------------------------------------------------
            # Gaming accessories and consoles
            # -----------------------------------------------------------------
            create_product(
                sku="GMS-LOG-GPROX-001",
                name="Logitech G Pro X Gaming Mouse",
                brand="Logitech",
                product_family="G Pro X",
                model_number="G Pro X",
                price_aed=349.00,
                in_stock=True,
                url="https://yourstore.ae/products/logitech-gpro-x",
                category="gaming-mice",
                subcategory="wireless-gaming-mice",
                description="Gaming mouse intended for competitive PC gaming.",
                specifications={
                    "device_type": "mouse",
                    "intended_use": "gaming",
                },
                search_keywords=["gaming mouse", "pc gaming", "logitech mouse"],
            ),
            create_product(
                sku="GKB-RAZ-BWV4-001",
                name="Razer BlackWidow V4 Keyboard",
                brand="Razer",
                product_family="BlackWidow V4",
                model_number="BlackWidow V4",
                price_aed=599.00,
                in_stock=True,
                url="https://yourstore.ae/products/razer-blackwidow-v4",
                category="gaming-keyboards",
                subcategory="mechanical-gaming-keyboards",
                description="Mechanical gaming keyboard intended for PC gaming.",
                specifications={
                    "device_type": "keyboard",
                    "intended_use": "gaming",
                },
                search_keywords=["gaming keyboard", "mechanical keyboard", "razer keyboard"],
            ),
            create_product(
                sku="CON-SON-PS5SLIM-001",
                name="PlayStation 5 Slim",
                brand="Sony",
                product_family="PlayStation 5 Slim",
                model_number="PS5 Slim",
                price_aed=1899.00,
                in_stock=False,
                url="https://yourstore.ae/products/ps5-slim",
                category="game-consoles",
                subcategory="home-game-consoles",
                description="Sony home gaming console.",
                specifications={
                    "device_type": "game console",
                    "platform": "PlayStation 5",
                },
                search_keywords=["playstation", "ps5", "gaming console"],
            ),

            # -----------------------------------------------------------------
            # Chargers and cables
            # -----------------------------------------------------------------
            create_product(
                sku="CHG-ANK-65WGAN-001",
                name="Anker 65W GaN Charger",
                brand="Anker",
                product_family="65W GaN Charger",
                model_number="65W GaN",
                price_aed=149.00,
                in_stock=True,
                url="https://yourstore.ae/products/anker-65w-gan",
                category="chargers",
                subcategory="usb-c-chargers",
                description="Compact 65W GaN wall charger for compatible USB-C devices.",
                specifications={
                    "maximum_power_w": 65,
                    "connector": "USB-C",
                    "charger_technology": "GaN",
                },
                search_keywords=["65w charger", "usb c charger", "gan charger", "laptop charger"],
            ),
            create_product(
                sku="CHG-APL-20WUSBC-001",
                name="Apple 20W USB-C Power Adapter",
                brand="Apple",
                product_family="20W USB-C Power Adapter",
                model_number="20W USB-C",
                price_aed=99.00,
                in_stock=True,
                url="https://yourstore.ae/products/apple-20w-adapter",
                category="chargers",
                subcategory="usb-c-chargers",
                description="Apple 20W USB-C wall power adapter.",
                specifications={
                    "maximum_power_w": 20,
                    "connector": "USB-C",
                },
                search_keywords=["apple charger", "20w charger", "usb c charger"],
            ),
            create_product(
                sku="CBL-GEN-USBC-LTG-1M-001",
                name="USB-C to Lightning Cable 1m",
                brand="Generic",
                product_family="USB-C to Lightning Cable",
                model_number="1m",
                price_aed=79.00,
                in_stock=True,
                url="https://yourstore.ae/products/usbc-lightning-cable",
                category="cables",
                subcategory="charging-cables",
                description="One-metre USB-C to Lightning charging and data cable.",
                specifications={
                    "connector_a": "USB-C",
                    "connector_b": "Lightning",
                    "length_m": 1,
                },
                search_keywords=["iphone cable", "lightning cable", "usb c cable"],
            ),
            create_product(
                sku="CBL-ANK-PWR-USBC-2M-001",
                name="Anker PowerLine USB-C Cable 2m",
                brand="Anker",
                product_family="PowerLine USB-C Cable",
                model_number="2m",
                price_aed=59.00,
                in_stock=False,
                url="https://yourstore.ae/products/anker-powerline-usbc",
                category="cables",
                subcategory="usb-c-cables",
                description="Two-metre Anker USB-C cable for compatible devices.",
                specifications={
                    "connector_a": "USB-C",
                    "connector_b": "USB-C",
                    "length_m": 2,
                },
                search_keywords=["usb c cable", "2m cable", "anker cable"],
            ),

            # -----------------------------------------------------------------
            # Smart home
            # -----------------------------------------------------------------
            create_product(
                sku="SMH-AMZ-ECHODOT5-001",
                name="Amazon Echo Dot (5th Gen)",
                brand="Amazon",
                product_family="Echo Dot",
                model_number="5th Gen",
                price_aed=199.00,
                in_stock=True,
                url="https://yourstore.ae/products/echo-dot-5",
                category="smart-home",
                subcategory="smart-speakers",
                description="Compact Alexa-enabled smart speaker.",
                specifications={
                    "device_type": "smart speaker",
                    "voice_assistant": "Alexa",
                    "generation": 5,
                },
                search_keywords=["smart speaker", "alexa", "echo dot"],
            ),
            create_product(
                sku="SMH-TPL-TAPOPLUG-001",
                name="TP-Link Tapo Smart Plug",
                brand="TP-Link",
                product_family="Tapo Smart Plug",
                model_number="Tapo",
                price_aed=49.00,
                in_stock=True,
                url="https://yourstore.ae/products/tapo-smart-plug",
                category="smart-home",
                subcategory="smart-plugs",
                description="App-controlled smart plug for compatible household devices.",
                specifications={
                    "device_type": "smart plug",
                    "wireless": "Wi-Fi",
                },
                search_keywords=["smart plug", "wifi plug", "tapo", "smart home"],
            ),
            # -----------------------------------------------------------------
            # Operating systems and software
            # -----------------------------------------------------------------
            create_product(
                sku="SFT-MSF-W11HOME-001",
                name="Microsoft Windows 11 Home Retail License",
                brand="Microsoft",
                product_family="Windows 11",
                model_number="Windows 11 Home",
                price_aed=599.00,
                in_stock=True,
                url="https://yourstore.ae/products/windows-11-home",
                category="software",
                subcategory="operating-systems",
                description=(
                    "Microsoft Windows 11 Home retail operating-system "
                    "licence for one compatible PC."
                ),
                specifications={
                    "product_type": "operating system",
                    "version": "Windows 11",
                    "edition": "Home",
                    "license_type": "Retail",
                    "device_count": 1,
                    "delivery_method": "Digital",
                    "architecture": "64-bit",
                    "transferable": True,
                    "test_configuration": True,
                },
                search_keywords=[
                    "windows 11",
                    "windows 11 home",
                    "windows license",
                    "windows licence",
                    "operating system",
                    "pc software",
                ],
            ),
            create_product(
                sku="SFT-MSF-W11PRO-001",
                name="Microsoft Windows 11 Pro Retail License",
                brand="Microsoft",
                product_family="Windows 11",
                model_number="Windows 11 Pro",
                price_aed=999.00,
                in_stock=True,
                url="https://yourstore.ae/products/windows-11-pro",
                category="software",
                subcategory="operating-systems",
                description=(
                    "Microsoft Windows 11 Pro retail operating-system "
                    "licence for one compatible PC."
                ),
                specifications={
                    "product_type": "operating system",
                    "version": "Windows 11",
                    "edition": "Pro",
                    "license_type": "Retail",
                    "device_count": 1,
                    "delivery_method": "Digital",
                    "architecture": "64-bit",
                    "transferable": True,
                    "test_configuration": True,
                },
                search_keywords=[
                    "windows 11",
                    "windows 11 pro",
                    "windows pro license",
                    "windows pro licence",
                    "operating system",
                    "business pc software",
                ],
            ),
        ]

        insert_sql = """
            INSERT INTO products (
                sku,
                name,
                brand,
                product_family,
                model_number,
                price_aed,
                in_stock,
                url,
                category,
                subcategory,
                description,
                specifications_json,
                search_keywords
            )
            VALUES (
                :sku,
                :name,
                :brand,
                :product_family,
                :model_number,
                :price_aed,
                :in_stock,
                :url,
                :category,
                :subcategory,
                :description,
                :specifications_json,
                :search_keywords
            )
        """

        cursor.executemany(insert_sql, sample_products)

        # Indexes make common catalogue filters faster when the database grows.
        cursor.execute(
            """
            CREATE INDEX idx_products_category
            ON products(category)
            """
        )
        cursor.execute(
            """
            CREATE INDEX idx_products_subcategory
            ON products(subcategory)
            """
        )
        cursor.execute(
            """
            CREATE INDEX idx_products_in_stock
            ON products(in_stock)
            """
        )
        cursor.execute(
            """
            CREATE INDEX idx_products_brand
            ON products(brand)
            """
        )
        cursor.execute(
            """
            CREATE INDEX idx_products_model_number
            ON products(model_number)
            """
        )
        cursor.execute(
            """
            CREATE INDEX idx_products_category_stock
            ON products(category, in_stock)
            """
        )

        connection.commit()

        category_count = len(
            {product["category"] for product in sample_products}
        )

        print(
            f"Test database created at: {DB_PATH}\n"
            f"Products inserted: {len(sample_products)}\n"
            f"Categories: {category_count}"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    create_test_database()