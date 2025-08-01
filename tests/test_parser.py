import pytest
import os
from unittest.mock import patch, mock_open

from parser import parser
from parser.config import PROCESSED_DATA_DIR
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

test_cases = [
	(
		"successful run",
		["/path/to/file1.txt", "/path/to/file2.txt"],
		{
			"/path/to/file1.txt": ["chunk1", "chunk2"],
			"/path/to/file2.txt": ["chunk3"]
		},
		True, 2, 2,
		["processed_file1.txt", "processed_file2.txt"],
		["chunk1\n---Chunk---\nchunk2", "chunk3"]
	),
	(
		"non-existent file",
		["/path/to/real.txt", "/path/to/fake.txt"],
		{"/path/to/real.txt": ["data"]},
		[True, False], 1, 1,
		["processed_real.txt"],
		["data"]
	),
	(
		"no chunks produced",
		["/path/to/file1.txt"],
		{"/path/to/file1.txt": []},
		True, 1, 0,
		[],
		[]
	),
	(
		"empty input list",
		[],
		{},
		True, 0, 0,
		[],
		[]
	)
]

@pytest.mark.parametrize(
	"test_id, input_files, chunks_map, path_exists, process_calls, open_calls, out_fnames, written_data",
	test_cases,
	ids=[case[0] for case in test_cases]
)
@patch('parser.parser.logging')
@patch('parser.parser.open', new_callable=mock_open)
@patch('parser.parser.process_and_chunk_file')
@patch('os.path.basename')
@patch('os.path.exists')
@patch('os.makedirs')
def test_parse_and_chunk_files(
	mock_makedirs,
	mock_exists,
	mock_basename,
	mock_process,
	mock_open_func,
	mock_logging,
	test_id,
	input_files,
	chunks_map,
	path_exists,
	process_calls,
	open_calls,
	out_fnames,
	written_data):
	"""
	Tests the main entry point, parse_and_chunk_files, for various scenarios.
	"""
	if isinstance(path_exists, list):
		mock_exists.side_effect = path_exists
	else:
		mock_exists.side_effect = [path_exists] * len(input_files)
	mock_process.side_effect = lambda f: chunks_map.get(f, [])
	mock_basename.side_effect = lambda p: p.split('/')[-1]

	result_dir = parser.parse_and_chunk_files(input_files)

	mock_makedirs.assert_called_once_with(PROCESSED_DATA_DIR, exist_ok=True)
	assert mock_process.call_count == process_calls
	assert mock_open_func.call_count == open_calls

	if open_calls > 0:
		for i, fname in enumerate(out_fnames):
			expected_path = os.path.join(PROCESSED_DATA_DIR, fname)
			mock_open_func.assert_any_call(expected_path, 'w')
			handle = mock_open_func()
			handle.write.assert_any_call(written_data[i])
	
	mock_logging.info.assert_called_with(f"All parsing and chunking tasks complete. Output is in '{PROCESSED_DATA_DIR}'")
	assert str(result_dir) == str(PROCESSED_DATA_DIR)