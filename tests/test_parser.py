import pytest
import os
from unittest.mock import patch, mock_open

from parser import parser
from parser.config import PROCESSED_DATA_DIR

@patch('parser.parser.RecursiveCharacterTextSplitter')
@patch('parser.parser.logging')
def test_process_and_chunk_file_success(mock_logging, mock_text_splitter):
	"""
	Tests successful processing of a file using the mocked text splitter.
	"""
	test_filepath = "dummy/path/file.txt"
	file_content = "--- Scraped content from ...\n---\n\nThis is the actual content."
	expected_chunks = ["This is the actual content."]

	mock_splitter_instance = mock_text_splitter.return_value
	mock_splitter_instance.split_text.return_value = expected_chunks

	with patch('parser.parser.open', mock_open(read_data=file_content)) as mock_file:
		result_chunks = parser.process_and_chunk_file(test_filepath)

		mock_file.assert_called_once_with(test_filepath, 'r')
		mock_text_splitter.assert_called_once()
		mock_splitter_instance.split_text.assert_called_once_with("This is the actual content.")
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
	mock_logging):
	"""
	Tests the main entry point, parse_and_chunk_files, for a successful scenario.
	"""
	input_files = ["/path/to/file1.txt", "/path/to/file2.txt"]
	chunks_map = {
		"/path/to/file1.txt": ["chunk1", "chunk2"],
		"/path/to/file2.txt": ["chunk3"]
	}
	out_fnames = ["processed_file1.txt", "processed_file2.txt"]
	written_data = ["chunk1\n---CHUNK---\nchunk2", "chunk3"]

	mock_exists.return_value = True
	mock_process.side_effect = lambda f: chunks_map.get(f, [])
	mock_basename.side_effect = lambda p: p.split('/')[-1]

	result_dir = parser.parse_and_chunk_files(input_files)

	mock_makedirs.assert_called_once_with(PROCESSED_DATA_DIR, exist_ok=True)
	assert mock_process.call_count == 2
	assert mock_open_func.call_count == 2

	for i, fname in enumerate(out_fnames):
		expected_path = os.path.join(PROCESSED_DATA_DIR, fname)
		mock_open_func.assert_any_call(expected_path, 'w')
		handle = mock_open_func()
		handle.write.assert_any_call(written_data[i])

	mock_logging.info.assert_called_with(f"All parsing and chunking tasks complete. Output is in '{PROCESSED_DATA_DIR}'")
	assert str(result_dir) == str(PROCESSED_DATA_DIR)