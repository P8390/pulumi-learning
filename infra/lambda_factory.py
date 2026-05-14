import pulumi
import pulumi_aws as aws


def create_lambda(name, env_vars=None):

    env_vars = env_vars or {}

    role = aws.iam.Role(
        f"{name}-role",
        assume_role_policy="""{
          "Version": "2012-10-17",
          "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
              "Service": "lambda.amazonaws.com"
            },
            "Effect": "Allow"
          }]
        }"""
    )

    aws.iam.RolePolicyAttachment(
        f"{name}-basic-execution",
        role=role.name,
        policy_arn=aws.iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE
    )

    layer = aws.lambda_.LayerVersion(
        f"{name}-layer",
        layer_name=f"{name}-layer",
        code=pulumi.FileArchive(
            f"./layers/{name}-layer.zip"
        ),
        compatible_runtimes=["python3.11"]
    )

    fn = aws.lambda_.Function(
        name,
        runtime="python3.11",
        role=role.arn,
        handler="app.handler",
        code=pulumi.FileArchive(
            f"./build/{name}.zip"
        ),
        environment=aws.lambda_.FunctionEnvironmentArgs(
            variables=env_vars
        ),
        layers=[layer.arn]
    )

    return fn
