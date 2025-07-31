import pytest
from unittest.mock import mock_open, patch

import vectorizer.vectorizer as vectorizer

test_cases = [
	(
		"multiple chunks",
		"chunk1\n---CHUNK---\nchunk2\n---CHUNK---\nchunk3",
		["chunk1", "chunk2", "chunk3"]
	),
	(
		"single chunk",
		"This is a single chunk of text.",
		["This is a single chunk of text."]
	),
	(
		"empty file",
		"",
		[]
	),
	(
		"chunks with extra whitespace",
		"  chunk1  \n---CHUNK---\n\n chunk2 \n",
		["chunk1", "chunk2"]
	),
	(
		"file with only separators",
		"\n---CHUNK---\n\n---CHUNK---\n",
		[]
	)
]
@pytest.mark.parametrize(
	"test_id, file_content, expected_output",
	test_cases,
	ids=[case[0] for case in test_cases]
)
def test_read_chunks_from_file(test_id, file_content, expected_output):
	"""
	Tests the read_chunks_from_file function with various scenarios.
	"""
	with patch('builtins.open', mock_open(read_data=file_content)) as mock_file:
		result = vectorizer.read_chunks_from_file("dummy_path.txt")
		assert result == expected_output
		mock_file.assert_called_once_with("dummy_path.txt", 'r')