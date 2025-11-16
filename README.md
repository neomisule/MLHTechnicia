# ROMA-VLM: Multimodal Vision Extension for ROMA

This project extends the ROMA (Recursive Open Meta-Agents) framework with Vision Language Model (VLM) capabilities, allowing each node (Atomizer, Planner, Executor, Aggregator, Verifier) to process both text and images.



# 🎯 Features

- **VLM-Powered Nodes**: Every ROMA node can accept images as inputs
- **Different VLMs per Node**: Configure different vision models for each agent
- **Configurable Prediction Strategies**: Use Chain of Thought, ReAct, or CodeAct for each node
- **Signature Instructions**: Customize agent behavior with domain-specific prompts (NEW!)
- **Few-Shot Learning**: Add demos for improved vision analysis accuracy (NEW!)
- **Recursive Image Processing**: Images flow through the task hierarchy
- **Zero ROMA Modifications**: Uses ROMA as a library, no core changes needed
- **Drop-in Replacement**: Compatible with existing ROMA workflows

# 🚀 Installation

```bash
# Create venv
python3 -m venv vlm-roma-env
source vlm-roma-env/bin/activate  # This is for macOS/Linux but for windows use roma-vlm\Scripts\activate 
pip install -r requirements.txt # install all the dependences

# now we need to install ROMA into this environment and hence use following
cd ..
git clone https://github.com/sentient-agi/ROMA.git
cd ../ROMA
pip install -e .
cd ../MLHTechnicia
pip install -e . # downloading roma-vlm into our env so that we can import it anywhere easily
```

# 📦 Project Structure

```
roma-vlm-extension/
├── roma_vlm/
│   ├── signatures/          # Multimodal signatures extending ROMA
│   ├── modules/             # VLM-enabled modules (Atomizer, Planner, etc.)
│   ├── engine/              # Multimodal solve() function
│   ├── config/              # VLM-specific configuration
│   └── utils/               # Image handling utilities
├── examples/                # Usage examples
├── tests/                   # Test suite
├── config/                  # YAML configuration profiles
└── pyproject.toml
```

# 🔄 Data Flow

## 1. Single Image Analysis (Atomic Task)

```
User Input: goal + image
         ↓
MultimodalAtomizer(goal, [image])
  ├─ VLM analyzes: "Can I handle this directly?"
  └─ Result: is_atomic = True
         ↓
MultimodalExecutor(goal, [image])
  ├─ VLM analyzes image
  └─ Result: analysis output
         ↓
MultimodalVerifier(goal, [image], output)
  ├─ VLM checks: "Does output match image?"
  └─ Result: verdict = True
         ↓
Final Result
```

## 2. Multi-Image Task with Planning

```
User Input: goal + images
         ↓
MultimodalAtomizer(goal, [img1, img2, img3])
  ├─ VLM: "This needs decomposition"
  └─ Result: is_atomic = False
         ↓
MultimodalPlanner(goal, [img1, img2, img3])
  ├─ VLM analyzes images
  ├─ Creates subtasks referencing specific images
  └─ Result: [subtask1, subtask2, subtask3]
         ↓
    ┌────┴────┬────────┐
    ▼         ▼        ▼
Executor   Executor  Executor
(img1)     (img2)    (img3)
    │         │        │
    └────┬────┴────────┘
         ↓
MultimodalAggregator(goal, [img1,img2,img3], results)
  ├─ VLM synthesizes with image context
  └─ Result: synthesized output
         ↓
MultimodalVerifier(goal, [img1,img2,img3], output)
  └─ Result: verdict
         ↓
Final Result
```