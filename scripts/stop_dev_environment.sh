#!/bin/bash

echo "--- Deleting Kubernetes resources ---"
kubectl delete deployment qa-bot-app
kubectl delete service qa-bot-service
kubectl delete deployment ollama
kubectl delete service ollama-service
echo "--- Stopping Kubernetes cluster ---"
minikube stop
# minikube delete - fresh start in case of corruption
echo -e "\n--- Project has terminated cleanly. ---"