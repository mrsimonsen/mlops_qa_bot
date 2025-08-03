import os
import git
import trafilatura
from urllib.parse import urlparse
import logging
import re
from typing import Set, Tuple, Annotated
from .config import SCRAPED_DATA_DIR, CLONED_REPOS_DIR

# --- Helper Functions ---
def sanitize_filename(url: str) -> str:
	"""
	Creates a safe and clean filename a URL.
	Example: 'https://github.com/zenml-io/zenml' > 'zenml-io_zenml.txt'

	ARGS:
		url: str, URL text
	RETURNS:
		filename: str, sanitized URL into a filename
	"""
	# use the path component of the url for a more descriptive name
	path = urlparse(url).path
	# remove leading/trailing slashes and replace internal slashes with underscores
	sanitized = path.strip('/').replace('/', '_')
	#remove characters that are not alphanumeric or underscores
	sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', sanitized)
	return f'{sanitized}.txt'


def is_doc_file(filepath: str) -> bool:
	"""
	Checks if a file has a documentation-related extension.

	ARGS:
		filepath: str, the path to the file
	RETURNS:
		is_doc: bool, True if the file has a doc-related extension
	"""
	return filepath.lower().endswith(('.md', '.mdx', '.rst', '.html'))

# --- Main Logic ---

def extract_text_from_file(filepath: str) ->str:
	"""
	Extracts text from a single file using trafilatura.

	ARGS:
		filepath: str, the path to the file
	RETURNS:
		text: str, the extracted text content of the file
	"""
	try:
		with open(filepath, 'r') as f:
			content = f.read()
		# use trafilatura to extract the main text from the file's content
		text = trafilatura.extract(content, include_comments=False, include_tables=False)
		return text or ''
	except Exception as e:
		logging.error(f"Error extracting text from {filepath}: {e}")
		return ''

def process_cloned_repo(repo_path: str, base_url: str, output_file: str) -> None:
	"""
	Processed a cloned repository, extracts text from documentation files,
	and saves it to a single output file.
	
	ARGS:
		repo_path: str, the local path to the cloned repository
		base_url: str, the original URL of the repository for context
		output_file: str, a filepath to save the scaped data
	"""
	logging.info(f"Processing repository for: {base_url}\nOutput will be saved to: {output_file}")

	with open(output_file, 'w') as f:
		f.write(f"--- Scraped content from {base_url} ---\n")

	for root, _, files in os.walk(repo_path):
		for file in files:
			if is_doc_file(file):
				file_path = os.path.join(root, file)
				logging.info(f"\tProcessing: {file_path}")
				text = extract_text_from_file(file_path)
				if text:
					with open(output_file, 'a') as f:
						relative_path = os.path.relpath(file_path, repo_path)
						f.write(f"\n\n--- Page: {base_url}/blob/main/{relative_path} ---\n\n")
						f.write(text)
	
	logging.info(f"Finished processing repository for {base_url}.")

def scrape_single_repo(repo_url: str) -> Annotated[str, "scraped_file_path"]:
	"""
	Main entry point to clone a single GitHub repository and extract its documentation.

	ARGS:
		repo_url: str, the URL of the GitHub repository to clone.
	RETURNS:
		filepath: str, the path to the text file that contains the scrapped content.
	"""
	os.makedirs(SCRAPED_DATA_DIR, exist_ok=True)
	os.makedirs(CLONED_REPOS_DIR, exist_ok=True)

	repo_name = urlparse(repo_url).path.split('/')[-1]
	clone_path = os.path.join(CLONED_REPOS_DIR, repo_name)

	try:
		if not os.path.exists(clone_path):
			logging.info(f"Cloning {repo_url} into {clone_path}")
			git.Repo.clone_from(repo_url, clone_path)
		else:
			logging.info(f"Repository {repo_name} already cloned. Pulling latest changes.")
			repo = git.Repo(clone_path)
			repo.remotes.origin.pull()
	except git.exc.GitCommandError as e: # type: ignore
		logging.error(f"Error cloning or pulling repository {repo_url}: e")
		return ""
	
	output_filename = sanitize_filename(repo_url)
	output_filepath = os.path.join(SCRAPED_DATA_DIR, output_filename)

	process_cloned_repo(clone_path, repo_url, output_filepath)
	return output_filepath