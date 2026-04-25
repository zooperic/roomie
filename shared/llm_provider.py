import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

MODEL_DEFAULTS = {
    "claude": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "ollama": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
}

ACTIVE_MODEL = os.getenv("LLM_MODEL") or MODEL_DEFAULTS.get(PROVIDER, "qwen2.5:7b")


async def get_llm_response(
    prompt: str,
    system: Optional[str] = None,
    json_mode: bool = False,
    max_tokens: int = 1024,
    image_base64: Optional[str] = None,
    image_media_type: str = "image/jpeg",
) -> str:
    if PROVIDER == "claude":
        return await _call_claude(prompt, system, json_mode, max_tokens, image_base64, image_media_type)
    elif PROVIDER == "openai":
        return await _call_openai(prompt, system, json_mode, max_tokens, image_base64, image_media_type)
    elif PROVIDER == "ollama":
        return await _call_ollama(prompt, system, json_mode, max_tokens)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}. Must be claude | openai | ollama")


async def _call_claude(prompt, system, json_mode, max_tokens, image_base64, image_media_type):
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    content: list = []
    if image_base64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": image_media_type, "data": image_base64}
        })
    content.append({"type": "text", "text": prompt})
    kwargs = {
        "model": ACTIVE_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        if json_mode:
            system += "\n\nRespond ONLY with valid JSON. No markdown, no explanation, no backticks."
        kwargs["system"] = system
    response = await client.messages.create(**kwargs)
    return response.content[0].text


async def _call_openai(prompt, system, json_mode, max_tokens, image_base64, image_media_type):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    messages = []
    if system:
        if json_mode:
            system += "\n\nRespond ONLY with valid JSON. No markdown, no explanation, no backticks."
        messages.append({"role": "system", "content": system})
    user_content: list = []
    if image_base64:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{image_media_type};base64,{image_base64}"}
        })
    user_content.append({"type": "text", "text": prompt})
    messages.append({"role": "user", "content": user_content})
    kwargs = {"model": ACTIVE_MODEL, "max_tokens": max_tokens, "messages": messages}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


async def _call_ollama(prompt, system, json_mode, max_tokens, *_):
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    payload = {
        "model": ACTIVE_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }
    if system:
        if json_mode:
            system += "\n\nRespond ONLY with valid JSON. No markdown, no explanation, no backticks."
        payload["system"] = system
    if json_mode:
        payload["format"] = "json"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{ollama_url}/api/generate", json=payload)
        response.raise_for_status()
        return response.json()["response"]


async def call_llm_vision(prompt: str, image_base64: str, system: Optional[str] = None) -> str:
    """Call vision-enabled LLM for image analysis"""
    if PROVIDER == "ollama":
        # Use qwen2.5vl:7b for vision with Ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        payload = {
            "model": "qwen2.5vl:7b",
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {"num_predict": 2048},
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{ollama_url}/api/generate", json=payload)
            response.raise_for_status()
            # At the end of call_llm_vision, before return
            print(f"\n[VISION DEBUG] Raw output:\n{result}\n")
            return result
            return response.json()["response"]
    else:
        # Use standard call for Claude/OpenAI (they support vision natively)
        # At the end of call_llm_vision, before return
        print(f"\n[VISION DEBUG] Raw output:\n{result}\n")
        return result
        return await get_llm_response(prompt, system, json_mode=True, max_tokens=2048, image_base64=image_base64)


def parse_json_response(raw: str) -> dict:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
    return json.loads(cleaned)


def get_provider_info() -> dict:
    return {"provider": PROVIDER, "model": ACTIVE_MODEL}
