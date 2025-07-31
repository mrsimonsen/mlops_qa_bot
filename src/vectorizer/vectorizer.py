import os
import logging
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
from .config import EMBEDDING_MODEL_NAME, PERSIST_DIRECTORY, COLLECTION_NAME

def read_chunks_from_file(filepath: str) -> List[str]:
	"""
	Reads processed text chunks from a file.
	"""
	with open(filepath, 'r') as f:
		content = f.read()

	chunks = content.split("\n---CHUNK---\n")
	return [stripped for chunk in chunks if (stripped := chunk.strip())]