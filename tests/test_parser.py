import pytest
from unittest.mock import patch, mock_open, MagicMock, ANY

import parser.parser as parser
from parser.config import OUTPUT_DIR
test_cases = [
	("no change", "This is a clean sentence.", "This is a clean sentence."),
	("excessive newlines", "Hello\n\n\n\nWorld", "Hello\n\nWorld"),
	("preserve paragraph break", "Paragraph 1\n\nParagraph 2", "Paragraph 1\n\nParagraph 2"),
	("strip whitespace", "  line one  \n   line two ", "line one\nline two"),
	("remove long non-alnum", "Delete this ---- but not this ---", "Delete this  but not this ---"),
	("remove long symbols", "Here is some text !@#$%^&* with symbols.", "Here is some text  with symbols."),
	("keep short non-alnum", "This is A-OK.", "This is A-OK."),
	("combined cleaning", "   First line.   \n\n\n\n------\n  Second line.  ", "First line.\n\n\nSecond line."),
	("empty string", "", ""),
	("whitespace only", "   \n   \n ", "\n\n"),
	("non-alnum only", "**********", "")
]
@pytest.mark.parametrize(
		"test_id, input_text, expected_output",
		test_cases,
		ids=[cases[0] for cases in test_cases]
	)
def test_clean_text(test_id, input_text, expected_output):
	"""
	Tests the clean_text function with various inputs.
	"""
	assert parser.clean_text(input_text) == expected_output

test_cases = [
	("empty string", "", []),
	(
		"text shorter than chunk",
		"This is short.",
		["This is short."]
	),
	(
		"standard text multiple chunks",
		"This is a long string for testing the chunking functionality.",
		[
			"This is a long strin", #text[0:20]
			"string for testing t", #text[15:35]
			"ing the chunking fun", #text[30:50]
			"g functionality.",     #text[45:65]
			"."                     #text[60:80]
		]
	)
]
TEST_CHUNK_SIZE = 20
TEST_CHUNK_OVERLAP = 5
@pytest.mark.parametrize(
		"test_id, input_text, expected_output",
		test_cases,
		ids=[cases[0] for cases in test_cases]
)
def test_chunk_text(monkeypatch, test_id, input_text, expected_output):
	"""
	Tests chunking by first patching the config constants with smaller,
	test-friendly values and then running various text scenarios.
	"""
	monkeypatch.setattr("parser.parser.CHUNK_SIZE", TEST_CHUNK_SIZE)
	monkeypatch.setattr("parser.parser.CHUNK_OVERLAP", TEST_CHUNK_OVERLAP)

	actual_output = parser.chunk_text(input_text)

	assert actual_output == expected_output

test_cases = [
	(
		"with header",
		"--- Scraped content from ...\n---\n\nThis is the actual content.",
		"This is the actual content.",
		["This is", "the actual", "content"]
	),
	(
		"no header",
		"No header here, just raw content.",
		"No header here, just raw content.",
		["No header", "here just", "raw content"]
	)
]
@pytest.mark.parametrize(
		"test_id, file_content, cleaned_input, expected_chunks",
		test_cases,
		ids=[case[0] for case in test_cases]
)
@patch('parser.parser.chunk_text')
@patch('parser.parser.clean_text')
@patch('parser.parser.logging')
def test_process_and_chunk_file_success(
	mock_logging,
	mock_clean_text,
	mock_chunk_text,
	test_id,
	file_content,
	cleaned_input,
	expected_chunks):
	"""
	Tests successful processing of a file, both with and without a header.
	"""
	test_filepath = "dummy/path/file.txt"
	with patch('parser.parser.open', mock_open(read_data=file_content)) as mock_file:
		mock_clean_text.return_value = cleaned_input
		mock_chunk_text.return_value = expected_chunks

		result_chunks = parser.process_and_chunk_file(test_filepath)

		mock_file.assert_called_once_with(test_filepath, 'r')
		mock_clean_text.assert_called_once_with(cleaned_input)
		mock_chunk_text.assert_called_once_with(cleaned_input)
		assert result_chunks == expected_chunks
		mock_logging.error.assert_not_called()


@patch('parser.parser.open')
@patch('parser.parser.logging')
def test_process_and_chunk_file_file_not_found(mock_logging, mock_open_func):
	"""
	Tests the function's error handling when a FileNotFoundError occurs.
	It ensures the error is logged and an empty list is returned.
	"""
	test_filepath = "nonexistent/file.txt"
	error_message = "File does not exist"
	mock_open_func.side_effect = FileNotFoundError(error_message)

	result_chunks = parser.process_and_chunk_file(test_filepath)

	assert result_chunks == []
	mock_logging.info.assert_called_once_with(f"Processing and chunking file: {test_filepath}")
	mock_logging.error.assert_called_once_with(f"Error processing file {test_filepath}: {error_message}")