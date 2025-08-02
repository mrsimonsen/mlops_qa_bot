# MLOps Q&A Bot

## Project Description

This project is a question-answering bot that specializes in MLOps tools. The bot is designed to answer questions about a variety of MLOps tools, including ZenML, MLflow, and Docker. The project is broken down into two main stages: first, building and containerizing the model locally, and second, creating an MLOps pipeline to automate the deployment of the model to a production environment on AWS.

## Project Goal

The primary goal of this project is to build a reliable and scalable question-answering bot that can be used to quickly find information about MLOps tools. This project will also serve as a practical example of how to build and deploy a machine learning model using modern MLOps practices.

## Project Plan

The project is divided into the following stages and phases:

### Stage 1: Model Development and Local Implementation

This stage focuses on creating and testing the core question-answering model on a local machine.

**Phase 1: Foundation & Data Engineering (Local)**

* **Task 1.1: Environment Setup**: Initialize a Git repository, set up a Python environment, and install Ollama for local LLM experimentation.
* **Task 1.2: Documentation Scraping**: Write and execute scripts to clone the official documentation repositories for the MLOps tools that the bot will be an expert on. These tools include ZenML, MLflow, Docker, and others. The script will then use `trafilatura` to extract and clean the text content from the documentation files (e.g., Markdown, reStructuredText).
* **Task 1.3: Data Processing and Chunking**: Clean the scraped text to remove irrelevant artifacts and then split it into smaller, more manageable chunks for processing.
* **Task 1.4: Vectorization and Storage**: Convert the text chunks into numerical embeddings and store them in a local ChromaDB instance to create a vector database.

**Phase 2: RAG Application Development (Local)**

* **Task 2.1: Core RAG Logic**: Develop the core Retrieval-Augmented Generation (RAG) logic, including the retriever that fetches relevant context from the vector database and the generator that creates answers.
* **Task 2.2: API Service with FastAPI**: Build a RESTful API with a `/query` endpoint using FastAPI to serve the model's answers.
* **Task 2.3: Containerize the Application**: Write a Dockerfile to package the FastAPI application into a container, ensuring that it can be deployed consistently across different environments.
* **Task 2.4: Unit & Integration Testing**: Use `pytest` to write and run tests that ensure the reliability and correctness of the application's components.

### Stage 2: MLOps Pipeline and Cloud Deployment

Once the model is working locally, this stage will focus on automating the data pipeline and deploying the application to a production environment on the cloud.

**Phase 3: MLOps Orchestration with Kubeflow (Local)**

* **Task 3.1: Local Kubernetes Setup**: Install and configure a local Kubernetes cluster using Docker Desktop or Minikube to simulate a production environment.
* **Task 3.2: ZenML Kubeflow Stack**: Install the ZenML Kubeflow integration and configure a new ZenML stack that uses the local Kubeflow instance as its orchestrator.
* **Task 3.3: ZenML Pipeline Execution**: Run the data ingestion pipeline on the Kubeflow stack, which will execute the pipeline's steps as pods within the local Kubernetes cluster.
* **Task 3.4: MLflow Integration**: Log pipeline parameters and evaluation metrics to MLflow to track experiments and monitor performance.

**Phase 4: Cloud Infrastructure as Code (IaC) with EKS**

* **Task 4.1: Terraform Scripts for AWS**: Write Terraform configuration files to define and provision the necessary cloud infrastructure on AWS, including:
    * An Amazon EKS (Elastic Kubernetes Service) cluster to serve as the production environment.
    * An ECR (Elastic Container Registry) to host the production Docker image.
    * An S3 bucket to store the production vector database and other artifacts.
    * IAM roles and security groups to ensure secure communication between the different services.
* **Task 4.2: Provision Infrastructure**: Run `terraform apply` to create the cloud resources defined in the scripts.

**Phase 5: Continuous Integration & Deployment (CI/CD) to EKS**

* **Task 5.1: GitHub Actions Workflow**: Create a CI/CD workflow using GitHub Actions by defining the necessary steps in a `.github/workflows/main.yml` file.
* **Task 5.2: CI - Automated Testing & Building**: Configure the workflow to:
    * Run the `pytest` suite automatically on every push to the main branch.
    * Build the Docker image and push it to the AWS ECR repository upon successful testing.
* **Task 5.3: CD - Automated Deployment to EKS**:
    * Store AWS credentials and EKS cluster details as secrets in GitHub to allow the workflow to access the cloud environment securely.
    * Use `kubectl` to apply a Kubernetes deployment manifest, which will instruct the EKS cluster to pull the new image from ECR and deploy it as a pod.

## Getting Started

### Prerequisites

* Python 3.8+
* Docker
* Git

### Installation

1.  Clone the repository:

```bash
git clone [https://github.com/your-username/your-repository.git](https://github.com/your-username/your-repository.git)
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn main:app --reload
```

## Tech Stack

* **Python**: The core programming language for the project.
* **FastAPI**: A modern, fast (high-performance), web framework for building APIs with Python 3.8+ based on standard Python type hints.
* **Docker**: A platform for developing, shipping, and running applications in containers.
* **ChromaDB**: An open-source embedding database for building AI applications.
* **ZenML**: An extensible, open-source MLOps framework for creating portable, production-ready MLOps pipelines.
* **MLflow**: An open-source platform for managing the end-to-end machine learning lifecycle.
* **Kubeflow**: A machine learning toolkit for Kubernetes.
* **AWS**: Amazon Web Services, a cloud computing platform.
* **Terraform**: An open-source infrastructure as code software tool.
* **GitHub Actions**: A CI/CD platform that allows you to automate your build, test, and deployment pipeline.
* **Pytest**: A testing framework for Python.
* **GitPython**: A Python library to interact with Git repositories.
* **Trafilatura**: A Python package for wep scraping and text extraction.