import os
import git
import trafilatura
from urllib.parse import urlparse
import logging
import re
from typing import Annotated
from src.config import SCRAPED_DATA_DIR, CLONED_REPOS_DIR

# --- Helper Functions ---

def get_base_repo_url(url:str) -> str:
	"""
	Extracts the base repository URL, removing subdirectories and branches.
	Example: 'https://github.com/zenml-io/zenml/tree/main/docs' -> 'https://github.com/zenml-io/zenml'
	"""
	parsed_url = urlparse(url)
	path_parts = parsed_url.path.strip('/').split('/')
	if len(path_parts) >= 2:
		base_repo_path = f"/{path_parts[0]}/{path_parts[1]}"
		return f"{parsed_url.scheme}://{parsed_url.netloc}{base_repo_path}"
	return url # return original url if not in the expected format


def sanitize_filename(url: str) -> str:
	"""
	Creates a safe and clean filename a URL based on its repo name.
	Example: 'https://github.com/zenml-io/zenml' > 'zenml-io_zenml.txt'
	"""
	# use the path component of the url for a more descriptive name
	path = urlparse(url).path
	parts = path.strip('/').split('/')
	# use the first two parts of the path for a unique name (e.g., user_repo)
	if len(parts) >=2:
		sanitized = f"{parts[0]}_{parts[1]}"
	else:
		sanitized = parts[-1] if parts else "unknown"
	# clean up any remaining invalid characters
	sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', sanitized)
	return f'{sanitized}.txt'

def is_doc_file(filepath: str) -> bool:
	"""
	Checks if a file has a documentation-related extension.
	"""
	return filepath.lower().endswith(('.md', '.mdx', '.rst', '.html'))

# --- Main Logic ---

def extract_text_from_file(filepath: str) ->str:
	"""
	Extracts text from a single file using trafilatura.
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
				# exclude .git from processing
				if ".git" in file_path:
					continue
				logging.info(f"\tProcessing: {file_path}")
				text = extract_text_from_file(file_path)
				if text:
					with open(output_file, 'a') as f:
						relative_path = os.path.relpath(file_path, repo_path)
						original_repo_url = get_base_repo_url(base_url)
						f.write(f"\n\n--- Page: {original_repo_url}/blob/main/{relative_path} ---\n\n")
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

	base_url = get_base_repo_url(repo_url)
	clone_url = base_url + '.git'
	repo_name_for_dir = sanitize_filename(base_url).replace('.txt','')
	clone_path = os.path.join(CLONED_REPOS_DIR, repo_name_for_dir)

	try:
		if not os.path.exists(clone_path):
			logging.info(f"Cloning {clone_url} into {clone_path}")
			git.Repo.clone_from(clone_url, clone_path)
		else:
			logging.info(f"Repository {repo_name_for_dir} already cloned. Pulling latest changes.")
			repo = git.Repo(clone_path)
			repo.remotes.origin.pull()
	except git.exc.GitCommandError as e: # type: ignore
		logging.error(f"Error cloning or pulling repository {repo_url}: e")
		return ""
	
	output_filename = sanitize_filename(repo_url)
	output_filepath = os.path.join(SCRAPED_DATA_DIR, output_filename)

	process_cloned_repo(clone_path, repo_url, output_filepath)
	return output_filepath