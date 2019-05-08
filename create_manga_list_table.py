import boto3
import os

dynamodb = None
if os.environ.get('ENV') == 'PROD':
  dynamodb = boto3.resource('dynamodb')
else:
  dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')

table = dynamodb.create_table(
  TableName = 'manga_list',
  KeySchema = [
    {
      'AttributeName' : 'manga_name',
      'KeyType' : 'HASH'
    }
  ],
  AttributeDefinitions = [
    {
      'AttributeName' : 'manga_name',
      'AttributeType' : 'S'
    }
  ],
  ProvisionedThroughput = {
    'ReadCapacityUnits' : 5,
    'WriteCapacityUnits' : 5
  }
)
