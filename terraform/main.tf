# ----------------------------------
# ECR (Elastic Container Repository)
# ----------------------------------
resource "aws_ecr_repository" "app_repo" {
	name = var.ecr_repository_name
	tags = {
		Project = var.project_name
	}
}
# ----------------------------------
# S3 (Simple Storage Service)
# ----------------------------------
resource "aws_s3_bucket" "artifacts" {
	bucket = var.s3_bucket_name
	tags = {
		Project = var.project_name
	}
}
# ----------------------------------
# IAM (Identity and Access Management) for EKS (Elastic Kubernetes Service)
# ----------------------------------
# EKS cluster role, assumed by EKS control plane.
resource "aws_iam_role" "eks_cluster_role" {
	name = "${var,eks_cluster_name}-cluster-role"

	assume_role_policy = jsonencode){
		Version = "2012-10-17",
		Statement = [
			{
				Effect = "Allow",
				Principal = {
					Service = "eks.amazonaws.com"
				},
				Action = "sts:AssumeRole"
			}
		]
	}
}

# attach the AmazonEKSClusterPolicy to the cluster role
resource "aws_iam_role_policy_attachment" "esk_cluster_policy" {
	policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
	role = aws_iam_role.eks_cluster_role.name
}

# EKS Node role assumed by the worker nodes
resource "aws_iam_role" "eks_node_role" {
	name = "${var.eks_cluster_name}-node-role"

	assume_role_policy = jsonencode({
		Version = "2012-10-17",
		Statement = [
			{
				Effect = "Allow",
				Principal = {
					Service = "ec2.amazonaws.com"
				},
				Action = "sts:AssumeRole"
			}
		]
	})
}

# Attach policies for worker node.
resource "aws_iam_role_policy_attachment", "eks_worker_node_policy" {
	policy_arn = "arn:aws:iam::aws:policy/AmazonEksWorkerNodePolicy"
	role = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
	policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
	role = aws_iam_role.eks_node_role.name
}

# ----------------------------------
# Networking (VPC)
# using default VPC and its subnets.
# For production, create a dedicated VPC.
# ----------------------------------
data "aws_vpc" "default" {
	default = true
}

data "aws_subnets" "default" {
	filter{
		name = "vpc-id"
		values = [data.aws_vpc.default.id]
	}
}

# ----------------------------------
# EKS (Elastic Kubernetes Service) cluster
# ----------------------------------
resource "aws_eks_cluster" "app_cluster" {
	name = var.eks_cluster_name
	role_arn = aws_iam_role.eks_cluster_role.arn

	vpc_config {
		subnet_ids = data.aws_subnets.default.ids
	}

	# ensure IAM role is created before the cluster.
	depends_on = [
		aws_iam_role_policy_attachment.esk_cluster_policy,
	]

	tags ={
		Project = var.project_name
	}
}

resource "aws_eks_node_group" "app_node_group" {
	cluster_name = aws_eks_cluster.app_cluster.name
	node_group_name = "${var.project_name}-node-group"
	node_role_arn = aws_iam_role.eks_node_role.arn
	subnet_ids = data.aws_subnets.default.ids

	#specify instance type and scaling configuration for worker nodes.
	instance_types = ["t3.medium"]
	scaling_config {
		desired_size = 2
		max_size = 3
		min_size = 1
	}

	#ensure the cluster and all node role policies are created first.
	depends_on = [
		aws_iam_role_policy_attachment.eks_worker_node_policy,
		aws_iam_role_policy_attachment.eks_cni_policy,
		aws_iam_role_policy_attachment.ecr_read_only_policy,
	]

	tags = {
		Project = var.project_name
	}
}