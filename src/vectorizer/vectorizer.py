import os
import logging
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
from .config import EMBEDDING_MODEL_NAME, PERSIST_DIRECTORY, COLLECTION_NAME

def read_chunks_from_file(filepath: str) -> List[str]:
	"""
	Reads processed text chunks from a file.
	"""
	with open(filepath, 'r') as f:
		content = f.read()

	chunks = content.split("\n---CHUNK---\n")
	return [stripped for chunk in chunks if (stripped := chunk.strip())]

def vectorize_and_store(processed_data_dir: str):
	"""
	Main function to vectorize processed data and store it in ChromaDB.

	ARGS:
		processed_data_dir: str, the directory containing the chunked text files.
	"""
	logging.info('Starting vectorization and storage process...')
	
	#1. Load the embeddings model
	logging.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
	model = SentenceTransformer(EMBEDDING_MODEL_NAME)

	#2. Initialize ChromaDB client
	client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
	collection = client.get_or_create_collection(name=COLLECTION_NAME)

	#3. Read all chunks from all processed files
	all_chunks = []
	all_metadata = []
	all_ids = []

	for filename in os.listdir(processed_data_dir):
		filepath = os.path.join(processed_data_dir, filename)
		if os.path.isfile(filepath):
			chunks = read_chunks_from_file(filepath)
			for i, chunk in enumerate(chunks):
				all_chunks.append(chunk)
				all_metadata.append({"source": filename})
				all_ids.append(f"{filename}-{i}")

	if not all_chunks:
		logging.warning("No chunks found to vectorize. Exiting.")
		return

	#4. Generate embeddings in batches (more efficient)
	embeddings = model.encode(all_chunks, show_progress_bar=True)

	#5. Add to ChromaDB collection
	collection.add(
		embeddings=embeddings.tolist(),
		documents=all_chunks,
		metadatas=all_metadata,
		ids=all_ids
	)

	logging.info(f"Successfully vectorized and stored {len(all_chunks)} documents in collection '{COLLECTION_NAME}")
	logging.info(f"Vector database persisted at: {PERSIST_DIRECTORY}")