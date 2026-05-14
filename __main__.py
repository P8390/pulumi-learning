from infra.api_factory import create_api_gateway, attach_route
from infra.cicd import *
from infra.cron_factory import create_cron
from infra.lambda_factory import create_lambda

config = pulumi.Config()
services = config.require_object('services')

"""
{
    "employee": {"auth": True},
    "invoice": {"auth": True},
    "reports": {"auth": False}
}
"""

# Create DynamoDB table
table = aws.dynamodb.Table(
    "employee-table",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name="employee_id",
            type="S"
        )
    ],
    hash_key="employee_id",
    billing_mode="PAY_PER_REQUEST"
)

# Export values
pulumi.export("table_name", table.name)
pulumi.export("table_arn", table.arn)

api = create_api_gateway("platform-api")

authorizer_lambda = create_lambda("api-authorizer")

authorizer = aws.apigatewayv2.Authorizer(
    "authorizer",
    api_id=api.id,
    authorizer_type="REQUEST",
    authorizer_uri=authorizer_lambda.invoke_arn,
    identity_sources=["$request.header.Authorization"],
    authorizer_payload_format_version="2.0",
    enable_simple_responses=True
)

aws.lambda_.Permission(
    "authorizer-permission",
    action="lambda:InvokeFunction",
    function=authorizer_lambda.name,
    principal="apigateway.amazonaws.com"
)

for service_name, service_config in services.items():
    fn = create_lambda(service_name, {"TABLE_NAME": table.name})
    attach_route(api, service_name, fn, authorizer if service_config["auth"] else None)

cron_jobs = config.require_object(
    "cron"
)

for job_name, job_config in cron_jobs.items():
    fn = create_lambda(job_name)
    create_cron(job_name, fn, job_config.get('schedule', {}))

pulumi.export(
    "api_url",
    api.api_endpoint
)
