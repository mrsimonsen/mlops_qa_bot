import logging
from typing import List, Annotated
from zenml import step, pipeline

from src.scraper.scraper import scrape_single_url

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


# --- ZenML Pipeline ---

@pipeline
def data_ingestion_pipeline():
	"""
	The data ingestion pipeline with parallel scraping.
	"""
	# The scraper steps are passed as a list to the gather step
	scraped_files = gather_scraped_files(*scraper_steps)
	
	logging.info("Pipeline finished.")


if __name__ == "__main__":
	data_ingestion_pipeline()