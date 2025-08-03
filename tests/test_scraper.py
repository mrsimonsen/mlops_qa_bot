import pytest
from unittest.mock import patch, mock_open, MagicMock
import git
import os

from scraper import scraper
from scraper.config import SCRAPED_DATA_DIR, CLONED_REPOS_DIR


# --- Test for Helper Functions ---

@pytest.mark.parametrize(
	"test_id, url_input, expected_output",
	[
		("standard_github_url", "https://github.com/zenml-io/zenml", "zenml-io_zenml.txt"),
		("url_with_subdirectories", "https://gitub.com/a/b/c", "a_b_c.txt"),
		("url_with_special_chars_in_path", "https://example.com/a!@$b", "ab.txt"),
		("url_with_trailing_slash", "https://gituhb.com/user/repo/", "user_repo.txt"),
		("url_with_no_path", "https://example.com", ".txt")
	],
	ids=lambda x: x[0] if isinstance(x, tuple) else None
)
def test_sanitize_filename(test_id, url_input, expected_output):
	"""
	Test the sanitize_filename function with various URL inputs.
	The new implementation bases the filename on the URL's path.
	"""
	assert scraper.sanitize_filename(url_input) == expected_output

@pytest.mark.parametrize(
	"filepath, expected",
	[
		('doc.md', True),
		('guide.mdx', True),
		('readme.rst', True),
		('index.html', True),
		('photo.jpg', False),
		('script.py', False),
		('Dockerfile', False),
		('UPPERCASE.MD', True)
	]
)
def test_is_doc_file(filepath, expected):
	"""
	Tests the is_doc_file function to correctly identify documentation files.
	"""
	assert scraper.is_doc_file(filepath) == expected


# --- Tests for Core Logic ---

@patch("trafilatura.extract")
@patch("builtins.open", new_callable=mock_open, read_data='file content')
def test_extract_text_from_file_success(mock_file, mock_trafilatura):
	"""
	Test successful extraction from a file using trafilatura.
	"""
	expected_result = "extracted text"
	mock_trafilatura.return_value = expected_result
	result = scraper.extract_text_from_file("dummy/path.md")
	mock_file.assert_called_once_with("dummy/path.md", 'r')
	mock_trafilatura.assert_called_once_with("file content", include_comments=False, include_tables=False)
	assert result == expected_result

@patch("trafilatura.extract")
@patch("builtins.open", new_callable=mock_open, read_data="file content")
def test_extract_text_from_file_no_text(mock_file, mock_trafilatura):
	"""
	Tests the case where trafilatura returns None (no main text found).
	"""
	mock_trafilatura.return_value = None
	result = scraper.extract_text_from_file("dummy/path.md")
	assert result == ''

@patch("builtins.open", side_effect=IOError("File not found"))
def test_extract_text_from_file_error(mock_file, caplog):
	"""
	Tests error handling when a file cannot be opened.
	"""
	result = scraper.extract_text_from_file("nonexistent/path.md")
	assert result == ''
	assert "Error extracting text from nonexistent/path.md" in caplog.text

@patch("os.walk")
@patch("scraper.scraper.is_doc_file")
@patch("scraper.scraper.extract_text_from_file")
@patch("builtins.open", new_callable=mock_open)
def test_process_cloned_repo(mock_open_file, mock_extract, mock_is_doc, mock_walk):
	"""
	Tests the processing of a directory of files.
	- Mocks os.walk to simulate a file structure.
	- Mocks helper function to isolate the logic of this function.
	- Verifies that the correct files are processed and written to the output.
	"""
	repo_path = '/tmp/repo'
	base_url = 'https://github.com/test/repo'
	output_file = '/temp/output.txt'

	#Simulate a file structure
	mock_walk.return_value = [
		(repo_path, [], ["index.md", "image.png"]),
		(f"{repo_path}/subdir", [], ['guide.rst', 'script.py'])
	]

	#Mock helpers to control which files are processed
	mock_is_doc.side_effect = lambda f: f.endswith((".md", (".rst")))
	mock_extract.side_effect = ['Text from index.', 'Text from guide.']

	scraper.process_cloned_repo(repo_path, base_url, output_file)

	#check that os.walk was called correctly
	mock_walk.assert_called_once_with(repo_path)
	
	#check that extract_text_from_file was called fo the doc files only
	assert mock_extract.call_count == 2
	mock_extract.assert_any_call(os.path.join(repo_path, 'index.md'))
	mock_extract.assert_any_call(os.path.join(repo_path, 'subdir', 'guide.rst'))

	#check file writing operations
	handle = mock_open_file()
	handle.write.assert_any_call(f"--- Scraped content from {base_url} ---\n")
	handle.write.assert_any_call(f"\n\n--- Page: https://github.com/test/repo/blob/main/index.md ---\n\n")
	handle.write.assert_any_call(f"Text from index.")
	handle.write.assert_any_call(f"\n\n--- Page: https://github.com/test/repo/blob/main/subdir/guide.rst ---\n\n")
	handle.write.assert_any_call(f"Text from guide.")


# --- Tests for Main Entry Point ---

@patch("os.makedirs")
@patch("os.path.exists", return_value=False)
@patch("git.Repo.clone_from")
@patch("scraper.scraper.process_cloned_repo")
def test_scrape_single_repo_clone(mock_process, mock_clone, mock_exists, mock_makedirs):
	"""
	Tests the main function when the repository need to be cloned.
	"""
	repo_url = "https://github.com/test/new-repo"
	expected_output_path = os.path.join(SCRAPED_DATA_DIR, 'test_new-repo.txt')
	clone_path = os.path.join(CLONED_REPOS_DIR, 'new-repo')

	result = scraper.scrape_single_repo(repo_url)

	# verify directories are created
	mock_makedirs.assert_any_call(SCRAPED_DATA_DIR, exist_ok=True)
	mock_makedirs.assert_any_call(CLONED_REPOS_DIR, exist_ok=True)

	# verify cloning and processing are called
	mock_clone.assert_any_call(repo_url, clone_path)
	mock_process.assert_called_once_with(clone_path, repo_url, expected_output_path)
	assert result == expected_output_path

	@patch("os.makedirs")
	@patch("os.path.exists", return_value=True)
	@patch("git.Repo")
	@patch("scraper.scraper.process_cloned_repo")
	def test_scrape_single_repo_pull(mock_process, mock_repo, mock_exists, mock_makedirs):
		"""
		Tests the main function when the repository already exists and should be pulled.
		"""
		repo_url = "https://github.com/test/existing.repo"
		expected_output_path = os.path.join(SCRAPED_DATA_DIR, '_test_existing-repo.txt')
		clone_path = os.path.join(CLONED_REPOS_DIR, 'existing-repo')

		# mock repository object and its pull method
		mock_repo_instance = MagicMock()
		mock_repo.return_value = mock_repo_instance

		result = scraper.scrape_single_repo(repo_url)

		# verify it check for existence and initializes a Repo object
		mock_exists.assert_called_once_with(clone_path)
		mock_repo.assert_called_once_with(clone_path)

		# verify pull is called
		mock_repo_instance.remotes.origin.pull.assert_called_once()

		# verify processing is called
		mock_process.assert_called_once_with(clone_path, repo_url, expected_output_path)
		assert result == expected_output_path

@patch("os.makedirs")
@patch("os.path.exists", return_value=False)
@patch("git.Repo.clone_from", side_effect=git.exc.GitCommandError("clone", "error")) # type: ignore
def test_scrape_single_repo_git_error(mock_clone, mock_exists, mock_makedirs, caplog):
	"""
	Test error handling during a git clone operation.
	"""
	repo_url = "https://github.com/test/fail-repo"
	result = scraper.scrape_single_repo(repo_url)

	assert "Error cloning or pulling repository" in caplog.text
	assert result == ''
