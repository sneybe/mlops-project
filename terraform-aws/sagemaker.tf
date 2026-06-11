# ── Variables ──────────────────────────────
variable "region" {
  default = "ca-central-1"
}

variable "account_id" {
  default = "961743401926"
}

# ── Provider ───────────────────────────────
provider "aws" {
  region = var.region
}

# ── IAM Role existant (ne pas recréer) ─────
resource "aws_iam_role" "sagemaker_role" {
  name = "mlops-sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "sagemaker.amazonaws.com"
      }
    }]
  })

  lifecycle {
    ignore_changes  = all
    prevent_destroy = false
  }
}

resource "aws_iam_role_policy_attachment" "sagemaker_policy" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"

  lifecycle {
    ignore_changes = all
  }
}

resource "aws_iam_role_policy_attachment" "s3_policy" {
  role       = aws_iam_role.sagemaker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"

  lifecycle {
    ignore_changes = all
  }
}

# ── SageMaker Model ────────────────────────
resource "aws_sagemaker_model" "iris_model" {
  name               = "iris-model-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  execution_role_arn = aws_iam_role.sagemaker_role.arn

  primary_container {
    image = "${var.account_id}.dkr.ecr.${var.region}.amazonaws.com/iris-model:latest"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ── Endpoint Configuration ─────────────────
resource "aws_sagemaker_endpoint_configuration" "iris_config" {
  name = "iris-model-config-${formatdate("YYYYMMDDhhmmss", timestamp())}"

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

  lifecycle {
    create_before_destroy = true
  }

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
