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

# --- Main Logic ---
def process_and_chunk_file(filepath: str) -> List[str]:
	"""
	Loads a single file, cleans its contents, and splits it into chucks.

	ARGS:
		filepath: str, the path to the text file.
	RETURNS:
		chunks: list[str], a list of processed text chunks.
	"""
	logging.info(f"Processing and chunking file: {filepath}")
	try:
		with open(filepath, 'r') as f:
			raw_text = f.read()
		#skip the header
		#"--- Scraped content from ..."
		content_start = raw_text.find("---\n\n")
		if content_start != -1:
			raw_text = raw_text[content_start+5:]
		
		cleaned_text = clean_text(raw_text)
		text_chunks = chunk_text(cleaned_text)

		logging.info(f"Successfully chunked {filepath} into {len(text_chunks)} chunks.")
		return text_chunks
	except Exception as e:
		logging.error(f"Error processing file {filepath}: {e}")
		return []
