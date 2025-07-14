@echo off
cd /d "%~dp0\scripts"

set SCRIPT_LIST=deploy_cognito.py deploy_s3.py deploy_iam.py deploy_dynamodb.py deploy_ecr.py deploy_ec2.py deploy_lambda.py

for %%S in (%SCRIPT_LIST%) do (
    python %%S
    if errorlevel 1 (
        echo Errore nell'esecuzione di %%S
        exit /b 1
    )
)
echo Tutti gli script sono stati eseguiti con successo!