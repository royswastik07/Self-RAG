import os
import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client.models import PointStruct
from markitdown import MarkItDown
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter

from database.models import Document, ChunkMetadata
from services.embeddings import generate_embeddings
from services.vector_store import vector_store
from core.config import settings

# Supported MIME types for document restructuring
SUPPORTED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/markdown",
    "text/html",
}

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """Convert any uploaded document to structured Markdown for RAG-optimized chunking.
    
    Uses Microsoft's MarkItDown to intelligently parse layout, tables, headers,
    and multi-column formats — rather than a naive top-to-bottom text extraction.
    """
    if file_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported file type: {file_type}. Supported types: {', '.join(SUPPORTED_TYPES)}")
    
    md_converter = MarkItDown()
    result = md_converter.convert(file_path)
    
    text = result.text_content.strip()
    if not text:
        raise ValueError(f"No text could be extracted from '{file_path}'. The document may be empty or image-only.")
    
    return text

async def process_document(
    db: AsyncSession, 
    dataset_id: int, 
    file_name: str, 
    file_path: str, 
    file_type: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    chunk_method: str = "recursive",
    embedding_model: str = "BAAI/bge-small-en-v1.5"
):
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if chunk_overlap >= chunk_size:
        raise ValueError(f"Chunk overlap ({chunk_overlap}) must be strictly smaller than chunk size ({chunk_size}).")

    # 1. Create DB Document
    db_doc = Document(
        dataset_id=dataset_id, 
        file_name=file_name, 
        file_type=file_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_method=chunk_method,
        embedding_model=embedding_model
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)

    try:
        # 2. Extract Text
        full_text = extract_text_from_file(file_path, file_type)

        # 3. Chunking
        if chunk_method == "character":
            text_splitter = CharacterTextSplitter(
                separator="\n\n",
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
        else:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
        chunks = text_splitter.split_text(full_text)

        if not chunks:
            return db_doc

        # 4. Generate Embeddings
        batch_size = 100
        points = []
        chunk_metadata_list = []
        
        for i in range(0, len(chunks), batch_size):
            chunk_batch = chunks[i:i+batch_size]
            embeddings = await generate_embeddings(chunk_batch, model_name=embedding_model)
            
            for j, text_chunk in enumerate(chunk_batch):
                global_idx = i + j
                qdrant_id = str(uuid.uuid4())
                
                # DB Metadata
                chunk_meta = ChunkMetadata(
                    document_id=db_doc.id,
                    qdrant_point_id=qdrant_id,
                    chunk_index=global_idx,
                    text_content=text_chunk,
                )
                chunk_metadata_list.append(chunk_meta)
                
                # Qdrant Point
                points.append(
                    PointStruct(
                        id=qdrant_id,
                        vector=embeddings[j],
                        payload={
                            "dataset_id": dataset_id,
                            "document_id": db_doc.id,
                            "file_name": file_name,
                            "chunk_index": global_idx,
                            "text": text_chunk
                        }
                    )
                )

        # 5. Save to Postgres
        db.add_all(chunk_metadata_list)
        await db.commit()

        # 6. Save to Qdrant
        await vector_store.initialize_collection(embedding_model)
        await vector_store.upsert_points(points, embedding_model)

        return db_doc

    except Exception as e:
        # Rollback the document creation if anything fails
        await db.delete(db_doc)
        await db.commit()
        raise e
