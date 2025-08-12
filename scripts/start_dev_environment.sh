#!/bin/bash

echo -e "\n--- Checking Minikube status ---"
if ! minikube status | grep -q "Running"; then
	echo "Starting Minikube with 8GB of memory..."
	minikube start --memory 8192
else
 echo "Minikube is already running."
fi

echo -e "\n--- Waiting for Kubernetes default service account to be ready ---"
until kubectl get sa default &> /dev/null; do
	echo "Default service account not found yet. Waiting..."
	sleep 2
done
echo "Default service account is ready."

echo "--- Setting and verifying Minikube Docker environment ---"
eval $(minikube -p minikube docker-env)

echo -e "\n--- Building the custom Ollama Docker image ---"
docker build -t ollama-custom -f ollama.Dockerfile .

echo -e "\n--- Starting Ollama server ---"
kubectl apply -f k8s/ollama-deployment.yaml

echo -e "\n--- Building the FastAPI Docker image ---"
docker build -t mlops_qa_bot .

echo -e "\n--- Deploying FastAPI application to Kubernetes ---"
kubectl apply -f k8s/qa-bot-deployment.yaml

echo -e "\n--- Forwarding service port to localhost ---"
echo "Waiting for ollama-service"
kubectl wait --for=condition=ready pod -l app=qa-bot-app --timeout=120s
echo "You can now access your application at the URL printed below."
minikube service qa-bot-service --url &