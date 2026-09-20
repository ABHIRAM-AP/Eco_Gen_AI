# collectors/genai_metadata.py
import time
from functools import wraps
from typing import Optional
import requests

INGEST_URL = "http://127.0.0.1:8000/ingest/event"

# Static lookup mapping known model names to parameter counts in billions (best-effort)
MODEL_PARAM_MAP: dict[str, float] = {
    # Gemma models
    "gemma3:270m": 0.27,
    "gemma3:1b": 1.0,
    "gemma3:4b": 4.0,
    "gemma3:12b": 12.0,
    "gemma3:27b": 27.0,
    "gemma:2b": 2.0,
    "gemma:7b": 7.0,
    "gemma2:2b": 2.6,
    "gemma2:9b": 9.2,
    "gemma2:27b": 27.2,
    # LLaMA models
    "llama3:8b": 8.0,
    "llama3:70b": 70.0,
    "llama3.1:8b": 8.0,
    "llama3.1:70b": 70.0,
    "llama3.1:405b": 405.0,
    "llama3.2:1b": 1.24,
    "llama3.2:3b": 3.21,
    "llama3.3:70b": 70.0,
    # Mistral / Mixtral
    "mistral:7b": 7.2,
    "mistral-small": 22.0,
    "mistral-large": 123.0,
    "mixtral:8x7b": 46.7,
    "mixtral:8x22b": 141.0,
    # Gemini models
    "gemini-1.5-flash": 8.0,
    "gemini-1.5-flash-8b": 8.0,
    "gemini-1.5-pro": 70.0,
    "gemini-2.0-flash": 8.0,
    "gemini-2.0-flash-lite": 4.0,
    "gemini-2.5-flash": 8.0,
    "gemini-3.5-flash": 8.0,
    # Qwen & others
    "qwen2.5:0.5b": 0.5,
    "qwen2.5:1.5b": 1.5,
    "qwen2.5:3b": 3.0,
    "qwen2.5:7b": 7.0,
    "qwen2.5:14b": 14.0,
    "qwen2.5:32b": 32.0,
    "qwen2.5:72b": 72.0,
    "phi-3-mini": 3.8,
    "phi-4": 14.0,
}


def get_model_param_count(model_name: str) -> Optional[float]:
    if not model_name:
        return None
    key = model_name.strip().lower()
    if key in MODEL_PARAM_MAP:
        return MODEL_PARAM_MAP[key]
    if "/" in key:
        base_name = key.split("/")[-1]
        if base_name in MODEL_PARAM_MAP:
            return MODEL_PARAM_MAP[base_name]
    return None


def _extract_tokens(response, provider: str):
    if provider == "gemini":
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            return getattr(usage, "prompt_token_count", 0), getattr(usage, "candidates_token_count", 0)
        return 0, 0

    if provider == "ollama":
        if isinstance(response, dict):
            return response.get("prompt_eval_count", 0), response.get("eval_count", 0)
        return 0, 0

    return 0, 0


def post_event(event_data: dict, region: Optional[str] = None):
    payload = {**event_data}
    if region is not None:
        payload["region"] = region
    try:
        resp = requests.post(INGEST_URL, json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ingest] failed to post event: {e}")
        return None


def track_inference(
    model_name: str,
    task_type: str,
    provider: str = "gemini",
    region: Optional[str] = None,
    auto_post: bool = True,
    pue: Optional[float] = 1.2,
    gpu_model: Optional[str] = None,
    num_gpus_used: Optional[int] = 1,
    batch_size: Optional[int] = 1,
    cost_usd: Optional[float] = None,
    department: Optional[str] = None,
    use_case: Optional[str] = None,
    param_count_b: Optional[float] = None,
    active_param_count_b: Optional[float] = None,
    **extra_kwargs,
):
    """
    Decorator to wrap an LLM call, auto-capturing runtime, token usage, and metadata,
    then (optionally) posting the event to the ingestion API.
    provider: "gemini" or "ollama" — controls how token usage is extracted and is persisted to the DB.
    """
    resolved_param_count = param_count_b if param_count_b is not None else get_model_param_count(model_name)
    resolved_active_param_count = active_param_count_b if active_param_count_b is not None else resolved_param_count

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            response = fn(*args, **kwargs)
            runtime = round(time.time() - start, 3)

            tokens_in, tokens_out = _extract_tokens(response, provider)

            event_data = {
                "model_name": model_name,
                "task_type": task_type,
                "provider": provider,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "runtime_sec": runtime,
                "pue": pue,
                "gpu_model": gpu_model,
                "num_gpus_used": num_gpus_used,
                "batch_size": batch_size,
                "cost_usd": cost_usd,
                "department": department,
                "use_case": use_case,
                "param_count_b": resolved_param_count,
                "active_param_count_b": resolved_active_param_count,
            }
            wrapper.last_event = event_data

            if auto_post:
                post_event(event_data, region=region)

            return response
        return wrapper
    return decorator