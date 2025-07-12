import boto3
import json
import botocore
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv('REGION', 'eu-west-2')
CV_BUCKET = os.getenv('S3_BUCKET', 'cvgram-cv-bucket')

s3 = boto3.client('s3')

with open(os.path.join(os.path.dirname(__file__), '../iam_arns.json')) as f:
    arns = json.load(f)
lambda_role_arn = arns['lambda_role_arn']
backend_role_arn = arns['backend_role_arn']

def create_bucket(BUCKET_NAME):
    try:
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
        )
        print(f"Bucket '{BUCKET_NAME}' creato.")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"WARNING: Bucket '{BUCKET_NAME}' già esistente")
        else:
            raise

def configure_cors(BUCKET_NAME):
    cors_config = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['PUT', 'POST', 'GET', 'HEAD'],
            'AllowedOrigins': ['*'],
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3000
        }]
    }
    s3.put_bucket_cors(Bucket=BUCKET_NAME, CORSConfiguration=cors_config)
    print("CORS configurato")

def enable_versioning(BUCKET_NAME):
    s3.put_bucket_versioning(
        Bucket=BUCKET_NAME,
        VersioningConfiguration={'Status': 'Enabled'}
    )
    print("Versionamento abilitato")

if __name__ == "__main__":
    create_bucket(CV_BUCKET)
    configure_cors(CV_BUCKET)
    enable_versioning(CV_BUCKET)