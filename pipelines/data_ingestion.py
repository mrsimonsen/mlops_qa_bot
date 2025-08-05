import logging
from typing import List, Annotated
from concurrent.futures import ThreadPoolExecutor, as_completed

from zenml import step, pipeline

# Import the core logic functions from your existing modules
from src.scraper.scraper import scrape_single_repo
from src.parser.parser import parse_and_chunk_files
from src.vectorizer.vectorizer import vectorize_and_store
from src.config import URLS_FILE

def load_base_urls(filepath: str) -> List[str]:
	"""Helper function to load URLs from a file."""
	try:
		with open(filepath, 'r') as f:
			urls = [line.strip() for line in f.readlines() if line.strip()]
		logging.info(f"Loaded {len(urls)} URLs from '{filepath}'")
		return urls
	except FileNotFoundError:
		logging.error(f"Error: URL file not found at '{filepath}'. Please create it.")
		return []

@step
def scrape_data_step() -> Annotated[List[str], "scraped_file_paths"]:
	"""
	ZenML step to scrape data from a list of URLs.
	This step wraps the parallel scraping logic from 'scripts/ingest_data.py'.
	"""
	logging.info("--- Starting Scraper Step ---")
	urls_to_scrape = load_base_urls(str(URLS_FILE))
	if not urls_to_scrape:
		logging.warning("No URLs found to scrape. Returning empty list.")
		return []

	scraped_files = []
	# Use a thread pool to scrape multiple repositories in parallel
	with ThreadPoolExecutor(max_workers=5) as executor:
		future_to_url = {executor.submit(scrape_single_repo, url): url for url in urls_to_scrape}
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


@step
def parse_data_step(scraped_file_paths: List[str]) -> Annotated[str, "processed_data_dir"]:
	"""
	ZenML step to parse and chunk the scraped files.
	"""
	logging.info("--- Starting Parser Step ---")
	if not scraped_file_paths:
		logging.warning("No files to parse. Skipping parser step.")
		return "" # Return empty string if there's nothing to parse
	
	output_dir = parse_and_chunk_files(scraped_file_paths)
	logging.info(f"Parser finished. Processed data is in: {output_dir}")
	logging.info("--- Parser Step Complete ---")
	return output_dir


@step
def vectorize_data_step(processed_data_dir: str) -> None:
	"""
	ZenML step to vectorize data and store it in ChromaDB.
	"""
	logging.info("--- Starting Vectorizer Step ---")
	if not processed_data_dir:
		logging.warning("No processed data directory provided. Skipping vectorizer step.")
		return
		
	vectorize_and_store(processed_data_dir)
	logging.info("--- Vectorizer Step Complete ---")


@pipeline(name="mlops_qa_data_ingestion")
def data_ingestion_pipeline():
	"""
	The data ingestion pipeline.
	It scrapes, parses, and vectorizes data from a list of URLs.
	"""
	logging.info("--- Starting Data Ingestion Pipeline on Kubeflow ---")
	scraped_paths = scrape_data_step()
	processed_dir = parse_data_step(scraped_file_paths=scraped_paths)
	vectorize_data_step(processed_data_dir=processed_dir)
	logging.info("--- Data Ingestion Pipeline Finished ---")