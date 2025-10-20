from typing import Dict

import boto3

client = boto3.client("bedrock-runtime")


def run_managed_prompt(prompt_version_arn: str, input_vars: Dict[str, str]) -> str:
    response = client.converse(
        modelId=prompt_version_arn,
        promptVariables=input_vars,
    )
    return response["output"]["message"]["content"][0]["text"]
