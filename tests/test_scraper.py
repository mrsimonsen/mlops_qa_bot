import pytest
from unittest.mock import patch, mock_open, MagicMock, ANY
import requests

from scraper import scraper
from scraper.config import SCRAPED_DATA_DIR

test_cases = [
	("standard domain", "docs.zenml.io", "docs_zenml_io.txt"),
	("special characters", "!@#$%^&*-=+:/<>,;?", ".txt"),
	("empty string", "", ".txt"),
	("all numbers", "123.45.67.89", "123_45_67_89.txt"),
	("multiple dots", "test..domain.org", "test__domain_org.txt"),
	("no dots", "localhost", "localhost.txt")
]
@pytest.mark.parametrize(
	"test_id, domain_input, expected_output",
	test_cases,
	ids=[cases[0] for cases in test_cases]
)
def test_sanitize_filename(test_id, domain_input, expected_output):
	"""
	Tests the sanitize_filename function with various inputs.
	Uses pytest.mark.parameterize to run the same test function
	with different inputs and expected outputs.
	"""
	assert scraper.sanitize_filename(domain_input) == expected_output

test_cases = [
	("positive", "https://docs.example.com/path/page", "docs.example.com", True),
	("different subdomain", "https://api.example.com/path/page", "docs.example.com", False),
	("different domains", "https://another-site.com", "docs.example.com", False),
	("relative url", "/path/page", "docs.example.com", False),
	("url with www vs base_domain", "https://www.example.com", "example.com", True)
]
@pytest.mark.parametrize(
	"test_id, url, base_domain, expected",
	test_cases,
	ids=[cases[0] for cases in test_cases]
)
def test_is_valid_url(test_id, url, base_domain, expected):
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
def test_scrape_single_url(mock_makedirs, mock_session_constructor, mock_crawl_site):
	"""
	Tests the main entry point for scraping a single URL.
	- Mocks dependencies to ensure they are called correctly.
	- Verifies that craw_site is called with the expected URL and file path.
	"""
	#set up
	base_url = "https://docs.test.com/some/path"
	expected_output_path = f'{SCRAPED_DATA_DIR}/docs_test_com.txt'
	
	mock_session_instance = MagicMock()
	mock_session_constructor.return_value = mock_session_instance

	# execute
	result_path = scraper.scrape_single_url(base_url)

	# assert
	#verify output directory creation
	mock_makedirs.assert_called_once_with(SCRAPED_DATA_DIR, exist_ok=True)
	# verify session was created and headers updated
	mock_session_constructor.assert_called_once()
	mock_session_instance.headers.update.assert_called_once()
	#verify that crawl_site() was called with correct args
	mock_crawl_site.assert_called_once_with(
		base_url,
		mock_session_instance,
		expected_output_path
	)
	#verify function returns correct output path
	assert result_path == expected_output_path