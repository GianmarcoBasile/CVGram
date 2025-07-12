
import boto3
from botocore.exceptions import ClientError
import json

region = 'eu-west-2'
s3_bucket = 'cvgram-cv-bucket'

session = boto3.Session(region_name=region)
cognito = session.client('cognito-idp')
identity = session.client('cognito-identity')
iam = session.client('iam')

def create_user_pool():
    try:
        response = cognito.create_user_pool(
            PoolName='CVGramUserPool',
            AutoVerifiedAttributes=['email'],
            UsernameAttributes=['email'],
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': False,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            },
            AccountRecoverySetting={
                'RecoveryMechanisms': [
                    {'Priority': 1, 'Name': 'verified_email'}
                ]
            }
        )
        user_pool_id = response['UserPool']['Id']
        print(f"User Pool creato con ID: {user_pool_id}")
        return user_pool_id
    except ClientError as e:
        print('Errore nella creazione del pool:', e)
        return None

def create_user_pool_client(user_pool_id):
    try:
        response = cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='CVGramFrontendClient',
            GenerateSecret=False,
            ExplicitAuthFlows=[
                'ALLOW_USER_PASSWORD_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH',
                'ALLOW_USER_SRP_AUTH',
                'ALLOW_CUSTOM_AUTH'
            ],
            AllowedOAuthFlows=['code', 'implicit'],
            AllowedOAuthScopes=['email', 'openid', 'profile'],
            AllowedOAuthFlowsUserPoolClient=True,
            CallbackURLs=['http://localhost:3000/'],
            LogoutURLs=['http://localhost:3000/']
        )
        client_id = response['UserPoolClient']['ClientId']
        print(f"User Pool Client creato con ID: {client_id}")
        return client_id
    except ClientError as e:
        print('Errore nella creazione del client:', e)
        return None
    

def create_identity_pool(user_pool_id, client_id):
    identity_pool_name = 'CVGramIdentityPool'
    provider_name = f'cognito-idp.{region}.amazonaws.com/{user_pool_id}'
    try:
        response = identity.create_identity_pool(
            IdentityPoolName=identity_pool_name,
            AllowUnauthenticatedIdentities=False,
            CognitoIdentityProviders=[{
                'ProviderName': provider_name,
                'ClientId': client_id,
                'ServerSideTokenCheck': False
            }]
        )
        identity_pool_id = response['IdentityPoolId']
        print(f"Identity Pool creato con ID: {identity_pool_id}")
        return identity_pool_id
    except ClientError as e:
        print('Errore nella creazione dell\'identity pool:', e)
        return None



def export_config_to_file(user_pool_id, client_id, identity_pool_id):
    config = {
        'userPoolId': user_pool_id,
        'clientId': client_id,
        'identityPoolId': identity_pool_id
    }
    with open('../cognito_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print("Configurazione esportata in cognito_config.json")

if __name__ == "__main__":
    user_pool_id = create_user_pool()
    client_id = create_user_pool_client(user_pool_id)
    identity_pool_id = create_identity_pool(user_pool_id, client_id)
    export_config_to_file(user_pool_id, client_id, identity_pool_id)
