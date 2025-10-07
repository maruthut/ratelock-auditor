# ECS Fargate services for RateLock microservices

# Get default VPC
data "aws_vpc" "default" {
  default = true
}

# Get default subnets
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-${var.environment}-alb-"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-alb-sg"
    Component = "compute"
  })
}

# Security group for ECS tasks
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.project_name}-${var.environment}-ecs-"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-ecs-sg"
    Component = "compute"
  })
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids

  enable_deletion_protection = false

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-alb"
    Component = "compute"
  })
}

# ALB Target Group for Conversion Engine
resource "aws_lb_target_group" "conversion_engine" {
  name        = "${var.project_name}-${var.environment}-conversion-v2"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-conversion-tg"
    Component = "compute"
  })
}

# ALB Listener
resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.conversion_engine.arn
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-listener"
    Component = "compute"
  })
}

# ECR Repository for Conversion Engine
resource "aws_ecr_repository" "conversion_engine" {
  name                 = "${var.project_name}/conversion-engine"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-conversion-engine-repo"
    Component = "compute"
  })
}

# ECR Repository for RateSync
resource "aws_ecr_repository" "ratesync" {
  name                 = "${var.project_name}/ratesync"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-ratesync-repo"
    Component = "compute"
  })
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-cluster"
    Component = "compute"
  })
}

# CloudWatch Log Group for Conversion Engine
resource "aws_cloudwatch_log_group" "conversion_engine" {
  name              = "/ecs/${var.project_name}-${var.environment}-conversion-engine"
  retention_in_days = 14

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-conversion-logs"
    Component = "compute"
  })
}

# CloudWatch Log Group for RateSync
resource "aws_cloudwatch_log_group" "ratesync" {
  name              = "/ecs/${var.project_name}-${var.environment}-ratesync"
  retention_in_days = 14

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-ratesync-logs"
    Component = "compute"
  })
}

# IAM role for ECS task execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-${var.environment}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-ecs-task-execution"
    Component = "compute"
  })
}

# Attach AmazonECSTaskExecutionRolePolicy
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM role for ECS tasks (application permissions)
resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-${var.environment}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-ecs-task"
    Component = "compute"
  })
}

# DynamoDB access policy for ECS tasks
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "${var.project_name}-${var.environment}-dynamodb-access"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.rate_cache_table_arn,
          var.audit_log_table_arn
        ]
      }
    ]
  })
}

# ECS Task Definition for Conversion Engine
resource "aws_ecs_task_definition" "conversion_engine" {
  family                   = "${var.project_name}-${var.environment}-conversion-engine"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "conversion-engine"
      image = "${aws_ecr_repository.conversion_engine.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "RATE_CACHE_TABLE"
          value = var.rate_cache_table_name
        },
        {
          name  = "AUDIT_LOG_TABLE"
          value = var.audit_log_table_name
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.conversion_engine.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-conversion-task"
    Component = "compute"
  })
}

# ECS Service for Conversion Engine
resource "aws_ecs_service" "conversion_engine" {
  name            = "${var.project_name}-${var.environment}-conversion-engine"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.conversion_engine.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = data.aws_subnets.default.ids
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.conversion_engine.arn
    container_name   = "conversion-engine"
    container_port   = 8080
  }

  depends_on = [aws_lb_listener.main]

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-conversion-service"
    Component = "compute"
  })
}

# ECS Task Definition for RateSync
resource "aws_ecs_task_definition" "ratesync" {
  family                   = "${var.project_name}-${var.environment}-ratesync"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = 256
  memory                  = 512
  execution_role_arn      = aws_iam_role.ecs_task_execution.arn
  task_role_arn          = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "ratesync"
      image     = "${aws_ecr_repository.ratesync.repository_url}:latest"
      essential = true

      environment = [
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        },
        {
          name  = "RATE_CACHE_TABLE"
          value = var.rate_cache_table_name
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ratesync.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-ratesync-task"
    Component = "compute"
  })
}

# ECS Service for RateSync (runs on schedule)
resource "aws_ecs_service" "ratesync" {
  name            = "${var.project_name}-${var.environment}-ratesync"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.ratesync.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = data.aws_subnets.default.ids
    assign_public_ip = true
  }

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-ratesync-service"
    Component = "compute"
  })
}