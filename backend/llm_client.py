# backend/llm_client.py

import os
from openai import AsyncOpenAI
from typing import AsyncGenerator

FEATHERLESS_BASE = "https://api.featherless.ai/v1"

def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.environ["FEATHERLESS_API_KEY"],
        base_url=FEATHERLESS_BASE,
    )

MODEL = "Qwen/Qwen2.5-7B-Instruct"

SYSTEM_PROMPT = """You are MELLM — a Multi-Context Conflict Resolver.
Your job is to resolve conflicts between what a user wants and what the real market offers.
You reason clearly, pick the best available option given hard constraints, and explain every tradeoff.
Be direct, specific, and structured. Always end with a clear final recommendation."""


def build_resolution_prompt(
    preference: str,
    constraint_text: str,
    constraints: dict,
    evaluations: list,
) -> str:
    """Build the full prompt for the LLM resolver."""

    products_block = ""
    for i, ev in enumerate(evaluations[:4], 1):
        p = ev.product
        conflict_lines = "\n".join(
            f"    - [{c.severity.upper()}] {c.constraint}: {c.description}"
            for c in ev.conflicts
        ) or "    - No conflicts"
        products_block += f"""
Product {i}: {p['title']}
  Price: ${p['price']:.2f}
  Delivery: {p.get('delivery', 'Unknown')}
  Rating: {p.get('rating', 'N/A')}/5
  Store: {p.get('store', 'Unknown')}
  Conflicts with user constraints:
{conflict_lines}
  Match score: {ev.match_score:.0f}/100
"""

    constraints_block = "\n".join(f"  - {k}: {v}" for k, v in constraints.items())

    return f"""USER PREFERENCES:
"{preference}"

USER CONSTRAINTS:
"{constraint_text}"

PARSED CONSTRAINTS:
{constraints_block}

REAL MARKET DATA (scraped live):
{products_block}

TASK:
1. Identify all conflicts between what the user wants and what the market offers.
2. For each conflict, state which constraint takes priority and why.
3. Pick the BEST product given the hard constraints. If no product satisfies all hard constraints, explain what was sacrificed and why it was the least bad option.
4. End with:
   FINAL RECOMMENDATION: [Product name]
   WHY THIS WON: [2-3 sentences max — which constraint mattered most]
   WHAT YOU SACRIFICED: [what preference was dropped and why it was acceptable]"""


async def stream_resolution(prompt: str) -> AsyncGenerator[str, None]:
    client = get_client()
    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        stream=True,
        max_tokens=800,
        temperature=0.4,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
