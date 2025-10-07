"""
Compute Stack for RateLock
Creates ECS Fargate services for ConversionEngine and RateSync
"""

from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_ecr as ecr,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    CfnOutput
)
from constructs import Construct
from .database_stack import DatabaseStack


class ComputeStack(Stack):
    """ECS Fargate services for RateLock microservices"""

    def __init__(self, scope: Construct, construct_id: str, 
                 database_stack: DatabaseStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Reference database tables
        self.rate_cache_table = database_stack.rate_cache_table
        self.audit_log_table = database_stack.audit_log_table

        # Create VPC for services (using default VPC to stay in free tier)
        self.vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)

        # Create ECS Cluster
        self.cluster = ecs.Cluster(
            self, "RateLockCluster",
            cluster_name="ratelock-cluster",
            vpc=self.vpc,
            container_insights=False,  # Keep costs low
        )

        # Create ECR repositories
        self.conversion_engine_repo = ecr.Repository(
            self, "ConversionEngineRepo",
            repository_name="ratelock/conversion-engine",
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=10,  # Keep only 10 images
                    description="Keep only 10 most recent images"
                )
            ]
        )

        self.ratesync_repo = ecr.Repository(
            self, "RateSyncRepo", 
            repository_name="ratelock/ratesync",
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=10,
                    description="Keep only 10 most recent images"
                )
            ]
        )

        # Create task execution role
        self.task_execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ]
        )

        # Create task role with DynamoDB permissions
        self.task_role = iam.Role(
            self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                "DynamoDBAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:PutItem", 
                                "dynamodb:UpdateItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:Query",
                                "dynamodb:Scan"
                            ],
                            resources=[
                                self.rate_cache_table.table_arn,
                                self.audit_log_table.table_arn
                            ]
                        )
                    ]
                )
            }
        )

        # Create CloudWatch log groups
        self.conversion_engine_logs = logs.LogGroup(
            self, "ConversionEngineLogGroup",
            log_group_name="/ecs/ratelock-conversion-engine",
            retention=logs.RetentionDays.ONE_WEEK  # Keep costs low
        )

        self.ratesync_logs = logs.LogGroup(
            self, "RateSyncLogGroup",
            log_group_name="/ecs/ratelock-ratesync", 
            retention=logs.RetentionDays.ONE_WEEK
        )

        # Create ConversionEngine Task Definition
        self.conversion_engine_task = ecs.FargateTaskDefinition(
            self, "ConversionEngineTask",
            family="ratelock-conversion-engine",
            cpu=256,  # 0.25 vCPU (free tier optimized)
            memory_limit_mib=512,  # 0.5 GB RAM (free tier optimized)
            execution_role=self.task_execution_role,
            task_role=self.task_role
        )

        # Add ConversionEngine container
        self.conversion_engine_container = self.conversion_engine_task.add_container(
            "conversion-engine",
            image=ecs.ContainerImage.from_ecr_repository(
                self.conversion_engine_repo, tag="latest"
            ),
            port_mappings=[
                ecs.PortMapping(container_port=8080, protocol=ecs.Protocol.TCP)
            ],
            environment={
                "AWS_DEFAULT_REGION": self.region,
                "RATE_CACHE_TABLE": self.rate_cache_table.table_name,
                "AUDIT_LOG_TABLE": self.audit_log_table.table_name,
                "ENVIRONMENT": "production"
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="ecs",
                log_group=self.conversion_engine_logs
            ),
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                retries=3,
                start_period=Duration.seconds(60)
            )
        )

        # Create RateSync Task Definition
        self.ratesync_task = ecs.FargateTaskDefinition(
            self, "RateSyncTask",
            family="ratelock-ratesync",
            cpu=256,  # 0.25 vCPU
            memory_limit_mib=512,  # 0.5 GB RAM
            execution_role=self.task_execution_role,
            task_role=self.task_role
        )

        # Add RateSync container
        self.ratesync_container = self.ratesync_task.add_container(
            "ratesync",
            image=ecs.ContainerImage.from_ecr_repository(
                self.ratesync_repo, tag="latest"
            ),
            environment={
                "AWS_DEFAULT_REGION": self.region,
                "RATE_CACHE_TABLE": self.rate_cache_table.table_name,
                "ENVIRONMENT": "production"
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="ecs",
                log_group=self.ratesync_logs
            )
        )

        # Create Application Load Balancer
        self.alb = elbv2.ApplicationLoadBalancer(
            self, "RateLockALB",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name="ratelock-alb"
        )

        # Create Target Group
        self.target_group = elbv2.ApplicationTargetGroup(
            self, "ConversionEngineTargetGroup",
            vpc=self.vpc,
            port=8080,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            health_check=elbv2.HealthCheck(
                path="/health",
                healthy_http_codes="200",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
                healthy_threshold_count=2,
                unhealthy_threshold_count=3
            )
        )

        # Add listener to ALB
        self.alb.add_listener(
            "ALBListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_target_groups=[self.target_group]
        )

        # Create ConversionEngine Service
        self.conversion_engine_service = ecs.FargateService(
            self, "ConversionEngineService",
            cluster=self.cluster,
            task_definition=self.conversion_engine_task,
            service_name="conversion-engine",
            desired_count=1,  # Start with 1 instance
            assign_public_ip=True,
            health_check_grace_period=Duration.seconds(120)
        )

        # Attach service to target group
        self.conversion_engine_service.attach_to_application_target_group(
            self.target_group
        )

        # Create EventBridge rule for RateSync (hourly execution)
        self.ratesync_rule = events.Rule(
            self, "RateSyncSchedule",
            rule_name="ratelock-hourly-sync",
            description="Trigger RateSync service every hour",
            schedule=events.Schedule.rate(Duration.hours(1))
        )

        # Add ECS task target to EventBridge rule
        self.ratesync_rule.add_target(
            targets.EcsTask(
                cluster=self.cluster,
                task_definition=self.ratesync_task,
                subnet_selection=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PUBLIC
                ),
                assign_public_ip=True,
                platform_version=ecs.FargatePlatformVersion.LATEST
            )
        )

        # Outputs
        CfnOutput(
            self, "LoadBalancerDNS",
            value=self.alb.load_balancer_dns_name,
            description="DNS name of the Application Load Balancer",
            export_name=f"{Stack.of(self).stack_name}-LoadBalancerDNS"
        )

        CfnOutput(
            self, "ConversionEngineRepoUri",
            value=self.conversion_engine_repo.repository_uri,
            description="URI of the ConversionEngine ECR repository"
        )

        CfnOutput(
            self, "RateSyncRepoUri", 
            value=self.ratesync_repo.repository_uri,
            description="URI of the RateSync ECR repository"
        )