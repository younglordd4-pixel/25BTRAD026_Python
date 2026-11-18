import qrcode
from PIL import ImageTk
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

class QRService:
    def generate_qr(self, data: str, filename: str = None) -> str:
        from config import EXPORTS_DIR
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        if not filename:
            filename = f"qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = EXPORTS_DIR / filename
        
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(str(path))
        return str(path)
    
    def generate_item_qr(self, item_id: int, item_type: str, item_name: str) -> str:
        data = f"CAMPUSFIND:ITEM:{item_id}:{item_type}:{item_name}"
        filename = f"qr_item_{item_id}_{item_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return self.generate_qr(data, filename)
    
    def get_qr_image(self, item_id: int, item_type: str, item_name: str, size: int = 150):
        """Returns PIL ImageTk.PhotoImage for displaying in GUI"""
        from PIL import Image
        import tkinter as tk
        if getattr(tk, '_default_root', None) is None:
            r = tk.Tk()
            r.withdraw()
        data = f"CAMPUSFIND:ITEM:{item_id}:{item_type}:{item_name}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img.thumbnail((size, size))
        return ImageTk.PhotoImage(img)

qr_service = QRService()
