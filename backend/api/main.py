from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.models import Base
from database.session import engine
from contextlib import asynccontextmanager
from api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Self-RAG API", lifespan=lifespan)

app.include_router(router, prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
