import os
from datetime import datetime
from typing import Optional, Callable
from uuid import uuid4
from pydantic import BaseModel
from qdrant_client import AsyncQdrantClient
from qdrant_client.grpc import Points, ScoredPoint
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import PayloadSchemaType
from qdrant_client.models import Distance, Filter, VectorParams, models
import asyncio
import numpy as np
import pandas as pd
import ast
from .generate_embeddings import generate_embeddings

COLLECTION_NAME = str(os.getenv("COLLECTION_NAME"))
client = AsyncQdrantClient(url=str(os.getenv("QDRANT_URL")))


class EmbeddedMemory(BaseModel):
    user_id: int
    memory_text: str
    categories: list[str]
    date: str
    embedding: list[float]


class RetrievedMemory(BaseModel):
    point_id: str
    user_id: int
    memory_text: str
    categories: list[str]
    date: str
    score: float


async def init_qdrant():
    collections = await client.get_collections()
    existing_names = {c.name for c in collections.collections}

    if COLLECTION_NAME not in existing_names:
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=1536,
                distance=models.Distance.COSINE,
            ),
        )
        print("Recreated collection", COLLECTION_NAME, "with size=1536")
    # Ensure payload index for faceting on `categories`
    try:
        await client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="categories",
            field_schema=PayloadSchemaType.KEYWORD,  # important
        )
    except UnexpectedResponse as e:
        # If index already exists, ignore; otherwise re-raise
        if "already has index for field" in str(e):
            pass
        else:
            raise


async def create_memory_collection():
    if not (await client.collection_exists(COLLECTION_NAME)):
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.DOT),
        )

        await client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="user_id",
            field_schema=models.PayloadSchemaType.INTEGER,
        )

        # Create an index on the 'categories' field
        await client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="categories",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        print("Collection created")
    else:
        print("Collection exists")


async def insert_memories(memories: list[EmbeddedMemory]):
    await client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=uuid4().hex,
                payload={
                    "user_id": memory.user_id,
                    "categories": memory.categories,
                    "memory_text": memory.memory_text,
                    "date": memory.date,
                },
                vector=memory.embedding,
            )
            for memory in memories
        ],
    )


async def search_memories(
    search_vector: list[float],
    collection_name: str,
    categories: Optional[list[str]] = None,
    score_threshold: float = 0.1,
    limit: int = 2,
):
    """
    Search for similar memories in the vector database using semantic similarity.
    
    Args:
        search_vector: Embedding vector (1536-dim) to search for
        collection_name: Name of the Qdrant collection to query
        categories: Optional list of categories to filter by
        score_threshold: Minimum similarity score (0-1) to return
        limit: Maximum number of results to return
        
    Returns:
        List of RetrievedMemory objects sorted by similarity score
    """
    must_conditions: list[models.Condition] = []
    
    if categories is not None and len(categories) > 0:
        must_conditions.append(
            models.FieldCondition(
                key="categories", match=models.MatchAny(any=categories)
            )
        )
    
    query_filter = Filter(must=must_conditions) if must_conditions else None
    
    outs = await client.query_points(
        collection_name=collection_name,
        query=search_vector,
        with_payload=True,
        query_filter=query_filter,
        score_threshold=score_threshold,
        limit=limit,
    )

    return [convert_retrieved_records(point) for point in outs.points if point is not None]

async def add_llm_response_memory(
    user_id: int,
    response_text: str,
    categories: Optional[list[str]] = None,
    date: Optional[str] = None,
):
    """
    Take an LLM response text, generate an embedding, and store it
    as a single memory record in Qdrant.

    Reuses:
      - generate_embeddings()
      - EmbeddedMemory
      - insert_memories()
    """
    if categories is None:
        categories = []

    # Use current UTC time if no date is provided
    if date is None:
        date_str = datetime.utcnow().isoformat()
    else:
        date_str = date

    # generate_embeddings already used in your CSV import (async)
    embeddings = await generate_embeddings([response_text])
    embedding = embeddings[0]

    memory = EmbeddedMemory(
        user_id=user_id,
        memory_text=response_text,
        categories=categories,
        date=date_str,
        embedding=embedding,
    )

    # Reuse existing insertion logic
    await insert_memories([memory])

    return memory  # optional, in case you want to inspect what was stored

# async def import_csv_to_qdrant(
#     csv_path: str,
#     user_id: int,
#     text_column: str,
#     categories_column: Optional[str] = None,
#     date_column: Optional[str] = None,
#     category_separator: str = ",",
# ):
#     """
#     Reads a CSV file, generates embeddings using OpenAI, and inserts into Qdrant.
#     """
#
#     df = pd.read_csv(csv_path)
#
#     # Get texts
#     texts = df[text_column].astype(str).tolist()
#
#     print(f"[INFO] Generating embeddings for {len(texts)} rows...")
#     embeddings = await generate_embeddings(texts)
#     print("[INFO] Embeddings generated.")
#
#     memories = []
#
#     for idx, row in df.iterrows():
#         memory_text = str(row[text_column])
#
#         # Categories
#         if categories_column and categories_column in df.columns:
#             raw_cats = row[categories_column]
#             if isinstance(raw_cats, str):
#                 try:
#                     parsed = ast.literal_eval(raw_cats)
#                     if isinstance(parsed, list):
#                         categories = [str(c).strip() for c in parsed]
#                     else:
#                         categories = [str(parsed).strip()]
#                 except Exception:
#                     categories = [
#                         c.strip()
#                         for c in raw_cats.split(category_separator)
#                         if c.strip()
#                     ]
#             else:
#                 categories = []
#         else:
#             categories = []
#
#         # Date
#         if date_column and date_column in df.columns:
#             if pd.notna(row[date_column]):
#                 date_str = str(row[date_column])
#             else:
#                 date_str = datetime.utcnow().isoformat()
#         else:
#             date_str = datetime.utcnow().isoformat()
#
#         # Build memory object
#         memories.append(
#             EmbeddedMemory(
#                 user_id=user_id,
#                 memory_text=memory_text,
#                 categories=categories,
#                 date=date_str,
#                 embedding=embeddings[idx],
#             )
#         )
#
#     print(f"[INFO] Inserting {len(memories)} rows into Qdrant...")
#     await insert_memories(memories)
#     print("[INFO] Done inserting CSV → Qdrant.")
#


async def delete_user_records(user_id):
    await client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id", match=models.MatchValue(value=user_id)
                    )
                ]
            )
        ),
    )


async def delete_records(point_ids):
    await client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.PointIdsList(points=point_ids),
    )


async def fetch_all_user_records(user_id):
    out = await client.query_points(
        collection_name=COLLECTION_NAME,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id", match=models.MatchValue(value=user_id)
                )
            ]
        ),
    )
    return [convert_retrieved_records(point) for point in out.points]


def convert_retrieved_records(point) -> RetrievedMemory:
    return RetrievedMemory(
        point_id=point.id,
        user_id=point.payload["user_id"],
        memory_text=point.payload["memory_text"],
        categories=point.payload["categories"],
        date=point.payload["date"],
        score=point.score,
    )


async def get_all_categories(collection_name: str):
    """
    Uses Qdrant's facet feature to efficiently get all unique categories
    from the indexed 'categories' field.
    
    Args:
        collection_name: Name of the Qdrant collection to query
        
    Returns:
        List of unique category strings found in the collection
    """
    # Use the facet method to get unique values from the indexed field
    facet_result = await client.facet(
        collection_name=collection_name,
        key="categories",
        limit=1000,  # Maximum number of unique categories to return
    )
    return [hit.value for hit in facet_result.hits]


def stringify_retrieved_point(retrieved_memory: RetrievedMemory):
    return f"""{retrieved_memory.memory_text} (Categories: {retrieved_memory.categories}) Relevance: {retrieved_memory.score:.2f}"""


if __name__ == "__main__":
    asyncio.run(create_memory_collection())