import boto3
import os
import datetime
import praw

dynamodb = None

if os.environ.get('ENV') == 'PROD':
  dynamodb = boto3.client('dynamodb')
else:
  dynamodb = boto3.client('dynamodb', endpoint_url = 'http://localhost:8000')

def lambda_handler(event, context):
  table_name = 'manga_list'
  lambda_client = None
  arn = ''
  # Get UTC time and subtract 6 minutes
  utc_time = (datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds()
  utc_time -= 60 * 6

  if os.environ.get('ENV') == 'PROD':
    lambda_client = boto3.client('lambda')
    arn = os.environ.get('MANGA_ALERT_LAMBDA_ARN')
    tags = lambda_client.list_tags(
      Resource = arn
    )
    tags = tags['Tags']
    utc_time = int(tags['last_retrieved_time'])

  # Create an instance of the reddit client using praw
  client_id = os.environ.get('REDDIT_CLIENT_ID')
  client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
  refresh_token = os.environ.get('REDDIT_REFRESH_TOKEN')
  user_agent = os.environ.get('REDDIT_USER_AGENT')

  reddit = praw.Reddit(
    client_id = client_id,
    client_secret = client_secret,
    refresh_token = refresh_token,
    user_agent = user_agent
  )

  print("Retrieving items from DynamoDB")
  response = dynamodb.scan(TableName = table_name)
  mangas = response['Items']
  # Keep scanning until all mangas have been retrieved
  while response.get('LastEvaluatedKey'):
    response = dynamodb.scan(
      TableName = table_name,
      ExclusiveStartKey = response.get('LastEvaluatedKey')
    )
    mangas.extend(response['Items'])

  # Create a dictionary of the mangas where the key is the name and
  # the value is the most recent chapter
  manga_dict = {}

  for manga in mangas:
    name = manga['manga_name']['S']
    most_recent_chapter = int(manga['most_recent_chapter']['N'])
    manga_dict[name] = most_recent_chapter

  # Dictionary where the key is the name of the manga that was updated and the
  # value is the new most recent chapter number
  updated = {}

  # Array to keep track of links to the updated chapter
  links = []

  update_lambda_tag = True
  last_retrieved_time = ''
  disc_submissions = []
  print('Getting most recent posts from /r/manga')
  # Loop through 15 most recent posts in manga subreddit
  for submission in reddit.subreddit('manga').new(limit=15):
    if update_lambda_tag:
      update_lambda_tag = False
      last_retrieved_time = str(int(submission.created_utc + 1))
    tag = submission.link_flair_text
    if type(tag) == str and tag.lower() == 'disc':
      disc_submissions.append(vars(submission))

  # Go through all the submissions from oldest to newest
  for i in range(len(disc_submissions) - 1, -1, -1):
    submission = disc_submissions[i]

    title = submission['title'].lower()

    for manga, chapter in manga_dict.items():
      if manga not in updated and manga in title and str(chapter + 1) in title:
        updated[manga] = chapter + 1
        links.append({
          'url' : submission['url'],
          'msg' : manga + ' Chapter ' + str(chapter + 1)
        })

  if len(links) > 0:
    print('Sending update SMS')
    # Send text that new chapter has been posted
    if os.environ.get('ENV') == 'PROD':
      text_msg = 'MANGALERT: New Chapters Have Been Posted! \n'
      for link in links:
        text_msg += link['msg'] + '\n' + link['url'] + '\n'
      sns = boto3.client('sns')
      sns.publish(
        TopicArn = os.environ.get('MANGA_ALERT_ARN'),
        Message = text_msg
      )
    else:
      for link in links:
        print(link)

  # Update the tag with the newest time
  if os.environ.get('ENV') == 'PROD':
    print('Updating tag')
    lambda_client.tag_resource(
      Resource = arn,
      Tags = {
        'last_retrieved_time' : last_retrieved_time
      }
    )

  # If a manga was updated, update all entries with the same name to have
  # the new most recent chapter
  for manga_name in updated:
    response = dynamodb.update_item(
      TableName = 'manga_list',
      Key = {
        'manga_name' : {"S" : manga_name}
      },
      ExpressionAttributeNames = {
        '#M' : 'most_recent_chapter'
      },
      ExpressionAttributeValues = {
        ':m' : {'N' : str(updated[manga_name])}
      },
      UpdateExpression = 'SET #M = :m'
    )

if os.environ.get('ENV') != 'PROD':
  lambda_handler({},{})
