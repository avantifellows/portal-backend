data "aws_lb" "shared" {
  name = var.alb_name
}

resource "aws_security_group" "tasks" {
  name        = "portal-backend-${var.environment}-sg"
  description = "Inbound from the shared ALB on the app port; egress all (db-service, SQS, OTP, ECR)."
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group_rule" "tasks_ingress_from_alb" {
  for_each = toset(data.aws_lb.shared.security_groups)

  type                     = "ingress"
  from_port                = var.app_port
  to_port                  = var.app_port
  protocol                 = "tcp"
  source_security_group_id = each.value
  security_group_id        = aws_security_group.tasks.id
  description              = "ALB to ECS task on app port"
}
