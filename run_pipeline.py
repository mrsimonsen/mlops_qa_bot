import logging
from typing import List, Annotated
from zenml import step, pipeline

from src.scraper.scraper import scrape_single_url
from src.parser.parser import parse_and_chunk_files
from src.vectorizer.vectorizer import vectorize_and_store

URLS_FILE = "urls_to_scrape.txt"

# --- Load URLs to Scrape ---
def load_base_urls(filepath: str) -> List[str]:
	"""Loads a list of base URLs from a text file."""
	try:
		with open(filepath, 'r') as f:
			urls = [line.strip() for line in f.readlines()]
		return urls
	except FileNotFoundError:
		logging.error(f"Error: URL file not found at '{filepath}'")
		return []

# --- ZenML Steps ---
@step
def scraper_step(url_to_scrape: str) -> Annotated[str, "scraped_file_path"]:
	"""
	ZenML step to run the web scraper for a single URL.
	"""
	logging.info(f"Starting scraper step for {url_to_scrape}...")
	return scrape_single_url(url_to_scrape)

@step
def parser_step(list_of_files: List[str]) -> Annotated[str, "processed_data_dir"]:
	"""
	ZenML step to run the data parser on a list of files.
	"""
	logging.info(f"Starting parser step for {len(list_of_files)} files...")
	output_dir = parse_and_chunk_files(list_of_files)
	return output_dir

@step
def vectorizer_step(processed_data_dir: str) -> None:
	"""
	ZenML step to vectorize data and store it in ChromaDB.
	"""
	logging.info("Starting vectorizer step...")
	vectorize_and_store(processed_data_dir)

# --- ZenML Pipeline ---

@pipeline(enable_cache=False)
def data_ingestion_pipeline():
	"""
	The data ingestion pipeline with parallel scraping.
	"""
	scraped_files_outputs = []
	for url in load_base_urls(URLS_FILE):
		# ZenML understands these are dependencies that need to be run.
		scraped_files_outputs.append(scraper_step(url_to_scrape=url))

	# ZenML will automatically wait for all scraper steps to complete.
	processed_data_dir = parser_step(list_of_files=scraped_files_outputs)
	vectorizer_step(processed_data_dir=processed_data_dir)

	logging.info("Data ingestion pipeline has completed successfully.")


if __name__ == "__main__":
	data_ingestion_pipeline()