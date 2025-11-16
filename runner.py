import asyncio
import sys
import os
from pathlib import Path
import dspy
from dotenv import load_dotenv
load_dotenv()
from roma_vlm import multimodal_solve
from roma_dspy.tools import (
    CalculatorToolkit,
    WebSearchToolkit,
    BinanceToolkit,
    CoinGeckoToolkit,
    DefiLlamaToolkit,
)

from memory.vectordb import init_qdrant, get_all_categories, search_memories, stringify_retrieved_point
from memory.generate_embeddings import generate_embeddings
from memory.update_memory import update_memories





image_path = sys.argv[1]
model = str(os.getenv("MODEL"))
web_search_model = str(os.getenv("WEB_SEARCH_MODEL"))
max_depth = int(os.getenv("MAX_DEPTH"))
use_verifier = bool(os.getenv("USE_VERIFIER"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
MEMORY_MODEL = str(os.getenv("MEMORY_MODEL"))

# goal = """Analyze this image in detail.         
# Provide:
# 1. A comprehensive description of what you see
# 2. All visible text (OCR if applicable)
# 3. Key objects, people, or elements
# 4. Colors, composition, and layout
# 5. Any notable details or patterns
        
# Be thorough and specific."""

goal = """Use a calculator tool to help me perform calculation as seen in the image"""

# Define custom signature instructions for vision tasks
ATOMIZER_INSTRUCTIONS = """
# Vision Task Atomizer

Analyze the goal and images to determine if the task is ATOMIC or needs PLANNING.

Vision-Specific Rules:
- ATOMIC: Single image analysis, simple OCR, object detection in one image
- COMPLEX: Multi-image comparison, sequential analysis, complex visual reasoning

Consider:
1. Number of images and their relationships
2. Complexity of visual analysis required
3. Need for cross-image synthesis
4. Whether tools are needed for analysis

Output: {"is_atomic": bool, "node_type": "EXECUTE"|"PLAN"}
"""

EXECUTOR_INSTRUCTIONS = """
# Vision Task Executor

Execute image analysis tasks with precision and detail.

Guidelines:
1. Analyze images thoroughly before responding
2. Extract all visible text (OCR) when relevant
3. Describe objects, people, and scenes accurately
4. Note colors, composition, and spatial relationships
5. Use tools when needed for calculations or web search
6. Be specific and factual - avoid speculation

For medical/technical images:
- Use proper terminology
- Note any visible measurements or scales
- Describe conditions objectively
"""

# MEDICAL_EXECUTOR_INSTRUCTIONS = """
# # Medical Image Executor

# Analyze medical images with professional accuracy.

# Critical Guidelines:
# 1. Use proper medical terminology
# 2. Identify visible structures, organs, or conditions
# 3. Note any measurements, scales, or labels
# 4. Describe findings objectively without diagnosis
# 5. Include relevant anatomical details
# 6. Add disclaimer: This is educational analysis only

# Format:
# - Observations: What is visible
# - Measurements: Any visible metrics
# - Notable Features: Key findings
# - Disclaimer: Educational purpose statement
# """


#     CALCULATOR_EXECUTOR_INSTRUCTIONS = """
# # Calculator-Enhanced Vision Executor

# Extract numbers from images and perform calculations.

# Workflow:
# 1. Extract all numbers visible in the image via OCR
# 2. Identify the mathematical operation needed
# 3. Use calculator tool to compute the result
# 4. Verify calculation matches image context
# 5. Present final answer clearly

# Be precise with number extraction - double-check OCR results.
# """



VERIFIER_INSTRUCTIONS = """
# Vision Output Verifier

Verify that the analysis accurately reflects the image content.

Verification Checklist:
1. Does the output match what's visible in the images?
2. Is all text accurately transcribed?
3. Are objects and elements correctly identified?
4. Are measurements and numbers accurate?
5. Is the analysis complete per the goal?

Be strict - if the goal requested specific elements and they're missing, verdict=false.

Output: {"verdict": bool, "feedback": str}
"""

PLANNER_INSTRUCTIONS = """
# Multi-Image Comparison Planner

Break down multi-image tasks into systematic subtasks.

Planning Strategy:
1. Create subtask for each image analysis (extract data)
2. Create synthesis subtask to compare results
3. Create summary subtask for final output

Each subtask should:
- Have clear goal mentioning specific image if relevant
- Specify task_type (THINK for analysis, WRITE for summary)
- List dependencies appropriately
"""
    
AGGREGATOR_INSTRUCTIONS = """
# Multi-Image Comparison Aggregator

Synthesize analysis from multiple images into comparative insights.

Synthesis Rules:
1. Present findings from each image clearly
2. Highlight similarities and differences
3. Provide comparative metrics when applicable
4. Draw meaningful conclusions from the comparison
5. Structure output for easy reading

Format as structured comparison.
"""

# Create few-shot demos for vision atomizer
ATOMIZER_DEMOS = [
    dspy.Example(
        goal="Read the text from this receipt image",
        is_atomic=True,
        node_type="EXECUTE"
    ).with_inputs("goal"),
    dspy.Example(
        goal="Compare prices across these 3 store receipt images and find the cheapest",
        is_atomic=False,
        node_type="PLAN"
    ).with_inputs("goal"),
    dspy.Example(
        goal="Analyze this medical chart and extract vitals",
        is_atomic=True,
        node_type="EXECUTE"
    ).with_inputs("goal"),
]
























async def test_image_analysis():
    
    calculator = CalculatorToolkit(enabled=True)
    binance = BinanceToolkit(enabled=True)  # Public endpoints
    coingecko = CoinGeckoToolkit(enabled=True)  # Free tier
    defillama = DefiLlamaToolkit(enabled=True)  # Completely free
    web_search = WebSearchToolkit(
        model=web_search_model,  # Separate model for web search
        search_engine="exa", 
        search_context_size="medium", 
        max_results=10, 
        temperature=0.3, 
        enabled=True
    )
    
    # Combine all tools
    all_tools = {
        **calculator.get_enabled_tools(),
        **binance.get_enabled_tools(),
        **coingecko.get_enabled_tools(),
        **defillama.get_enabled_tools(),
        **web_search.get_enabled_tools(),
    }
    
    # Initialize the memory database
    await init_qdrant()

    # Get related memories from memory database using input query and categories
    goal_embedding = (await generate_embeddings([goal]))[0]
    retrieved_memories = await search_memories(
        search_vector=goal_embedding,
        collection_name=COLLECTION_NAME,
        categories=None,  # Search across all categories
        score_threshold=0.3,  # Minimum similarity score
        limit=5  # Return top 5 most relevant memories
    )
    
    # Format memories for injection into the prompt
    memories_text = None
    if retrieved_memories:
        memories_list = [stringify_retrieved_point(m) for m in retrieved_memories]
        memories_text = "\n\n## Relevant Memories from Previous Interactions:\n" + "\n- ".join(memories_list)
    
    result = await multimodal_solve(
        goal=goal,
        images=image_path,
        memories=memories_text,        
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
        atomizer_strategy="chain_of_thought",    # Options: "chain_of_thought", "react", "code_act"
        planner_strategy="chain_of_thought",
        executor_strategy="react",
        aggregator_strategy="chain_of_thought",
        verifier_strategy="chain_of_thought",
        executor_tools=all_tools,  # Pass all tools to executor
        max_depth=max_depth,
        verify=use_verifier,
        atomizer_signature_instructions=ATOMIZER_INSTRUCTIONS,
        executor_signature_instructions=EXECUTOR_INSTRUCTIONS,
        verifier_signature_instructions=VERIFIER_INSTRUCTIONS,
        planner_signature_instructions=PLANNER_INSTRUCTIONS,
        aggregator_signature_instructions=AGGREGATOR_INSTRUCTIONS,
        atomizer_demos=ATOMIZER_DEMOS,
    )
    
    
    # Update memories based on the interaction
    await update_memories(existing_memories=retrieved_memories, messages=[
        {"role": "user", "content": goal},
        {"role": "assistant", "content": result}], model = MEMORY_MODEL)
        
    return result

if __name__ == "__main__":
    result = asyncio.run(test_image_analysis())
    print(result)