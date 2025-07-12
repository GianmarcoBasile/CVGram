import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

load_dotenv()

AWS_REGION = os.getenv('REGION', 'eu-west-2')

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

def create_cv_table():
    try:
        table = dynamodb.create_table(
            TableName='CVs',
            KeySchema=[
                {'AttributeName': 'cv_id', 'KeyType': 'HASH'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'cv_id', 'AttributeType': 'S'},
                {'AttributeName': 'email', 'AttributeType': 'S'},
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'EmailIndex',
                    'KeySchema': [
                        {'AttributeName': 'email', 'KeyType': 'HASH'},
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print('Creazione tabella in corso...')
        table.meta.client.get_waiter('table_exists').wait(TableName='CVs')
        print('Tabella creata con successo!')
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print('La tabella esiste già.')
        else:
            print('Errore:', e)

if __name__ == '__main__':
    create_cv_table()
