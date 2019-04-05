import boto3
import os
import requests

dynamodb = None

if os.environ.get('ENV') == 'PROD':
  dynamodb = boto3.client('dynamodb')
else:
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

  # Build a dictionary where the key is a manga name and the value is
  # a list of indicies corresponding to the manga's index in the mangas array
  # Ex:
  #   mangas = [a, b, c, a]
  #   manga_name_tracker = {'a':[0,3], 'b':[1], 'c':[2]}
  manga_name_tracker = {}
  for i in range(len(mangas)):
    manga_name = mangas[i]['manga_name']['S']
    if manga_name_tracker.get(manga_name):
      manga_name_tracker[manga_name].append(i)
    else:
      manga_name_tracker[manga_name] = [i]

  # Dictionary where the key is the name of the manga that was updated and the
  # value is the new most recent chapter number
  updated = {}
  for manga in mangas:
    # Get the name of the manga
    og_manga_name = manga['manga_name']['S']

    # If already detected that the manga has been updated, skip to next manga
    if updated.get(og_manga_name):
      continue

    # Get the 10 most recent posts of the user
    submissions = requests.get(
      'https://api.pushshift.io/reddit/submission/search/',
      params = {
        'author' : manga['poster']['S'],
        'size' : 10,
        'before' : None,
        'sort' : 'desc',
        'sort_type' : 'created_utc'
      }
    )
    submissions = submissions.json()['data']
    for submission in submissions:
      title = submission['title'].lower()
      manga_name = og_manga_name.lower()
      current_chapter = int(manga['most_recent_chapter']['N']) + 1
      # If the user created a reddit post with the manga name and chapter in the title
      # It is probably the post for the weekly chapter
      if manga_name in title and str(current_chapter) in title and 'prediction' not in title:
        updated[og_manga_name] = current_chapter
        # Send text that new chapter has been posted
        if os.environ.get('ENV') == 'PROD':
          sns = boto3.client('sns')
          sns.publish(
            TopicArn = os.environ.get('MANGA_ALERT_ARN'),
            Message = og_manga_name + ' Chapter ' + str(current_chapter) + ' has been posted! \n' + submission['full_link']
          )
        else:
          print(submission['full_link'])

  # If a manga was updated, update all entries with the same name to have
  # the new most recent chapter
  for manga_name in updated:
    for manga_ind in manga_name_tracker[manga_name]:
      manga = mangas[manga_ind]
      response = dynamodb.update_item(
        TableName = 'manga_list',
        Key = {
          'manga_name' : manga['manga_name'],
          'poster' : manga['poster']
        },
        ExpressionAttributeNames = {
          '#M' : 'most_recent_chapter'
        },
        ExpressionAttributeValues = {
          ':m' : {'N' : str(int(manga['most_recent_chapter']['N']) + 1)}
        },
        UpdateExpression = 'SET #M = :m'
      )

if os.environ.get('ENV') != 'PROD':
  lambda_handler({},{})
