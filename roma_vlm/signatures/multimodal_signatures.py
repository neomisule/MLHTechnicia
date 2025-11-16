"""Multimodal signatures that extend ROMA's base signatures with image support."""

import dspy
from typing import Optional, Dict, List, Any, Union

# Import from ROMA library
from roma_dspy.core.signatures.base_models.subtask import SubTask
from roma_dspy.types import NodeType

# Import DSPy's Image type for proper vision API formatting
try:
    from dspy.adapters.types import Image as DspyImage
except ImportError:
    # Fallback if import path changes
    DspyImage = Any


class MultimodalAtomizerSignature(dspy.Signature):
    """
    Atomizer signature with multimodal input support.
    
    Extends ROMA's AtomizerSignature to accept images alongside text goals.
    VLM can analyze images to determine if task is atomic or needs planning.
    """
    
    goal: str = dspy.InputField(
        description="Task to atomize. Can reference images provided."
    )
    images: Optional[List[Union[str, DspyImage]]] = dspy.InputField(
        default=None,
        description="List of images (as dspy.Image objects or data URIs) for vision analysis"
    )
    memories: Optional[str] = dspy.InputField(
        default=None,
        description="Relevant memories from previous interactions for context"
    )
    context: Optional[str] = dspy.InputField(
        default=None, 
        description="Execution context (XML format from ROMA)"
    )
    
    is_atomic: bool = dspy.OutputField(
        description="True if task can be executed directly, False if planning needed"
    )
    node_type: NodeType = dspy.OutputField(
        description="Type of node to process (PLAN or EXECUTE)"
    )


class MultimodalPlannerSignature(dspy.Signature):
    """
    Planner signature with image understanding.
    
    Extends ROMA's PlannerSignature to allow VLM to understand images
    when decomposing tasks into subtasks.
    """
    
    goal: str = dspy.InputField(
        description="Complex task that needs decomposition into subtasks"
    )
    images: Optional[List[Union[str, DspyImage]]] = dspy.InputField(
        default=None,
        description="Images (as dspy.Image objects or data URIs) for planning context"
    )
    memories: Optional[str] = dspy.InputField(
        default=None,
        description="Relevant memories from previous interactions for context"
    )
    context: Optional[str] = dspy.InputField(
        default=None,
        description="Execution context (XML format from ROMA)"
    )
    
    subtasks: List[SubTask] = dspy.OutputField(
        description="List of generated subtasks with goals, types, and dependencies"
    )
    dependencies_graph: Optional[Dict[str, List[str]]] = dspy.OutputField(
        default=None,
        description="Task dependency mapping. Keys are subtask indices as strings, values are dependency indices."
    )


class MultimodalExecutorSignature(dspy.Signature):
    """
    Executor signature with vision capabilities.
    
    Extends ROMA's ExecutorSignature to enable VLM-powered execution
    that can analyze, process, and reason about images.
    """
    
    goal: str = dspy.InputField(
        description="Atomic task to execute. Can involve image analysis, OCR, visual reasoning, etc."
    )
    images: Optional[List[Union[str, DspyImage]]] = dspy.InputField(
        default=None,
        description="Images (as dspy.Image objects or data URIs) for task execution"
    )
    memories: Optional[str] = dspy.InputField(
        default=None,
        description="Relevant memories from previous interactions for context"
    )
    context: Optional[str] = dspy.InputField(
        default=None,
        description="Execution context (XML format from ROMA)"
    )
    
    output: str = dspy.OutputField(
        description="Execution result. Can include image analysis, extracted data, or visual insights."
    )
    sources: Optional[List[str]] = dspy.OutputField(
        default_factory=list,
        description="Information sources used (including which images were analyzed)"
    )


class MultimodalAggregatorSignature(dspy.Signature):
    """
    Aggregator signature with multimodal synthesis.
    
    Extends ROMA's AggregatorSignature to synthesize results that may
    involve visual information from parent images.
    """
    
    original_goal: str = dspy.InputField(
        description="Original goal that was decomposed into subtasks"
    )
    original_images: Optional[List[Union[str, DspyImage]]] = dspy.InputField(
        default=None,
        description="Original images (as dspy.Image objects or data URIs) for synthesis context"
    )
    memories: Optional[str] = dspy.InputField(
        default=None,
        description="Relevant memories from previous interactions for context"
    )
    subtasks_results: List[SubTask] = dspy.InputField(
        description="List of subtask results to synthesize into final answer"
    )
    context: Optional[str] = dspy.InputField(
        default=None,
        description="Execution context (XML format from ROMA)"
    )
    
    synthesized_result: str = dspy.OutputField(
        description="Final synthesized output that integrates all subtask results"
    )


class MultimodalVerifierSignature(dspy.Signature):
    """
    Verifier signature with visual verification support.
    
    Extends ROMA's VerifierSignature to verify outputs that involve
    visual information or image analysis.
    """
    
    goal: str = dspy.InputField(
        description="Original task goal to verify against"
    )
    images: Optional[List[str]] = dspy.InputField(
        default=None,
        description="Original images for verification context. VLM can check if output matches image content."
    )
    memories: Optional[str] = dspy.InputField(
        default=None,
        description="Relevant memories from previous interactions for context"
    )
    candidate_output: str = dspy.InputField(
        description="Output to verify against goal and images"
    )
    context: Optional[str] = dspy.InputField(
        default=None,
        description="Execution context (XML format from ROMA)"
    )
    
    verdict: bool = dspy.OutputField(
        description="True if candidate output satisfies goal (considering image context)"
    )
    feedback: Optional[str] = dspy.OutputField(
        default=None,
        description="Explanation or fixes when verdict is False"
    )

