"""Multimodal Executor that extends ROMA's Executor with VLM capabilities."""

from __future__ import annotations

import dspy
from typing import Union, Any, Optional, Dict, List, Mapping, Sequence

# Import from ROMA library
from roma_dspy.core.modules.base_module import BaseModule
from roma_dspy.types import PredictionStrategy

# Import our multimodal signature
from roma_vlm.signatures import MultimodalExecutorSignature


class MultimodalExecutor(BaseModule):
    """
    Executor with Vision Language Model support.
    
    Extends ROMA's BaseModule to process both text and images.
    Can use any VLM (Claude 3.5 Sonnet, GPT-4V, Gemini, etc.)
    
    Example:
        executor = MultimodalExecutor(
            model="openrouter/anthropic/claude-3-5-sonnet",
            model_config={"temperature": 0.7}
        )
        
        result = await executor.aforward(
            goal="Analyze this chest X-ray for abnormalities",
            images=["xray.jpg"]
        )
    """

    DEFAULT_SIGNATURE = MultimodalExecutorSignature

    def __init__(
        self,
        prediction_strategy: Union[PredictionStrategy, str] = PredictionStrategy.CHAIN_OF_THOUGHT,
        *,
        signature: Any = None,
        signature_instructions: Optional[str] = None,
        demos: Optional[List] = None,
        config: Optional[Any] = None,
        lm: Optional[dspy.LM] = None,
        model: Optional[str] = None,
        model_config: Optional[Mapping[str, Any]] = None,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        **strategy_kwargs: Any,
    ) -> None:
        """
        Initialize multimodal executor.
        
        Args:
            prediction_strategy: DSPy prediction strategy (cot, react, etc.)
            signature: Custom signature (defaults to MultimodalExecutorSignature)
            signature_instructions: Custom instructions to guide executor behavior
            demos: List of dspy.Example objects for few-shot learning
            config: Module configuration
            lm: Pre-configured DSPy LM instance
            model: Model string (e.g., "openrouter/anthropic/claude-3-5-sonnet")
            model_config: Model configuration dict (temperature, cache, etc.)
            tools: Optional tools for ReAct/CodeAct strategies
            **strategy_kwargs: Additional strategy arguments
        """
        # Handle signature instructions
        final_signature = signature if signature is not None else self.DEFAULT_SIGNATURE
        if signature_instructions:
            # Clone the signature and inject instructions
            final_signature = type(
                f"{final_signature.__name__}WithInstructions",
                (final_signature,),
                {"__doc__": signature_instructions}
            )
        
        super().__init__(
            signature=final_signature,
            config=config,
            prediction_strategy=prediction_strategy,
            lm=lm,
            model=model,
            model_config=model_config,
            tools=tools,
            **strategy_kwargs,
        )
        
        # Add demos if provided
        if demos and hasattr(self, '_predictor'):
            self._predictor.demos = demos

    def forward(
        self,
        goal: str,
        images: Optional[List[str]] = None,
        context: Optional[str] = None,
        *,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None,
        call_context: Optional[Dict[str, Any]] = None,
        call_params: Optional[Dict[str, Any]] = None,
        **call_kwargs: Any,
    ):
        """
        Execute task with optional image inputs (synchronous).
        
        Args:
            goal: Task description
            images: List of image paths or base64 encoded images
            context: ROMA execution context (XML)
            tools: Optional tools for this execution
            config: Per-call LM config overrides
            call_context: DSPy context overrides
            call_params: Additional predictor parameters
            **call_kwargs: Additional keyword arguments
            
        Returns:
            ExecutorResult with output and sources
        """
        runtime_tools = self._merge_tools(self._tools, tools)

        ctx = dict(self._context_defaults)
        if call_context:
            ctx.update(call_context)
        ctx.setdefault("lm", self._lm)
        if hasattr(self, "_adapter") and self._adapter is not None:
            ctx["adapter"] = self._adapter

        extra = dict(call_params or {})
        if call_kwargs:
            extra.update(call_kwargs)
        if config is not None:
            extra["config"] = config
        if runtime_tools:
            extra["tools"] = runtime_tools

        target_method = getattr(self._predictor, "forward", None)
        filtered = self._filter_kwargs(target_method, extra)

        with dspy.context(**ctx):
            return self._predictor(
                goal=goal,
                images=images,
                context=context,
                **filtered
            )

    async def aforward(
        self,
        goal: str,
        images: Optional[List[str]] = None,
        context: Optional[str] = None,
        *,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None,
        call_context: Optional[Dict[str, Any]] = None,
        call_params: Optional[Dict[str, Any]] = None,
        **call_kwargs: Any,
    ):
        """
        Execute task with images asynchronously.
        
        Args:
            goal: Task description
            images: List of image paths or base64 encoded images
            context: ROMA execution context (XML)
            tools: Optional tools for this execution
            config: Per-call LM config overrides
            call_context: DSPy context overrides
            call_params: Additional predictor parameters
            **call_kwargs: Additional keyword arguments
            
        Returns:
            ExecutorResult with output and sources
        """
        # Get execution-scoped tools if available (ROMA toolkit integration)
        execution_tools = await self._get_execution_tools()
        runtime_tools = self._merge_tools(execution_tools, tools)
        self._update_predictor_tools(runtime_tools)

        ctx = dict(self._context_defaults)
        if call_context:
            ctx.update(call_context)
        ctx.setdefault("lm", self._lm)
        if hasattr(self, "_adapter") and self._adapter is not None:
            ctx["adapter"] = self._adapter

        extra = dict(call_params or {})
        if call_kwargs:
            extra.update(call_kwargs)
        if config is not None:
            extra["config"] = config
        if runtime_tools:
            extra["tools"] = runtime_tools

        method_for_filter = getattr(self._predictor, "aforward", None) or getattr(
            self._predictor, "forward", None
        )
        filtered = self._filter_kwargs(method_for_filter, extra)

        with dspy.context(**ctx):
            acall = getattr(self._predictor, "acall", None)
            payload = dict(goal=goal, images=images, context=context)
            if acall is not None:
                return await acall(**payload, **filtered)
            return self._predictor(**payload, **filtered)

    @classmethod
    def from_provider(
        cls,
        prediction_strategy: Union[PredictionStrategy, str] = PredictionStrategy.CHAIN_OF_THOUGHT,
        *,
        model: str,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        **model_config: Any,
    ) -> "MultimodalExecutor":
        """
        Create executor from model provider string.
        
        Args:
            prediction_strategy: Prediction strategy
            model: Model string (e.g., "openrouter/anthropic/claude-3-5-sonnet")
            tools: Optional tools
            **model_config: Model configuration
            
        Returns:
            Configured MultimodalExecutor instance
        """
        return cls(
            prediction_strategy,
            model=model,
            model_config=model_config or None,
            tools=tools,
        )

