from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

from rag_app.main import app
client = TestClient(app)

def test_read_root():
	"""
	Test the root endpoint to ensure the service is running.
	"""
	response = client.get('/')
	assert response.status_code == 200
	assert response.json() == {"message": "MLOps Q&A Bot is running!"}

@patch('rag_app.main.qa_chain')
def test_query_endpoint_success(mock_qa_chain):
	"""
	Test the /query endpoint for a successful response.
	It mocks the qa_chain to avoid calling the actual LLM.
	"""
	# configure the mock object
	mock_result = {
		"result": "ZenML is a pipeline tool.",
		"source_documents": [
			type('obj', (object,), {'metadata': {'source': 'doc1.html'}})()
		]
	}
	mock_qa_chain.return_value = mock_result

	# make api request 
	question = 'What is ZenML?'
	response = client.post("/query", json={'question': question})

	# assert results
	assert response.status_code == 200
	response_data = response.json()
	assert response_data['answer'] == mock_result['result']
	assert response_data['source_documents'] == ['doc1.html']

	# verify the mock was called correctly
	mock_qa_chain.assert_called_once_with({'query': question})

@patch('rag_app.main.qa_chain', None)
def test_query_endpoint_chain_unavailable():
	"""
	Tests the /query endpoint for the case where the RAG chain fails to initialize.
	"""
	# make api request
	response = client.post('/query', json={'question': "This should fail."})

	# assert results
	assert response.status_code == 500
	assert response.json() == {'detail': "RAG pipeline is not available."}