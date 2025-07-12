import boto3
from botocore.exceptions import ClientError
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
S3_BUCKET = os.getenv("S3_BUCKET", "cvgram-cv-bucket")
COGNITO_USER_POOL_NAME = "CVGramUserPool"
COGNITO_CLIENT_NAME = "CVGramFrontendClient"
COGNITO_IDENTITY_POOL_NAME = "CVGramIdentityPool"

session = boto3.Session(region_name=AWS_REGION)
cognito = session.client("cognito-idp")
identity = session.client("cognito-identity")
iam = session.client("iam")


def get_user_pool_by_name(pool_name):
    paginator = cognito.get_paginator("list_user_pools")
    for page in paginator.paginate(MaxResults=60):
        for pool in page["UserPools"]:
            if pool["Name"] == pool_name:
                return pool["Id"]
    return None


def get_user_pool_client_by_name(user_pool_id, client_name):
    response = cognito.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=60)
    for client in response["UserPoolClients"]:
        # Recupera i dettagli per confrontare il nome
        client_details = cognito.describe_user_pool_client(
            UserPoolId=user_pool_id, ClientId=client["ClientId"]
        )
        if client_details["UserPoolClient"]["ClientName"] == client_name:
            return client["ClientId"]
    return None


def get_identity_pool_by_name(pool_name):
    paginator = identity.get_paginator("list_identity_pools")
    for page in paginator.paginate(MaxResults=60):
        for pool in page["IdentityPools"]:
            if pool["IdentityPoolName"] == pool_name:
                return pool["IdentityPoolId"]
    return None


def create_user_pool():
    try:
        response = cognito.create_user_pool(
            PoolName=COGNITO_USER_POOL_NAME,
            AutoVerifiedAttributes=["email"],
            UsernameAttributes=["email"],
            Policies={
                "PasswordPolicy": {
                    "MinimumLength": 8,
                    "RequireUppercase": False,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": False,
                }
            },
            AccountRecoverySetting={
                "RecoveryMechanisms": [{"Priority": 1, "Name": "verified_email"}]
            },
        )
        user_pool_id = response["UserPool"]["Id"]
        print(f"User Pool creato con ID: {user_pool_id}")
        return user_pool_id
    except ClientError as e:
        print("Errore nella creazione del pool:", e)
        return None


def create_user_pool_client(user_pool_id):
    try:
        response = cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=COGNITO_CLIENT_NAME,
            GenerateSecret=False,
            ExplicitAuthFlows=[
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH",
                "ALLOW_USER_SRP_AUTH",
                "ALLOW_CUSTOM_AUTH",
            ],
            CallbackURLs=["http://localhost:3000/"],
            LogoutURLs=["http://localhost:3000/"],
        )
        client_id = response["UserPoolClient"]["ClientId"]
        print(f"User Pool Client creato con ID: {client_id}")
        return client_id
    except ClientError as e:
        print("Errore nella creazione del client:", e)
        return None


def create_identity_pool(user_pool_id, client_id):
    provider_name = f"cognito-idp.{AWS_REGION}.amazonaws.com/{user_pool_id}"
    try:
        response = identity.create_identity_pool(
            IdentityPoolName=COGNITO_IDENTITY_POOL_NAME,
            AllowUnauthenticatedIdentities=False,
            CognitoIdentityProviders=[
                {
                    "ProviderName": provider_name,
                    "ClientId": client_id,
                    "ServerSideTokenCheck": False,
                }
            ],
        )
        identity_pool_id = response["IdentityPoolId"]
        print(f"Identity Pool creato con ID: {identity_pool_id}")
        return identity_pool_id
    except ClientError as e:
        print("Errore nella creazione dell'identity pool:", e)
        return None


def export_config_to_file(user_pool_id, client_id, identity_pool_id):
    config = {
        "userPoolId": user_pool_id,
        "clientId": client_id,
        "identityPoolId": identity_pool_id,
    }
    with open("../cognito_config.json", "w") as f:
        json.dump(config, f, indent=4)
    print("Configurazione esportata in cognito_config.json")


if __name__ == "__main__":
    user_pool_id = get_user_pool_by_name(COGNITO_USER_POOL_NAME)
    if user_pool_id:
        print(f"User Pool già esistente con ID: {user_pool_id}")
    else:
        user_pool_id = create_user_pool()

    client_id = get_user_pool_client_by_name(user_pool_id, COGNITO_CLIENT_NAME)
    if client_id:
        print(f"User Pool Client già esistente con ID: {client_id}")
    else:
        client_id = create_user_pool_client(user_pool_id)

    identity_pool_id = get_identity_pool_by_name(COGNITO_IDENTITY_POOL_NAME)
    if identity_pool_id:
        print(f"Identity Pool già esistente con ID: {identity_pool_id}")
    else:
        identity_pool_id = create_identity_pool(user_pool_id, client_id)

    export_config_to_file(user_pool_id, client_id, identity_pool_id)
