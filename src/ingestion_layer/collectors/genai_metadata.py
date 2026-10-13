"""
Compatibility module re-exporting gen_ai_data components for collectors/genai_metadata.
"""
from .gen_ai_data import (
    MODEL_PARAM_MAP,
    MOE_ACTIVE_PARAM_MAP,
    get_model_param_count,
    get_active_param_count,
    track_inference,
    post_event,
)

__all__ = [
    "MODEL_PARAM_MAP",
    "MOE_ACTIVE_PARAM_MAP",
    "get_model_param_count",
    "get_active_param_count",
    "track_inference",
    "post_event",
]
