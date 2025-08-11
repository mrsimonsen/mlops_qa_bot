import os
import logging
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
from src.config import EMBEDDING_MODEL_NAME, DB_DIR, COLLECTION_NAME

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
	This version processes data in batches to avoid exceeding ChromaDB's limits.

	ARGS:
		processed_data_dir: str, the directory containing the chunked text files.
	"""
	logging.info('Starting vectorization and storage process...')
	
	#1. Load the embeddings model
	logging.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
	model = SentenceTransformer(EMBEDDING_MODEL_NAME)

	#2. Initialize ChromaDB client
	client = chromadb.PersistentClient(path=DB_DIR)
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
	batch_size = 4000
	for i in range(0, len(all_chunks), batch_size):
		end_i = min(i + batch_size, len(all_chunks))

		batch_chunks = all_chunks[i: end_i]
		batch_embeddings = model.encode(batch_chunks, show_progress_bar=True)
		batch_metadatas = all_metadata[i:end_i]
		batch_ids = all_ids[i:end_i]

		logging.info(f"Adding batch {i//batch_size + 1} with {len(batch_chunks)} documents to ChromaDB.")
		#5. add the batch to the collection
		collection.add(
		embeddings=batch_embeddings.tolist(),
		documents=batch_chunks,
		metadatas=batch_metadatas,
		ids=batch_ids
		)

	logging.info(f"Successfully vectorized and stored {len(all_chunks)} documents in collection '{COLLECTION_NAME}")
	logging.info(f"Vector database persisted at: {DB_DIR}")