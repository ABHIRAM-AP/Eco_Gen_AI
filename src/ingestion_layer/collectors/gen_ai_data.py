# collectors/genai_metadata.py
import time
from functools import wraps
import requests

INGEST_URL = "http://127.0.0.1:8000/ingest/event"


def _extract_tokens(response, provider: str):
    if provider == "gemini":
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            return usage.prompt_token_count, usage.candidates_token_count
        return 0, 0

    if provider == "ollama":
        if isinstance(response, dict):
            return response.get("prompt_eval_count", 0), response.get("eval_count", 0)
        return 0, 0

    return 0, 0


def post_event(event_data: dict, region: str | None = None):
    payload = {**event_data, "region": region}
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
    region: str = None,
    auto_post: bool = True,
):
    """
    Decorator to wrap an LLM call, auto-capturing runtime and token usage,
    then (optionally) posting the event to the ingestion API.
    provider: "gemini" or "ollama" — controls how token usage is extracted.
    """
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
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "runtime_sec": runtime,
            }
            wrapper.last_event = event_data

            if auto_post:
                post_event(event_data, region=region)

            return response
        return wrapper
    return decorator