import json
import requests
import boto3
from botocore.exceptions import ClientError
import os

FUNC_RESPONSE = {
    'statusCode': 200,
    'body': ''
}

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

API_GATEWAY = os.environ.get("API_GATEWAY")

USER_STORAGE_URL = os.environ.get("USER_STORAGE_URL")
USER_ORIGIN_STORAGE_URL = os.environ.get("USER_ORIGIN_STORAGE_URL")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")


def send_message(text, message):
    message_id = message['message_id']
    chat_id = message['chat']['id']
    reply_message = {'chat_id': chat_id,
                     'text': text,
                     'reply_to_message_id': message_id}

    requests.post(url=f'{TELEGRAM_API_URL}/sendMessage', json=reply_message)

def send_message_by_chat_id(text, chat_id):
    reply_message = {
        'chat_id': chat_id,
        'text': text
    }

    requests.post(url=f'{TELEGRAM_API_URL}/sendMessage', json=reply_message)


def send_photo(key, message):
    chat_id = message['chat']['id']
    print(chat_id)
    params = {'chat_id': chat_id}

    file = requests.get(url=f'{API_GATEWAY}/{key}')
    files = {'photo': file.content}

    requests.post(url=f'{TELEGRAM_API_URL}/sendPhoto', params=params, files=files)


def get_photos_by_name(name, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=USER_STORAGE_URL,
            region_name='ru-central1',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

    table = dynamodb.Table('photo_data')

    try:
        response = table.scan()['Items']
        return list(filter(lambda c: c['name'] == name, response))

    except ClientError as e:
        print(e.response['Error']['Message'])


def post_name_by_empty_face(name, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url=USER_STORAGE_URL,
            region_name='ru-central1',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

    table = dynamodb.Table('photo_data')

    try:
        response = table.scan()['Items']
        empty_faces = list(filter(lambda c: c['name'] == '', response))
        key_id = empty_faces[0]['photo_key_id']
        find_item_response = table.get_item(Key={'photo_key_id': key_id})
        item = find_item_response['Item']
        item['name'] = name
        table.put_item(Item=item)

    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response


def get_photos(name, chat_id):
    items = get_photos_by_name(name)

    if len(items) == 0:
        return send_message_by_chat_id(f"Фотографии с {name} не найдены", chat_id)

    s3 = boto3.client(
        service_name='s3',
        endpoint_url=USER_ORIGIN_STORAGE_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    for item in items:
        response_get = s3.get_object(Bucket='vvot01-photo', Key=item['original_photo_key_id'])
        img = response_get['Body'].read()

        params = {'chat_id': chat_id}
        files = {'photo': img}
        requests.post(url=f'{TELEGRAM_API_URL}/sendPhoto', params=params, files=files)


def get_no_name_photo(message):
    item = get_photos_by_name('')[0]
    photo_key = item['photo_key_id']
    send_photo(photo_key, message)


def handler(event, context):
    print(event)
    if TELEGRAM_BOT_TOKEN is None:
        return FUNC_RESPONSE

    update = json.loads(event['body'])

    print(event)
    if 'message' not in update:
        return FUNC_RESPONSE

    message_in = update['message']

    if 'text' in message_in:
        text = message_in['text']

        if 'entities' in message_in:
            entity_type = message_in['entities'][0]['type']

            if entity_type == 'bot_command':
                if text.startswith('/start'):
                    send_message('Далее', message_in)

                if text.startswith('/find'):
                    print('find')
                    name = text.replace('/find ', '')
                    get_photos(name, message_in['chat']['id'])

                elif text.startswith('/getface'):
                    print('get face')
                    update = json.loads(event['body'])
                    message_in = update['message']
                    get_no_name_photo(message_in)

        else:
            print('post photo')
            post_name_by_empty_face(text)

    return FUNC_RESPONSE