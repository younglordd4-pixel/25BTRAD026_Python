from pathlib import Path
import shutil, uuid, os
from PIL import Image, ImageTk
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

class ImageService:
    def process_upload(self, source_path: str, dest_dir=None) -> str:
        """Copy image to uploads dir, resize if needed. Returns relative path string."""
        # Import config here to avoid circular import at module level
        from config import UPLOADS_DIR, MAX_IMAGE_SIZE, ALLOWED_IMAGE_TYPES, BASE_DIR
        if dest_dir is None: dest_dir = UPLOADS_DIR
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        source = Path(source_path)
        ext = source.suffix.lower()
        if ext not in ALLOWED_IMAGE_TYPES:
            raise ValueError(f"File type {ext} not allowed")
        
        new_name = f"{uuid.uuid4().hex}{ext}"
        dest = dest_dir / new_name
        shutil.copy2(source, dest)
        
        # Resize if too large
        with Image.open(dest) as img:
            if img.width > MAX_IMAGE_SIZE[0] or img.height > MAX_IMAGE_SIZE[1]:
                img.thumbnail(MAX_IMAGE_SIZE, Image.LANCZOS)
                img.save(dest)
        
        return str(dest.relative_to(BASE_DIR))
    
    def validate_image(self, path: str) -> tuple:
        from config import ALLOWED_IMAGE_TYPES, MAX_IMAGE_MB
        p = Path(path)
        if p.suffix.lower() not in ALLOWED_IMAGE_TYPES:
            return False, f"File type must be one of: {', '.join(ALLOWED_IMAGE_TYPES)}"
        if p.stat().st_size > MAX_IMAGE_MB * 1024 * 1024:
            return False, f"File size must be less than {MAX_IMAGE_MB}MB"
        try:
            with Image.open(path) as img:
                img.verify()
            return True, "Valid image"
        except Exception as e:
            return False, f"Invalid image file: {e}"
    
    def get_thumbnail(self, image_path: str, size=(150, 150)):
        """Returns PIL ImageTk.PhotoImage or None if file missing/invalid."""
        from config import BASE_DIR
        if not image_path:
            return None
        # Try as relative path first, then absolute
        p = Path(image_path)
        if not p.is_absolute():
            p = BASE_DIR / image_path
        if not p.exists():
            return None
        try:
            import tkinter as tk
            if getattr(tk, '_default_root', None) is None:
                r = tk.Tk()
                r.withdraw()
            with Image.open(p) as img:
                img.thumbnail(size, Image.LANCZOS)
                img = img.convert("RGBA")
                return ImageTk.PhotoImage(img)
        except Exception:
            return None
    
    def resize_image(self, image_path: str, max_size=(800, 600)):
        from config import BASE_DIR
        p = Path(image_path)
        if not p.is_absolute():
            p = BASE_DIR / image_path
        if not p.exists():
            return
        try:
            with Image.open(p) as img:
                if img.width > max_size[0] or img.height > max_size[1]:
                    img.thumbnail(max_size, Image.LANCZOS)
                    img.save(p)
        except Exception:
            pass
    
    def safe_filename(self, original: str) -> str:
        import re
        ext = Path(original).suffix.lower()
        base = re.sub(r'[^\w]', '_', Path(original).stem)
        return f"{uuid.uuid4().hex}_{base}{ext}"

image_service = ImageService()
