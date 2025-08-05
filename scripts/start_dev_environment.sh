#!/bin/bash

echo "--- Checking Minikube status ---"
if ! minikube status | grep -q "Running"; then
	echo "Minikube not running. Starting it now..."
	minikube start
fi

echo -e "\n--- Starting local MinIO instance for artifact storage ---"
kubectl apply -f k8s/minio-deployment.yaml

echo -e "\n--- Starting Ollama server container ---"
if ! docker ps --filter "name=ollama" --filter "status=running" | grep -q "ollama"; then
	echo "Ollama container not running. Starting it now in detached mode ..."
	docker rm ollama >/dev/null 2>&1 || true
	docker run -d \
		-v ollama:/root/.ollama \
		-p 11434:11434 \
		--name ollama \
		ollama/ollama
else
	echo "Ollama container is already running."
fi

echo -e"\n--- Starting ZenML server ---"
if ! zenml status | grep -q "ZenML Server is running"; then
	echo "ZenML server not running. Starting it now..."
	zenml login --local
else
	echo "ZenML server is already running."
fi

echo -e "\n--- Building the FastAPI Docker image ---"
docker build -t mlops_qa_bot .

echo -e "\n--- Running FastAPI application container ---"
echo "Ensuring no old 'qa-bot-app' container exists..."
docker rm -f qa-bot-app >/dev/null 2>&1 || true
echo "Starting new 'qa-bot-app' container..."
docker run -d --rm \
	-p 8000:8000 \
	--name qa-bot-app \
	mlops_qa_bot

echo -e "\n--- Development environment setup is complete. ---"
echo "Your Q&A bot is now running at http://localhost:8000"