import boto3

dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')

table = dynamodb.create_table(
  TableName = 'manga_list',
  KeySchema = [
    {
      'AttributeName' : 'day_of_week',
      'KeyType' : 'HASH'
    },
    {
      'AttributeName' : 'manga_name',
      'KeyType' : 'RANGE'
    }
  ],
  AttributeDefinitions = [
    {
      'AttributeName' : 'day_of_week',
      'AttributeType' : 'N'
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
