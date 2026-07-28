import os
import uuid
import shutil
import json
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.session import get_db
from database.models import Dataset, Document, ChatHistory, ReflectionLog, ChunkMetadata
from schemas.schemas import (
    DatasetCreate, DatasetResponse, DocumentResponse, 
    ChatRequest, ChatResponse, ChunkData, ReflectionData
)
from services.ingestion import process_document
from services.retrieval import retrieval_service
from services.generation import generation_service
from services.reflection import reflection_service
from core.config import settings

router = APIRouter()

@router.post("/datasets", response_model=DatasetResponse)
async def create_dataset(dataset: DatasetCreate, db: AsyncSession = Depends(get_db)):
    db_dataset = Dataset(name=dataset.name)
    db.add(db_dataset)
    await db.commit()
    await db.refresh(db_dataset)
    return DatasetResponse(
        id=db_dataset.id, 
        name=db_dataset.name, 
        created_at=db_dataset.created_at,
        document_count=0,
        chunk_count=0
    )

@router.get("/datasets", response_model=List[DatasetResponse])
async def get_datasets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset))
    datasets = result.scalars().all()
    
    response = []
    for d in datasets:
        # Count documents
        doc_count = await db.scalar(select(func.count()).select_from(Document).where(Document.dataset_id == d.id))
        
        # Count chunks
        chunk_count = await db.scalar(
            select(func.count()).select_from(ChunkMetadata)
            .join(Document, ChunkMetadata.document_id == Document.id)
            .where(Document.dataset_id == d.id)
        )
        
        response.append(DatasetResponse(
            id=d.id, 
            name=d.name, 
            created_at=d.created_at, 
            document_count=doc_count or 0, 
            chunk_count=chunk_count or 0
        ))
    return response

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_datasets = await db.scalar(select(func.count()).select_from(Dataset))
    total_documents = await db.scalar(select(func.count()).select_from(Document))
    avg_conf = await db.scalar(select(func.avg(ReflectionLog.confidence)))
    
    return {
        "totalDatasets": total_datasets or 0,
        "totalDocuments": total_documents or 0,
        "avgConfidence": f"{round((avg_conf or 0) * 100)}%"
    }

@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dataset_id: int = Form(...),
    chunk_size: int = Form(None),
    chunk_overlap: int = Form(None),
    chunk_method: str = Form("recursive"),
    embedding_model: str = Form("BAAI/bge-small-en-v1.5"),
    db: AsyncSession = Depends(get_db)
):
    # Verify dataset exists
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # We await the process directly for simplicity, but could be background
    try:
        db_doc = await process_document(
            db=db, 
            dataset_id=dataset_id, 
            file_name=file.filename, 
            file_path=file_path, 
            file_type=file.content_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_method=chunk_method,
            embedding_model=embedding_model
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return DocumentResponse(
        id=db_doc.id,
        dataset_id=db_doc.dataset_id,
        file_name=db_doc.file_name,
        file_type=db_doc.file_type,
        uploaded_at=db_doc.uploaded_at
    )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())
    
    current_query = request.query
    reflections = []
    
    # Fetch unique embedding models used in this dataset
    models_result = await db.execute(select(Document.embedding_model).where(Document.dataset_id == request.dataset_id).distinct())
    embedding_models = [m for m in models_result.scalars().all() if m]
    if not embedding_models:
        embedding_models = ["BAAI/bge-small-en-v1.5"]

    # Self-RAG Loop
    for iteration in range(settings.MAX_REFLECTION_ITERATIONS):
        # 1. Retrieve & Rerank
        retrieved_chunks = await retrieval_service.retrieve_and_rerank(
            query=current_query, 
            dataset_id=request.dataset_id,
            embedding_models=embedding_models
        )
        
        context_text = "\n\n".join([f"Source: {c['file_name']}\n{c['content']}" for c in retrieved_chunks])
        
        # 2. Generate Draft Answer
        draft_answer = await generation_service.generate_answer(current_query, context_text)
        
        # 3. Reflection
        reflection_result = await reflection_service.evaluate_and_reflect(
            query=current_query, 
            context=context_text, 
            draft_answer=draft_answer
        )
        
        reflection_data = ReflectionData(
            iteration=iteration + 1,
            retrieved_chunks=[ChunkData(**c) for c in retrieved_chunks],
            draft_answer=draft_answer,
            is_supported=reflection_result.get("supported", False),
            confidence=reflection_result.get("confidence", 0.0),
            retrieve_again=reflection_result.get("retrieve_again", False),
            new_query=reflection_result.get("new_query"),
            reason=reflection_result.get("reason", "")
        )
        reflections.append(reflection_data)
        
        # 4. Check if we need to loop
        if reflection_data.is_supported or not reflection_data.retrieve_again or iteration == settings.MAX_REFLECTION_ITERATIONS - 1:
            break
            
        # Update query for next iteration
        current_query = reflection_data.new_query or request.query

    # Final Answer
    final_answer = reflections[-1].draft_answer
    
    # If not supported, override the answer based on grounding requirements
    if not reflections[-1].is_supported and reflections[-1].confidence < 0.5:
        final_answer = "I could not find sufficient evidence in the uploaded documents."

    # Save to DB
    chat_hist = ChatHistory(session_id=session_id, user_query=request.query, final_answer=final_answer)
    db.add(chat_hist)
    await db.commit()
    await db.refresh(chat_hist)
    
    # Save reflections to DB
    reflection_logs = []
    for r in reflections:
        db_reflection = ReflectionLog(
            chat_id=chat_hist.id,
            iteration=r.iteration,
            retrieved_chunks=json.dumps([c.dict() for c in r.retrieved_chunks]),
            draft_answer=r.draft_answer,
            is_supported=r.is_supported,
            confidence=r.confidence,
            retrieve_again=r.retrieve_again,
            new_query=r.new_query,
            reason=r.reason
        )
        reflection_logs.append(db_reflection)
        
    db.add_all(reflection_logs)
    await db.commit()
    return ChatResponse(
        session_id=session_id,
        answer=final_answer,
        sources=reflections[-1].retrieved_chunks,
        reflections=reflections,
        chat_id=chat_hist.id
    )
