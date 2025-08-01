from pathlib import Path
import logging

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
SCRAPED_DATA_DIR = DATA_DIR / "scrapped_data"
PROCESSED_DATA_DIR = DATA_DIR / "processed_data"
DB_DIR = DATA_DIR / "chroma_db"
URLS_FILE = DATA_DIR / "urls_to_scrape.txt"
LOGGING_LEVEL = logging.INFO