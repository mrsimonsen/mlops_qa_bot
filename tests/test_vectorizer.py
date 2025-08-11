import pytest
import numpy as np
from unittest.mock import mock_open, patch, MagicMock

import src.vectorizer.vectorizer as vectorizer
from src.config import EMBEDDING_MODEL_NAME, DB_DIR, COLLECTION_NAME

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

@patch('src.vectorizer.vectorizer.os')
@patch('src.vectorizer.vectorizer.logging')
@patch('src.vectorizer.vectorizer.chromadb')
@patch('src.vectorizer.vectorizer.SentenceTransformer')
@patch('src.vectorizer.vectorizer.read_chunks_from_file')
def test_vectorize_and_store(mock_read_chunks, mock_sentence_transformer, mock_chromadb, mock_logging, mock_os, tmp_path):
	test_db_path = str(tmp_path / "test_chroma_db")

	mock_os.path.join.side_effect = lambda a, b: f"{a}/{b}"
	mock_os.listdir.return_value = ['test_file.txt']
	mock_os.path.isfile.return_value = True
	mock_read_chunks.return_value = ['chunk1', 'chunk2']

	mock_model = MagicMock()
	mock_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])
	mock_model.encode.return_value = mock_embeddings
	mock_sentence_transformer.return_value = mock_model

	mock_collection = MagicMock()
	mock_client = MagicMock()
	mock_client.get_or_create_collection.return_value = mock_collection
	mock_chromadb.PersistentClient.return_value = mock_client

	with patch('src.vectorizer.vectorizer.DB_DIR', test_db_path):
		vectorizer.vectorize_and_store('processed_data')

	mock_os.listdir.assert_called_once_with("processed_data")
	mock_read_chunks.assert_called_once_with('processed_data/test_file.txt')
	mock_sentence_transformer.assert_called_once_with(EMBEDDING_MODEL_NAME)
	mock_model.encode.assert_called_once_with(['chunk1', 'chunk2'], show_progress_bar=True)
	mock_chromadb.PersistentClient.assert_called_once_with(path=test_db_path)
	mock_client.get_or_create_collection.assert_called_once_with(name=COLLECTION_NAME)
	mock_collection.add.assert_called_once_with(
		embeddings=mock_embeddings.tolist(),
		documents=['chunk1', 'chunk2'],
		metadatas=[{'source': "test_file.txt"}, {'source': "test_file.txt"}],
		ids=['test_file.txt-0', 'test_file.txt-1']
	)

@patch('src.vectorizer.vectorizer.os')
@patch('src.vectorizer.vectorizer.logging')
@patch('src.vectorizer.vectorizer.read_chunks_from_file')
@patch('src.vectorizer.vectorizer.SentenceTransformer')
def test_vectorize_and_store_no_chunks(mock_sentence_transformer, mock_read_chunks, mock_logging, mock_os, tmp_path):
	"""
	Tests that vectorize_and_store handles the case where no chunks are found.
	"""
	test_db_path= str(tmp_path / "test_chroma_db_empty")
	mock_os.listdir.return_value = ['test_file.txt']
	mock_os.path.isfile.return_value = True
	mock_read_chunks.return_value = [] # No chunks

	with patch("src.vectorizer.vectorizer.DB_DIR", test_db_path):
		vectorizer.vectorize_and_store('processed_data')

	mock_logging.warning.assert_called_with("No chunks found to vectorize. Exiting.")