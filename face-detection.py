import boto3
import requests
import base64
import os


QUEUE_URL = os.environ.get("QUEUE_URL")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION")

TOKEN = os.environ.get("TOKEN")
FOLDER_KEY = os.environ.get("FOLDER_KEY")

def send_message_to_queue(message_body):
    sqs = boto3.resource(
        service_name='sqs',
        endpoint_url='https://message-queue.api.cloud.yandex.net',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_ACCESS_KEY,
        region_name=AWS_REGION
    ).Queue(QUEUE_URL)

    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=message_body
    )

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Message sent successfully")
    else:
        print(f"Failed to send message. Status code: {response['ResponseMetadata']['HTTPStatusCode']}")


def handler(event, context):
    bucket_name = event['messages'][0]['details']['bucket_id']
    object_key = event['messages'][0]['details']['object_id']

    session = boto3.session.Session()

    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_ACCESS_KEY
    )

    obj = s3.get_object(Bucket=bucket_name, Key=object_key)

    image_data = obj['Body'].read()
    encoded_image = base64.b64encode(image_data)

    response = requests.post(
        url='https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze',
        headers={
            'Authorization': f'Bearer {TOKEN}',
            'x-folder-id': FOLDER_KEY
        },
        json={
            "folderId": FOLDER_KEY,
            "analyze_specs": [
                {
                    "content": encoded_image.decode('utf-8'),
                    "features": [
                        {
                            "type": "FACE_DETECTION"
                        }
                    ]
                }
            ]
        }
    )

    print(response)

    if response.ok:
        data = response.json()
        faces = data['results'][0]['results'][0]['faceDetection']['faces']

        print('ok')
        print(f'Обнаружено {len(faces)}')
        for face in faces:
            print(face)
            send_message_to_queue(str({
                'boundingBox': face['boundingBox'],
                'originalKey': object_key
            }))

    else:
        print(f'Произошла ошибка {response.text}')

    return {
        'statusCode': 200,
        'body': 'Hello World!',
    }
