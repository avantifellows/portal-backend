# Separate from the AWS root: pointing the hostname at the ALB is the cutover step.
#   terraform init -backend-config="key=portal-backend/dns-staging/terraform.tfstate"
terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    bucket  = "111766607077-dbservice-test-terraform-state"
    region  = "ap-south-1"
    encrypt = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

variable "cloudflare_zone_id" {
  type = string
}

variable "name" {
  type        = string
  description = "Record name, e.g. staging-portal-backend"
}

variable "alb_name" {
  type    = string
  default = "af-load-balancer"
}

variable "proxied" {
  type    = bool
  default = false
}

data "aws_lb" "shared" {
  name = var.alb_name
}

resource "cloudflare_record" "this" {
  zone_id = var.cloudflare_zone_id
  name    = var.name
  type    = "CNAME"
  content = data.aws_lb.shared.dns_name
  proxied = var.proxied
  ttl     = 1
}
