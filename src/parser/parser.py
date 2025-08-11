import os
import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import PROCESSED_DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP

# --- Main Logic ---
def process_and_chunk_file(filepath: str) -> List[str]:
	"""
	Loads a single file, cleans its contents, and splits it into chunks.

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

		text_splitter = RecursiveCharacterTextSplitter(
			chunk_size=CHUNK_SIZE,
			chunk_overlap=CHUNK_OVERLAP,
			add_start_index=False, # We don't need this for our use case
		)
		text_chunks = text_splitter.split_text(raw_text)

		logging.info(f"Successfully chunked {filepath} into {len(text_chunks)} chunks.")
		return text_chunks
	except Exception as e:
		logging.error(f"Error processing file {filepath}: {e}")
		return []


def parse_and_chunk_files(list_of_files: List[str]) -> str:
	"""
	Main entry point for the parser. It processes all files from the input list
	and saves the chunked data to a new directory.

	ARGS:
		list_of_files: list[str], A list of file path from the scraper steps.
	RETURNS:
		output_dir: str, the path to the output directory.
	"""
	os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

	for file_path in list_of_files:
		if os.path.exists(file_path):
			chunks = process_and_chunk_file(file_path)
			if chunks:
				base_filename = os.path.basename(file_path)
				output_filepath = os.path.join(PROCESSED_DATA_DIR, f"processed_{base_filename}")
				with open(output_filepath, 'w') as f:
					f.write("\n---CHUNK---\n".join(chunks))
				logging.info(f"Saved {len(chunks)} chunks to {output_filepath}")

	logging.info(f"All parsing and chunking tasks complete. Output is in '{PROCESSED_DATA_DIR}'")
	return str(PROCESSED_DATA_DIR)