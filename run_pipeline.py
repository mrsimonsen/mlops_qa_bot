import logging
from zenml import step, pipeline

from src.scraper.scraper import main as scrape_data

@step
def scraper_step() -> str:
	"""
	ZenML step to run the web scraper.
	This step will return the path to the directory with scraped data.
	"""
	logging.info("Starting scraper step...")
	output_dir = scrape_data()
	return output_dir

@pipeline
def data_ingestion_pipeline():
	"""
	The data ingestion pipeline.
	This connects the scraper and parser steps.
	"""
	scraped_data_dir = scraper_step()
	logging.info("Pipeline finished.")


if __name__ == "__main__":
	data_ingestion_pipeline()