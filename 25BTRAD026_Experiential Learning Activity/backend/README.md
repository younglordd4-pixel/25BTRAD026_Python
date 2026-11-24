# StudyVerse Offline Backend — Stage 1

This backend provides the local document foundation for StudyVerse Offline. It uses FastAPI, SQLite, SQLAlchemy, and PyMuPDF. Uploaded PDFs stay under `backend/data/uploads/`; extracted page text is stored in the local SQLite database at `backend/data/studyverse.db`.

Stage 1 includes:

- `GET /health`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/pages?include_text=true`
- `DELETE /documents/{document_id}`
- Swagger at `/docs`

Scanned/image-only PDFs are retained with a `warning` extraction status and no searchable text. Invalid or encrypted PDFs are retained with a `failed` status and a readable message. The API never sends documents to an external service.

## Setup

From the repository root:

```powershell
cd backend
py -3.13 -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the API:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for Swagger.

Run tests:

```powershell
pytest -q
```

Tests use a temporary SQLite database and temporary upload directory. They do not modify the real local database.
