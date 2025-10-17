# AWS Prompt Engineering Workshop

## Requirements

- AWS SAM CLI installed ([installation guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
- AWS CLI installed and configured with an `AWS_PROFILE` ([configuration guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html))
- Request service quota increases for:
  - Total number of notebook instances (50)
  - ml.t3.medium for notebook instance usage (50)

## Deploy the environments

Tweak the `template.yml` file to match the needed amount of participants.

```shell
export AWS_PROFILE=...
make login
make deploy
```
