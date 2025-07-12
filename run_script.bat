@echo off
cd /d "%~dp0\scripts"

set SCRIPT_LIST=deploy_cognito.py deploy_s3.py deploy_iam.py deploy_dynamodb.py deploy_ecr.py deploy_ec2.py deploy_lambda.py

for %%S in (%SCRIPT_LIST%) do (
    if "%%S" == "deploy_ecr.py" (
        echo Aggiorno index.ts con i valori di cognito_config.json...
        python update_frontend_cognito.py
        npm --prefix ../Frontend run build
        rmdir /S /Q "..\Backend\out"
        move /Y "..\Frontend\out" "..\Backend\"
    )
    echo Sto eseguendo %%S...
    python %%S
    if errorlevel 1 (
        echo Errore nell'esecuzione di %%S
        exit /b 1
    )
)
echo Tutti gli script sono stati eseguiti con successo!