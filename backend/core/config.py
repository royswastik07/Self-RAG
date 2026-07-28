from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Self-RAG API"
    
    # Postgres
    DATABASE_URL: str = "postgresql+asyncpg://user_v2:password_v2@localhost:5433/self_rag_v2"
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    
    # Groq
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    VISION_LLM_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANK: int = 5
    MAX_REFLECTION_ITERATIONS: int = 2
    LLM_TEMPERATURE: float = 0.0

    class Config:
        env_file = ".env"

settings = Settings()
