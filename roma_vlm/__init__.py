"""ROMA-VLM: Multimodal Vision Extension for ROMA Framework.

This package extends ROMA with Vision Language Model capabilities,
allowing each node to process both text and images.
"""

from roma_vlm.engine.solve import multimodal_solve
from roma_vlm.modules.atomizer import MultimodalAtomizer
from roma_vlm.modules.planner import MultimodalPlanner
from roma_vlm.modules.executor import MultimodalExecutor
from roma_vlm.modules.aggregator import MultimodalAggregator
from roma_vlm.modules.verifier import MultimodalVerifier

__version__ = "0.1.0"

__all__ = [
    "multimodal_solve",
    "MultimodalAtomizer",
    "MultimodalPlanner",
    "MultimodalExecutor",
    "MultimodalAggregator",
    "MultimodalVerifier",
]

