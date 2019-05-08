import boto3
import os
import requests
import time

dynamodb = None

if os.environ.get('ENV') == 'PROD':
  dynamodb = boto3.client('dynamodb')
else:
  dynamodb = boto3.client('dynamodb', endpoint_url = 'http://localhost:8000')

def lambda_handler(event, context):
  # number of milliseconds in a day
  NUM_MS_IN_DAY = 86400000
  DAILY_WAIT = 0.75
  WEEKLY_WAIT = 6
  BIWEEKLY_WAIT = 13
  MONTHLY_WAIT = 28
  CURRENT_TIME = int(round(time.time() * 1000))
  table_name = 'manga_list'
  filter_exp = ('ended = :e and ('
               'update_type=:o or '
               '(update_type=:d and #lut <= :dlut) or '
               '(update_type=:w and #lut <= :wlut) or '
               '(update_type=:b and #lut <= :blut) or '
               '(update_type=:m and #lut <= :mlut))')

  exp_att_val = {
    ':e' : {'BOOL' : False},
    ':o' : {'S' : 'other'},
    ':d' : {'S' : 'daily'},
    ':w' : {'S' : 'weekly'},
    ":b" : {'S' : 'biweekly'},
    ":m" : {'S' : 'monthly'},
    ':dlut' : {'N' : str(CURRENT_TIME - (NUM_MS_IN_DAY * DAILY_WAIT))},
    ':wlut' : {'N' : str(CURRENT_TIME - (NUM_MS_IN_DAY * WEEKLY_WAIT))},
    ':blut' : {'N' : str(CURRENT_TIME - (NUM_MS_IN_DAY * BIWEEKLY_WAIT))},
    ':mlut' : {'N' : str(CURRENT_TIME - (NUM_MS_IN_DAY * BIWEEKLY_WAIT))}
  }
  exp_att_name = {
    '#lut' : 'last_updated_time'
  }

  # Scan the dynamodb table for all mangas that have not ended yet
  # and has reached the time where it could be updated.
  # For example, for weekly mangas this is after 6 days so check
  # to see that current_time - 6days >= last updated time for that manga
  response = dynamodb.scan(
    TableName = table_name,
    FilterExpression = filter_exp,
    ExpressionAttributeValues = exp_att_val,
    ExpressionAttributeNames = exp_att_name
  )
  mangas = response['Items']
  # Keep scanning until all mangas have been retrieved
  while response.get('LastEvaluatedKey'):
    response = dynamodb.scan(
      TableName = table_name,
      FilterExpression = filter_exp,
      ExpressionAttributeValues = exp_att_val,
      ExpressionAttributeName = exp_att_name,
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

    submissions = []
    for subreddit in manga['subreddits']['L']:
      # Get the 10 most recent posts of the user
      submission = requests.get(
        'https://api.pushshift.io/reddit/search/submission',
        params = {
          'subreddit' : subreddit,
          'size' : 20,
          'before' : None,
          'sort' : 'desc',
          'sort_type' : 'created_utc'
        }
      )
      submission = submission.json()['data']
    submissions.extend(submission)
    # Array to keep track of links to the updated chapter
    links = []
    for submission in submissions:
      title = submission['title'].lower()
      manga_name = og_manga_name.lower()
      current_chapter = int(manga['most_recent_chapter']['N']) + 1
      # If the user created a reddit post with the manga name and chapter in the title
      # It is probably the post for the weekly chapter
      if manga_name in title and str(current_chapter) in title and 'prediction' not in title:
        updated[og_manga_name] = current_chapter
        links.append(submission['full_link'])

    if len(links) > 0:
      # Send text that new chapter has been posted
      if os.environ.get('ENV') == 'PROD':
        sns = boto3.client('sns')
        sns.publish(
          TopicArn = os.environ.get('MANGA_ALERT_ARN'),
          Message = og_manga_name + ' Chapter ' + str(current_chapter) + ' has been posted!' + ' '.join(links)
        )
      else:
        for link in links:
          print(link)


  # If a manga was updated, update all entries with the same name to have
  # the new most recent chapter
  for manga_name in updated:
    for manga_ind in manga_name_tracker[manga_name]:
      manga = mangas[manga_ind]
      response = dynamodb.update_item(
        TableName = 'manga_list',
        Key = {
          'manga_name' : manga['manga_name']
        },
        ExpressionAttributeNames = {
          '#M' : 'most_recent_chapter',
          '#T' : 'last_updated_time'
        },
        ExpressionAttributeValues = {
          ':m' : {'N' : str(updated[manga_name])},
          ':t' : {'N' : str(CURRENT_TIME)}
        },
        UpdateExpression = 'SET #M = :m, #T = :t'
      )

if os.environ.get('ENV') != 'PROD':
  lambda_handler({},{})
