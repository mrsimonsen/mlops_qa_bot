import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from config import URLS_FILE, LOGGING_LEVEL
from scraper.scraper import scrape_single_url
from parser.parser import parse_and_chunk_files
from vectorizer.vectorizer import vectorize_and_store

# --- Main Logic ---
def setup_logging():
	"""Sets up basic logging for the script."""
	logging.basicConfig(level=LOGGING_LEVEL, 
						format='%(asctime)s - %(levelname)s - %(message)s')

def load_base_urls(filepath: str) -> List[str]:
	"""Loads a list of base URLs from a text file."""
	try:
		with open(filepath, 'r') as f:
			urls = [line.strip() for line in f.readlines() if line.strip()]
		logging.info(f"Loaded {len(urls)} URLs from '{filepath}'")
		return urls
	except FileNotFoundError:
		logging.error(f"Error: URL file not found at '{filepath}'. Please create it.")
		return []

def run_scraper(urls_to_scrape: List[str]) -> List[str]:
	"""
	Scrapes all URLs in parallel and returns a list of file paths.
	"""
	logging.info("--- Starting Scraper Step ---")
	scraped_files = []
	with ThreadPoolExecutor(max_workers=5) as executor:
		future_to_url = {executor.submit(scrape_single_url, url): url for url in urls_to_scrape}
		for future in as_completed(future_to_url):
			url = future_to_url[future]
			try:
				file_path = future.result()
				if file_path:
					scraped_files.append(file_path)
					logging.info(f"Successfully scraped {url} -> {file_path}")
			except Exception as e:
				logging.error(f"Scraping {url} generated an exception: {e}", exc_info=True)
	logging.info("--- Scraper Step Complete ---")
	return scraped_files

def run_parser(scraped_file_paths: List[str]) -> str:
	"""
	Parses and chunks all scraped files.
	"""
	logging.info("--- Starting Parser Step ---")
	output_dir = parse_and_chunk_files(scraped_file_paths)
	logging.info(f"Parser finished. Processed data is in: {output_dir}")
	logging.info("--- Parser Step Complete ---")
	return output_dir

def run_vectorizer(processed_data_dir: str) -> None:
	"""
	Vectorizes data and stores it in ChromaDB.
	"""
	logging.info("--- Starting Vectorizer Step ---")
	vectorize_and_store(processed_data_dir)
	logging.info("--- Vectorizer Step Complete ---")

if __name__ == "__main__":
	setup_logging()
	logging.info("Starting data ingestion pipeline...")

	urls = load_base_urls(str(URLS_FILE))
	if not urls:
		logging.warning("No URLs found. Exiting pipeline.")
	else:
		scraped_paths = run_scraper(urls)
		if not scraped_paths:
			logging.warning("Scraper did not produce any files. Exiting.")
		else:
			processed_dir = run_parser(scraped_paths)
			run_vectorizer(processed_dir)
			logging.info("Data ingestion pipeline has completed successfully.")
	