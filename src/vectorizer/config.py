from src.config import PROCESSED_DATA_DIR, DB_DIR

#a good, lightweight Sentence Transformer model for general purpose
# we'll use to create embeddings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
#name of the collection within chromadb
COLLECTION_NAME = "mlops_docs"