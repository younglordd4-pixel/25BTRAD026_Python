from __future__ import annotations
import pytest
from sqlalchemy import create_engine, text as sqltext
from sqlalchemy.orm import sessionmaker
from ..database import Base
from ..models import Document, PageText, Chunk
from ..services import chunk_service, embedding_service, search_service

# Use an in-memory database for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    # Setup FTS5 table for tests
    with engine.connect() as conn:
        conn.execute(sqltext("""
            CREATE VIRTUAL TABLE chunk_fts USING fts5(
                chunk_id UNINDEXED,
                document_id UNINDEXED,
                page_number UNINDEXED,
                text
            )
        """))
        conn.commit()
        
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_chunking_logic(db_session):
    # Create a test document and page
    doc = Document(filename="test.pdf", stored_filename="test_123.pdf", page_count=1, has_extractable_text=True, extraction_status="completed")
    db_session.add(doc)
    db_session.commit()
    
    # Create a long page of text
    long_text = "This is a test sentence. " * 50 # ~1200 characters
    page = PageText(document_id=doc.id, page_number=1, text=long_text, character_count=len(long_text))
    db_session.add(page)
    db_session.commit()
    
    drafts = chunk_service.create_chunk_drafts_for_document(db_session, doc.id)
    
    assert len(drafts) > 0
    for d in drafts:
        assert len(d.text) >= 150
        assert d.document_id == doc.id
        assert d.page_number == 1

def test_fts_search(db_session):
    doc = Document(filename="test.pdf", stored_filename="test_123.pdf", page_count=1, has_extractable_text=True, extraction_status="completed")
    db_session.add(doc)
    db_session.commit()
    
    chunk = Chunk(document_id=doc.id, page_number=1, chunk_number=1, text="The formula for force is F = ma", character_count=30)
    db_session.add(chunk)
    db_session.commit()
    
    search_service.insert_chunk_fts_entries(db_session, [chunk])
    
    results = search_service.keyword_search(db_session, "F = ma", [doc.id], 5)
    assert len(results) == 1
    assert "F = ma" in results[0].text

def test_deletion_cleanup(db_session):
    doc = Document(filename="test.pdf", stored_filename="test_123.pdf", page_count=1, has_extractable_text=True, extraction_status="completed")
    db_session.add(doc)
    db_session.commit()
    
    chunk = Chunk(document_id=doc.id, page_number=1, chunk_number=1, text="Some text", character_count=9)
    db_session.add(chunk)
    db_session.commit()
    search_service.insert_chunk_fts_entries(db_session, [chunk])
    
    chunk_id = chunk.id
    search_service.delete_document_chunks(db_session, doc.id)
    
    assert db_session.get(Chunk, chunk_id) is None
    assert search_service.fts_entry_count(db_session, doc.id) == 0
