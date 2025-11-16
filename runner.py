import asyncio
import sys
import os
from pathlib import Path
import dspy

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

# Import all configurations
from config import (
    MODEL,
    WEB_SEARCH_MODEL,
    MAX_DEPTH,
    USE_VERIFIER,
    COLLECTION_NAME,
    MEMORY_MODEL,
    DEFAULT_GOAL,
    ATOMIZER_INSTRUCTIONS,
    EXECUTOR_INSTRUCTIONS,
    VERIFIER_INSTRUCTIONS,
    PLANNER_INSTRUCTIONS,
    AGGREGATOR_INSTRUCTIONS,
    ATOMIZER_DEMOS,
    MODEL_CONFIGS,
    STRATEGIES,
    TOOL_CONFIGS,
    MEMORY_CONFIG,
)

async def runner(goal, image_path):
    # Initialize tools with configurations
    calculator = CalculatorToolkit(**TOOL_CONFIGS["calculator"])
    binance = BinanceToolkit(**TOOL_CONFIGS["binance"])
    coingecko = CoinGeckoToolkit(**TOOL_CONFIGS["coingecko"])
    defillama = DefiLlamaToolkit(**TOOL_CONFIGS["defillama"])
    web_search = WebSearchToolkit(**TOOL_CONFIGS["web_search"])
    
    # Combine all tools
    all_tools = {
        **calculator.get_enabled_tools(),
        **binance.get_enabled_tools(),
        **coingecko.get_enabled_tools(),
        **defillama.get_enabled_tools(),
        **web_search.get_enabled_tools(),
    }
    
    # Initialize the memory database
    # await init_qdrant()

    # Get related memories from memory database using input query and categories
    # goal_embedding = (await generate_embeddings([goal]))[0]
    # retrieved_memories = await search_memories(
    #     search_vector=goal_embedding,
    #     collection_name=COLLECTION_NAME,
    #     categories=None,  # Search across all categories
    #     score_threshold=MEMORY_CONFIG["score_threshold"],
    #     limit=MEMORY_CONFIG["limit"]
    # )
    
    # Format memories for injection into the prompt
    memories_text = None
    # if retrieved_memories:
    #     memories_list = [stringify_retrieved_point(m) for m in retrieved_memories]
    #     memories_text = "\n\n## Relevant Memories from Previous Interactions:\n" + "\n- ".join(memories_list)
    
    result = await multimodal_solve(
        goal=goal,
        images=image_path,
        memories=memories_text,        
        atomizer_model=MODEL, 
        planner_model=MODEL,   
        executor_model=MODEL,  
        aggregator_model=MODEL,
        verifier_model=MODEL,
        atomizer_config=MODEL_CONFIGS["atomizer"],
        planner_config=MODEL_CONFIGS["planner"],
        executor_config=MODEL_CONFIGS["executor"],
        aggregator_config=MODEL_CONFIGS["aggregator"],
        verifier_config=MODEL_CONFIGS["verifier"],
        atomizer_strategy=STRATEGIES["atomizer"],
        planner_strategy=STRATEGIES["planner"],
        executor_strategy=STRATEGIES["executor"],
        aggregator_strategy=STRATEGIES["aggregator"],
        verifier_strategy=STRATEGIES["verifier"],
        executor_tools=all_tools,
        max_depth=MAX_DEPTH,
        verify=USE_VERIFIER,
        atomizer_signature_instructions=ATOMIZER_INSTRUCTIONS,
        executor_signature_instructions=EXECUTOR_INSTRUCTIONS,
        verifier_signature_instructions=VERIFIER_INSTRUCTIONS,
        planner_signature_instructions=PLANNER_INSTRUCTIONS,
        aggregator_signature_instructions=AGGREGATOR_INSTRUCTIONS,
        atomizer_demos=ATOMIZER_DEMOS,
    )
    
    
    # Update memories based on the interaction
    # await update_memories(existing_memories=retrieved_memories, messages=[
    #     {"role": "user", "content": goal},
    #     {"role": "assistant", "content": result}], model = MEMORY_MODEL)
        
    return result

if __name__ == "__main__":
    result = asyncio.run(runner(DEFAULT_GOAL, sys.argv[1]))
    print(result)