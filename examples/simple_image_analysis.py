"""Simple example: Analyze a single image with ROMA-VLM."""

import asyncio
from roma_vlm import multimodal_solve


async def main():
    """Analyze a single image."""
    
    # Simple image analysis
    result = await multimodal_solve(
        goal="What objects can you see in this image? List them.",
        images="path/to/your/image.jpg",  # Replace with actual image path
        executor_model="openrouter/anthropic/claude-3-5-sonnet"
    )
    
    print("Analysis Result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

