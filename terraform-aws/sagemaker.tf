terraform {
  backend "s3" {
    bucket = "mlops-samba-artifacts"
    key    = "terraform/sagemaker.tfstate"
    region = "ca-central-1"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

variable "region" {
  default = "ca-central-1"
}

variable "account_id" {
  default = "961743401926"
}

provider "aws" {
  region = var.region
}

# ── Utiliser le rôle existant ──────────────
data "aws_iam_role" "sagemaker_role" {
  name = "mlops-sagemaker-role"
}

# ── SageMaker Model ────────────────────────
resource "aws_sagemaker_model" "iris_model" {
  name               = "iris-model"
  execution_role_arn = data.aws_iam_role.sagemaker_role.arn

  primary_container {
    image = "${var.account_id}.dkr.ecr.${var.region}.amazonaws.com/iris-model:latest"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ── Endpoint Configuration ─────────────────
resource "aws_sagemaker_endpoint_configuration" "iris_config" {
  name = "iris-model-config"

  production_variants {
    variant_name           = "primary"
    model_name             = aws_sagemaker_model.iris_model.name
    initial_instance_count = 1
    instance_type          = "ml.t2.medium"
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Project = "mlops-project"
    Owner   = "sambasy"
  }
}

# ── Endpoint ───────────────────────────────
resource "aws_sagemaker_endpoint" "iris_endpoint" {
  name                 = "iris-model-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.iris_config.name

  tags = {
    Project = "mlops-project"
    Owner   = "sambasy"
  }
}

# ── Outputs ────────────────────────────────
output "endpoint_name" {
  value = aws_sagemaker_endpoint.iris_endpoint.name
}

output "endpoint_arn" {
  value = aws_sagemaker_endpoint.iris_endpoint.arn
}
