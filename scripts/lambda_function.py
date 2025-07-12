import boto3
import time
import logging
import urllib.parse

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    textract = boto3.client('textract')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('CVs')

    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(record['s3']['object']['key'])

    # Logga info file
    s3 = boto3.client('s3')
    head = s3.head_object(Bucket=bucket, Key=key)
    logger.info(f"Bucket: {bucket}, Key: {key}, Size: {head['ContentLength']} bytes, Content-Type: {head['ContentType']}")

    time.sleep(2)
    
    # Textract
    response = textract.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}}
    )
    
    logger.info(f"Risposta Textract: {response}")
    
    # Estrazione testo
    lines = [item.get('Text', '') for item in response['Blocks'] if item['BlockType'] == 'LINE']
    if lines:
        text = ' '.join(lines)
    else:
        words = [item.get('Text', '') for item in response['Blocks'] if item['BlockType'] == 'WORD']
        text = ' '.join(words)
    logger.info(f"Testo estratto: {text[:200]}...")
    logger.info(f"User Email: {head['Metadata']}")

    # Carica i dati su DynamoDB
    table.put_item(Item={
        'cv_id': key,
        'email': head['Metadata'].get('email'),
        'original_filename': head['Metadata'].get('originalname', key),
        'uploaded_at': head['Metadata'].get('uploaddate'),
        's3_key': key,
        'text': text.lower(),
    })

    return {'status': 'ok', 'text': text}
