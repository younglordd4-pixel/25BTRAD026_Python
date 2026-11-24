from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

# Add faiss_cpu.libs to DLL directory on Windows
_dll_handles = []
for base in (Path(__file__).resolve().parents[2], Path(__file__).resolve().parents[3]):
    for candidate in (base / ".venv" / "Lib" / "site-packages" / "faiss_cpu.libs", base / "backend" / ".venv" / "Lib" / "site-packages" / "faiss_cpu.libs"):
        if candidate.is_dir():
            if hasattr(os, "add_dll_directory"):
                try:
                    _dll_handles.append(os.add_dll_directory(str(candidate)))
                except Exception:
                    pass
            os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from ..database import DATA_DIR
from ..models import Chunk, Document

INDEX_DIR = DATA_DIR / "indexes"
INDEX_DIR.mkdir(parents=True, exist_ok=True)

class EmbeddingModel:
    """Singleton wrapper for the SentenceTransformer model."""
    _instance: SentenceTransformer | None = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._instance is None:
            # Load model once per process
            cls._instance = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._instance

def build_document_faiss_index(
    document: Document,
    chunks: list[Chunk],
    index_path: Path | None = None,
    metadata_path: Path | None = None,
) -> bool:
    """
    Generates embeddings for chunks, builds a FAISS index, and saves both to disk.
    """
    if not chunks:
        return False

    model = EmbeddingModel.get_model()
    texts = [c.text for c in chunks]
    
    # Encode and convert to float32 numpy array
    embeddings = model.encode(texts, convert_to_numpy=True).astype("float32")
    
    # L2 Normalize for Cosine Similarity using IndexFlatIP
    faiss.normalize_L2(embeddings)
    
    # Build IndexFlatIP (Inner Product on normalized vectors = Cosine Similarity)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    
    # Save FAISS index
    faiss_path = index_path or (INDEX_DIR / f"document_{document.id}.faiss")
    faiss.write_index(index, str(faiss_path))
    
    # Save metadata mapping: FAISS index position -> chunk details
    metadata = [
        {
            "chunk_id": c.id,
            "document_id": c.document_id,
            "page_number": c.page_number,
            "chunk_number": c.chunk_number,
            "filename": document.filename,
        }
        for c in chunks
    ]
    metadata_file = metadata_path or (INDEX_DIR / f"document_{document.id}.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f)
        
    return True

def document_index_exists(document_id: int) -> tuple[bool, bool]:
    """Checks if both FAISS index and metadata JSON exist for a document."""
    faiss_exists = (INDEX_DIR / f"document_{document_id}.faiss").exists()
    metadata_exists = (INDEX_DIR / f"document_{document_id}.json").exists()
    return faiss_exists, metadata_exists

def remove_document_faiss_files(document_id: int) -> dict[str, bool]:
    """Deletes FAISS index and metadata for a document."""
    faiss_path = INDEX_DIR / f"document_{document_id}.faiss"
    metadata_path = INDEX_DIR / f"document_{document_id}.json"
    
    faiss_deleted = False
    if faiss_path.exists():
        try:
            faiss_path.unlink()
            faiss_deleted = True
        except OSError:
            faiss_deleted = False
            
    metadata_deleted = False
    if metadata_path.exists():
        try:
            metadata_path.unlink()
            metadata_deleted = True
        except OSError:
            metadata_deleted = False
            
    return {
        "faiss_index_deleted": faiss_deleted,
        "metadata_deleted": metadata_deleted
    }
