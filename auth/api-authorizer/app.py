def handler(event, context):

    token = event.get(
        "headers", {}
    ).get("authorization")

    if token == "secret123":
        return {
            "isAuthorized": True
        }

    return {
        "isAuthorized": False
    }
