import os
import dspy
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Environment Variables
# ============================================================================
MODEL = str(os.getenv("MODEL"))
WEB_SEARCH_MODEL = str(os.getenv("WEB_SEARCH_MODEL"))
MAX_DEPTH = int(os.getenv("MAX_DEPTH"))
USE_VERIFIER = bool(os.getenv("USE_VERIFIER"))
COLLECTION_NAME = "wellness_excercises"
MEMORY_MODEL = str(os.getenv("MEMORY_MODEL"))

# ============================================================================
# Default Goal/Task
# ============================================================================
DEFAULT_GOAL = """Use a calculator tool to help me perform calculation as seen in the image"""

# ============================================================================
# Signature Instructions for Different Components
# ============================================================================
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

# ============================================================================
# Few-Shot Demonstrations
# ============================================================================
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

# ============================================================================
# Model Configurations
# ============================================================================
MODEL_CONFIGS = {
    "atomizer": {"temperature": 0.3},    # Lower = more focused
    "planner": {"temperature": 0.4},     # Slightly higher for planning
    "executor": {"temperature": 0.2},    # Very low for accuracy
    "aggregator": {"temperature": 0.3},  # Low for precise synthesis
    "verifier": {"temperature": 0.0},    # Zero for strict verification
}

# ============================================================================
# Strategy Configurations
# ============================================================================
STRATEGIES = {
    "atomizer": "chain_of_thought",    # Options: "chain_of_thought", "react", "code_act"
    "planner": "chain_of_thought",
    "executor": "react",
    "aggregator": "chain_of_thought",
    "verifier": "chain_of_thought",
}

# ============================================================================
# Tool Configurations
# ============================================================================
TOOL_CONFIGS = {
    "calculator": {"enabled": True},
    "binance": {"enabled": False},
    "coingecko": {"enabled": False},
    "defillama": {"enabled": False},
    "web_search": {
        "model": WEB_SEARCH_MODEL,
        "search_engine": "exa",
        "search_context_size": "medium",
        "max_results": 10,
        "temperature": 0.3,
        "enabled": False
    }
}

# ============================================================================
# Memory Configuration
# ============================================================================
MEMORY_CONFIG = {
    "score_threshold": 0.3,  # Minimum similarity score
    "limit": 5,  # Return top 5 most relevant memories
}