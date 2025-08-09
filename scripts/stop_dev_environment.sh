#!/bin/bash

echo "--- Stopping development containers ---"
docker stop qa-bot-app ollama >/dev/null 2>&1 || true
echo "--- Deleting Kubernetes resources ---"
kubectl delete deployment qa-bot-app
kubectl delete service qa-bot-service
echo "--- Stopping ZenML server ---"
zenml logout --local
echo "--- Stopping Kubernetes cluster ---"
minikube stop
minikube delete
echo -e "\n--- Project has terminated cleanly. ---"