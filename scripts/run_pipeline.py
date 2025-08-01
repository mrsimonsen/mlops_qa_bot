import logging
from typing import List, Annotated
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

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
		logging.info(f"Loaded {len(urls)} URLs from '{filepath}")
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
	scraped_files = []
	with ThreadPoolExecutor(max_workers=5) as executor:
		future_to_url = {executor.submit(scrape_single_url, url): url for url in urls_to_scrape}
		for future in as_completed(future_to_url):
			url = future_to_url[future]
			try:
				file_path = future.result()
				if file_path:
					scraped_files.append(file_path)
					logging.info(f"Successfully scraped {url} to {file_path}")
			except Exception as e:
				logging.error(f"{url} generated an exception: {e}")
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
	# MINIKUBE_IP=$(minikube ip)
	# export AWS_ENDPOINT_URL=http://${MINIKUBE_IP}:30000
	# mc alias set myminio $AWS_ENDPOINT_URL minio minio123
	# mc mb myminio/zenml
	# zenml pipeline run run_pipeline.data_ingestion_pipeline
	data_ingestion_pipeline_instance = data_ingestion_pipeline()
	logging.info("Pipeline definition loaded. To run, use ZenML CLI.")