# All app values live in one JSON secret, one key per env var (see README "Secrets").
# Terraform creates only the empty secret; the value is set with the CLI, so it never
# appears in state or plans.
resource "aws_secretsmanager_secret" "app" {
  name                    = "portal-backend/${var.environment}/app"
  description             = "portal-backend ${var.environment} app settings (JSON, one key per env var)"
  recovery_window_in_days = 7

  lifecycle {
    prevent_destroy = true
  }
}

locals {
  secret_keys = [
    "JWT_SECRET_KEY",
    "DB_SERVICE_URL",
    "DB_SERVICE_TOKEN",
    "SQS_ACCESS_KEY",
    "SQS_SECRET_ACCESS_KEY",
    "AWS_SQS_URL",
    "OTP_SERVICE_URL",
    "SASHAKT_API_URL",
    "SASHAKT_WEBAPP_URL",
    "SASHAKT_ADMIN_EMAIL",
    "SASHAKT_ADMIN_PASSWORD",
  ]
}
