import os

import openai
from mem0 import MemoryClient
from openai import OpenAI

"""
Get a Mem0 API key here: https://mem0.dev/api-keys-avb

Ensure to export the MEM0_API_KEY environment variable.

```bash
export MEM0_API_KEY=your_key_here
```
"""

user_id = "avb"

memory = MemoryClient()
client = openai.Client()
# client = OpenAI(
#     api_key="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",
#     base_url="https://openrouter.ai/api/v1",
# )
messages = []


while True:
    user_input = input("User: ")

    messages.append({"role": "user", "content": user_input})

    related_memories = memory.search(user_input, user_id=user_id)
    print(related_memories)

    related_memories_text = "/n -".join([f"{m['memory']}" for m in related_memories])

    print(related_memories_text)

    ### TODO Sarvesh : Comment this prompt below, and pass the memory
    ### to the ROMA prompt
    system_message = [
        {
            "role": "system",
            "content": f"""answer the user's question honestly.
Here are some relevant information you may find useful that previous interactions with the user has taught us:
{related_memories_text}
        """,
        }
    ]

    ### TODO Sarvesh : Comment this llm call below, and pass the messages
    ### to the ROMA prompt
    response = client.chat.completions.create(
        messages=system_message + messages,
        model=os.getenv("LLM_MODEL_NAME"),
        reasoning_effort="minimal",
    )

    ### TODO Sarvesh : Don't forget to update the memory on the basis of
    ### the llm response.
    answer = response.choices[0].message.content

    messages.append({"role": "assistant", "content": answer})
    print(f"\nAssistant: {answer} \n")

    memory.add(messages[-2:], user_id=user_id)
