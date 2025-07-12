import boto3
import json
import botocore
import os

CV_BUCKET = 'cvgram-cv-bucket'

s3 = boto3.client('s3')
region = "eu-west-2"

with open(os.path.join(os.path.dirname(__file__), '../iam_arns.json')) as f:
    arns = json.load(f)
lambda_role_arn = arns['lambda_role_arn']
backend_role_arn = arns['backend_role_arn']

def create_bucket(BUCKET_NAME):
    try:
        s3.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
        print(f"✅ Bucket '{BUCKET_NAME}' creato.")
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"ℹ️ Bucket '{BUCKET_NAME}' già esistente.")
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
    print("✅ CORS configurato.")

def apply_bucket_policy(BUCKET_NAME):
  policy = {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowLambdaAndBackendAccess",
        "Effect": "Allow",
        "Principal": {"AWS": [lambda_role_arn, backend_role_arn]},
        "Action": ["s3:PutObject", "s3:GetObject"],
        "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
      }
    ]
  }
  s3.put_bucket_policy(Bucket=BUCKET_NAME, Policy=json.dumps(policy))
  print("✅ Policy del bucket applicata.")

def enable_versioning(BUCKET_NAME):
    s3.put_bucket_versioning(
        Bucket=BUCKET_NAME,
        VersioningConfiguration={'Status': 'Enabled'}
    )
    print("✅ Versionamento abilitato.")

if __name__ == "__main__":
    create_bucket(CV_BUCKET)
    configure_cors(CV_BUCKET)
    apply_bucket_policy(CV_BUCKET)
    enable_versioning(CV_BUCKET)