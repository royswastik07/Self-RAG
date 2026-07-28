import asyncio
from typing import List, Tuple
from sentence_transformers import CrossEncoder
from core.config import settings

class RerankerService:
    def __init__(self):
        # Initialize the cross-encoder model.
        # This will download the model on first run if not cached.
        self.model = CrossEncoder("BAAI/bge-reranker-large")

    def _rerank_sync(self, query: str, texts: List[str], top_k: int) -> List[Tuple[int, float]]:
        """
        Runs the reranking model.
        Returns a list of tuples (index_in_texts, score), sorted by score descending.
        """
        if not texts:
            return []
            
        pairs = [[query, text] for text in texts]
        scores = self.model.predict(pairs)
        
        # Combine indices with scores
        scored_indices = list(enumerate(scores))
        
        # Sort descending
        scored_indices.sort(key=lambda x: x[1], reverse=True)
        
        return scored_indices[:top_k]

    async def rerank(self, query: str, texts: List[str], top_k: int = settings.TOP_K_RERANK) -> List[Tuple[int, float]]:
        """
        Asynchronously calls the synchronous reranker model.
        """
        return await asyncio.to_thread(self._rerank_sync, query, texts, top_k)

reranker_service = RerankerService()
