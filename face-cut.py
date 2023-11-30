import json
import logging
import os
from PIL import Image
import io
from random import choice
from string import ascii_uppercase

import boto3
from botocore.exceptions import ClientError

QUEUE_URL = os.environ.get("QUEUE_URL")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION")

PHOTO_BUCKET_NAME = os.environ.get("PHOTO_BUCKET_NAME")
FACES_BUCKET_NAME = os.environ.get("FACES_BUCKET_NAME")

USER_STORAGE_URL = os.environ.get("USER_STORAGE_URL")
TABLE_NAME = os.environ.get("TABLE_NAME")


def create_photo(photo_key_id, original_photo_key_id, name, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=USER_STORAGE_URL,
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_ACCESS_KEY
        )

    table = dynamodb.Table(TABLE_NAME)

    response = table.put_item(
        Item={
            'photo_key_id': str(photo_key_id),
            'original_photo_key_id': str(original_photo_key_id),
            'name': str(name)
        }
    )

    return response


def handler(event, context):
    eventData = event['messages'][0]['details']['message']['body']

    s3 = boto3.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net/',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_ACCESS_KEY,
        region_name=AWS_REGION
    )

    jsonEventData = json.loads(eventData.replace("\'", "\""))
    originalKey = jsonEventData['originalKey']

    response_get = s3.get_object(Bucket=PHOTO_BUCKET_NAME, Key=originalKey)

    img = response_get['Body'].read()
    coords = jsonEventData['boundingBox']['vertices']

    original_image = Image.open(io.BytesIO(img))

    cropped_image = original_image.crop(
        (int(coords[0]['x']), int(coords[0]['y']), int(coords[2]['x']), int(coords[2]['y'])))

    img_byte_arr = io.BytesIO()
    cropped_image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    random_key = ''.join(choice(ascii_uppercase) for i in range(12))

    response_post = s3.put_object(Bucket=FACES_BUCKET_NAME, Key=random_key, Body=img_byte_arr)

    if response_post['ResponseMetadata']['HTTPStatusCode'] == 200:
        create_photo(random_key, originalKey, '')

        return {
            'statusCode': 200,
            'body': 'Hello World!',
        }

    return {
        'statusCode': 400,
        'body': 'Error',
    }