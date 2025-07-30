import os
import re
import logging
from typing import List, Annotated
from .config import OUTPUT_DIR, CHUNK_SIZE, CHUNK_OVERLAP

# --- Helper Functions ---
def clean_text(text: str) -> str:
	"""
	Cleans the input text by removing excessive newlines, long strings of 
	non-alphanumeric characters, and other unwanted artifacts.

	ARGS:
		text: str, the raw text to be cleaned.
	RETURNS:
		cleaned_text: str, the cleaned text.
	"""
	#replace multiple newlines with a single one, but keep the paragraph break
	text = re.sub(r'\n{3,}', '\n\n', text)
	#remove leading/trailing whitespace from each line
	text = "\n".join([line.strip() for line in text.split('\n')])
	# remove long non-alphanumeric sequences
	text = re.sub(r'[^a-zA-Z0-9\n\s]{4,}', '', text)
	return text

def chunk_text(text: str) -> List[str]:
	"""
	Splits the text into overlapping chunks based on the configuration.
	
	ARGS:
		text: str, the input text to be chunked.
	RETURNS:
		chunks: list[str], a list of text chunks.
	"""
	if not text:
		return []
	chunks = []
	start_index=0
	while start_index < len(text):
		end_index = start_index + CHUNK_SIZE
		chunks.append(text[start_index:end_index])
		start_index += CHUNK_SIZE - CHUNK_OVERLAP
	return chunks