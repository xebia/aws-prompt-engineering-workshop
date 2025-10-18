import boto3

client = boto3.client("bedrock-runtime")
model_id = "amazon.nova-lite-v1:0"


def run_guarded_prompt(
    user_message: str, guardrail_id: str, guardrail_version: str
) -> str:
    conversation = [
        {
            "role": "user",
            "content": [{"text": user_message}],
        }
    ]

    response = client.converse(
        modelId=f"eu.{model_id}",
        messages=conversation,
        inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        guardrailConfig={
            "guardrailIdentifier": guardrail_id,
            "guardrailVersion": guardrail_version,
        },
    )
    return response["output"]["message"]["content"][0]["text"]
