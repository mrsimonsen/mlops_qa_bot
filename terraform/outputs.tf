# ----------------------------------
# EKS Cluster Outputs
# ----------------------------------
output "eks_cluster_name" {
	description = "The name of the Amazon EKS cluster."
	value = aws_eks_cluster.app_cluster.name
}

# ----------------------------------
# ECR Repository Outputs
# ----------------------------------
output "ecr_repository_url" {
	description = "The URL of the ECR repository to which Docker images will be pushed."
	value = aws_ecr_repository.app_repo.repository_url
}

# ----------------------------------
# S3 Bucket Outputs
# ----------------------------------
output "s3_buk3t_id" {
	description = "The ID (name) of the S3 bucket."
	value = aws_s3_bucket.artifacts.id
}
