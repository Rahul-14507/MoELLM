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

SYSTEM_PROMPT = """You are MOLLM — a Multi-Context Conflict Resolver.
Your job is to pick the best available product from the market data provided, resolving conflicts between user preferences and reality.
Be extremely direct and concise. Do NOT provide a long reasoning chain or re-list every conflict.
Focus only on the single best choice and the primary reasons for selecting it."""


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
  Store: {p.get('store', 'Unknown')}
  Conflicts:
{conflict_lines}
  Match score: {ev.match_score:.0f}/100
"""

    return f"""USER PREFERENCES: "{preference}"
USER CONSTRAINTS: "{constraint_text}"

REAL MARKET DATA & DETECTED CONFLICTS:
{products_block}

TASK:
Identify the single BEST choice from the products above.
Respond ONLY with this structure in PLAIN TEXT. Do NOT use markdown (no #, no *).

BEST CHOICE: [Product title]

WHY IT WON: [2 sentences max — the primary priority that led to this choice]

THE TRADEOFF: [1 sentence max — what was sacrificed to make this work]"""


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

CHAT_SYSTEM_PROMPT = """You are MOLLM, a helpful, direct, and concise AI assistant. 
You are answering follow-up questions from a user about a recommendation you just made.
You must be focused on explaining your choice or considering the alternatives in the context.

Here is the context of the recommendation and the evaluated products:
{context}

Answer the user's questions based primarily on this context. Be concise, direct, and conversational."""

async def stream_chat(messages: list[dict], context: str) -> AsyncGenerator[str, None]:
    client = get_client()
    sys_prompt = {"role": "system", "content": CHAT_SYSTEM_PROMPT.format(context=context)}
    
    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[sys_prompt] + messages,
        stream=True,
        max_tokens=600,
        temperature=0.5,
    )
    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
