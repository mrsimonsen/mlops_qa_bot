import pytest
from unittest.mock import patch, mock_open

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