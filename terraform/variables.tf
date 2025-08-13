variable "aws_region" {
	description = "The AWS region to deploy resources in. Set to us west as it is the closest to denver"
	type = string
	default = "us-west-2"
}

variable "project_name" {
	description = "The name of the project, used for tagging and naming resources"
	type = string
	default = "mlops-qa-bot"
}

variable "ecr_repository_name" {
	#development container stored on GHCR
	#best practice to use AWS for production due to performance and IAM integration.
	description = "The name for the Elastic Container Registry (ECR) repository."
	type = string
	default = "mlops-qa-bot-repository"
}

variable "eks_cluster_name" {
	description = "THe n ame for the Elastic Kubernetes Service (EKS) cluster."
	type = string
	default = "mlops-qa-bot-cluster"
}

variable "s3_bucket_name" {
	description = "The globally unique name for the S3 bucket."
	type = string
	default = "mlops-qa-bot-bucket-mirsimonsen"
}