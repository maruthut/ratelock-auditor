"""
Frontend Stack for RateLock
Creates S3 static website hosting for the frontend
"""

from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    Duration,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct
from .api_stack import ApiStack


class FrontendStack(Stack):
    """S3 static website for RateLock frontend"""

    def __init__(self, scope: Construct, construct_id: str,
                 api_stack: ApiStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Reference API Gateway URL
        self.api_url = api_stack.api.url

        # Create S3 bucket for static website hosting
        self.website_bucket = s3.Bucket(
            self, "WebsiteBucket",
            bucket_name=f"ratelock-frontend-{self.account}-{self.region}",
            website_index_document="index.html",
            website_error_document="error.html",
            public_read_access=True,
            removal_policy=RemovalPolicy.DESTROY,  # For dev/test
            auto_delete_objects=True,  # Clean up on stack deletion
            
            # CORS configuration for API calls
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.POST],
                    allowed_origins=["*"],
                    allowed_headers=["*"]
                )
            ]
        )

        # Deploy frontend files to S3
        self.deployment = s3deploy.BucketDeployment(
            self, "DeployWebsite",
            sources=[
                s3deploy.Source.asset("../frontend")  # Path to frontend folder
            ],
            destination_bucket=self.website_bucket,
            
            # Cache settings
            cache_control=[
                s3deploy.CacheControl.max_age(Duration.hours(1))
            ]
        )

        # Outputs
        CfnOutput(
            self, "WebsiteUrl",
            value=self.website_bucket.bucket_website_url,
            description="URL of the static website",
            export_name="RateLock-WebsiteUrl"
        )

        CfnOutput(
            self, "WebsiteBucketName",
            value=self.website_bucket.bucket_name,
            description="Name of the website S3 bucket"
        )