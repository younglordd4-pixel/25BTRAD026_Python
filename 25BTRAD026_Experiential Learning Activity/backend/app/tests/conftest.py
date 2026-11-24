# conftest.py — Windows DLL directory registration for FAISS and pytest
import os
import sys
from pathlib import Path

# Add faiss_cpu.libs directory to Windows DLL search path
venv_site_packages = Path(__file__).resolve().parents[2] / ".venv" / "Lib" / "site-packages"
faiss_libs = venv_site_packages / "faiss_cpu.libs"

_dll_handles = []
if faiss_libs.is_dir() and hasattr(os, "add_dll_directory"):
    try:
        _dll_handles.append(os.add_dll_directory(str(faiss_libs)))
    except Exception:
        pass

# Ensure PATH also contains it
if faiss_libs.is_dir():
    os.environ["PATH"] = str(faiss_libs) + os.pathsep + os.environ.get("PATH", "")

try:
    import faiss
except Exception:
    pass
