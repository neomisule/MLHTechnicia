"""Multimodal Aggregator that extends ROMA's Aggregator with VLM capabilities."""

from __future__ import annotations

import dspy
from typing import Union, Any, Optional, Dict, List, Mapping, Sequence

# Import from ROMA library
from roma_dspy.core.modules.base_module import BaseModule
from roma_dspy.types import PredictionStrategy
from roma_dspy.core.signatures.base_models.subtask import SubTask

# Import our multimodal signature
from roma_vlm.signatures import MultimodalAggregatorSignature


class MultimodalAggregator(BaseModule):
    """
    Aggregator with Vision Language Model support.
    
    Synthesizes subtask results while maintaining awareness of original images.
    VLM can reference images when creating final synthesis.
    
    Example:
        aggregator = MultimodalAggregator(
            model="openrouter/anthropic/claude-3-5-sonnet",
            model_config={"temperature": 0.65}
        )
        
        result = await aggregator.aforward(
            original_goal="Analyze these X-rays",
            original_images=["xray1.jpg", "xray2.jpg"],
            subtasks_results=[...]
        )
    """

    DEFAULT_SIGNATURE = MultimodalAggregatorSignature

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
        original_goal: str,
        subtasks_results: Sequence[SubTask],
        original_images: Optional[List[str]] = None,
        *,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None,
        call_context: Optional[Dict[str, Any]] = None,  # Dict for dspy.context()
        context: Optional[str] = None,  # String context from ROMA
        call_params: Optional[Dict[str, Any]] = None,
        **call_kwargs: Any,
    ):
        """
        Aggregate subtask results with image context (synchronous).
        
        Args:
            original_goal: Original task goal
            subtasks_results: List of subtask results
            original_images: Original images for synthesis context
            tools: Optional tools
            config: Per-call config
            call_context: DSPy context dict
            context: ROMA string context
            call_params: Additional params
            **call_kwargs: Additional kwargs
        """
        runtime_tools = self._merge_tools(self._tools, tools)

        ctx = dict(self._context_defaults)
        if call_context:
            ctx.update(call_context)
        ctx.setdefault("lm", self._lm)

        extra = dict(call_params or {})
        if call_kwargs:
            extra.update(call_kwargs)
        if config is not None:
            extra["config"] = config
        if runtime_tools:
            extra["tools"] = runtime_tools
        if context is not None:
            extra["context"] = context

        target_method = getattr(self._predictor, "forward", None)
        filtered = self._filter_kwargs(target_method, extra)

        with dspy.context(**ctx):
            return self._predictor(
                original_goal=original_goal,
                original_images=original_images,
                subtasks_results=list(subtasks_results),
                **filtered,
            )

    async def aforward(
        self,
        original_goal: str,
        subtasks_results: Sequence[SubTask],
        original_images: Optional[List[str]] = None,
        *,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None,
        call_context: Optional[Dict[str, Any]] = None,  # Dict for dspy.context()
        context: Optional[str] = None,  # String context from ROMA (was context_payload)
        call_params: Optional[Dict[str, Any]] = None,
        **call_kwargs: Any,
    ):
        """Aggregate subtask results with images asynchronously."""
        execution_tools = await self._get_execution_tools()
        runtime_tools = self._merge_tools(execution_tools, tools)
        self._update_predictor_tools(runtime_tools)

        ctx = dict(self._context_defaults)
        if call_context:
            ctx.update(call_context)
        ctx.setdefault("lm", self._lm)

        extra = dict(call_params or {})
        if call_kwargs:
            extra.update(call_kwargs)
        if config is not None:
            extra["config"] = config
        if runtime_tools:
            extra["tools"] = runtime_tools
        if context is not None:
            extra["context"] = context

        method_for_filter = getattr(self._predictor, "aforward", None) or getattr(
            self._predictor, "forward", None
        )
        filtered = self._filter_kwargs(method_for_filter, extra)

        with dspy.context(**ctx):
            acall = getattr(self._predictor, "acall", None)
            payload = dict(
                original_goal=original_goal,
                original_images=original_images,
                subtasks_results=list(subtasks_results),
            )
            if acall is not None:
                return await acall(**payload, **filtered)
            return self._predictor(**payload, **filtered)

