import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
import logging
from .config import URLS_FILE, OUTPUT_DIR, REQUEST_DELAY

# --- Helper Functions ---

def load_base_url(filepath):
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

if __name__ == '__main__':
	print(load_base_url(URLS_FILE))