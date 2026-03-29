# backend/conflict_engine.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Conflict:
    constraint: str        # e.g. "budget", "availability", "brand", "screen"
    severity: str          # "hard" | "soft"
    expected: str          # what the user wanted
    actual: str            # what reality says
    description: str       # human-readable


@dataclass
class ProductEvaluation:
    product: dict
    conflicts: list[Conflict]
    passes_hard_constraints: bool
    conflict_score: int    # lower = better (fewer/softer conflicts)
    match_score: float     # higher = better preference match


def parse_constraints(constraint_text: str) -> dict:
    """
    Parse natural language constraints into structured fields.
    Handles: budget ($X, max $X, under $X), availability (today, pickup, shipping)
    """
    import re
    constraints = {}

    text = constraint_text.lower()

    # Budget parsing
    budget_match = re.search(r"\$?([\d,]+)", text)
    if budget_match:
        constraints["max_budget"] = float(budget_match.group(1).replace(",", ""))

    # Availability parsing
    if any(word in text for word in ["today", "pickup", "store pickup", "same day"]):
        constraints["requires_today"] = True
    else:
        constraints["requires_today"] = False

    # Shipping tolerance
    ship_match = re.search(r"(\d+)\s*day", text)
    if ship_match:
        constraints["max_shipping_days"] = int(ship_match.group(1))

    return constraints


def parse_preferences(preference_text: str) -> dict:
    """Extract structured preferences from natural language."""
    text = preference_text.lower()
    prefs = {}

    # Brand preference
    brands = ["asus", "dell", "hp", "lenovo", "acer", "msi", "razer", "samsung", "lg", "apple"]
    for brand in brands:
        if brand in text:
            prefs["preferred_brand"] = brand
            break

    # Screen type
    if "oled" in text:
        prefs["preferred_screen"] = "oled"
    elif "ips" in text:
        prefs["preferred_screen"] = "ips"

    # Tier
    if any(w in text for w in ["high-end", "premium", "best", "top"]):
        prefs["tier"] = "high-end"
    elif any(w in text for w in ["budget", "cheap", "affordable"]):
        prefs["tier"] = "budget"
    else:
        prefs["tier"] = "mid-range"

    return prefs


def evaluate_products(
    products: list[dict],
    preferences: dict,
    constraints: dict,
) -> list[ProductEvaluation]:
    """Score each product against preferences and constraints."""
    evaluations = []

    for product in products:
        conflicts = []
        match_score = 100.0

        title_lower = product["title"].lower()
        delivery_lower = product.get("delivery", "").lower()
        avail_lower = product.get("availability", "").lower()

        # ── Hard constraint: budget ──────────────────────────────
        max_budget = constraints.get("max_budget")
        if max_budget and product["price"] > 0:
            if product["price"] > max_budget:
                over_by = product["price"] - max_budget
                conflicts.append(Conflict(
                    constraint="budget",
                    severity="hard",
                    expected=f"max ${max_budget:.0f}",
                    actual=f"${product['price']:.2f}",
                    description=f"Price is ${over_by:.0f} over your budget of ${max_budget:.0f}",
                ))
                match_score -= 40

        # ── Hard constraint: availability today ──────────────────
        requires_today = constraints.get("requires_today", False)
        if requires_today:
            is_available_today = any(
                word in delivery_lower or word in avail_lower
                for word in ["today", "pickup", "same day", "in stock"]
            )
            if not is_available_today:
                conflicts.append(Conflict(
                    constraint="availability",
                    severity="hard",
                    expected="available for pickup today",
                    actual=product.get("delivery", "shipping only"),
                    description=f"Not available for store pickup today — {product.get('delivery', 'delivery only')}",
                ))
                match_score -= 35

        # ── Soft constraint: brand preference ────────────────────
        preferred_brand = preferences.get("preferred_brand")
        if preferred_brand and preferred_brand not in title_lower:
            conflicts.append(Conflict(
                constraint="brand",
                severity="soft",
                expected=f"preferred brand: {preferred_brand.upper()}",
                actual=product["title"][:40],
                description=f"Not your preferred brand ({preferred_brand.upper()})",
            ))
            match_score -= 15

        # ── Soft constraint: screen type ─────────────────────────
        preferred_screen = preferences.get("preferred_screen")
        if preferred_screen and preferred_screen not in title_lower:
            conflicts.append(Conflict(
                constraint="screen",
                severity="soft",
                expected=f"{preferred_screen.upper()} display",
                actual="non-OLED display",
                description=f"Does not have your preferred {preferred_screen.upper()} screen",
            ))
            match_score -= 10

        # ── Rating bonus ─────────────────────────────────────────
        rating = product.get("rating", 0)
        if rating >= 4.5:
            match_score += 5

        hard_violations = [c for c in conflicts if c.severity == "hard"]

        evaluations.append(ProductEvaluation(
            product=product,
            conflicts=conflicts,
            passes_hard_constraints=len(hard_violations) == 0,
            conflict_score=len(hard_violations) * 10 + len([c for c in conflicts if c.severity == "soft"]) * 2,
            match_score=max(0, match_score),
        ))

    # Sort: passing products first, then by match score
    evaluations.sort(key=lambda e: (-int(e.passes_hard_constraints), e.conflict_score, -e.match_score))
    return evaluations
