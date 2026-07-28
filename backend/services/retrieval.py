from typing import List, Tuple, Dict, Any
from services.vector_store import vector_store
from services.embeddings import generate_embedding
from services.reranker import reranker_service
from core.config import settings

class RetrievalService:
    async def retrieve_and_rerank(
        self, 
        query: str, 
        dataset_id: int = None, 
        top_k_retrieval: int = settings.TOP_K_RETRIEVAL, 
        top_k_rerank: int = settings.TOP_K_RERANK,
        embedding_models: List[str] = ["BAAI/bge-small-en-v1.5"]
    ) -> List[Dict[str, Any]]:
        """
        1. Generates query embeddings for each model used in the dataset.
        2. Retrieves Top-K from each Qdrant collection.
        3. Reranks using cross-encoder.
        4. Returns Top-N reranked chunks.
        """
        scored_points = []
        seen_points = set()
        
        # Query each collection
        for model in embedding_models:
            # 1. Generate query embedding for this model
            query_vector = await generate_embedding(query, model_name=model)

            # 2. Vector Search
            model_points = await vector_store.search(
                query_vector=query_vector, 
                limit=top_k_retrieval,
                dataset_id=dataset_id,
                embedding_model=model
            )
            
            # Deduplicate by chunk_index/document to avoid feeding duplicates to reranker
            for point in model_points:
                point_key = f"{point.payload.get('document_id')}_{point.payload.get('chunk_index')}"
                if point_key not in seen_points:
                    seen_points.add(point_key)
                    scored_points.append(point)

        if not scored_points:
            return []

        # Extract texts for reranking
        texts = [point.payload.get("text", "") for point in scored_points]

        # 3. Rerank
        reranked_indices_scores = await reranker_service.rerank(query, texts, top_k=top_k_rerank)

        # 4. Map back to original points and format
        final_chunks = []
        for index, score in reranked_indices_scores:
            original_point = scored_points[index]
            final_chunks.append({
                "id": original_point.payload.get("chunk_index"), # Using chunk_index as pseudo-ID or we can use DB ID if we stored it
                "file_name": original_point.payload.get("file_name"),
                "page_number": None,
                "section_title": None,
                "content": original_point.payload.get("text"),
                "confidence_score": float(score)
            })

        return final_chunks

retrieval_service = RetrievalService()
