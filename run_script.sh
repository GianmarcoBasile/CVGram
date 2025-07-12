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
  if [[ "$script" == "deploy_ecr.py" ]]; then
    echo "Aggiorno index.ts con i valori di cognito_config.json..."
    python update_frontend_cognito.py
    npm --prefix ../Frontend run build
    rm -rf ../Backend/out
    mv ../Frontend/out ../Backend/
  fi
done

echo "Tutti gli script sono stati eseguiti con successo!"