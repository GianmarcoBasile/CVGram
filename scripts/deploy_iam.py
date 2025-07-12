import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("REGION", "eu-west-2")

S3_BUCKET = os.getenv("S3_BUCKET", "cvgram-cv-bucket")

LAMBDA_ROLE_NAME = "lambda-cv-upload-role"
BACKEND_ROLE_NAME = "backend-cv-access-role"
COGNITO_AUTH_ROLE_NAME = "identity-pool-auth-role"
GITHUB_USER_NAME = "cvgram-github-actions"

LAMBDA_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
            ],
            "Resource": "arn:aws:logs:*:*:*",
        },
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject"],
            "Resource": "arn:aws:s3:::cvgram-cv-bucket/*",
        },
        {"Effect": "Allow", "Action": ["textract:*"], "Resource": "*"},
        {
            "Effect": "Allow",
            "Action": ["dynamodb:PutItem", "dynamodb:UpdateItem"],
            "Resource": "arn:aws:dynamodb:*:*:table/CVs",
        },
    ],
}

BACKEND_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": "arn:aws:s3:::cvgram-cv-bucket/*",
        },
        {
            "Effect": "Allow",
            "Action": ["dynamodb:*"],
            "Resource": "arn:aws:dynamodb:*:*:table/CVs",
        },
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
            ],
            "Resource": "*",
        },
    ],
}

ECR_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:DescribeRepositories",
                "ecr:CreateRepository",
                "ecr:ListImages",
                "ecr:DeleteRepository",
                "ecr:BatchDeleteImage",
            ],
            "Resource": "*",
        }
    ],
}

COGNITO_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:PutObject", "s3:GetObject"],
            "Resource": "arn:aws:s3:::cvgram-cv-bucket/*",
        },
        {
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": "arn:aws:s3:::cvgram-cv-bucket",
        },
    ],
}


iam = boto3.client("iam")
identity = boto3.client("cognito-identity", region_name=REGION)


def create_role_and_policy(role_name, policy_doc, assume_role_policy=None):
    """Crea un ruolo IAM e associa una policy."""
    try:
        role = iam.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )
        print(f"Ruolo creato: {role_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)
        print(f"Ruolo già esistente: {role_name}")
    role_arn = role["Role"]["Arn"]
    policy_name = f"{role_name}-policy"
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_doc),
        )
        print(f"Policy associata a {role_name}")
    except Exception as e:
        print(f"Errore policy: {e}")

    # Ruolo che permette a Lambda di scrivere su CloudWatch
    if role_name == LAMBDA_ROLE_NAME:
        try:
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            )
            print(f"Policy AWSLambdaBasicExecutionRole allegata a {role_name}")
        except Exception as e:
            print(f"Errore attach policy: {e}")
    return role_arn


def ensure_instance_profile(role_name):
    """Crea un Instance Profile e associa il ruolo specificato."""
    profile_name = role_name
    try:
        iam.create_instance_profile(InstanceProfileName=profile_name)
        print(f"Instance Profile creato: {profile_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Instance Profile già esistente: {profile_name}")
    try:
        iam.add_role_to_instance_profile(
            InstanceProfileName=profile_name, RoleName=role_name
        )
        print(f"Ruolo {role_name} associato a Instance Profile {profile_name}")
    except iam.exceptions.LimitExceededException:
        print(f"Limite ruoli superato per Instance Profile {profile_name}")
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Ruolo già associato a Instance Profile {profile_name}")
    except Exception as e:
        if "already associated" in str(e):
            print(f"Ruolo già associato a Instance Profile {profile_name}")
        else:
            print(f"Errore associazione ruolo/profile: {e}")


def main():
    lambda_assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    backend_assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    # Creazione dei ruoli con le relative policy e Instance Profile
    lambda_arn = create_role_and_policy(
        LAMBDA_ROLE_NAME, LAMBDA_POLICY, lambda_assume_role_policy
    )
    backend_arn = create_role_and_policy(
        BACKEND_ROLE_NAME, BACKEND_POLICY, backend_assume_role_policy
    )
    ensure_instance_profile(BACKEND_ROLE_NAME)

    # Creazione dell'utente per GitHub Actions
    try:
        iam.create_user(UserName=GITHUB_USER_NAME)
        print(f"Utente IAM creato: {GITHUB_USER_NAME}")
    except iam.exceptions.EntityAlreadyExistsException:
        iam.get_user(UserName=GITHUB_USER_NAME)
        print(f"WARNING: Utente IAM già esistente: {GITHUB_USER_NAME}")
    policy_name = f"{GITHUB_USER_NAME}-ecr-policy"
    try:
        iam.put_user_policy(
            UserName=GITHUB_USER_NAME,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(ECR_POLICY),
        )
        print(f"Policy ECR associata a {GITHUB_USER_NAME}")
    except Exception as e:
        print(f"Errore policy utente GitHub: {e}")

    # Creazione della access key per GitHub Actions
    try:
        keys = iam.list_access_keys(UserName=GITHUB_USER_NAME)["AccessKeyMetadata"]
        if len(keys) == 0:
            access_key = iam.create_access_key(UserName=GITHUB_USER_NAME)["AccessKey"]
            print(f"Access key creata per {GITHUB_USER_NAME}")
        else:
            print(
                f"Access key già esistente per {GITHUB_USER_NAME}, non ne creo altre."
            )
            access_key = None
    except Exception as e:
        print(f"Errore creazione access key: {e}")

    # Creazione ruolo Cognito e associazione policy
    cognito_config_path = os.path.join(
        os.path.dirname(__file__), "../cognito_config.json"
    )
    if os.path.exists(cognito_config_path):
        with open(cognito_config_path) as f:
            cognito_conf = json.load(f)
        identity_pool_id = cognito_conf.get("identityPoolId")
    else:
        identity_pool_id = None
    if identity_pool_id:
        cognito_assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Federated": "cognito-identity.amazonaws.com"},
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            "cognito-identity.amazonaws.com:aud": identity_pool_id
                        },
                        "ForAnyValue:StringLike": {
                            "cognito-identity.amazonaws.com:amr": "authenticated"
                        },
                    },
                }
            ],
        }
        cognito_auth_role_arn = create_role_and_policy(
            COGNITO_AUTH_ROLE_NAME, COGNITO_POLICY, cognito_assume_role_policy
        )

        # Associazione ruolo cognito all'identity pool
        try:
            identity.set_identity_pool_roles(
                IdentityPoolId=identity_pool_id,
                Roles={"authenticated": cognito_auth_role_arn},
            )
            print(f"Ruolo autenticato associato a Identity Pool {identity_pool_id}")
        except Exception as e:
            print(f"Errore associazione ruolo/identity pool: {e}")
    else:
        print("identityPoolId non trovato, salto creazione ruolo Cognito.")

    # Esportazione degli ARN e chiavi in un file JSON
    output = {
        "lambda_role_arn": lambda_arn,
        "backend_role_arn": backend_arn,
        "cognito_auth_role_arn": cognito_auth_role_arn,
    }
    if access_key:
        output["github_actions_access_key_id"] = access_key["AccessKeyId"]
        output["github_actions_secret_access_key"] = access_key["SecretAccessKey"]
    with open("../iam_arns.json", "w") as f:
        json.dump(output, f, indent=2)
    print("ARN esportati in iam_arns.json (inclusi access key GitHub se creati)")


if __name__ == "__main__":
    main()
