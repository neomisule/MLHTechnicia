"""Example: Build custom pipeline with individual modules."""

import asyncio
from roma_vlm.modules import (
    MultimodalAtomizer,
    MultimodalPlanner,
    MultimodalExecutor,
    MultimodalAggregator,
)
from roma_vlm.engine import create_multimodal_pipeline


async def use_individual_modules():
    """Use modules individually for custom orchestration."""
    
    # Initialize modules with specific VLMs
    executor = MultimodalExecutor(
        model="openrouter/anthropic/claude-3-5-sonnet",
        model_config={"temperature": 0.7}
    )
    
    # Direct execution without full pipeline
    result = await executor.aforward(
        goal="Describe the main subjects in this image in detail",
        images=["path/to/image.jpg"]
    )
    
    print("Direct Execution Result:")
    print(result.output)


async def custom_orchestration():
    """Build custom orchestration logic."""
    
    # Create pipeline
    pipeline = create_multimodal_pipeline(
        atomizer_model="openrouter/google/gemini-2.0-flash-exp",
        executor_model="openrouter/anthropic/claude-3-5-sonnet",
        planner_model="openrouter/openai/gpt-4o"
    )
    
    goal = "Analyze this product image and suggest improvements"
    images = ["path/to/product.jpg"]
    
    # Custom logic: Try atomic execution first
    atomized = await pipeline["atomizer"].aforward(
        goal=goal,
        images=images
    )
    
    if atomized.is_atomic:
        print("Task is atomic - executing directly")
        result = await pipeline["executor"].aforward(
            goal=goal,
            images=images
        )
        final_output = result.output
    else:
        print("Task needs planning - decomposing")
        plan = await pipeline["planner"].aforward(
            goal=goal,
            images=images
        )
        
        print(f"Created {len(plan.subtasks)} subtasks:")
        for i, subtask in enumerate(plan.subtasks, 1):
            print(f"  {i}. {subtask.goal}")
        
        # Execute subtasks
        results = []
        for subtask in plan.subtasks:
            sub_result = await pipeline["executor"].aforward(
                goal=subtask.goal,
                images=images
            )
            subtask.result = sub_result.output
            results.append(subtask)
        
        # Aggregate
        aggregated = await pipeline["aggregator"].aforward(
            original_goal=goal,
            original_images=images,
            subtasks_results=results
        )
        final_output = aggregated.synthesized_result
    
    print("\n" + "=" * 80)
    print("FINAL OUTPUT")
    print("=" * 80)
    print(final_output)


async def parallel_analysis():
    """Analyze multiple images in parallel with same executor."""
    
    executor = MultimodalExecutor(
        model="openrouter/anthropic/claude-3-5-sonnet",
        model_config={"temperature": 0.5}
    )
    
    images = [
        "path/to/image1.jpg",
        "path/to/image2.jpg",
        "path/to/image3.jpg",
    ]
    
    # Parallel execution
    tasks = [
        executor.aforward(
            goal=f"Analyze image {i+1} and describe key features",
            images=[img]
        )
        for i, img in enumerate(images)
    ]
    
    results = await asyncio.gather(*tasks)
    
    print("Parallel Analysis Results:")
    for i, result in enumerate(results, 1):
        print(f"\nImage {i}:")
        print(result.output)
        print("-" * 80)


if __name__ == "__main__":
    # Use individual modules
    asyncio.run(use_individual_modules())
    
    # Or custom orchestration
    # asyncio.run(custom_orchestration())
    
    # Or parallel analysis
    # asyncio.run(parallel_analysis())

