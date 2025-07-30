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
