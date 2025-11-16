# query could be like attach an image and ask the agent to go figure out what problem is the agent facing
    # - Medical image analysis (educational)
    # - Cell counting
    # - Chart/graph extraction
    # - Microscopy analysis




# ROMA-VLM Configuration Profile: Medical Vision Agent
# Optimized for medical imaging analysis with conservative settings

defaults:
  temperature: 0.3  # Lower for medical accuracy
  cache: true
  max_tokens: 8192  # Higher for detailed reports

agents:
  atomizer:
    model: "openrouter/anthropic/claude-3-5-sonnet"
    temperature: 0.4
    cache: false
    description: "Conservative atomization for medical tasks"
    
  planner:
    model: "openrouter/openai/gpt-4o"
    temperature: 0.5
    cache: true
    description: "Structured medical task planning"
    
  executor:
    model: "openrouter/anthropic/claude-3-5-sonnet"
    temperature: 0.3
    cache: true
    max_tokens: 8192
    description: "Detailed medical image analysis"
    
  aggregator:
    model: "openrouter/anthropic/claude-3-5-sonnet"
    temperature: 0.4
    cache: true
    max_tokens: 8192
    description: "Careful synthesis of medical findings"
    
  verifier:
    model: "openrouter/anthropic/claude-3-5-sonnet"
    temperature: 0.0
    cache: false
    description: "Strict medical output verification"

image_settings:
  max_size_mb: 10.0  # Larger for medical images
  max_dimension: 4096  # Higher resolution
  allowed_formats: ["JPEG", "PNG", "DICOM"]  # Medical formats
  auto_resize: false  # Preserve medical image quality

execution:
  max_depth: 3  # Controlled depth for medical tasks
  verify_by_default: true  # Always verify medical outputs
  parallel_subtasks: false

# Medical-specific settings
medical:
  disclaimer: true  # Add educational disclaimer
  structured_output: true  # Enforce structured reports
  confidence_scores: true  # Include confidence in findings

