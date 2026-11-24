from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import documents, health, practice, progress, revision, search


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="StudyVerse Offline Backend",
    version="2.0.0",
    description="Offline-first academic PDF extraction, indexing, search, spaced repetition, and practice arena backend.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(practice.router)
app.include_router(revision.router)
app.include_router(progress.router)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {"message": "StudyVerse Offline Backend", "stage": "2"}
