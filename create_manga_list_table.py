import boto3

dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')

table = dynamodb.create_table(
  TableName = 'manga_list',
  KeySchema = [
    {
      'AttributeName' : 'poster',
      'KeyType' : 'HASH'
    },
    {
      'AttributeName' : 'manga_name',
      'KeyType' : 'RANGE'
    }
  ],
  AttributeDefinitions = [
    {
      'AttributeName' : 'poster',
      'AttributeType' : 'S'
    },
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
