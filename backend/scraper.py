# backend/scraper.py

import os
import httpx
from typing import Any

BRIGHT_DATA_API_KEY = os.environ.get("BRIGHT_DATA_API_KEY", "")

# Bright Data endpoint — uses the Web Unlocker / SERP API
# We'll use their Amazon product search endpoint
BRIGHT_DATA_BASE = "https://api.brightdata.com/request"


async def scrape_products(preference: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Send a scraping job to Bright Data.
    Returns a list of product dicts with keys:
      title, price, availability, store, url, rating
    """

    # Build a clean search query from the preference
    search_query = _preference_to_query(preference)

    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_API_KEY}",
        "Content-Type": "application/json",
    }

    # Bright Data Web Scraper API payload
    # Uses their Amazon scraper dataset
    payload = {
        "url": f"https://www.amazon.com/s?k={search_query.replace(' ', '+')}",
        "format": "json",
        "country": "us",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                BRIGHT_DATA_BASE,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            raw = response.json()
            return _parse_products(raw, max_results)
        except Exception as e:
            # Fallback: return mock data so the app still runs if scrape fails
            print(f"Bright Data error: {e} — falling back to mock data")
            return _mock_products(preference)


def _preference_to_query(preference: str) -> str:
    """Extract a clean search query from a natural language preference string."""
    # Simple keyword extraction — good enough for demo
    stopwords = {"i", "want", "a", "an", "the", "with", "and", "or", "preferably", "some", "my"}
    words = preference.lower().replace(",", "").replace(".", "").split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return " ".join(keywords[:6])


def _parse_products(raw: Any, max_results: int) -> list[dict]:
    """Parse Bright Data response into a standard product list."""
    products = []

    # Handle both list response and nested response formats
    items = raw if isinstance(raw, list) else raw.get("results", raw.get("organic", []))

    for item in items[:max_results]:
        try:
            # Extract price — handle "$1,299.99" format
            price_raw = item.get("price", item.get("price_str", "0"))
            price = _parse_price(str(price_raw))

            products.append({
                "title": item.get("title", item.get("name", "Unknown Product"))[:120],
                "price": price,
                "availability": item.get("availability", item.get("in_stock", "Unknown")),
                "store": item.get("seller", item.get("brand", "Amazon")),
                "url": item.get("url", item.get("link", "#")),
                "rating": float(item.get("rating", item.get("stars", 0)) or 0),
                "delivery": item.get("delivery", item.get("shipping", "Ships in 3-5 days")),
            })
        except Exception:
            continue

    return products if products else _mock_products("")


def _parse_price(price_str: str) -> float:
    """Convert '$1,299.99' → 1299.99"""
    import re
    nums = re.findall(r"[\d,]+\.?\d*", price_str.replace(",", ""))
    return float(nums[0]) if nums else 0.0


def _mock_products(preference: str) -> list[dict]:
    """Fallback mock data when Bright Data is unavailable."""
    return [
        {
            "title": "ASUS ROG Zephyrus G16 OLED Gaming Laptop (RTX 4070)",
            "price": 1499.99,
            "availability": "Ships in 3 days",
            "store": "Amazon",
            "url": "https://amazon.com",
            "rating": 4.7,
            "delivery": "Ships in 3 days",
        },
        {
            "title": "ASUS TUF Gaming A15 (No OLED, RTX 4060)",
            "price": 1099.99,
            "availability": "In stock — pickup today at Best Buy",
            "store": "Best Buy",
            "url": "https://bestbuy.com",
            "rating": 4.4,
            "delivery": "Store pickup available today",
        },
        {
            "title": "Lenovo LOQ 15 Gaming Laptop (RTX 4060, IPS)",
            "price": 849.99,
            "availability": "In stock — pickup today",
            "store": "Best Buy",
            "url": "https://bestbuy.com",
            "rating": 4.2,
            "delivery": "Store pickup available today",
        },
        {
            "title": "ASUS Vivobook Pro 16X OLED (RTX 4060)",
            "price": 1349.99,
            "availability": "Ships in 5 days",
            "store": "Newegg",
            "url": "https://newegg.com",
            "rating": 4.5,
            "delivery": "Ships in 5 days",
        },
    ]
