import os
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
SCRAPED_DATA_DIR = DATA_DIR / "scrapped_data"
PROCESSED_DATA_DIR = DATA_DIR / "processed_data"
DB_DIR = DATA_DIR / "chroma_db"
URLS_FILE = DATA_DIR / "urls_to_scrape.txt"
CLONED_REPOS_DIR = DATA_DIR / "cloned_repos"

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()

CHUNK_SIZE = 1024
CHUNK_OVERLAP = 128

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mlops_docs")