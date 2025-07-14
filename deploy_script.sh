#!/bin/bash
set -e

cd "$(dirname "$0")/scripts"

SCRIPT_LIST=(
  deploy_cognito.py
  deploy_s3.py
  deploy_iam.py
  deploy_dynamodb.py
  deploy_ecr.py
  deploy_ec2.py
  deploy_lambda.py
)

for script in "${SCRIPT_LIST[@]}"; do
  echo "Sto eseguendo $script..."
  python "$script"
done

echo "Tutti gli script sono stati eseguiti con successo!"