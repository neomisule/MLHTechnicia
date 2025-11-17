import asyncio
import sys
import os
from pathlib import Path
import dspy
import importlib

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

# ============================================================================
# Config Loader
# ============================================================================
def load_agent_config(agent_name):
    """
    Dynamically load the appropriate config module based on the agent name.
    
    Args:
        agent_name: Name of the agent (e.g., "general_agent", "crypto_agent", "travel_agent")
    
    Returns:
        Config module with all necessary configurations
    """
    # Map agent names to config module names
    agent_config_map = {
        "general_agent": "configs.general_config",
        "crypto_agent": "configs.crypto_agent_config",
        "travel_agent": "configs.travel_agent_config",
        "self_care_agent": "configs.self_care_agent_config",
        "capital_one_agent": "configs.c1_agent_config",
    }
    
    # Get the config module name, default to general_config if not found
    config_module_name = agent_config_map.get(agent_name, "configs.general_config")
    
    try:
        # Dynamically import the config module
        config_module = importlib.import_module(config_module_name)
        print(f"✓ Loaded config for agent: {agent_name}")
        return config_module
    except ImportError as e:
        print(f"⚠ Warning: Could not load config for {agent_name}, falling back to general_config. Error: {e}")
        # Fall back to general config if specific config not found
        return importlib.import_module("configs.general_config")

async def runner(goal, image_path, model=None, agent="general_agent"):
    """
    Main runner function that processes requests with agent-specific configurations.
    
    Args:
        goal: The task/question to solve
        image_path: Path(s) to image file(s) 
        model: Optional model override (if None, uses config default)
        agent: Agent type (e.g., "general_agent", "crypto_agent", "travel_agent")
    
    Returns:
        Result from multimodal_solve
    """
    # Load the appropriate config for the selected agent
    config = load_agent_config(agent)
    
    # Use the model from parameter or fall back to config
    selected_model = model if model is not None else config.MODEL
    
    print(f"✓ Using model: {selected_model}")
    print(f"✓ Using agent config: {agent}")
    
    # Initialize tools with configurations from the loaded config
    calculator = CalculatorToolkit(**config.TOOL_CONFIGS["calculator"])
    binance = BinanceToolkit(**config.TOOL_CONFIGS["binance"])
    coingecko = CoinGeckoToolkit(**config.TOOL_CONFIGS["coingecko"])
    defillama = DefiLlamaToolkit(**config.TOOL_CONFIGS["defillama"])
    web_search = WebSearchToolkit(**config.TOOL_CONFIGS["web_search"])
    
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
    #     collection_name=config.COLLECTION_NAME,
    #     categories=None,  # Search across all categories
    #     score_threshold=config.MEMORY_CONFIG["score_threshold"],
    #     limit=config.MEMORY_CONFIG["limit"]
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
        atomizer_model=selected_model, 
        planner_model=selected_model,   
        executor_model=selected_model,  
        aggregator_model=selected_model,
        verifier_model=selected_model,
        atomizer_config=config.MODEL_CONFIGS["atomizer"],
        planner_config=config.MODEL_CONFIGS["planner"],
        executor_config=config.MODEL_CONFIGS["executor"],
        aggregator_config=config.MODEL_CONFIGS["aggregator"],
        verifier_config=config.MODEL_CONFIGS["verifier"],
        atomizer_strategy=config.STRATEGIES["atomizer"],
        planner_strategy=config.STRATEGIES["planner"],
        executor_strategy=config.STRATEGIES["executor"],
        aggregator_strategy=config.STRATEGIES["aggregator"],
        verifier_strategy=config.STRATEGIES["verifier"],
        executor_tools=all_tools,
        max_depth=config.MAX_DEPTH,
        verify=config.USE_VERIFIER,
        atomizer_signature_instructions=config.ATOMIZER_INSTRUCTIONS,
        executor_signature_instructions=config.EXECUTOR_INSTRUCTIONS,
        verifier_signature_instructions=config.VERIFIER_INSTRUCTIONS,
        planner_signature_instructions=config.PLANNER_INSTRUCTIONS,
        aggregator_signature_instructions=config.AGGREGATOR_INSTRUCTIONS,
        atomizer_demos=config.ATOMIZER_DEMOS,
    )
    
    
    # Update memories based on the interaction
    # await update_memories(existing_memories=retrieved_memories, messages=[
    #     {"role": "user", "content": goal},
    #     {"role": "assistant", "content": result}], model = config.MEMORY_MODEL)
        
    return result

if __name__ == "__main__":
    result = asyncio.run(runner())
    print(result)