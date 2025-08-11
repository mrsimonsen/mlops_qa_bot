# MLOps Q&A Bot

## Project Description

This project is a question-answering bot that specializes in MLOps tools. The bot is designed to answer questions about a variety of MLOps tools by using a Retrieval-Augmented Generation (RAG) approach with a local Large Language Model (LLM).

The project is broken down into two main stages. The first stage focuses on building and containerizing the model locally. The second stage focuses on creating the configuration and workflows for cloud deployment without actually deploying the resources, resulting in a "deployment-ready" application and a complete blueprint for automation.

## Project Goal

The primary goal of this project is to build a reliable and containerized question-answering bot. This project serves as a practical example of how to develop a modern machine learning application and prepare it for deployment using Infrastructure as Code (IaC) and CI/CD planning.

## Project Plan

The project is divided into the following stages and phases:

### Stage 1: Model Development and Final Containerization

*This stage focuses on the hands-on development of the application, from data ingestion to creating a shareable, containerized final product.*

**Phase 1: Foundation & Data Engineering (Local)**
- **Task 1.1: Environment Setup**: Initialize a Git repository, set up a Python environment, and install Ollama for local LLM experimentation.
- **Task 1.2: Documentation Scraping**: Write and execute scripts to clone the official documentation repositories for the MLOps tools that the bot will be an expert on.
- **Task 1.3: Data Processing and Chunking**: Clean the scraped text to remove irrelevant artifacts and then split it into smaller, more manageable chunks for processing.
- **Task 1.4: Vectorization and Storage**: Convert the text chunks into numerical embeddings and store them in a local ChromaDB instance to create a vector database.

**Phase 2: RAG Application Development & Packaging**
- **Task 2.1: Core RAG Logic**: Develop the core Retrieval-Augmented Generation (RAG) logic, including the retriever that fetches relevant context from the vector database and the generator that creates answers.
- **Task 2.2: API Service with FastAPI**: Build a RESTful API with a `/query` endpoint using FastAPI to serve the model's answers.
- **Task 2.3: Containerize the Application**: Write a Dockerfile to package the FastAPI application into a container, ensuring that it can be deployed consistently across different environments.
- **Task 2.4: Unit & Integration Testing**: Use `pytest` to write and run tests that ensure the reliability and correctness of the application's components.
- **Task 2.5: Push Container to Docker Hub**: Create a public repository on Docker Hub and push the container image, making the application easily shareable and verifiable.
- **Task 2.6: Simple Web Interface**:
    - **Backend CORS Configuration**: Update the FastAPI application to include CORS (Cross-Origin Resource Sharing) middleware.
    - **Frontend Integration**: Add an HTML and JavaScript-based user interface to an existing webpage (mrsimonsen.net) to send queries to the backend API and display results.

### Stage 2: Deployment and Automation Planning

*This stage focuses on creating the configuration and workflows for cloud deployment without actually provisioning costly resources. The output is a complete, documented blueprint for automation.*

**Phase 3: Infrastructure and Automation Definition**
- **Task 3.1: Infrastructure as Code Definition with Terraform**:
    - Write Terraform configuration files (`.tf`) to define the AWS infrastructure needed for deployment (EKS cluster, ECR repository, S3 bucket, IAM roles).
    - Validate the configuration by running `terraform init` and `terraform plan` to review the execution plan.
    - **Note**: `terraform apply` will not be run to avoid incurring costs.

- **Task 3.2: CI/CD Workflow Creation with GitHub Actions**:
    - Create a complete CI/CD workflow file at `.github/workflows/main.yml`.
    - **Implement the CI Portion**: Configure the workflow to trigger on pushes to the `main` branch to automatically run the `pytest` suite and build the Docker image.
    - **Define (but comment out) the CD Portion**: Write the deployment steps within the workflow file as a template for future deployment, including pushing the image to a container registry and applying a Kubernetes manifest.

## Tech Stack

### Core Technologies

This project is built using the following core technologies:

* **Python**: The core programming language for the project.
* **FastAPI**: A modern, high-performance web framework for building APIs.
* **Docker**: A platform for developing, shipping, and running applications in containers.
* **ChromaDB**: An open-source embedding database for building AI applications.
* **LangChain**: A framework for developing applications powered by language models.
* **Ollama**: A tool for running large language models locally.
* **DVC**: A tool for data versioning.
* **Terraform**: An open-source infrastructure as code software tool.
* **GitHub Actions**: A CI/CD platform for automating build, test, and deployment pipelines.
* **Pytest**: A testing framework for Python.

### Knowledge Base

The bot's knowledge is derived from the official documentation of the following MLOps and cloud-native technologies:

* AWS (Boto3)
* ChromaDB
* DVC
* Docker
* FastAPI
* Git
* GitHub Actions
* Kubeflow
* Kubernetes
* LangChain
* LangSmith
* MLflow
* Ollama
* Terraform
* ZenML

## Getting Started

### Prerequisites

- Python 3.8+
- Docker
- Git

### Installation

1.  Clone the repository:
    ```bash
    git clone [https://github.com/mrsimonsen/mlops_qa_bot.git](https://github.com/mrsimonsen/mlops_qa_bot.git)
    ```
2.  Navigate to the project directory:
    ```bash
    cd mlops_qa_bot
    ```
3.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the application:
    ```bash
    uvicorn src.main:app --reload
    ```