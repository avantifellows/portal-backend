resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/portal-backend-${var.environment}"
  retention_in_days = 30
}
