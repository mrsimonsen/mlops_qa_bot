#!/bin/bash

echo -e "\n--- Checking Minikube status ---"
if ! minikube status | grep -q "Running"; then
	echo "Starting Minikube..."
	minikube start
else
 echo "Minikube is already running."
fi

echo -e "\n---Starting local MinIO instance for artifact storage ---"
kubectl apply -f k8s/minio-deployment.yaml


echo "--- Setting and verifying Minikube Docker environment ---"
eval $(minikube -p minikube docker-env)

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

echo -e "\n--- Starting ZenML server ---"
if ! zenml status | grep -q "ZenML Server is running"; then
	echo "ZenML server not running. Starting it now..."
	zenml login --local
else
	echo "ZenML server is already running."
fi

echo -e "\n--- Building the FastAPI Docker image ---"
docker build -t mlops_qa_bot .

echo -e "\n--- Deploying FastAPI application to Kubernetes ---"
kubectl apply -f k8s/qa-bot-deployment.yaml

echo -e "\n--- Forwarding service port to localhost ---"
echo "You can now access your application at the URL printed below."
minikube service qa-bot-service