"""Multimodal Verifier that extends ROMA's Verifier with VLM capabilities."""

from __future__ import annotations

import dspy
from typing import Union, Any, Optional, Dict, List, Mapping, Sequence

# Import from ROMA library
from roma_dspy.core.modules.base_module import BaseModule
from roma_dspy.types import PredictionStrategy

# Import our multimodal signature
from roma_vlm.signatures import MultimodalVerifierSignature


class MultimodalVerifier(BaseModule):
    """
    Verifier with Vision Language Model support.
    
    Validates outputs against goals while considering image context.
    VLM can verify if outputs correctly describe or analyze images.
    
    Example:
        verifier = MultimodalVerifier(
            model="openrouter/anthropic/claude-3-5-sonnet",
            model_config={"temperature": 0.0}
        )
        
        result = await verifier.aforward(
            goal="Identify objects in image",
            images=["photo.jpg"],
            candidate_output="I see a cat, a tree, and a house"
        )
        
        if result.verdict:
            print("Output verified!")
        else:
            print(f"Issue: {result.feedback}")
    """

    DEFAULT_SIGNATURE = MultimodalVerifierSignature

    def __init__(
        self,
        prediction_strategy: Union[PredictionStrategy, str] = PredictionStrategy.PREDICT,
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
        goal: str,
        candidate_output: str,
        images: Optional[List[str]] = None,
        memories: Optional[str] = None,
        context: Optional[str] = None,
        *,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None,
        call_context: Optional[Dict[str, Any]] = None,
        call_params: Optional[Dict[str, Any]] = None,
        **call_kwargs: Any,
    ):
        """Verify output with image context and memories (synchronous)."""
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
                memories=memories,
                candidate_output=candidate_output,
                context=context,
                **filtered
            )

    async def aforward(
        self,
        goal: str,
        candidate_output: str,
        images: Optional[List[str]] = None,
        memories: Optional[str] = None,
        context: Optional[str] = None,
        *,
        tools: Optional[Union[Sequence[Any], Mapping[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None,
        call_context: Optional[Dict[str, Any]] = None,
        call_params: Optional[Dict[str, Any]] = None,
        **call_kwargs: Any,
    ):
        """Verify output with images and memories asynchronously."""
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
            payload = dict(
                goal=goal,
                images=images,
                memories=memories,
                candidate_output=candidate_output,
                context=context
            )
            if acall is not None:
                return await acall(**payload, **filtered)
            return self._predictor(**payload, **filtered)

