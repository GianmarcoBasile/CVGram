import boto3
import zipfile
import os
import json
import time

LAMBDA_NAME = 'cvgram-cv-processing'  # Nome funzione Lambda su AWS
LAMBDA_FILE = 'lambda_function.py'  # File python da zippare (es: lambda_helloworld.py o lambda_function.py)
HANDLER = 'lambda_function.lambda_handler'  # handler (es: lambda_helloworld.lambda_handler o lambda_function.lambda_handler)

with open(os.path.join(os.path.dirname(__file__), '../iam_arns.json')) as f:
    arns = json.load(f)
ROLE_ARN = arns['lambda_role_arn']
RUNTIME = 'python3.12'
ZIP_FILE = 'lambda_cv_processing.zip'
REGION = 'eu-west-2'

lambda_client = boto3.client('lambda', region_name=REGION)

# 1. Crea lo zip della lambda

def create_lambda_zip():
    with zipfile.ZipFile(ZIP_FILE, 'w') as zf:
        zf.write(LAMBDA_FILE)
    print(f"✅ Creato {ZIP_FILE}")

# 2. Crea o aggiorna la lambda

def deploy_lambda():
    with open(ZIP_FILE, 'rb') as f:
        code_bytes = f.read()
    try:
        lambda_client.get_function(FunctionName=LAMBDA_NAME)
        # Se esiste, aggiorna solo codice
        lambda_client.update_function_code(
            FunctionName=LAMBDA_NAME,
            ZipFile=code_bytes
        )
        print(f"♻️  Codice Lambda aggiornato: {LAMBDA_NAME}")
    except lambda_client.exceptions.ResourceNotFoundException:
        # Se non esiste, crea
        lambda_client.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime=RUNTIME,
            Role=ROLE_ARN,
            Handler=HANDLER,
            Code={'ZipFile': code_bytes},
            Timeout=300,
            MemorySize=512,
            Environment={
                'Variables': {
                    'CVS_TABLE': 'CVs',
                    'REGION': REGION
                }
            }
        )
        print(f"✅ Lambda creata: {LAMBDA_NAME}")


BUCKET = 'cvgram-cv-bucket'

def add_lambda_permission():
    function_arn = lambda_client.get_function(FunctionName=LAMBDA_NAME)['Configuration']['FunctionArn']
    statement_id = 'AllowS3Invoke'
    bucket_arn = f'arn:aws:s3:::{BUCKET}'
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=bucket_arn
        )
        print("✅ Permission Lambda per S3 aggiunta.")
    except lambda_client.exceptions.ResourceConflictException:
        print("ℹ️ Permission Lambda già presente.")

def add_s3_trigger():
    s3 = boto3.client('s3', region_name=REGION)
    notification = {
        'LambdaFunctionConfigurations': [
            {
                'LambdaFunctionArn': lambda_client.get_function(FunctionName=LAMBDA_NAME)['Configuration']['FunctionArn'],
                'Events': ['s3:ObjectCreated:*'],
                'Filter': {
                    'Key': {
                        'FilterRules': [
                            {'Name': 'suffix', 'Value': '.pdf'}
                        ]
                    }
                }
            }
        ]
    }
    s3.put_bucket_notification_configuration(
        Bucket=BUCKET,
        NotificationConfiguration=notification
    )
    print(f"✅ Trigger S3 configurato su {BUCKET}")

if __name__ == "__main__":
    create_lambda_zip()
    deploy_lambda()
    # Attendi propagazione IAM
    print("⏳ Attendo propagazione IAM...")
    time.sleep(10)
    add_lambda_permission()
    add_s3_trigger()
