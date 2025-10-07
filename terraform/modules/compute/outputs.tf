output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "conversion_engine_repository_url" {
  description = "URL of the conversion engine ECR repository"
  value       = aws_ecr_repository.conversion_engine.repository_url
}

output "ratesync_repository_url" {
  description = "URL of the ratesync ECR repository"
  value       = aws_ecr_repository.ratesync.repository_url
}

output "conversion_engine_service_name" {
  description = "Name of the conversion engine ECS service"
  value       = aws_ecs_service.conversion_engine.name
}