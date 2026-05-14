import pulumi_aws as aws


def create_cron(name, lambda_fn, schedule):
    rule = aws.cloudwatch.EventRule(
        f"{name}-rule",
        schedule_expression=schedule
    )

    aws.cloudwatch.EventTarget(
        f"{name}-target",
        rule=rule.name,
        arn=lambda_fn.arn
    )

    aws.lambda_.Permission(
        f"{name}-permission",
        action="lambda:InvokeFunction",
        function=lambda_fn.name,
        principal="events.amazonaws.com",
        source_arn=rule.arn
    )
    return rule
