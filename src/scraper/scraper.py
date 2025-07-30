import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
import logging
from .config import URLS_FILE, OUTPUT_DIR, REQUEST_DELAY

# --- Helper Functions ---

def load_base_url(filepath: str) -> list[str]:
	"""
	Loads a list of base URLs from a text file.

	ARGS:
		filepath: str, location of text file containing the list of URLS
	RETURNS:
		urls: list, list of base URL strings
	"""
	if not os.path.exists(filepath):
		logging.error(f"Error: URL file not found at '{filepath}'")
		return []
	with open(filepath, 'r') as f:
		urls = [line.strip() for line in f.readlines()]
	return urls

def sanitize_filename(domain: str) -> str:
	"""
	Creates a safe and clean filename from a domain name.
	Example: 'docs.zenml.io' > 'docs_zenml_io.txt'

	ARGS:
		domain: str, URL text
	RETURNS:
		filename: str, sanitized URL into a filename
	"""
	#replace dots with underscores
	sanitized = domain.replace('.','_')
	#remove characters that are not alphanumeric or underscores
	sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
	return f'{sanitized}.txt'


# --- Main Logic ---

def main():
	"""
	Main function to load URLs and orchestrate the scraping for all sites.
	"""
	#load list of urls
	base_urls = load_base_url(URLS_FILE)
	if not base_urls:
		logging.error(f"No URLs to scrape. Please create '{URLS_FILE}' and add URLs to it.")
		return
	logging.info("base urls loaded")
		#create output directory
	os.makedirs(OUTPUT_DIR, exists_ok=True)
	logging.info("output directory is ready")
	
	#create session
	session = requests.Session()
	session.headers.update( {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
	logging.info("session created")

	#Crawl each site from list and save in own file
	for url in base_urls:
		domain = urlparse(url).netloc
		output_filename = sanitize_filename(domain)

if __name__ == '__main__':
	main()