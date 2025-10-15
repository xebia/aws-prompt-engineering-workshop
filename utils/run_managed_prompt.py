from typing import Dict

import boto3

client = boto3.client("bedrock-runtime")


def run_managed_prompt(prompt_arn: str, input_vars: Dict[str, str]) -> str:
    response = client.invoke_model(
        modelId=prompt_arn,
        contentType="text/plain",
        accept="application/json",
    )
    result = response["body"].read().decode("utf-8")
    return result
