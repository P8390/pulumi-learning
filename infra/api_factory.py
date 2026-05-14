import pulumi_aws as aws


def create_api_gateway(name):

    api = aws.apigatewayv2.Api(
        name,
        protocol_type="HTTP"
    )

    aws.apigatewayv2.Stage(
        f"{name}-stage",
        api_id=api.id,
        name="$default",
        auto_deploy=True
    )

    return api


def attach_route(
    api,
    route_name,
    lambda_fn,
    authorizer=None
):

    integration = aws.apigatewayv2.Integration(
        f"{route_name}-integration",
        api_id=api.id,
        integration_type="AWS_PROXY",
        integration_uri=lambda_fn.arn,
        payload_format_version="2.0"
    )

    route_args = {
        "api_id": api.id,
        "route_key": f"GET /{route_name}",
        "target": integration.id.apply(
            lambda i: f"integrations/{i}"
        )
    }

    if authorizer:
        route_args["authorization_type"] = "CUSTOM"
        route_args["authorizer_id"] = authorizer.id

    aws.apigatewayv2.Route(
        f"{route_name}-route",
        **route_args
    )

    aws.lambda_.Permission(
        f"{route_name}-permission",
        action="lambda:InvokeFunction",
        function=lambda_fn.name,
        principal="apigateway.amazonaws.com"
    )
