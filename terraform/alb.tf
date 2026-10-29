resource "aws_lb_target_group" "this" {
  name_prefix = "pbe-"
  port        = var.app_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    path                = "/health"
    matcher             = "200"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 5
  }

  deregistration_delay = 30

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb_listener_rule" "this" {
  listener_arn = var.alb_https_listener_arn
  priority     = var.listener_rule_priority

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }

  condition {
    host_header {
      values = [var.domain]
    }
  }
}
