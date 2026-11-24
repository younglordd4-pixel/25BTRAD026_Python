# conftest.py — Windows DLL directory registration for FAISS and pytest
import os
import sys
from pathlib import Path

# Add faiss_cpu.libs directory to Windows DLL search path
backend_libs = Path(__file__).resolve().parents[2] / "backend" / ".venv" / "Lib" / "site-packages" / "faiss_cpu.libs"
root_libs = Path(__file__).resolve().parents[2] / ".venv" / "Lib" / "site-packages" / "faiss_cpu.libs"

for faiss_libs in (backend_libs, root_libs):
    if faiss_libs.is_dir() and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(faiss_libs))
        except Exception:
            pass
    if faiss_libs.is_dir():
        os.environ["PATH"] = str(faiss_libs) + os.pathsep + os.environ.get("PATH", "")

try:
    import faiss
except Exception:
    pass

