import pytest
from unittest.mock import patch, mock_open, MagicMock, call

import scraper.scraper as scraper

@patch('os.path.exists', return_value=True)
@patch(
	  'builtins.open',
	  new_callable=mock_open,
	  read_data="https://example.com\n  https://test.com  \nhttp://anotherexample.org")
def test_load_base_url_success(mock_file, mock_exists):
	"""
	Test successful URL loading by mocking file system calls.
	- os.path.exists is mocked to return True.
	- builtins.open is mocked to simulate reading a file in memory.
	"""
	dummy_filepath = 'any/path/urls.txt'
	result = scraper.load_base_url(dummy_filepath)
	expected = ["https://example.com","https://test.com","http://anotherexample.org"]
	
	assert result == expected
	mock_exists.assert_called_once_with(dummy_filepath)
	mock_file.assert_called_once_with(dummy_filepath, 'r')

@patch('os.path.exists', return_value=False)
def test_load_base_url_failure(mock_exists, caplog):
	"""
	Tests the file-not-found case by mocking os.path.exists to return False.
	The 'caplog' fixture captures logging output.
	"""
	non_existent_file = 'path/that/does/not/exist.txt'
	result = scraper.load_base_url(non_existent_file)

	assert result == []
	mock_exists.assert_called_once_with(non_existent_file)
	assert f"Error: URL file not found at '{non_existent_file}'" in caplog.text

@pytest.mark.parametrize("domain_input, expected_output", [
	#Test case: standard domain
	("docs.zenml.io", "docs_zenml_io.txt"),
	#Test case: special characters
	("!@#$%^&*-=+:/<>,;?", ".txt"),
	#Test case: empty string
	("", ".txt"),
	#Test case: all numbers
	("123.45.67.89", "123_45_67_89.txt"),
	#Test case: multiple dots
	("test..domain.org", "test__domain_org.txt"),
	#Test case: no dots
	("localhost", "localhost.txt")
])
def test_sanitize_filename(domain_input, expected_output):
	"""
	Tests the sanitize_filename function with various inputs.
	Uses pytest.mark.parameterize to run the same test function
	with different inputs and expected outputs.
	"""
	assert scraper.sanitize_filename(domain_input) == expected_output

@pytest.mark.parametrize("url, base_domain, expected", [
	#Test case: positive
	("https://docs.example.com/path/page", "docs.example.com", True),
	#Test case different subdomain
	("https://api.example.com/path/page", "docs.example.com", False),
	#Test case: different domains
	("https://another-site.com", "docs.example.com", False),
	#Test case: relative url
	("/path/page", "docs.example.com", False),
	#Test case: edge - url with www vs base_domain
	("https://www.example.com", "example.com", False)
])
def test_is_valid_url(url, base_domain, expected):
	"""
	Tests the URL validation logic with various cases.
	This test uses pytest.mark.parameterize to check multiple scenarios
	efficiently without needing mocks.
	"""
	assert scraper.is_valid_url(url, base_domain) == expected