# backend/qwen_client.py

import os
from openai import AsyncOpenAI
from typing import AsyncGenerator

def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.environ["FEATHERLESS_API_KEY"],
        base_url="https://api.featherless.ai/v1",
    )

async def stream_completion(
    model_id: str,
    user_query: str,
    task: str,
    system_hint: str = "",
) -> AsyncGenerator[str, None]:
    client = get_client()

    system_prompt = (
        system_hint or
        f"You are a helpful assistant. Answer the following {task} query concisely and accurately."
    )

    stream = await client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        stream=True,
        max_tokens=1024,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
