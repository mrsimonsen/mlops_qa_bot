import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from config import DB_DIR
from vectorizer.config import COLLECTION_NAME, EMBEDDING_MODEL_NAME

# --- Configuration & Setup ---
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Pydantic Models for API ---
class QueryRequest(BaseModel):
	question: str

class QueryResponse(BaseModel):
	answer: str
	source_documents: list

# --- FastAPI Application ---
app = FastAPI()

# --- Add CORS middleware ---
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"https://mrsimonsen.net",
		"http://mrsimonsen.net",
		"https://www.mrsimonsen.net",
		"http://www.mrsimonsen.net"
	],
	allow_methods=["GET", "POST"],
	allow_headers=["Content-Type"]
	
)

# --- RAG Components ---
try:
	# initialize db client and get collection
	logging.info(f"Connecting to vector database as: {DB_DIR}")
	client = chromadb.PersistentClient(path=str(DB_DIR))

	# initialize the embedding function
	logging.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
	embedding_function = SentenceTransformer(EMBEDDING_MODEL_NAME)

	# create a LanChain vector store
	vector_store = Chroma(
		client=client,
		collection_name = COLLECTION_NAME,
		embedding_function=embedding_function # type: ignore
	)

	# create retriever from vector store
	retriever = vector_store.as_retriever(search_kwargs={'k':5})

	# initialize the llm
	logging.info("Initializing the Ollama LLM")
	llm = OllamaLLM(model='llama3')

	#define the prompt template
	prompt_template = """
	Use the following pieces of context to answer the question at the end.
	If you don't know the answer, just say that you don't know, don't try to make up an answer.

	Context:
	{context}

	Question: {question}

	Helpful Answer:
	"""
	QA_CHAIN_PROMPT = PromptTemplate(
		input_variables=["context", "question"],
		template=prompt_template
	)

	# create the RetrievalQA chain
	qa_chain = RetrievalQA.from_chain_type(
		llm,
		retriever=retriever,
		chain_type_kwargs={'prompt': QA_CHAIN_PROMPT},
		return_source_documents=True
	)
	logging.info("RAG pipeline initialized successfully.")

except Exception as e:
	logging.error(f"Failed to initialize the RAG pipeline: {e}")
	qa_chain = None

# --- API Endpoints ---
@app.post("/query", response_model=QueryResponse)
def query_endpoint(query_request: QueryRequest):
	"""
	Receives a question, processes it through the RAG pipeline, and returns the answer.
	"""
	if not qa_chain:
		raise HTTPException(status_code=500, detail="RAG pipeline is not available.")
	
	try:
		logging.info(f"Received query: {query_request.question}")
		result = qa_chain({"query": query_request.question})

		return{
			"answer": result['result'],
			"source_documents": [doc.metadata.get('source', 'unknown') for doc in result['source_documents']]
		}
	except Exception as e:
		logging.error(f"Error processing query: {e}", exc_info=True)
		raise HTTPException(status_code=500, detail="Failed to process the query.")
	
@app.get("/")
def read_root():
	return {"message": "MLOps Q&A Bot is running!"}