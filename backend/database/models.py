from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    documents = relationship("Document", back_populates="dataset", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"))
    file_name = Column(String)
    file_type = Column(String)
    chunk_size = Column(Integer, nullable=True)
    chunk_overlap = Column(Integer, nullable=True)
    chunk_method = Column(String, nullable=True)
    embedding_model = Column(String, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    dataset = relationship("Dataset", back_populates="documents")
    chunks = relationship("ChunkMetadata", back_populates="document", cascade="all, delete-orphan")

class ChunkMetadata(Base):
    __tablename__ = "chunk_metadata"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    qdrant_point_id = Column(String, unique=True, index=True) # UUID for Qdrant
    chunk_index = Column(Integer)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String, nullable=True)
    text_content = Column(Text) # Keep text in Postgres too for easy retrieval
    
    document = relationship("Document", back_populates="chunks")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_query = Column(Text)
    final_answer = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    reflections = relationship("ReflectionLog", back_populates="chat", cascade="all, delete-orphan")

class ReflectionLog(Base):
    __tablename__ = "reflection_logs"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chat_history.id", ondelete="CASCADE"))
    iteration = Column(Integer)
    retrieved_chunks = Column(Text) # JSON string of chunks
    draft_answer = Column(Text, nullable=True)
    is_supported = Column(Boolean)
    confidence = Column(Float)
    retrieve_again = Column(Boolean)
    new_query = Column(Text, nullable=True)
    reason = Column(Text)
    
    chat = relationship("ChatHistory", back_populates="reflections")
