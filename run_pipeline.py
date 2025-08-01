import logging
from typing import List, Annotated
import json
from concurrent.futures import ThreadPoolExecutor

from zenml import step, pipeline
from zenml.config.docker_settings import DockerSettings

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
def scraper_step(urls_to_scrape: List[str]) -> Annotated[List[str], "scraped_file_paths"]:
	"""
	Scrapes all URLs in parallel and returns a list of file paths.
	"""
	def scrape(url):
		return scrape_single_url(url)
	with ThreadPoolExecutor() as executor:
		scraped_files = list(executor.map(scrape, urls_to_scrape))
	return scraped_files

@step
def parser_step(scraped_file_paths: List[str]) -> Annotated[str, "processed_data_dir"]:
	"""
	Parses and chunks all scraped files.
	"""
	output_dir = parse_and_chunk_files(scraped_file_paths)
	return output_dir

@step
def vectorizer_step(processed_data_dir: str) -> None:
	"""
	ZenML step to vectorize data and store it in ChromaDB.
	"""
	logging.info("Starting vectorizer step...")
	vectorize_and_store(processed_data_dir)

# --- Docker Settings for the Pipeline ---
docker_settings = DockerSettings(disable_automatic_requirements_detection=False)

@pipeline(enable_cache=False, settings={"docker": docker_settings})
def data_ingestion_pipeline():
	"""
	The data ingestion pipeline with parallel scraping using .map().
	"""
	base_urls = load_base_urls(URLS_FILE)
	if not base_urls:
		logging.warning("No URLs to scrape. Pipeline will not run.")
		return
	scraped_files = scraper_step(base_urls)
	processed_data_dir = parser_step(scraped_files)
	vectorizer_step(processed_data_dir)

	logging.info("Data ingestion pipeline has completed successfully.")


if __name__ == "__main__":
	# To run this pipeline, use the ZenML CLI with an active Kubeflow stack:
	# service docker start
	# minikube start --driver=docker
	# kubectl port-forward service/minio-service 9000:9000
	# zenml pipeline run run_pipeline.data_ingestion_pipeline
	data_ingestion_pipeline_instance = data_ingestion_pipeline()
	logging.info("Pipeline definition loaded. To run, use ZenML CLI.")