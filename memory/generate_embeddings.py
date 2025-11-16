import asyncio
import openai
import numpy as np

client = openai.AsyncClient()
async def generate_embeddings(strings: list[str]):
    out = await client.embeddings.create(input=strings,model="text-embedding-3-small",dimensions=1536)
    return [item.embedding for item in out.data]