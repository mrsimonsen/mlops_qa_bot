import pytest
from unittest.mock import patch, mock_open, MagicMock, ANY, call
import requests

import scraper.scraper as scraper
from scraper.config import OUTPUT_DIR

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

@patch('requests.Session')
def test_scrape_page_success(mock_session):
	"""
	Tests successful page scraping.
	- Mocks the requests.Session to return a fake HTML response.
	- Verifies that text is extracted correctly from the <main> tag.
	- Verifies that only valid, on-domain links are returned.
	"""
	base_url = "https://test.com"
	base_domain = "test.com"
	html_content= """
<html>
	<body>
		<header>Some awesome header</header>
		<main>
			<h1>Main Title</h1>
			<p>This is the main content.</p>
			<a href="/page2">Internal Link</a>
			<a href="https://test.com/page3#section">Internal Link with fragment</a>
			<a href="https://external.com">External Link</a>
		</main>
	</body>
</html>
"""

	mock_response = MagicMock()
	mock_response.content = html_content.encode('utf-8')
	mock_response.headers = {'Content-Type': 'text/html'}
	mock_response.raise_for_status.return_value = None

	mock_session.get.return_value = mock_response
	
	text, links = scraper.scrape_page(base_url, mock_session, base_domain)

	expected_text = "Main Title\nThis is the main content.\nInternal Link\nInternal Link with fragment\nExternal Link"
	expected_links = {"https://test.com/page2", "https://test.com/page3"}

	assert text.strip() == expected_text
	assert links == expected_links
	mock_session.get.assert_called_once_with(base_url, timeout=10)

@patch('requests.Session')
def test_scrape_page_request_error(mock_session, caplog):
	"""
	Tests how scrape_page handles a network error.
	- Mocks the session's get method to raise a RequestException.
	- Verifies that the function returns empty values and logs an error.
	"""
	url = "https://test.com"
	mock_session.get.side_effect = requests.exceptions.RequestException("Test Error")

	text, links = scraper.scrape_page(url, mock_session, "test.com")

	assert text == ""
	assert links == set()
	assert f'Error scraping {url}: Test Error' in caplog.text

@patch('time.sleep', return_value=None)
@patch('scraper.scraper.scrape_page')
@patch('builtins.open', new_callable=mock_open)
def test_crawl_site(mock_file, mock_scrape_page, mock_sleep, caplog):
	"""
	Tests the complete crawling process for a single site.
	- Mocks 'scrape_page' to simulate discovering new pages.
	- Mocks 'builtin.open' to check file writing without touching disk.
	- Mocks 'time.sleep' to prevent delays.
	- Simulates a two-page crawl and verifies the calls and file content.
	"""
	base_url = "https://crawler.test"
	page2_url = "https://crawler.test/page2"

	mock_scrape_page.side_effect = [
		("Text from page 1.", {page2_url}),
		("Text from page 2.", set())
	]

	scraper.crawl_site(base_url, requests.Session(), "dummy_output.txt")

	assert mock_scrape_page.call_count == 2
	mock_scrape_page.assert_any_call(base_url, ANY, "crawler.test")
	mock_scrape_page.assert_any_call(page2_url, ANY, "crawler.test")

	handle = mock_file()
	handle.write.assert_any_call(f"--- Scraped content from {base_url} ---\n")
	handle.write.assert_any_call(f"\n\n--- Page: {base_url} ---\n\n")
	handle.write.assert_any_call(f"Text from page 1.")
	handle.write.assert_any_call(f"\n\n--- Page: {page2_url} ---\n\n")
	handle.write.assert_any_call(f"Text from page 2.")

@patch('scraper.scraper.crawl_site')
@patch('requests.Session')
@patch('os.makedirs')
@patch('scraper.scraper.load_base_url')
def test_main_flow(mock_load_urls, mock_makedirs, mock_session, mock_crawl_site):
	"""
	Tests the main function's orchestration logic.
	- Mocks all helper functions to ensure 'main' calls them correctly.
	- 'load_base_url' is mocked to return a list of URLs to process.
	- Verifies that 'crawl_site' is called once for each URL with the correct
	 parameters.
	"""
	urls = ['https://site1.com', 'https://site2.org']
	mock_load_urls.return_value = urls

	scraper.main()

	mock_load_urls.assert_called_once()
	mock_makedirs.assert_called_once_with(OUTPUT_DIR, exist_ok=True)

	assert mock_crawl_site.call_count == 2
	expected_calls = [
		call("https://site1.com", ANY, f'{OUTPUT_DIR}/site1_com.txt'),
		call("https://site2.org", ANY, f'{OUTPUT_DIR}/site2_org.txt')
	]
	mock_crawl_site.assert_has_calls(expected_calls, any_order=False)