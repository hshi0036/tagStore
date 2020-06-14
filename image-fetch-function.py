import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('tagStoreDB')


def lambda_handler(event, context):
    objects = []
    if event['httpMethod'] == 'POST':
        data = json.loads(event['body'])
        objects = data['objects']

    records = table.scan()
    response = {}
    response['links'] = []
    for i in records['Items']:
        if set(objects) <= set(i['tags']):
            response['links'].append(i['url'])

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response)
    }
