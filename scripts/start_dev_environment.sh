#!/bin/bash

echo "--- Checking Minikube status ---"
if ! minikube status | grep -q "Running"; then
	echo "Minikube not running. Starting it now..."
	minikube start
fi

echo -e "\n--- Starting local MinIO instance for artifact storage ---"
kubectl apply -f k8s/minio-deployment.yaml

echo -e "\n--- Building the FastAPI Docker image ---"
docker build -t mlops_qa_bot .

echo -e "\n--- Development environment setup is complete. ---"