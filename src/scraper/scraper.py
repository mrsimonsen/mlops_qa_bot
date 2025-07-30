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


def is_valid_url(url: str, base_domain: str) -> bool:
	"""
	Checks if a URL is valid and belongs to the same domain as the base URL.

	ARGS:
		url: str, the URL to check
		base_domain: str, the base URL to establish the domain
	RETURNS:
		is_valid: bool, True if the full URL is valid and a part of the base_domain
	"""
	parsed_url = urlparse(url)
	return bool(parsed_url.scheme) and bool(parsed_url.netloc) and parsed_url.netloc == base_domain

# --- Main Logic ---


def scrape_page(url: str, session: requests.Session, base_domain: str) -> tuple[str, set[str]]:
	"""
	Scrapes a single page, extracts the main text content, and finds all valid links.

	ARGS:
		url: str, the page to be scraped
		session: request.Session, session object for making HTML requests
		base_domain: str, the base domain to keep from leaving the site
	RETURNS:
		text: str, the text content of the scraped page
		links: set, the links found from the page that are in the base_domain
	"""
	try:
		response = session.get(url, timeout=10)
		response.raise_for_status()
	
		#skip this page if no text
		if 'text/html' not in response.headers.get('Content Type', ''):
			return '', set()
		
		soup = BeautifulSoup(response.content, 'html.parser')
		
		main_content = soup.find('main') or soup.find('article') or soup.find('div', role='main')
		if main_content:
			text = main_content.get_text(separator='\n', strip=True)
		else:
			text = soup.body.get_text(separator='\n', strip=True)

		links = set()
		for a_tag in soup.find_all('a', href=True):
			href = a_tag['href']
			full_url = urljoin(url, href)
			full_url = full_url.split('#')[0].split('?')[0]

			if is_valid_url(full_url, base_domain):
				links.add(full_url)
		return text, links
	except requests.exceptions.RequestException as e:
		logging.error(f'Error scraping {url}: {e}')
		return '', set()

def crawl_site(base_url: str, session: requests.Session, output_file: str) -> None:
	"""
	Orchestrates the scraping process for a single base URL, saving to a specific file.
	
	ARGS:
		base_url: str, the base URL for the site to be scraped
		session: requests.Session, session object for making HTML requests
		output_file: str, a filepath to save the scrapped data
	"""
	base_domain = urlparse(base_url).netloc
	to_visit = {base_url}
	visited = set()

	logging.info(f"Starting crawl for: {base_url}/nOutput saved to: {output_file}")

	#clear output_file before starting crawl
	with open(output_file, 'w') as f:
		f.write(f"--- Scraped content from {base_url} ---\n")
	
	while to_visit:
		current_url = to_visit.pop()
		# don't scrape the same page twice
		if current_url in visited:
			continue
		
		logging.info(f"\tScraping: {current_url}")
		visited.add(current_url)

		text, new_links = scrape_page(current_url, session, base_domain)

		if text:
			with open(output_file, 'a') as f:
				f.write(f"\n\n--- Page: {current_url} ---\n\n")
				f.write(text)
		
		to_visit.update(new_links - visited)
		time.sleep(REQUEST_DELAY)

	logging.info(f"Finished crawling {base_url}. Visited {len(visited)} pages.")


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
	os.makedirs(OUTPUT_DIR, exist_ok=True)
	logging.info("output directory is ready")
	
	#create session
	session = requests.Session()
	session.headers.update( {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
	logging.info("session created")

	#Crawl each site from list and save in own file
	for url in base_urls:
		domain = urlparse(url).netloc
		output_filename = sanitize_filename(domain)
		output_filepath = os.path.join(OUTPUT_DIR, output_filename)

		crawl_site(url, session, output_filepath)
	logging.info(f"All scraping tasks complete and saved in '{OUTPUT_DIR}'")
if __name__ == '__main__':
	main()