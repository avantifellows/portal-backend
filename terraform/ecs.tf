locals {
  image = "${aws_ecr_repository.this.repository_url}:${var.image_tag}"
}

resource "aws_ecs_cluster" "this" {
  name = "portal-backend-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "this" {
  family                   = "portal-backend-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.task_execution.arn

  container_definitions = jsonencode([
    {
      name         = "portal-backend"
      image        = local.image
      essential    = true
      portMappings = [{ containerPort = var.app_port, protocol = "tcp" }]

      environment = [
        { name = "WEB_CONCURRENCY", value = var.web_concurrency },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "JWT_SECRET_KEY", value = var.jwt_secret_key },
        { name = "DB_SERVICE_URL", value = var.db_service_url },
        { name = "DB_SERVICE_TOKEN", value = var.db_service_token },
        { name = "SQS_ACCESS_KEY", value = var.sqs_access_key },
        { name = "SQS_SECRET_ACCESS_KEY", value = var.sqs_secret_access_key },
        { name = "AWS_SQS_URL", value = var.aws_sqs_url },
        { name = "OTP_SERVICE_URL", value = var.otp_service_url },
        { name = "SASHAKT_API_URL", value = var.sashakt_api_url },
        { name = "SASHAKT_WEBAPP_URL", value = var.sashakt_webapp_url },
        { name = "SASHAKT_ADMIN_EMAIL", value = var.sashakt_admin_email },
        { name = "SASHAKT_ADMIN_PASSWORD", value = var.sashakt_admin_password },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:${var.app_port}/health')\""]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
    }
  ])
}

resource "aws_ecs_service" "this" {
  name             = "portal-backend-${var.environment}"
  cluster          = aws_ecs_cluster.this.id
  task_definition  = aws_ecs_task_definition.this.arn
  desired_count    = var.desired_count
  launch_type      = "FARGATE"
  platform_version = "LATEST"

  health_check_grace_period_seconds = 60

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "portal-backend"
    container_port   = var.app_port
  }

  # The deploy workflow registers new task definitions; autoscaling owns the count.
  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  depends_on = [aws_lb_listener_rule.this]
}

resource "aws_appautoscaling_target" "this" {
  min_capacity       = var.min_capacity
  max_capacity       = var.max_capacity
  resource_id        = "service/${aws_ecs_cluster.this.name}/${aws_ecs_service.this.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  lifecycle {
    ignore_changes = [min_capacity, max_capacity]
  }
}

resource "aws_appautoscaling_policy" "cpu" {
  name               = "cpu-target"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.this.resource_id
  scalable_dimension = aws_appautoscaling_target.this.scalable_dimension
  service_namespace  = aws_appautoscaling_target.this.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = var.cpu_target
    scale_in_cooldown  = 300
    scale_out_cooldown = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
