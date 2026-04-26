import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Model routing for different task types (Ollama only)
MODEL_ROUTING = {
    "chat": "llama3.1:8b",           # General conversation
    "vision": "qwen2.5vl:7b",        # Photo analysis
    "code": "qwen2.5-coder:7b",      # Code generation
    "reasoning": "deepseek-r1:8b",   # Complex reasoning
    "fast": "mistral:7b",   # Quick responses
}

MODEL_DEFAULTS = {
    "claude": "claude-haiku-4-5-20251001",
    "openai": "gpt-4o-mini",
    "ollama": os.getenv("OLLAMA_MODEL", MODEL_ROUTING["chat"]),
}

ACTIVE_MODEL = os.getenv("LLM_MODEL") or MODEL_DEFAULTS.get(PROVIDER, MODEL_ROUTING["chat"])


def select_model(task_type: str = "chat") -> str:
    """
    Intelligently select model based on task type.
    Only applies to Ollama provider - Claude/OpenAI use their defaults.
    
    Args:
        task_type: One of "chat", "vision", "code", "reasoning", "fast"
    
    Returns:
        Model name string
    """
    if PROVIDER != "ollama":
        return ACTIVE_MODEL
    
    return MODEL_ROUTING.get(task_type, MODEL_ROUTING["chat"])


async def get_llm_response(
    prompt: str,
    system: Optional[str] = None,
    json_mode: bool = False,
    max_tokens: int = 1024,
    image_base64: Optional[str] = None,
    image_media_type: str = "image/jpeg",
    task_type: str = "chat",  # New parameter for model routing
) -> str:
    """
    Get LLM response with intelligent model selection.
    
    Args:
        task_type: One of "chat", "vision", "code", "reasoning", "fast"
                   Only affects Ollama - Claude/OpenAI use their defaults
    """
    # Use vision model if image is provided
    if image_base64:
        task_type = "vision"
    
    # Select appropriate model
    model_to_use = select_model(task_type)
    
    if PROVIDER == "claude":
        return await _call_claude(prompt, system, json_mode, max_tokens, image_base64, image_media_type, model_to_use)
    elif PROVIDER == "openai":
        return await _call_openai(prompt, system, json_mode, max_tokens, image_base64, image_media_type, model_to_use)
    elif PROVIDER == "ollama":
        return await _call_ollama(prompt, system, json_mode, max_tokens, model_to_use)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER}. Must be claude | openai | ollama")


async def _call_claude(prompt, system, json_mode, max_tokens, image_base64, image_media_type, model):
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
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        if json_mode:
            system += "\n\nRespond ONLY with valid JSON. No markdown, no explanation, no backticks."
        kwargs["system"] = system
    prompt_tokens_approx = (len(prompt) + len(system or "")) // 4
    print(f"[LLM] model={model} | input≈{prompt_tokens_approx} tokens | max_out={max_tokens} | json={json_mode}")
    print(f"[LLM] prompt preview: {prompt[:120].strip()!r}{'...' if len(prompt) > 120 else ''}")
    import time as _t; _t0 = _t.time()
    response = await client.messages.create(**kwargs)
    result = response.content[0].text
    _elapsed = _t.time() - _t0
    out_tokens_approx = len(result) // 4
    print(f"[LLM] done in {_elapsed:.1f}s | output≈{out_tokens_approx} tokens")
    print(f"[LLM] output preview: {result[:120].strip()!r}{'...' if len(result) > 120 else ''}")
    return result


async def _call_openai(prompt, system, json_mode, max_tokens, image_base64, image_media_type, model):
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
    kwargs = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    prompt_tokens_approx = (len(prompt) + len(system or "")) // 4
    print(f"[LLM] model={model} | input≈{prompt_tokens_approx} tokens | max_out={max_tokens} | json={json_mode}")
    print(f"[LLM] prompt preview: {prompt[:120].strip()!r}{'...' if len(prompt) > 120 else ''}")
    import time as _t; _t0 = _t.time()
    response = await client.chat.completions.create(**kwargs)
    result = response.choices[0].message.content
    _elapsed = _t.time() - _t0
    print(f"[LLM] done in {_elapsed:.1f}s | output≈{len(result)//4} tokens")
    print(f"[LLM] output preview: {result[:120].strip()!r}{'...' if len(result) > 120 else ''}")
    return result


async def _call_ollama(prompt, system, json_mode, max_tokens, model):
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    payload = {
        "model": model,
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
    
    prompt_tokens_approx = (len(prompt) + len(system or "")) // 4
    print(f"[LLM] model={model} | input≈{prompt_tokens_approx} tokens | max_out={max_tokens} | json={json_mode}")
    print(f"[LLM] prompt preview: {prompt[:120].strip()!r}{'...' if len(prompt) > 120 else ''}")
    import time as _t; _t0 = _t.time()
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(f"{ollama_url}/api/generate", json=payload)
        response.raise_for_status()
        result = response.json()["response"]
    _elapsed = _t.time() - _t0
    out_tokens_approx = len(result) // 4
    print(f"[LLM] done in {_elapsed:.1f}s | output≈{out_tokens_approx} tokens | speed≈{out_tokens_approx/_elapsed:.0f} tok/s")
    print(f"[LLM] output preview: {result[:120].strip()!r}{'...' if len(result) > 120 else ''}")
    return result


async def call_llm_vision(prompt: str, image_base64: str, system: Optional[str] = None) -> str:
    """Call vision-enabled LLM for image analysis"""
    if PROVIDER == "ollama":
        # Use qwen2.5vl:7b for vision with Ollama
        vision_model = MODEL_ROUTING["vision"]
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        payload = {
            "model": vision_model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {"num_predict": 2048},
        }
        if system:
            payload["system"] = system
        
        print(f"[VISION] Using model: {vision_model}")
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{ollama_url}/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()["response"]
            print(f"[VISION] Detected items from image")
            return result
    else:
        # Use standard call for Claude/OpenAI (they support vision natively)
        result = await get_llm_response(prompt, system, json_mode=True, max_tokens=2048, image_base64=image_base64, task_type="vision")
        print(f"[VISION] Processed image via {PROVIDER}")
        return result


def parse_json_response(raw: str) -> dict:
    """
    Parse JSON from LLM output. Handles:
    - ```json ... ``` fences
    - Plain ``` ... ``` fences
    - Leading/trailing whitespace
    - Thinking tags from DeepSeek (<think>...</think>)
    """
    print(f"[LLM parse] raw output ({len(raw)} chars): {raw[:200].strip()!r}{'...' if len(raw)>200 else ''}")
    import re as _re
    cleaned = raw.strip()

    # Strip DeepSeek thinking tags
    cleaned = _re.sub(r'<think>.*?</think>', '', cleaned, flags=_re.DOTALL).strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    if cleaned.startswith("```"):
        # Remove opening fence line
        cleaned = _re.sub(r'^```[a-zA-Z]*\n?', '', cleaned).strip()
        # Remove closing fence
        cleaned = _re.sub(r'\n?```$', '', cleaned).strip()

    # Find the first { or [ and last } or ] to extract pure JSON
    start = next((i for i, c in enumerate(cleaned) if c in '{['), None)
    end_brace = cleaned.rfind('}')
    end_bracket = cleaned.rfind(']')
    end = max(end_brace, end_bracket)

    if start is not None and end > start:
        cleaned = cleaned[start:end + 1]

    return json.loads(cleaned)


def get_provider_info() -> dict:
    return {"provider": PROVIDER, "model": ACTIVE_MODEL}
