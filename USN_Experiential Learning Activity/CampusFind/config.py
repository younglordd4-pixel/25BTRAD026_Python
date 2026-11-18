"""
CampusFind - Central Configuration
"""
import os
from pathlib import Path

APP_NAME = "CampusFind"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).parent

# Database
DB_PATH = BASE_DIR / "database" / "campusfind.db"

# Directory paths
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = BASE_DIR / "assets" / "icons"

# Window settings
WINDOW_WIDTH = 1366
WINDOW_HEIGHT = 768
MIN_WIDTH = 1024
MIN_HEIGHT = 600
SIDEBAR_WIDTH = 220

# Matching
MATCH_THRESHOLD = 60

# Image settings
MAX_IMAGE_SIZE = (800, 600)
ALLOWED_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".webp"]
MAX_IMAGE_MB = 5

# SMTP / Email
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "")
EMAIL_ENABLED = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)

# Categories and locations
CATEGORIES = [
    "Electronics",
    "Personal Belongings",
    "Documents & ID Cards",
    "Books & Stationery",
    "Clothing & Accessories",
    "Keys",
    "Other",
]

CAMPUS_LOCATIONS = [
    "Library",
    "Cafeteria",
    "Main Block",
    "Science Block",
    "Engineering Block",
    "Sports Complex",
    "Hostel",
    "Parking Area",
    "Auditorium",
    "Admin Block",
    "Other",
]

# Ensure all directories exist
for _dir in (DB_PATH.parent, UPLOADS_DIR, EXPORTS_DIR, ASSETS_DIR, ICONS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
