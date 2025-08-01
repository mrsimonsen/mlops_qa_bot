from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
SCRAPED_DATA_DIR = DATA_DIR / "scrapped_data"
PROCESSED_DATA_DIR = DATA_DIR / "processed_data"
DB_DIR = DATA_DIR / "chroma_db"
