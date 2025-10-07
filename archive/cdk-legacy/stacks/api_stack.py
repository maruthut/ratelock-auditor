"""
API Stack for RateLock
Creates API Gateway to expose ConversionEngine service
"""

from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_logs as logs,
    Duration,
    CfnOutput,
    Fn
)
from constructs import Construct
from .compute_stack import ComputeStack


class ApiStack(Stack):
    """API Gateway for RateLock currency conversion service"""

    def __init__(self, scope: Construct, construct_id: str,
                 compute_stack: ComputeStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import ALB DNS name from compute stack
        self.alb_dns = Fn.import_value(f"{compute_stack.stack_name}-LoadBalancerDNS")

        # Create API Gateway access logs
        self.api_logs = logs.LogGroup(
            self, "ApiGatewayLogs",
            log_group_name="/aws/apigateway/ratelock-api",
            retention=logs.RetentionDays.ONE_WEEK
        )

        # Create REST API
        self.api = apigateway.RestApi(
            self, "RateLockApi",
            rest_api_name="ratelock-api",
            description="RateLock auditable currency conversion API",
            
            # Enable CORS for frontend
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            ),
            
            # Configure access logging
            deploy_options=apigateway.StageOptions(
                stage_name="v1",
                access_log_destination=apigateway.LogGroupLogDestination(self.api_logs),
                access_log_format=apigateway.AccessLogFormat.clf(),
                data_trace_enabled=True,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                metrics_enabled=True,
                tracing_enabled=False  # Keep costs low
            ),
            
            # Free tier optimization
            endpoint_configuration=apigateway.EndpointConfiguration(
                types=[apigateway.EndpointType.REGIONAL]
            )
        )

        # Create HTTP integration with ALB
        self.alb_integration = apigateway.HttpIntegration(
            f"http://{self.alb_dns}/{{proxy}}",
            http_method="ANY",
            options=apigateway.IntegrationOptions(
                request_parameters={
                    "integration.request.path.proxy": "method.request.path.proxy"
                },
                connection_type=apigateway.ConnectionType.INTERNET,
                timeout=Duration.seconds(29)  # API Gateway max timeout
            )
        )

        # Add health endpoint
        health_resource = self.api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigateway.HttpIntegration(
                f"http://{self.alb_dns}/health",
                http_method="GET"
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                )
            ]
        )

        # Add v1 API resource
        v1_resource = self.api.root.add_resource("v1")
        
        # Add convert endpoint
        convert_resource = v1_resource.add_resource("convert")
        convert_resource.add_method(
            "GET",
            apigateway.HttpIntegration(
                f"http://{self.alb_dns}/v1/convert",
                http_method="GET",
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.querystring.from": "method.request.querystring.from",
                        "integration.request.querystring.to": "method.request.querystring.to", 
                        "integration.request.querystring.amount": "method.request.querystring.amount"
                    }
                )
            ),
            request_parameters={
                "method.request.querystring.from": True,
                "method.request.querystring.to": True,
                "method.request.querystring.amount": True
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                ),
                apigateway.MethodResponse(status_code="400"),
                apigateway.MethodResponse(status_code="503")
            ]
        )

        # Add audit endpoint
        audit_resource = v1_resource.add_resource("audit")
        audit_id_resource = audit_resource.add_resource("{transaction_id}")
        audit_id_resource.add_method(
            "GET",
            apigateway.HttpIntegration(
                f"http://{self.alb_dns}/v1/audit/{{transaction_id}}",
                http_method="GET",
                options=apigateway.IntegrationOptions(
                    request_parameters={
                        "integration.request.path.transaction_id": "method.request.path.transaction_id"
                    }
                )
            ),
            request_parameters={
                "method.request.path.transaction_id": True
            },
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                ),
                apigateway.MethodResponse(status_code="404")
            ]
        )

        # Add rates endpoint (for monitoring)
        rates_resource = v1_resource.add_resource("rates")
        rates_resource.add_method(
            "GET",
            apigateway.HttpIntegration(
                f"http://{self.alb_dns}/v1/rates",
                http_method="GET"
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                ),
                apigateway.MethodResponse(status_code="503")
            ]
        )

        # Outputs
        CfnOutput(
            self, "ApiGatewayUrl",
            value=self.api.url,
            description="URL of the API Gateway",
            export_name="RateLock-ApiGatewayUrl"
        )

        CfnOutput(
            self, "ApiGatewayId",
            value=self.api.rest_api_id,
            description="ID of the API Gateway"
        )