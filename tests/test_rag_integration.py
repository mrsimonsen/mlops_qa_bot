import os
import pytest
import shutil
from pathlib import Path
import chromadb
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
import subprocess
import time
import requests

from src.rag_app.prompts import QA_PROMPT_TEMPLATE

TEST_DB_DIR = Path("./test_chroma_db")
TEST_COLLECTION_NAME = "test_mlops_docs"
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
OLLAMA_TEST_URL = "http://localhost:11434"
OLLAMA_CONTAINER_NAME = "ollama-test-server"

@pytest.fixture(scope="module")
def ollama_service():
	"""
	A fixture to start and stop a local Ollama Docker container for the tests.
	"""
	#1. ---Start Ollama container---
	print(f"\nStarting Ollama container '{OLLAMA_CONTAINER_NAME}' ...")
	subprocess.run(
		[
			"docker", "run", "-d", "--rm",
			"-p", "11434:11434",
			"--name", OLLAMA_CONTAINER_NAME,
			"ollama/ollama"
		],
		check=True,
		capture_output=True
	)

	#2. ---Wait for Ollama service to be ready---
	retries = 15
	delay = 2
	for i in range(retries):
		try:
			response = requests.get(OLLAMA_TEST_URL)
			if response.status_code == 200:
				print("Ollama service is ready.")
				break
		except requests.ConnectionError:
			print(f"Waiting for Ollama service... (attempt {i+1}/{retries})")
			time.sleep(delay)
	else:# if loop ends without breaking
		pytest.fail("Ollama service did not become ready in time.")
	
	#3. ---Pull model into container---
	print("Pulling 'llama3' model into the Ollama container...")
	subprocess.run(
		["docker", "exec", OLLAMA_CONTAINER_NAME, "ollama", "pull", "llama3"],
		check=True,
		capture_output=True
	)
	print("'llama3' model pulled successfully.")

	#4. ---Yield control to the tests---
	yield OLLAMA_TEST_URL

	#5. ---Teardown---
	print(f"\nStopping Ollama container '{OLLAMA_CONTAINER_NAME}' ...")
	subprocess.run(["docker", "stop", OLLAMA_CONTAINER_NAME], check=True, capture_output=True)
	print("Ollama container stopped")

@pytest.fixture(scope="module")
def rag_qa_chain(ollama_service):
	"""
	A pytest fixture to setup a complete, isolated RAG pipeline for testing.
	'scope="module"' ensures this setup runs only once for all tests in this file.
	"""
	#1. ---Create temporary, isolated vector database---
	if TEST_DB_DIR.exists():
		#clean any previous not finished test runs
		shutil.rmtree(TEST_DB_DIR)
	
	#create a persistent client at the for the temporary db
	test_client = chromadb.PersistentClient(path=str(TEST_DB_DIR))
	#create test collection
	test_collection = test_client.get_or_create_collection(name=TEST_COLLECTION_NAME)

	#2. ---Add a small, known set of documents to the test database---
	known_documents = [
		"ZenML is an extensible, open-source MLOps framework for creating portable, production-ready MLOps pipelines.",
		"MLflow is an open source platform to manage the ML lifecycle, including experimentation, reproducibility, deployment, and a central model registry.",
		"To install Docker, you must first download the Docker Desktop installer from the official Docker website."
	]
	test_collection.add(
		documents=known_documents,
		ids=["doc1", "doc2", "doc3"]
	)

	#3. ---Initialize the components of a real RAG chain---
	embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
	
	#create langchain vector store from test db
	vector_store = Chroma(
		client=test_client,
		collection_name=TEST_COLLECTION_NAME,
		embedding_function=embedding_function
	)

	#create retriever from the test vector store
	retriever = vector_store.as_retriever(search_kwargs={'k':1})#only grab one doc for tests

	#init the llm using ollama_service fixture
	llm = OllamaLLM(model='llama3', base_url=ollama_service)

	#use the imported prompt template
	QA_CHAIN_PROMPT = PromptTemplate.from_template(QA_PROMPT_TEMPLATE)

	#4. ---Create the final RetrievalQA chain---
	qa_chain = RetrievalQA.from_chain_type(
		llm,
		retriever=retriever,
		chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
	)

	#5. ---Yield the chain to the test function---
	yield qa_chain

	#6. ---Teardown---
	shutil.rmtree(TEST_DB_DIR)


def test_rag_pipeline_with_known_document(rag_qa_chain):
	"""
	Integration test that uses the fully assembled RAG chain form the fixture to
	ask a question and validate the answer.
	"""
	question = "What is ZenML?"

	result = rag_qa_chain.invoke({"query": question})
	answer = result.get("result", "").lower()

	#Assert
	assert answer
	assert "zenml" in answer
	assert "mlops" in answer
	assert "framework" in answer