
import asyncio
import os
from scraper import scrape_products

async def test_scraper():
    print("Testing Tavily Scraper (with placeholder key)...")
    # This should trigger the placeholder/missing key error or fall back to mock
    try:
        products = await scrape_products("gaming laptop", max_results=2)
        print(f"Scraper returned {len(products)} products.")
        for p in products:
            print(f"- {p['title']} ({p['store']}) AT {p['price']}")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    # Ensure we are in the backend directory context for imports
    asyncio.run(test_scraper())
