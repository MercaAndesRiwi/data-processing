"""Seeded master catalog: products, sellers and stores share one ID space.

Replaces the missing Excel workbook dependency. POS (F2), inventory (F3)
and marketplace events (F4) must import from here so they all use the
same SKU, store and seller IDs (acceptance criterion 1).

Determinism contract: same (seed, per_category) always builds the same
catalog. Callers create their own ``random.Random(f"{seed}-...")`` for
row generation so streams do not interfere with each other.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from src.common.config import (
    CATALOG_ACTIVE_RATE,
    CATALOG_PER_CATEGORY,
    COUNTRIES,
    MASTER_SEED,
)

# 71 reference categories. Kept as a constant so the default build is
# 71 x 15 = 1065 products, the same scale as the reference workbook.
CATEGORIES: tuple[str, ...] = (
    "health_beauty",
    "computers_accessories",
    "auto",
    "bed_bath_table",
    "furniture_decor",
    "sports_leisure",
    "perfumery",
    "housewares",
    "telephony",
    "watches_gifts",
    "food_drink",
    "baby",
    "stationery",
    "tablets_printing_image",
    "toys",
    "fixed_telephony",
    "garden_tools",
    "fashion_bags_accessories",
    "small_appliances",
    "consoles_games",
    "audio",
    "fashion_shoes",
    "cool_stuff",
    "luggage_accessories",
    "air_conditioning",
    "construction_tools_construction",
    "kitchen_dining_laundry_garden_furniture",
    "costruction_tools_garden",
    "fashion_male_clothing",
    "pet_shop",
    "office_furniture",
    "market_place",
    "electronics",
    "home_appliances",
    "party_supplies",
    "home_confort",
    "costruction_tools_tools",
    "agro_industry_and_commerce",
    "furniture_mattress_and_upholstery",
    "books_technical",
    "home_construction",
    "musical_instruments",
    "furniture_living_room",
    "construction_tools_lights",
    "industry_commerce_and_business",
    "food",
    "art",
    "furniture_bedroom",
    "books_general_interest",
    "construction_tools_safety",
    "fashion_underwear_beach",
    "fashion_sport",
    "signaling_and_security",
    "computers",
    "christmas_supplies",
    "fashio_female_clothing",
    "home_appliances_2",
    "books_imported",
    "drinks",
    "cine_photo",
    "la_cuisine",
    "music",
    "home_comfort_2",
    "small_appliances_home_oven_and_coffee",
    "cds_dvds_musicals",
    "dvds_blu_ray",
    "flowers",
    "arts_and_craftsmanship",
    "diapers_and_hygiene",
    "fashion_childrens_clothes",
    "security_and_services",
)

# 7 propio sellers: one physical owner per country plus central
# e-commerce and marketplace operators.
PROPIO_SELLERS: tuple[tuple[str, str], ...] = (
    ("SEL-PRV-001", "MercaAndes Retail Colombia"),
    ("SEL-PRV-002", "MercaAndes Retail Peru"),
    ("SEL-PRV-003", "MercaAndes Retail Ecuador"),
    ("SEL-PRV-004", "MercaAndes Retail Bolivia"),
    ("SEL-PRV-005", "MercaAndes Retail Chile"),
    ("SEL-PRV-006", "MercaAndes E-commerce Central"),
    ("SEL-PRV-007", "MercaAndes Marketplace Operator"),
)

THIRD_PARTY_NAMES: tuple[str, ...] = (
    "AndesMarket Global",
    "Inversiones del Pacifico",
    "Distribuidora Andina",
    "Comercializadora Rionegro",
    "Tecnologia y Retail del Sur",
    "Global Trade Andina",
    "Importaciones Bolivar",
    "E-Commerce Solutions",
    "Ventas y Soluciones Andinas",
    "Multiservicios del Valle",
    "Innova Retail Partners",
    "Andes Digital Hub",
    "Comercio Express Latam",
    "Alpha Trading Co",
    "NovaMarket",
    "Comercializadora Austral",
    "Importadora Los Andes",
    "Soluciones del Norte",
    "Nexus Retail Group",
    "Tienda Virtual Cordillera",
    "Inversiones Comerciales Andinas",
    "MegaStore Express",
    "Boutique de Oportunidades",
    "Distribuciones Exclusivas",
    "Pacific Trading Corp",
    "Comercial Andina del Norte",
    "Marketplace Express CO",
    "Soluciones Integrales del Peru",
)


def category_code(category: str) -> str:
    """Return a 6-letter ASCII code for a category name."""
    letters = re.sub(r"[^A-Z]", "", category.upper())
    return (letters[:6] or "XXXXXX").ljust(6, "X")


@dataclass(frozen=True)
class Seller:
    seller_id: str
    name: str
    seller_type: str  # "propio" | "third_party"


@dataclass(frozen=True)
class Store:
    store_id: str
    name: str
    country: str
    channel: str
    seller_id: str


@dataclass(frozen=True)
class Product:
    sku: str
    name: str
    category: str
    country: str
    seller_id: str
    base_price_usd: float
    cost_usd: float
    stock_total: int
    status: str  # "Activo" | "Inactivo"


@dataclass
class MasterCatalog:
    """Immutable ID space shared by POS, inventory and events."""

    seed: int
    sellers: tuple[Seller, ...]
    stores: tuple[Store, ...]
    products: tuple[Product, ...]
    sellers_by_id: dict[str, Seller] = field(default_factory=dict)
    stores_by_id: dict[str, Store] = field(default_factory=dict)
    products_by_sku: dict[str, Product] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.sellers_by_id = {s.seller_id: s for s in self.sellers}
        self.stores_by_id = {s.store_id: s for s in self.stores}
        self.products_by_sku = {p.sku: p for p in self.products}

    @property
    def active_products(self) -> tuple[Product, ...]:
        """Products eligible for sale/event generation."""
        return tuple(p for p in self.products if p.status == "Activo")

    def random_product(self, rng: random.Random) -> Product:
        return rng.choice(self.active_products)

    def random_store_for_country(
        self, rng: random.Random, country: str
    ) -> Store:
        candidates = [s for s in self.stores if s.country == country]
        if not candidates:
            raise ValueError(f"No stores for country {country}.")
        return rng.choice(candidates)

    def random_seller(self, rng: random.Random) -> Seller:
        return rng.choice(self.sellers)


def _build_sellers() -> tuple[Seller, ...]:
    sellers: list[Seller] = [
        Seller(seller_id=sid, name=name, seller_type="propio")
        for sid, name in PROPIO_SELLERS
    ]
    for index, name in enumerate(THIRD_PARTY_NAMES, start=101):
        sellers.append(
            Seller(
                seller_id=f"SEL-3P-{index}",
                name=name,
                seller_type="third_party",
            )
        )
    return tuple(sellers)


def _build_stores() -> tuple[Store, ...]:
    """4 stores per country: 2 physical, 1 e-commerce, 1 marketplace."""
    country_seller = {
        "CO": "SEL-PRV-001",
        "PE": "SEL-PRV-002",
        "EC": "SEL-PRV-003",
        "BO": "SEL-PRV-004",
        "CL": "SEL-PRV-005",
    }
    stores: list[Store] = []
    for country in COUNTRIES:
        stores.append(
            Store(
                store_id=f"STO-{country}-FIS-001",
                name=f"MercaAndes Fisica {country} 1",
                country=country,
                channel="Tienda Fisica",
                seller_id=country_seller[country],
            )
        )
        stores.append(
            Store(
                store_id=f"STO-{country}-FIS-002",
                name=f"MercaAndes Fisica {country} 2",
                country=country,
                channel="Tienda Fisica",
                seller_id=country_seller[country],
            )
        )
        stores.append(
            Store(
                store_id=f"STO-{country}-ECOM-001",
                name=f"MercaAndes E-commerce {country}",
                country=country,
                channel="E-commerce Propio",
                seller_id="SEL-PRV-006",
            )
        )
        stores.append(
            Store(
                store_id=f"STO-{country}-MKT-001",
                name=f"MercaAndes Marketplace {country}",
                country=country,
                channel="Marketplace Propietario",
                seller_id="SEL-PRV-007",
            )
        )
    return tuple(stores)


def build_master_catalog(
    seed: int = MASTER_SEED,
    per_category: int = CATALOG_PER_CATEGORY,
    active_rate: float = CATALOG_ACTIVE_RATE,
) -> MasterCatalog:
    """Build the full catalog deterministically from a seed."""
    if per_category <= 0:
        raise ValueError("per_category must be positive.")
    if not 0 < active_rate <= 1:
        raise ValueError("active_rate must be in (0, 1].")

    rng = random.Random(seed)
    sellers = _build_sellers()
    stores = _build_stores()
    propio_ids = [s.seller_id for s in sellers if s.seller_type == "propio"]
    third_ids = [
        s.seller_id for s in sellers if s.seller_type == "third_party"
    ]
    country_codes = list(COUNTRIES)

    products: list[Product] = []
    seq = 1
    for category in CATEGORIES:
        code = category_code(category)
        for _ in range(per_category):
            country = rng.choice(country_codes)
            # ~68% propio mirrors the reference workbook mix.
            if rng.random() < 0.68:
                seller_id = rng.choice(propio_ids)
            else:
                seller_id = rng.choice(third_ids)
            base_price = round(rng.uniform(12.0, 1200.0), 2)
            margin = round(rng.uniform(0.30, 0.47), 2)
            cost = round(base_price * (1 - margin), 2)
            stock = rng.randint(10, 450)
            status = "Activo" if rng.random() < active_rate else "Inactivo"
            sku = f"SKU-{code}-{country}-{seq:05d}"
            name = (
                f"{category.replace('_', ' ').title()} "
                f"item {seq:05d} ({country})"
            )
            products.append(
                Product(
                    sku=sku,
                    name=name,
                    category=category,
                    country=country,
                    seller_id=seller_id,
                    base_price_usd=base_price,
                    cost_usd=cost,
                    stock_total=stock,
                    status=status,
                )
            )
            seq += 1

    return MasterCatalog(
        seed=seed, sellers=sellers, stores=stores, products=tuple(products)
    )
