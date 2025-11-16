"""Multimodal recursive solve function that extends ROMA's solve with VLM support."""

from typing import Optional, List, Union
from pathlib import Path
import functools

# Import our multimodal modules
from roma_vlm.modules import (
    MultimodalAtomizer,
    MultimodalPlanner,
    MultimodalExecutor,
    MultimodalAggregator,
    MultimodalVerifier,
)
from roma_vlm.utils import encode_image_base64, resize_image_if_needed, get_image_info

# Import ROMA core components
from roma_dspy.core.engine.solve import RecursiveSolver
from roma_dspy.core.registry.agent_registry import AgentRegistry
from roma_dspy.config.schemas.root import ROMAConfig
from roma_dspy.config.schemas.observability import ObservabilityConfig, MLflowConfig
from roma_dspy.types import AgentType
from roma_dspy.core.signatures import TaskNode

# Import DSPy's Image type for proper vision API formatting
import dspy
try:
    from dspy.adapters.types import Image as DspyImage
except ImportError:
    # Fallback - create a simple wrapper
    class DspyImage:
        def __init__(self, url):
            self.url = url


def _convert_images_to_data_uris(images: Optional[List[str]], max_dimension: int = 2048) -> Optional[List[str]]:
    """
    Convert image paths to data URIs for VLM APIs with automatic resizing.
    
    Args:
        images: List of image paths, URLs, or already-encoded data URIs
        max_dimension: Maximum width/height before resizing (default: 2048px)
        
    Returns:
        List of data URIs or URLs (ready for VLM APIs)
    """
    if images is None:
        return None
    
    converted = []
    for img in images:
        # Already a URL or data URI
        if img.startswith("http://") or img.startswith("https://") or img.startswith("data:"):
            converted.append(img)
        else:
            # Local file path - need to convert to base64 data URI
            path = Path(img)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {img}")
            
            # Check image size and resize if needed to prevent context window overflow
            img_info = get_image_info(path)
            print(f"  Original: {img_info['width']}x{img_info['height']}, {img_info['file_size_mb']:.2f}MB")
            
            # Resize if image is too large (prevents 200K+ token images)
            if max(img_info['width'], img_info['height']) > max_dimension:
                print(f"  ⚠️  Image too large, resizing to max {max_dimension}px...")
                resized_path = resize_image_if_needed(path, max_dimension=max_dimension)
                path = resized_path
                img_info = get_image_info(path)
                print(f"  ✓ Resized: {img_info['width']}x{img_info['height']}, {img_info['file_size_mb']:.2f}MB")
            
            # Get file extension to determine MIME type
            ext = path.suffix.lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.bmp': 'image/bmp',
            }
            mime_type = mime_types.get(ext, 'image/png')
            
            # Encode to base64
            base64_data = encode_image_base64(path)
            base64_size_mb = len(base64_data) / (1024 * 1024)
            estimated_tokens = len(base64_data) // 4  # Rough estimate: 4 chars ≈ 1 token
            
            print(f"  📊 Base64 size: {base64_size_mb:.2f}MB (~{estimated_tokens:,} tokens)")
            
            # Warn if still very large
            if estimated_tokens > 100000:
                print(f"  ⚠️  WARNING: Image is still very large ({estimated_tokens:,} tokens)!")
                print(f"     Consider reducing max_dimension or using a smaller image.")
            
            # Create data URI
            data_uri = f"data:{mime_type};base64,{base64_data}"
            converted.append(data_uri)
    
    return converted


def _wrap_forward_with_images(module, images: Optional[List[str]], memories: Optional[str] = None, param_name: str = 'images'):
    """
    Wrap a module's forward and aforward methods to automatically inject images and memories.
    
    This allows ROMA's RecursiveSolver to work with multimodal modules without
    modification - the wrapper injects images and memories into all calls transparently.
    
    Also handles parameter name mapping: ROMA uses 'input_task' and 'context_payload',
    but multimodal modules use 'goal' and 'context'.
    
    Args:
        module: The module to wrap
        images: The images to inject
        memories: The memories to inject
        param_name: The parameter name to use (e.g., 'images' or 'original_images')
    """
    # Store original methods
    original_forward = module.forward
    original_aforward = module.aforward
    
    # Wrap forward (sync)
    @functools.wraps(original_forward)
    def wrapped_forward(*args, **kwargs):
        # Map ROMA's parameter names to multimodal module parameter names
        if 'input_task' in kwargs and 'goal' not in kwargs:
            kwargs['goal'] = kwargs.pop('input_task')
        # Note: Don't map context_payload to context - they are different parameters
        # context_payload is a string, context is a dict for dspy.context()
        
        # Inject images if not already provided
        if param_name not in kwargs:
            kwargs[param_name] = images
        
        # Inject memories if not already provided
        if 'memories' not in kwargs:
            kwargs['memories'] = memories
        
        return original_forward(*args, **kwargs)
    
    # Wrap aforward (async)
    @functools.wraps(original_aforward)
    async def wrapped_aforward(*args, **kwargs):
        # Map ROMA's parameter names to multimodal module parameter names
        if 'input_task' in kwargs and 'goal' not in kwargs:
            kwargs['goal'] = kwargs.pop('input_task')
        # Note: Don't map context_payload to context - they are different parameters
        # context_payload is a string, context is a dict for dspy.context()
        
        # Inject images if not already provided
        if param_name not in kwargs:
            kwargs[param_name] = images
        
        # Inject memories if not already provided
        if 'memories' not in kwargs:
            kwargs['memories'] = memories
        
        return await original_aforward(*args, **kwargs)
    
    # Replace methods with wrapped versions
    module.forward = wrapped_forward
    module.aforward = wrapped_aforward


async def multimodal_solve(
    goal: str,
    images: Optional[Union[str, List[str]]] = None,
    memories: Optional[str] = None,
    *,
    atomizer_model: str = "openrouter/openai/gpt-4o-mini",
    planner_model: str = "openrouter/openai/gpt-4o-mini",
    executor_model: str = "openrouter/openai/gpt-4o",
    aggregator_model: str = "openrouter/openai/gpt-4o-mini",
    verifier_model: str = "openrouter/openai/gpt-4o-mini",
    atomizer_config: Optional[dict] = None,
    planner_config: Optional[dict] = None,
    executor_config: Optional[dict] = None,
    aggregator_config: Optional[dict] = None,
    verifier_config: Optional[dict] = None,
    atomizer_strategy: str = "chain_of_thought",
    planner_strategy: str = "chain_of_thought",
    executor_strategy: str = "chain_of_thought",
    aggregator_strategy: str = "chain_of_thought",
    verifier_strategy: str = "chain_of_thought",
    atomizer_tools: Optional[dict] = None,
    planner_tools: Optional[dict] = None,
    executor_tools: Optional[dict] = None,
    aggregator_tools: Optional[dict] = None,
    atomizer_signature_instructions: Optional[str] = None,
    planner_signature_instructions: Optional[str] = None,
    executor_signature_instructions: Optional[str] = None,
    aggregator_signature_instructions: Optional[str] = None,
    verifier_signature_instructions: Optional[str] = None,
    atomizer_demos: Optional[List] = None,
    planner_demos: Optional[List] = None,
    executor_demos: Optional[List] = None,
    aggregator_demos: Optional[List] = None,
    verifier_demos: Optional[List] = None,
    max_depth: int = 5,
    verify: bool = True,
    enable_mlflow: bool = True,
    mlflow_tracking_uri: str = "http://localhost:5001",
    mlflow_experiment_name: str = "ROMA-VLM",
    max_image_dimension: int = 2048,
) -> str:
    """
    Recursively solve a task with multimodal VLM support using ROMA's solve infrastructure.
    
    This is the main entry point for using ROMA-VLM. It leverages ROMA's recursive solve
    function with custom multimodal modules that support images at every level.
    
    Args:
        goal: Task description (can reference images)
        images: Single image path/URL or list of images to process.
                Local file paths are automatically converted to base64 data URIs.
                Supports: file paths, http(s):// URLs, or data: URIs
        memories: Relevant memories from previous interactions for context
        atomizer_model: VLM for atomization decisions
        planner_model: VLM for task decomposition
        executor_model: VLM for task execution
        aggregator_model: VLM for result synthesis
        verifier_model: VLM for output verification
        *_config: Model configuration dicts (temperature, cache, etc.)
        atomizer_strategy: Prediction strategy for atomizer (default: "chain_of_thought")
                          Options: "chain_of_thought", "react", "code_act"
        planner_strategy: Prediction strategy for planner (default: "chain_of_thought")
        executor_strategy: Prediction strategy for executor (default: "chain_of_thought")
        aggregator_strategy: Prediction strategy for aggregator (default: "chain_of_thought")
        verifier_strategy: Prediction strategy for verifier (default: "chain_of_thought")
        atomizer_tools: Optional dict of tools for atomizer (required for react/code_act strategies)
        planner_tools: Optional dict of tools for planner (required for react/code_act strategies)
        executor_tools: Optional dict of tools for executor (required for react/code_act strategies)
        aggregator_tools: Optional dict of tools for aggregator (required for react/code_act strategies)
        atomizer_signature_instructions: Custom instructions for atomizer behavior
        planner_signature_instructions: Custom instructions for planner behavior
        executor_signature_instructions: Custom instructions for executor behavior
        aggregator_signature_instructions: Custom instructions for aggregator behavior
        verifier_signature_instructions: Custom instructions for verifier behavior
        atomizer_demos: List of dspy.Example objects for atomizer few-shot learning
        planner_demos: List of dspy.Example objects for planner few-shot learning
        executor_demos: List of dspy.Example objects for executor few-shot learning
        aggregator_demos: List of dspy.Example objects for aggregator few-shot learning
        verifier_demos: List of dspy.Example objects for verifier few-shot learning
        max_depth: Maximum recursion depth
        verify: Whether to verify final output
        enable_mlflow: Enable MLflow tracking and logging (default: True)
        mlflow_tracking_uri: MLflow tracking server URI (default: "http://localhost:5001")
        mlflow_experiment_name: MLflow experiment name (default: "ROMA-VLM")
        max_image_dimension: Max width/height for images before resizing (default: 2048px).
                            Prevents context window overflow from large images.
        
    Returns:
        Final synthesized result string
    """
    # Normalize images to list
    if images is not None:
        if isinstance(images, str):
            images = [images]
        
        # Convert local file paths to base64 data URIs
        # This is crucial - VLM APIs need base64-encoded images, not file paths!
        print(f"📷 Processing {len(images)} image(s) for VLM...")
        images = _convert_images_to_data_uris(images, max_dimension=max_image_dimension)
        
        # Convert data URIs to dspy.Image objects for proper vision API formatting
        # This ensures DSPy sends images in the correct format (not as text in prompt)
        images = [DspyImage(url=img) if isinstance(img, str) else img for img in images]
        print(f"✓ Images converted to DSPy Image objects for proper vision API handling")
    
    # Initialize all VLM-powered modules with prediction strategies and signature instructions
    atomizer = MultimodalAtomizer(
        prediction_strategy=atomizer_strategy,
        model=atomizer_model,
        model_config=atomizer_config or {"temperature": 0.6, "cache": False},
        tools=atomizer_tools,
        signature_instructions=atomizer_signature_instructions,
        demos=atomizer_demos
    )
    
    planner = MultimodalPlanner(
        prediction_strategy=planner_strategy,
        model=planner_model,
        model_config=planner_config or {"temperature": 0.7, "cache": True},
        tools=planner_tools,
        signature_instructions=planner_signature_instructions,
        demos=planner_demos
    )
    
    executor = MultimodalExecutor(
        prediction_strategy=executor_strategy,
        model=executor_model,
        model_config=executor_config or {"temperature": 0.5, "cache": True},
        tools=executor_tools,
        signature_instructions=executor_signature_instructions,
        demos=executor_demos
    )
    
    aggregator = MultimodalAggregator(
        prediction_strategy=aggregator_strategy,
        model=aggregator_model,
        model_config=aggregator_config or {"temperature": 0.65, "cache": True},
        tools=aggregator_tools,
        signature_instructions=aggregator_signature_instructions,
        demos=aggregator_demos
    )
    
    # Store images in module state so they're available during forward calls
    # This allows ROMA's solver to work with multimodal modules seamlessly
    atomizer._images = images
    planner._images = images
    executor._images = images
    aggregator._images = images
    
    # Wrap the forward methods to inject images and memories automatically
    # Aggregator uses 'original_images' parameter name, others use 'images'
    _wrap_forward_with_images(atomizer, images, memories, param_name='images')
    _wrap_forward_with_images(planner, images, memories, param_name='images')
    _wrap_forward_with_images(executor, images, memories, param_name='images')
    _wrap_forward_with_images(aggregator, images, memories, param_name='original_images')
    
    # Create a custom AgentRegistry with our multimodal modules
    registry = AgentRegistry()
    registry.register_agent(AgentType.ATOMIZER, None, atomizer)
    registry.register_agent(AgentType.PLANNER, None, planner)
    registry.register_agent(AgentType.EXECUTOR, None, executor)
    registry.register_agent(AgentType.AGGREGATOR, None, aggregator)
    
    # Create a config with MLflow observability settings
    # The config won't be used for agent configuration since we're providing a custom registry
    mlflow_config = MLflowConfig(
        enabled=enable_mlflow,
        tracking_uri=mlflow_tracking_uri,
        experiment_name=mlflow_experiment_name,
        log_traces=True,
        log_traces_from_eval=True,
        log_evals=True,
    )
    
    observability_config = ObservabilityConfig(mlflow=mlflow_config)
    
    config = ROMAConfig(observability=observability_config)
    
    # Create RecursiveSolver with the custom registry and minimal config
    solver = RecursiveSolver(
        config=config,
        registry=registry,
        max_depth=max_depth,
        enable_logging=False,
        enable_checkpoints=False
    )
    
    # Use ROMA's solve infrastructure for recursive decomposition
    result_node: TaskNode = await solver.async_solve(goal)
    
    # Extract the result from the TaskNode
    if hasattr(result_node, 'result') and result_node.result is not None:
        result = str(result_node.result)
    elif hasattr(result_node, 'output') and result_node.output is not None:
        result = str(result_node.output)
    else:
        result = str(result_node)
    
    # Optional verification with VLM
    if verify:
        verifier = MultimodalVerifier(
            prediction_strategy=verifier_strategy,
            model=verifier_model,
            model_config=verifier_config or {"temperature": 0.0, "cache": False},
            signature_instructions=verifier_signature_instructions,
            demos=verifier_demos
        )
        
        verdict = await verifier.aforward(
            goal=goal,
            images=images,
            memories=memories,
            candidate_output=result
        )
        
        if not verdict.verdict:
            # Verification failed - return with feedback
            return f"[VERIFICATION FAILED]\n{verdict.feedback}\n\nOriginal Output:\n{result}"
    
    return result


def create_multimodal_pipeline(
    atomizer_model: str = "openrouter/google/gemini-2.0-flash-exp",
    planner_model: str = "openrouter/openai/gpt-4o",
    executor_model: str = "openrouter/anthropic/claude-3-5-sonnet",
    aggregator_model: str = "openrouter/anthropic/claude-3-5-sonnet",
    verifier_model: str = "openrouter/anthropic/claude-3-5-sonnet",
    **model_configs
):
    """
    Create a reusable multimodal pipeline with configured VLMs.
    
    Returns a dictionary of initialized modules that can be used
    in custom orchestration logic.
    
    Example:
        pipeline = create_multimodal_pipeline(
            executor_model="openrouter/anthropic/claude-3-5-sonnet",
            executor_config={"temperature": 0.7}
        )
        
        # Use modules individually
        result = await pipeline["executor"].aforward(
            goal="Analyze this image",
            images=["photo.jpg"]
        )
    """
    return {
        "atomizer": MultimodalAtomizer(
            model=atomizer_model,
            model_config=model_configs.get("atomizer_config", {"temperature": 0.6})
        ),
        "planner": MultimodalPlanner(
            model=planner_model,
            model_config=model_configs.get("planner_config", {"temperature": 0.7})
        ),
        "executor": MultimodalExecutor(
            model=executor_model,
            model_config=model_configs.get("executor_config", {"temperature": 0.5})
        ),
        "aggregator": MultimodalAggregator(
            model=aggregator_model,
            model_config=model_configs.get("aggregator_config", {"temperature": 0.65})
        ),
        "verifier": MultimodalVerifier(
            model=verifier_model,
            model_config=model_configs.get("verifier_config", {"temperature": 0.0})
        ),
    }

