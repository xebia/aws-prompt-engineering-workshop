import boto3


def resolve_user_settings(username_: str) -> dict:
    ssm = boto3.client("ssm")
    path = f"/{username_}/"
    params = {}
    next_token = None
    while True:
        kwargs = {"Path": path, "Recursive": True, "WithDecryption": True}
        if next_token:
            kwargs["NextToken"] = next_token
        response = ssm.get_parameters_by_path(**kwargs)
        for param in response.get("Parameters", []):
            # Strip the path prefix for the key
            key = param["Name"].replace(path, "")
            params[key] = param["Value"]
        next_token = response.get("NextToken")
        if not next_token:
            break
    return params
