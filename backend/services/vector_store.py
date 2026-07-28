from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, ScoredPoint, Filter, FieldCondition, MatchValue
from core.config import settings
from typing import List, Dict, Any
import uuid

# We will import get_embedding_dimension dynamically to avoid circular imports if any,
# or we can import it at the top. Let's import at top since it's just a function.
from services.embeddings import get_embedding_dimension

class VectorStore:
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.QDRANT_URL)

    def get_collection_name(self, embedding_model: str) -> str:
        # Backward compatibility for the original hardcoded collection
        if embedding_model == "BAAI/bge-small-en-v1.5":
            return "documents"
        
        # Sanitize model name for Qdrant collection name
        sanitized = embedding_model.replace("/", "_").replace("-", "_").lower()
        return f"documents_{sanitized}"

    async def initialize_collection(self, embedding_model: str = "BAAI/bge-small-en-v1.5"):
        collection_name = self.get_collection_name(embedding_model)
        collections = await self.client.get_collections()
        if not any(c.name == collection_name for c in collections.collections):
            vector_size = get_embedding_dimension(embedding_model)
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    async def upsert_points(self, points: List[PointStruct], embedding_model: str = "BAAI/bge-small-en-v1.5"):
        await self.initialize_collection(embedding_model)
        collection_name = self.get_collection_name(embedding_model)
        await self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    async def search(self, query_vector: List[float], limit: int = 20, dataset_id: int = None, embedding_model: str = "BAAI/bge-small-en-v1.5") -> List[ScoredPoint]:
        collection_name = self.get_collection_name(embedding_model)
        
        # We need to make sure the collection exists, but usually we only search if we have documents.
        collections = await self.client.get_collections()
        if not any(c.name == collection_name for c in collections.collections):
            return []

        qfilter = None
        # if dataset_id:
        #    qfilter = Filter(must=[FieldCondition(key="dataset_id", match=MatchValue(value=dataset_id))])
        
        response = await self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            query_filter=qfilter
        )
        return response.points

vector_store = VectorStore()
