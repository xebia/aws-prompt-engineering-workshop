$(VERBOSE).SILENT:
SHELL = /bin/bash -c
VIRTUAL_ENV = $(PWD)/.venv
export BASH_ENV=$(VIRTUAL_ENV)/bin/activate
export AWS_REGION ?= eu-central-1

EXCLUDE_AWS_PROFILE_CHECK := help

ifneq ($(filter $(MAKECMDGOALS),$(EXCLUDE_AWS_PROFILE_CHECK)),)
else ifeq ($(origin AWS_PROFILE),undefined)
$(error Make sure you have set the AWS_PROFILE environment variable)
endif


.DEFAULT_GOAL:=help

.PHONY: help
help:  ## Display this help
	$(info Xebia - AWS Prompt Engineering Workshop)
	$(info =========================)
	$(info Profile: $(AWS_PROFILE))
	$(info Region: $(AWS_REGION))
	awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: login
login: ## Login to the SSO Session
	aws sso login

deploy: ## Build and deploy the application
	sam build
	sam deploy \
		--region $(AWS_REGION) \
		--stack-name aws-prompt-engineering-workshop \
		--template-file .aws-sam/build/template.yaml \
		--resolve-s3 \
		--capabilities CAPABILITY_NAMED_IAM

credentials:
	uv run ./utils/create_credentials.py --stack-name aws-prompt-engineering-workshop

delete-credentials:
	uv run ./utils/create_credentials.py --stack-name aws-prompt-engineering-workshop --delete
