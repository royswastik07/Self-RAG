from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class DatasetCreate(BaseModel):
    name: str

class DatasetResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    document_count: Optional[int] = 0
    chunk_count: Optional[int] = 0

class DocumentResponse(BaseModel):
    id: int
    dataset_id: int
    file_name: str
    file_type: str
    uploaded_at: datetime

class ChatRequest(BaseModel):
    query: str
    dataset_id: Optional[int] = None
    session_id: Optional[str] = None

class ChunkData(BaseModel):
    id: int
    file_name: str
    page_number: Optional[int]
    section_title: Optional[str]
    content: str
    confidence_score: Optional[float] = None

class ReflectionData(BaseModel):
    iteration: int
    retrieved_chunks: List[ChunkData]
    draft_answer: Optional[str]
    is_supported: bool
    confidence: float
    retrieve_again: bool
    new_query: Optional[str]
    reason: str

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[ChunkData]
    reflections: List[ReflectionData]
    chat_id: int
