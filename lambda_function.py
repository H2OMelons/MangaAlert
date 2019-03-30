import boto3
import asyncio
import aioboto3
import praw
import os
dynamodb = boto3.client('dynamodb', endpoint_url = 'http://localhost:8000')

def lambda_handler(event, context):
  table_name = 'manga_list'
  filter_exp = 'ended = :e'
  exp_att_val = {':e' : {"BOOL" : False}}

  # Scan the dynamodb table for all mangas that have not ended yet
  response = dynamodb.scan(
    TableName = table_name,
    FilterExpression = filter_exp,
    ExpressionAttributeValues = exp_att_val
  )
  mangas = response['Items']
  # Keep scanning until all mangas have been retrieved
  while response.get('LastEvaluatedKey'):
    response = dynamodb.scan(
      TableName = table_name,
      FilterExpression = filter_exp,
      ExpressionAttributeValues = exp_att_val,
      ExclusiveStartKey = resp.get('LastEvaluatedKey')
    )
    mangas.extend(response['Items'])

  client_id = os.environ.get('REDDIT_CLIENT_ID')
  client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
  password = os.environ.get('REDDIT_PASSWORD')
  user_agent = os.environ.get('REDDIT_USER_AGENT')
  username = os.environ.get('REDDIT_USERNAME')

  # Build an instance of praw (Reddit api wrapper)
  reddit = praw.Reddit(
    client_id = client_id,
    client_secret = client_secret,
    password = password,
    user_agent = user_agent,
    username = username
  )

  for manga in mangas:
    # Get the reddit user who posts the weekly chapter
    redditor = reddit.redditor(manga['poster']['S'])
    for submission in redditor.submissions.new(limit=10):
      title = submission.title.lower()
      og_manga_name = manga['manga_name']['S']
      manga_name = og_manga_name.lower()
      current_chapter = int(manga['most_recent_chapter']['N']) + 1
      # If the user created a reddit post with the manga name and chapter in the title
      # It is probably the post for the weekly chapter
      if manga_name in title and str(current_chapter) in title and 'prediction' not in title:
        print(submission.shortlink)
        sns = boto3.client('sns')
        sns.publish(
          TopicArn = os.environ.get('MANGA_ALERT_ARN'),
          Message = og_manga_name + ' Chapter ' + str(current_chapter) + ' has been posted! \n' + submission.shortlink
        )

lambda_handler({},{})
#loop = asyncio.get_event_loop()
#loop.run_until_complete(dynamodb.close())
