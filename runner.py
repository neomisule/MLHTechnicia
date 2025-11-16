import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from roma_vlm import multimodal_solve

image_path = sys.argv[1] if len(sys.argv) > 1 else "imgs/reciept.png"



async def test_image_analysis():
    
    result = await multimodal_solve(
        # More detailed goal/prompt
        goal="""Analyze this image in detail. 
        
        Provide:
        1. A comprehensive description of what you see
        2. All visible text (OCR if applicable)
        3. Key objects, people, or elements
        4. Colors, composition, and layout
        5. Any notable details or patterns
        
        Be thorough and specific.""",
        
        images=image_path,
        
        # Use best available models (from your account)
        atomizer_model="anthropic/claude-sonnet-4-5",  # Best for decisions
        planner_model="anthropic/claude-sonnet-4-5",   # Best for planning
        executor_model="anthropic/claude-sonnet-4-5",  # Best for analysis
        aggregator_model="anthropic/claude-sonnet-4-5", # Best for synthesis
        verifier_model="anthropic/claude-sonnet-4-5",   # Best for verification
        
        # Better temperature settings
        atomizer_config={"temperature": 0.3},    # Lower = more focused
        planner_config={"temperature": 0.4},     # Slightly higher for planning
        executor_config={"temperature": 0.2},    # Very low for accuracy
        aggregator_config={"temperature": 0.3},  # Low for precise synthesis
        verifier_config={"temperature": 0.0},    # Zero for strict verification
        
        # Allow deeper recursion for complex tasks
        max_depth=5,  # Default, allows proper task decomposition
        
        # Enable verification
        verify=True
    )
    
    print("=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_image_analysis())

