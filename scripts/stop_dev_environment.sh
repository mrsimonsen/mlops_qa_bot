#!/bin/bash

echo "--- Stopping development containers ---"
docker stop qa-bot-app ollama
echo "--- Stopping ZenML server ---"
zenml logout --local
echo "--- Stopping Kubernetes cluster ---"
minikube stop
echo -e "\n--- Project has terminated cleanly. ---"