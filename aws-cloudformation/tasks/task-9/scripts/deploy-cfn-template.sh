#!/usr/bin/env bash

if [ -z "$3" ]; then
  echo "Usage: ./scripts/deploy-cfn-template.sh <BUCKET_NAME> <AWS_REGION> <ROLE_ARN>"
  exit 1
else
  BUCKET_NAME="$1"
  AWS_REGION="$2"
  ROLE_ARN="$3"
fi
STACK_NAME="cfn-package-deploy"

printf "\n--> Packaging and uploading templates to the %s S3 bucket ...\n" "${BUCKET_NAME}"

aws cloudformation package \
  --template-file ./infrastructure.template \
  --s3-bucket "${BUCKET_NAME}" \
  --s3-prefix "${STACK_NAME}" \
  --output-template-file ./infrastructure-packaged.template

printf "\n--> Validating template ...\n"

aws cloudformation validate-template \
  --template-body file://infrastructure-packaged.template

printf "\n--> Deploying %s template...\n" "${STACK_NAME}"

aws cloudformation deploy \
  --template-file ./infrastructure-packaged.template \
  --stack-name "${STACK_NAME}" \
  --region "${AWS_REGION}" \
  --parameter-overrides LambdaExecutionRoleArn="${ROLE_ARN}"
