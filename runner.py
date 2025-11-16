import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from roma_vlm import multimodal_solve

image_path = sys.argv[1]
model = os.getenv("MODEL", "anthropic/claude-sonnet-4-5")
max_depth = os.getenv("MAX_DEPTH", 5)
use_verifier = os.getenv("USE_VERIFIER", "True")

goal = """Analyze this image in detail.         
Provide:
1. A comprehensive description of what you see
2. All visible text (OCR if applicable)
3. Key objects, people, or elements
4. Colors, composition, and layout
5. Any notable details or patterns
        
Be thorough and specific."""

async def test_image_analysis():
    
    result = await multimodal_solve(
        goal=goal,
        images=image_path,        
        atomizer_model=model, 
        planner_model=model,   
        executor_model=model,  
        aggregator_model=model,
        verifier_model=model,
        atomizer_config={"temperature": 0.3},    # Lower = more focused
        planner_config={"temperature": 0.4},     # Slightly higher for planning
        executor_config={"temperature": 0.2},    # Very low for accuracy
        aggregator_config={"temperature": 0.3},  # Low for precise synthesis
        verifier_config={"temperature": 0.0},    # Zero for strict verification        
        max_depth=max_depth,
        verify=use_verifier
    )
    
    print("=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(result)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_image_analysis())