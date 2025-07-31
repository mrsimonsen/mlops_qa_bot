# MLOps Stack Q&A Bot

This project is a comprehensive Question-Answering bot that uses a Retrieval-Augmented Generation (RAG) architecture to answer questions about MLOps tools. It leverages a modern MLOps stack, including ZenML for pipeline orchestration, Kubeflow for Kubernetes-native execution, and FastAPI for API delivery.

The entire workflow, from data ingestion to cloud deployment, is automated, showcasing a production-grade approach to building and managing LLM applications.

## Core Technology Stack

- **Application Framework**: Python, FastAPI
- **LLM Engine**: Ollama (for local development and experimentation)
- **Vector Database**: ChromaDB
- **Pipeline Orchestration**: ZenML
- **Orchestrator**: **Kubeflow** (on local K8s & AWS EKS)
- **Experiment Tracking**: MLflow
- **Containerization**: Docker
- **Cloud Provider**: AWS (Amazon Web Services)
- **Infrastructure as Code**: Terraform
- **Deployment Target**: **Amazon EKS (Elastic Kubernetes Service)**
- **CI/CD**: GitHub Actions

## Architecture Overview

The project follows a standard MLOps workflow, orchestrated by ZenML and Kubeflow.

```
+-------------------+      +----------------------+      +------------------+
|   Documentation   |----->|  Data Ingestion      |----->|  Vector Database |
| (ZenML, MLflow)   |      |  (ZenML Pipeline)    |      |  (ChromaDB)      |
+-------------------+      +----------------------+      +------------------+
        ^                           |                            |
        |                           | (Run on Kubeflow)          | (Retrieved Context)
        |                           |                            v
+-------------------+      +----------------------+      +------------------+
|   User via API    |<---->|  FastAPI Application |----->|  RAG Engine      |
|  (FastAPI)        |      |  (Docker Container)  |      |  (Ollama)        |
+-------------------+      +----------------------+      +------------------+
```

## Project Phases

This project is structured into several distinct phases:

1.  **Foundation & Data Engineering**: Scraping documentation, processing it, and creating a vector store.
2.  **RAG Application Development**: Building the core FastAPI application that serves answers.
3.  **MLOps Orchestration with Kubeflow**: Defining and running the data pipeline on a local Kubernetes cluster.
4.  **Cloud Infrastructure as Code**: Using Terraform to provision the necessary AWS resources (EKS, ECR, S3).
5.  **CI/CD to EKS**: Automating the build, test, and deployment process with GitHub Actions.

## Local Setup and Installation

### Prerequisites

-   Python 3.9+
-   Docker Desktop (with Kubernetes enabled) or Minikube
-   Terraform
-   An AWS account with credentials configured locally

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install and initialize ZenML:**
    ```bash
    zenml init
    ```

5.  **Set up a local Kubernetes cluster:**
    -   **Using Docker Desktop**: Go to `Settings > Kubernetes` and check `Enable Kubernetes`.
    -   **Using Minikube**: Follow the official Minikube installation guide.

6.  **Install the ZenML Kubeflow Integration:**
    ```bash
    zenml integration install kubeflow -y
    ```

7.  **Register a Kubeflow Stack:**
    Create a ZenML stack that points to your local Kubernetes cluster.
    ```bash
    zenml orchestrator register kubeflow_orchestrator --flavor=kubeflow
    zenml stack register kubeflow_stack -o kubeflow_orchestrator -a default
    zenml stack set kubeflow_stack
    ```

## Running the Pipeline

The core data ingestion process is managed by a ZenML pipeline.

1.  **Populate the URL list:**
    Add the documentation URLs you want to scrape into the `urls_to_scrape.txt` file.

2.  **Run the ZenML pipeline:**
    This command will execute the pipeline using your active ZenML stack (which should be the Kubeflow stack).
    ```bash
    python run_pipeline.py
    ```
    ZenML will translate this pipeline into a Kubeflow workflow, which will run as pods in your local Kubernetes cluster.

3.  **Launch the API:**
    Once the pipeline has successfully populated the vector database, you can run the FastAPI application.
    ```bash
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    You can now send queries to `http://localhost:8000/query`.

## Cloud Deployment (CI/CD)

This project is designed for automated deployment to AWS EKS using Terraform and GitHub Actions.

1.  **Infrastructure as Code**: The Terraform scripts in the `/terraform` directory define the cloud infrastructure, including the EKS cluster, ECR registry, and S3 bucket for artifacts.

2.  **GitHub Actions Workflow**: The `.github/workflows/main.yml` file defines the CI/CD pipeline:
    -   **CI**: On every push to `main`, the workflow installs dependencies, runs `pytest`, and builds a new Docker image.
    -   **CD**: If the CI steps pass, the Docker image is pushed to AWS ECR. A Kubernetes deployment manifest is then applied to the EKS cluster, which triggers a rolling update to the new application version.