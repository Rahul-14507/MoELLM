# backend/scraper.py

import os
import re
from typing import Any

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# ── Query type detection ───────────────────────────────────────────────────────

QUERY_PROFILES = {
    "flight": {
        "keywords": ["fly", "flight", "airline", "airport", "ticket", "hyderabad", "london",
                     "new york", "dubai", "nonstop", "non-stop", "layover", "economy", "business class"],
        "search_template": "{query} cheapest flights price",
        "include_domains": ["kayak.com", "google.com/travel", "skyscanner.com",
                            "expedia.com", "makemytrip.com", "booking.com", "momondo.com"],
        "price_label": "ticket",
        "store_label": "airline",
        "delivery_label": "departure",
    },
    "hotel": {
        "keywords": ["hotel", "stay", "room", "resort", "hostel", "airbnb", "accommodation", "check-in"],
        "search_template": "{query} price per night booking",
        "include_domains": ["booking.com", "hotels.com", "airbnb.com", "expedia.com", "trivago.com"],
        "price_label": "per night",
        "store_label": "hotel",
        "delivery_label": "check-in",
    },
    "laptop": {
        "keywords": ["laptop", "notebook", "macbook", "chromebook", "gaming laptop", "ultrabook"],
        "search_template": "{query} price buy",
        "include_domains": ["amazon.com", "bestbuy.com", "newegg.com", "walmart.com", "bhphotovideo.com"],
        "price_label": "price",
        "store_label": "store",
        "delivery_label": "delivery",
    },
    "phone": {
        "keywords": ["phone", "iphone", "samsung", "pixel", "smartphone", "android"],
        "search_template": "{query} price buy",
        "include_domains": ["amazon.com", "bestbuy.com", "walmart.com", "apple.com", "samsung.com"],
        "price_label": "price",
        "store_label": "store",
        "delivery_label": "delivery",
    },
    "generic": {
        "keywords": [],
        "search_template": "{query} price buy",
        "include_domains": ["amazon.com", "bestbuy.com", "walmart.com", "google.com/shopping"],
        "price_label": "price",
        "store_label": "store",
        "delivery_label": "delivery",
    },
}


def _detect_query_type(preference: str) -> str:
    """Detect what category the user's preference falls into."""
    text = preference.lower()
    for qtype, profile in QUERY_PROFILES.items():
        if qtype == "generic":
            continue
        if any(kw in text for kw in profile["keywords"]):
            return qtype
    return "generic"


def _build_search_query(preference: str, qtype: str) -> str:
    """Build a focused search query based on query type."""
    stopwords = {"i", "want", "a", "an", "the", "with", "and", "or",
                 "preferably", "some", "my", "but", "on", "to", "from",
                 "prefer", "would", "like", "need", "looking", "for"}
    words = preference.lower().replace(",", "").replace(".", "").split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    base = " ".join(keywords[:8])
    template = QUERY_PROFILES[qtype]["search_template"]
    return template.format(query=base)


# ── Main scraper ───────────────────────────────────────────────────────────────

async def scrape_products(preference: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search for real listings using Tavily, context-aware by query type.
    Falls back to relevant mock data if search fails.
    """
    qtype = _detect_query_type(preference)
    profile = QUERY_PROFILES[qtype]
    search_query = _build_search_query(preference, qtype)

    print(f"Query type detected: {qtype} | Search: {search_query}")

    try:
        from tavily import AsyncTavilyClient

        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is missing")

        client = AsyncTavilyClient(api_key=TAVILY_API_KEY)

        result = await client.search(
            query=search_query,
            search_depth="advanced",
            max_results=max_results + 3,
            include_answer=False,
            include_raw_content=True,
            include_domains=profile["include_domains"],
        )

        all_items = _parse_tavily_response(result, max_results + 3, qtype)

        priced = [p for p in all_items if p["price"] > 0]
        unpriced = [p for p in all_items if p["price"] == 0]
        items = (priced + unpriced)[:max_results]

        if items:
            print(f"Tavily: {len(items)} results ({len(priced)} with prices) — type={qtype}")
            return items

        print("Tavily: empty result — falling back to mock data")
        return _mock_data(preference, qtype)

    except Exception as e:
        print(f"Tavily error: {e} — falling back to mock data")
        return _mock_data(preference, qtype)


# ── Response parser ────────────────────────────────────────────────────────────

def _parse_tavily_response(result: dict, max_results: int, qtype: str) -> list[dict]:
    products = []
    items = result.get("results", [])

    for item in items[:max_results]:
        try:
            content = item.get("content", "")
            raw = item.get("raw_content") or ""
            full_text = raw if len(raw) > len(content) else content

            price = _extract_price(full_text) or _extract_price(content)
            title = item.get("title", "Result")[:120]
            url = item.get("url", "#")
            store = _guess_source(url, qtype)

            # Availability / delivery — context-sensitive
            text_lower = full_text.lower()
            if qtype == "flight":
                avail_words = ["available", "seats available", "book now"]
                delivery_words = ["departs", "departure", "nonstop", "non-stop", "layover", "direct"]
            else:
                avail_words = ["in stock", "available", "pickup today", "same day"]
                delivery_words = ["free delivery", "same-day", "next day", "ships in", "arrives", "pickup"]

            availability = (
                "Available" if any(w in text_lower for w in avail_words)
                else "Check site"
            )

            delivery = "Check site"
            for kw in delivery_words:
                idx = text_lower.find(kw)
                if idx != -1:
                    delivery = full_text[idx:idx+50].split("\n")[0].strip()
                    break

            products.append({
                "title": title,
                "price": price or 0.0,
                "availability": availability,
                "store": store,
                "url": url,
                "rating": _extract_rating(full_text) or 0.0,
                "delivery": delivery,
            })
        except Exception:
            continue

    return products


# ── Helpers ────────────────────────────────────────────────────────────────────

def _guess_source(url: str, qtype: str) -> str:
    u = url.lower()
    mapping = {
        "amazon": "Amazon", "bestbuy": "Best Buy", "newegg": "Newegg",
        "walmart": "Walmart", "kayak": "Kayak", "skyscanner": "Skyscanner",
        "expedia": "Expedia", "makemytrip": "MakeMyTrip", "booking": "Booking.com",
        "momondo": "Momondo", "airbnb": "Airbnb", "hotels": "Hotels.com",
        "apple": "Apple", "samsung": "Samsung",
    }
    for key, name in mapping.items():
        if key in u:
            return name
    return "Online"


def _extract_price(text: str) -> float:
    # Match $1,299.99 or $999 — skip tiny amounts < $1 (likely per-unit rates)
    nums = re.findall(r"\$\s?([\d,]+\.?\d*)", text)
    for n in nums:
        try:
            val = float(n.replace(",", ""))
            if val >= 1.0:
                return val
        except Exception:
            continue
    return 0.0


def _extract_rating(text: str) -> float:
    matches = re.findall(r"(\d\.?\d?)\s?(?:out of 5|stars?|/5)", text, re.IGNORECASE)
    if matches:
        try:
            return min(5.0, float(matches[0]))
        except Exception:
            pass
    return 0.0


# ── Mock fallbacks ─────────────────────────────────────────────────────────────

def _mock_data(preference: str, qtype: str) -> list[dict]:
    if qtype == "flight":
        return [
            {"title": "Air India HYD→LHR Non-stop (Economy)", "price": 980.0,
             "availability": "Available", "store": "MakeMyTrip",
             "url": "https://makemytrip.com", "rating": 3.8, "delivery": "Non-stop · 10h 30m"},
            {"title": "Emirates HYD→DXB→LHR (1 stop)", "price": 750.0,
             "availability": "Available", "store": "Kayak",
             "url": "https://kayak.com", "rating": 4.5, "delivery": "1 stop via Dubai · 14h"},
            {"title": "Qatar Airways HYD→DOH→LHR (1 stop)", "price": 820.0,
             "availability": "Available", "store": "Expedia",
             "url": "https://expedia.com", "rating": 4.7, "delivery": "1 stop via Doha · 13h"},
            {"title": "British Airways HYD→LHR Non-stop", "price": 1150.0,
             "availability": "Available", "store": "Skyscanner",
             "url": "https://skyscanner.com", "rating": 4.2, "delivery": "Non-stop · 10h 15m"},
        ]
    if qtype == "hotel":
        return [
            {"title": "Premier Inn London City (Budget)", "price": 89.0,
             "availability": "Available", "store": "Booking.com",
             "url": "https://booking.com", "rating": 4.1, "delivery": "Check-in from 3pm"},
            {"title": "Travelodge London Central (Economy)", "price": 65.0,
             "availability": "Available", "store": "Hotels.com",
             "url": "https://hotels.com", "rating": 3.7, "delivery": "Check-in from 2pm"},
        ]
    # Generic product fallback
    return [
        {"title": "Top Result (Mock)", "price": 299.99, "availability": "In Stock",
         "store": "Amazon", "url": "https://amazon.com", "rating": 4.3, "delivery": "Ships in 2 days"},
    ]
