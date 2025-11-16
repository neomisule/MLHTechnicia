"""Multimodal signatures for ROMA-VLM.

These signatures extend ROMA's base signatures to support image inputs.
"""

from roma_vlm.signatures.multimodal_signatures import (
    MultimodalAtomizerSignature,
    MultimodalPlannerSignature,
    MultimodalExecutorSignature,
    MultimodalAggregatorSignature,
    MultimodalVerifierSignature,
)

__all__ = [
    "MultimodalAtomizerSignature",
    "MultimodalPlannerSignature",
    "MultimodalExecutorSignature",
    "MultimodalAggregatorSignature",
    "MultimodalVerifierSignature",
]

