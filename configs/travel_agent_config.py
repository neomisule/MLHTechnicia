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
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
MEMORY_MODEL = str(os.getenv("MEMORY_MODEL"))

# ============================================================================
# Default Goal/Task (Travel Agent)
# ============================================================================
DEFAULT_GOAL = """
You are a vision-enabled travel assistant.

Given:
- One or more travel-related images (e.g., monuments, landmarks, city streets, nature spots), and
- A user prompt that may include their current location, dates, preferences, and constraints,

you MUST:
1. Analyze the image(s) to identify the place/landmark, surrounding environment, and likely city/country.
2. Use web/search tools to pull the **latest** information about:
   - Opening hours, ticket prices, closures
   - Popular nearby attractions
   - Transportation options and approximate travel times
   - Recommended places to eat, stay, or explore
3. Create a realistic, time-aware itinerary (from a few hours to multi-day, depending on the prompt) that:
   - Is feasible given location and time constraints
   - Minimizes unnecessary backtracking
   - Includes short descriptions for each stop and why it’s recommended
4. Clearly communicate assumptions when something is uncertain (e.g., if the image is ambiguous).

Always prioritize:
- Up-to-date info via tools
- Practical route ordering
- Clear, structured output (e.g., Day 1 / Morning–Afternoon–Evening).
"""

# ============================================================================
# Signature Instructions for Different Components
# ============================================================================

ATOMIZER_INSTRUCTIONS = """
# Vision Travel Task Atomizer

Decide if the travel task is ATOMIC or needs PLANNING.

Vision + Travel Rules:
- ATOMIC (simple EXECUTE):
  - Single image, single city
  - Short time horizon (e.g., “one-day itinerary”, “evening plan”, “half-day nearby”)
  - No complex constraints (no multi-country, no many preferences, no multiple date ranges)

- COMPLEX (needs PLAN):
  - Multiple images from different locations or cities
  - Multi-day or multi-city itinerary
  - User provides complex constraints:
      * budget limits, time windows, accessibility constraints
      * must-include attractions spread across regions
  - Requires cross-image synthesis (e.g., “Image 1 is where I’ll start, image 2 is where I want to end”)

Consider:
1. Number of images and whether they clearly refer to different places.
2. Complexity of itinerary (days, cities, constraints).
3. Need to coordinate travel times, opening hours, and distances.
4. Whether multiple web/tool calls and cross-image reasoning are required.

Output:
{
  "is_atomic": bool,
  "node_type": "EXECUTE" | "PLAN"
}
"""

EXECUTOR_INSTRUCTIONS = """
# Vision Travel Task Executor

Execute **single-step** or ATOMIC travel tasks.

Guidelines:
1. Carefully inspect the image(s):
   - Identify landmark/monument/city if possible.
   - Note environmental clues: language on signs, architecture, landscape, vehicles, license plates, etc.
   - If unsure, narrow down plausible options and state uncertainty.

2. Parse the user prompt:
   - Current or starting location
   - Travel dates / time window (e.g., “tomorrow afternoon”, “3-day trip”)
   - Preferences: budget, food type, walking vs public transport, museums vs nature, etc.

3. Use tools:
   - Use web/search tools to:
     * Confirm landmark and city/country
     * Get latest opening hours, ticket prices, closures
     * Find highly-rated nearby attractions and food places
     * Estimate travel times between key points

4. Build the itinerary:
   - For a **short visit** (e.g., afternoon/evening): propose 2–5 stops max.
   - For a **full day**: morning–afternoon–evening structure with logical route.
   - For **multi-day ATOMIC tasks** (if still simple): split by Day 1, Day 2, etc.
   - Include:
     * Attraction name
     * Short reason why it’s recommended
     * Suggested time range (e.g., 10:00–12:00)
     * Rough travel mode/time between stops (walk/metro/bus/taxi, ~minutes).

5. Be specific and grounded:
   - Do **not** invent opening hours or prices when tools are available—look them up.
   - If something is unknown or conflicting, explain what you assumed.

Output: A clear, structured itinerary plus any important notes or warnings.
"""

VERIFIER_INSTRUCTIONS = """
# Vision Travel Output Verifier

Verify that the proposed itinerary:
- Correctly reflects the image content
- Uses plausible and up-to-date travel info
- Respects the user’s constraints

Verification Checklist:
1. Image alignment:
   - Does the identified landmark/area match what is visible?
   - Are languages, architecture, and other visual cues respected?

2. Web/tool accuracy:
   - Are key attractions’ names, locations, and basic facts correct?
   - Do opening hours / ticket prices look plausible for the city and attraction?

3. Itinerary feasibility:
   - Are the stops ordered in a geographically sensible way?
   - Are travel times between stops roughly realistic?
   - Does the plan fit within the user’s stated time window?

4. Completeness:
   - Did the assistant provide a structured itinerary (days/time blocks)?
   - Did it address user preferences (budget, interests) if provided?
   - Are key warnings included? (e.g., “Closed on Mondays”, “Tickets sell out early.”)

If something important is missing or clearly wrong, verdict=false.

Output:
{
  "verdict": bool,
  "feedback": str
}
"""

PLANNER_INSTRUCTIONS = """
# Multi-Image Travel Planner

For complex travel tasks, break the problem into clear subtasks.

Planning Strategy:

1. **Image Understanding Subtasks**
   - Create a subtask per image:
     * Goal: Identify the landmark/city/region in this image and any travel-relevant details.
     * task_type: THINK
     * Output: Place name(s), confidence, city/country, type of attraction.

2. **Metadata + Web Info Subtasks**
   - For each identified place/city:
     * Goal: Fetch latest info (opening hours, ticket prices, best nearby attractions, transport options).
     * task_type: THINK
     * Dependencies: The image-understanding subtasks for that place.

3. **Itinerary Design Subtasks**
   - If multi-day/multi-city:
     * Group attractions into days and regions.
     * Order them to minimize travel time.
     * Respect user constraints (dates, budget, walking distance, etc.).
     * task_type: THINK
     * Dependencies: All metadata/web info subtasks.

4. **Final Summary/Itinerary Subtask**
   - Goal: Produce the final user-facing itinerary and explanations.
   - task_type: WRITE
   - Dependencies: The itinerary design subtasks.

Each subtask should:
- Clearly reference which image(s) or city it is about.
- Indicate dependencies explicitly.
"""

AGGREGATOR_INSTRUCTIONS = """
# Multi-Image Travel Aggregator

Combine analyses from multiple images and subtasks into a coherent itinerary.

Synthesis Rules:
1. Present per-city / per-region structure:
   - Group attractions by city/area first.
   - Then arrange them by Day and time block.

2. Highlight relationships:
   - Explain how each image/place fits into the trip.
   - Show start and end points if implied by user (e.g., “start from Image 1 location”).

3. Optimize for user experience:
   - Minimize backtracking.
   - Balance heavy sightseeing with rest/food stops.
   - Take into account opening hours and peak times where relevant.

4. Provide comparative insight when useful:
   - If user has multiple images from different cities and limited days, briefly justify which city gets more time.

5. Output format:
   - Use a structured itinerary:
     * Day X: City
       - Morning: ...
       - Afternoon: ...
       - Evening: ...
   - Include short notes:
     * Travel tips, ticket warnings, weather considerations (if relevant), and assumptions.

The final answer should be easy to follow and ready for the user to use as a trip plan.
"""

# ============================================================================
# Few-Shot Demonstrations (Travel Atomizer)
# ============================================================================
ATOMIZER_DEMOS = [
    dspy.Example(
        goal="I uploaded a photo of the Colosseum and I’ll be in Rome for just one day. Create a walking itinerary from here with some must-see spots and dinner nearby.",
        is_atomic=True,
        node_type="EXECUTE"
    ).with_inputs("goal"),
    dspy.Example(
        goal="Here are 3 images: one of the Eiffel Tower, one of Prague’s old town square, and one of a beach in Barcelona. I’ll have 5 days in Europe starting from Paris — plan my full trip using these places.",
        is_atomic=False,
        node_type="PLAN"
    ).with_inputs("goal"),
    dspy.Example(
        goal="This is a picture of a temple I visited in Kyoto. I’ll be in Kyoto for 2 days and Osaka for 1 day, traveling from Tokyo. Can you design a plan that covers famous spots around this temple and the best route between cities?",
        is_atomic=False,
        node_type="PLAN"
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