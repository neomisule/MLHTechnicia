"""Multimodal Atomizer that extends ROMA's Atomizer with VLM capabilities."""

from __future__ import annotations

import dspy
from typing import Union, Any, Optional, Dict, List, Mapping, Sequence

# Import from ROMA library
from roma_dspy.core.modules.base_module import BaseModule
from roma_dspy.types import PredictionStrategy

# Import our multimodal signature
from roma_vlm.signatures import MultimodalAtomizerSignature


class MultimodalAtomizer(BaseModule):
    """
    Atomizer with Vision Language Model support.
    
    Determines if a task (with optional images) is atomic or needs planning.
    VLM can analyze images to make better atomization decisions.
    
    Example:
        atomizer = MultimodalAtomizer(
            model="openrouter/google/gemini-2.0-flash-exp",
            model_config={"temperature": 0.6}
        )
        
        result = await atomizer.aforward(
            goal="Extract data from these medical charts",
            images=["chart1.png", "chart2.png"]
        )
        
        if result.is_atomic:
            # Can execute directly
        else:
            # Needs planning
    """

    DEFAULT_SIGNATURE = MultimodalAtomizerSignature

    def __init__(
        self,
        prediction_strategy: Union[PredictionStrategy, str] = PredictionStrategy.CHAIN_OF_THOUGHT,
        *,
        signature: Any = None,
        config: Optional[Any] = None,
        lm: Optional[dspy.LM] = None,
        model: Optional[str] = None,
        model_config: Optional[Mapping[str, Any]] = None,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        **strategy_kwargs: Any,
    ) -> None:
        super().__init__(
            signature=signature if signature is not None else self.DEFAULT_SIGNATURE,
            config=config,
            prediction_strategy=prediction_strategy,
            lm=lm,
            model=model,
            model_config=model_config,
            tools=tools,
            **strategy_kwargs,
        )

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
        """Atomize task with optional image context (synchronous)."""
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
        """Atomize task with images asynchronously."""
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

