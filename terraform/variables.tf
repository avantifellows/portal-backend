variable "environment" {
  type = string
}

variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "domain" {
  type        = string
  description = "Hostname the ALB routes to this service."
}

variable "listener_rule_priority" {
  type = number
}

variable "vpc_id" {
  type    = string
  default = "vpc-0a48a661"
}

variable "subnet_ids" {
  type    = list(string)
  default = ["subnet-84ffe8ec", "subnet-434c080f", "subnet-5cd65827"]
}

variable "alb_name" {
  type    = string
  default = "af-load-balancer"
}

variable "alb_https_listener_arn" {
  type    = string
  default = "arn:aws:elasticloadbalancing:ap-south-1:111766607077:listener/app/af-load-balancer/8c412f577b269ab0/5b6cfc3f4677e5c4"
}

variable "app_port" {
  type    = number
  default = 8000
}

variable "cpu" {
  type    = number
  default = 1024
}

variable "memory" {
  type    = number
  default = 2048
}

variable "web_concurrency" {
  type    = string
  default = "4"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "desired_count" {
  type    = number
  default = 2
}

variable "min_capacity" {
  type    = number
  default = 2
}

variable "max_capacity" {
  type    = number
  default = 10
}

variable "cpu_target" {
  type    = number
  default = 50
}

# Secrets come in as TF_VAR_<name> (lowercase); see README.md for where each value comes from.

variable "jwt_secret_key" {
  type      = string
  sensitive = true
}

variable "db_service_url" {
  type      = string
  sensitive = true
}

variable "db_service_token" {
  type      = string
  sensitive = true
}

variable "sqs_access_key" {
  type      = string
  sensitive = true
}

variable "sqs_secret_access_key" {
  type      = string
  sensitive = true
}

variable "aws_sqs_url" {
  type      = string
  sensitive = true
}

variable "otp_service_url" {
  type      = string
  sensitive = true
}

variable "sashakt_api_url" {
  type      = string
  sensitive = true
}

variable "sashakt_webapp_url" {
  type      = string
  sensitive = true
}

variable "sashakt_admin_email" {
  type      = string
  sensitive = true
}

variable "sashakt_admin_password" {
  type      = string
  sensitive = true
}
