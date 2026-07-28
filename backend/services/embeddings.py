import asyncio
from sentence_transformers import SentenceTransformer
from core.config import settings
from typing import Dict

# Cache for loaded models so we don't reload them in memory
_models_cache: Dict[str, SentenceTransformer] = {}

def get_model(model_name: str) -> SentenceTransformer:
    if model_name not in _models_cache:
        _models_cache[model_name] = SentenceTransformer(model_name)
    return _models_cache[model_name]

def get_embedding_dimension(model_name: str) -> int:
    model = get_model(model_name)
    return model.get_sentence_embedding_dimension()

async def generate_embedding(text: str, model_name: str = "BAAI/bge-small-en-v1.5") -> list[float]:
    model = get_model(model_name)
    embedding = await asyncio.to_thread(model.encode, text, normalize_embeddings=True)
    return embedding.tolist()

async def generate_embeddings(texts: list[str], model_name: str = "BAAI/bge-small-en-v1.5") -> list[list[float]]:
    model = get_model(model_name)
    embeddings = await asyncio.to_thread(model.encode, texts, normalize_embeddings=True)
    return embeddings.tolist()
