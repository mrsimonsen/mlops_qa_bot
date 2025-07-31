import logging
from typing import List, Annotated
from zenml import step, pipeline

from src.scraper.scraper import scrape_single_url
from src.parser.parser import parse_and_chunk_files
from src.vectorizer.vectorizer import vectorize_and_store

URLS_FILE = "urls_to_scrape.txt"

# --- Load URLs to Scrape ---
def load_base_urls(filepath: str) -> Annotated[List[str], "base_urls_list"]:
	"""Loads a list of base URLs from a text file."""
	try:
		with open(filepath, 'r') as f:
			urls = [line.strip() for line in f.readlines()]
		return urls
	except FileNotFoundError:
		logging.error(f"Error: URL file not found at '{filepath}'")
		return []

base_urls = load_base_urls(URLS_FILE)

# --- ZenML Steps ---
scraper_steps = []
for url in base_urls:
	#factory function to create unique step for each URL
	@step(name=f"scrape_{url.split('//')[1].split('.')[0]}")
	def scraper_step(url_to_scrape: str) -> Annotated[str, "scraped_file_path"]:
		"""
		ZenML step to run the web scraper for a single URL.
		"""
		logging.info("Starting scraper step for {url_to_scrape}...")
		return scrape_single_url(url_to_scrape)
	
@step
def gather_scraped_files(
	*args: str,
) -> Annotated[List[str], "list_of_scraped_files"]:
	"""
	This step gathers the file paths from all the parallel scraper steps.
	"""
	# args will be a tuple of all the input file paths
	file_paths = list(args)
	logging.info(f"Gathered {len(file_paths)} files.")
	return file_paths

@step
def parser_step(list_of_files: List[str]) -> Annotated[str, "processed_data_dir"]:
	"""
	ZenML step to run the data parser on a list of files.
	"""
	logging.info("Starting parser step...")
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

@pipeline
def data_ingestion_pipeline():
	"""
	The data ingestion pipeline with parallel scraping.
	"""
	# The scraper steps are passed as a list to the gather step
	scraped_files = gather_scraped_files(*scraper_steps)
	processed_data_dir = parser_step(scraped_files)
	vectorizer_step(processed_data_dir)
	
	logging.info("Data ingestion pipeline has completed successfully.")


if __name__ == "__main__":
	data_ingestion_pipeline()