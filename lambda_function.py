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
  table_name = 'manga_list'

  response = dynamodb.scan(TableName = table_name)
  mangas = response['Items']
  # Keep scanning until all mangas have been retrieved
  while response.get('LastEvaluatedKey'):
    response = dynamodb.scan(
      TableName = table_name,
      ExclusiveStartKey = response.get('LastEvaluatedKey')
    )
    mangas.extend(response['Items'])

  # Create list of subreddits
  # Each subreddit entry has a list. Each entry in the list is a dictionary that contains
  # The manga name, most recent chapter, and additional filters to apply
  subreddits_list = {}
  for manga in mangas:
    for subreddit in manga['subreddits']['L']:
      subreddit = subreddit['S']
      additional_filters = []
      if manga.get('additional_filters'):
        additional_filters = {x['M']['subreddit']['S'] : x['M'] for x in manga['additional_filters']['L']}

      manga_item = {
        'name' : manga['manga_name']['S'].lower(),
        'most_recent_chapter' : manga['most_recent_chapter']['N'],
        'additional_filters' : additional_filters
      }

      if subreddits_list.get(subreddit):
        subreddits_list[subreddit].append(manga_item)
      else:
        subreddits_list[subreddit] = [manga_item]

  # Dictionary where the key is the name of the manga that was updated and the
  # value is the new most recent chapter number
  updated = {}

  # Array to keep track of links to the updated chapter
  links = []

  # Loop through all subreddits and get the newest 20 posts
  for subreddit in subreddits_list:
    # Get all the mangas that we want to check if a new chapter has been
    # posted to the subreddit
    mangas_list = subreddits_list[subreddit]
    # Remove all mangas that we already found updates for (in other subreddits)
    i = 0
    while i < len(mangas_list):
      if updated.get(mangas_list[i]['name']):
        mangas_list.pop(i)
        i -= 1
      i += 1

    # If we already found updates for all mangas that we want to check for in this
    # subreddit, skip the subreddit
    if len(mangas_list) == 0:
      continue

    # Get the posts made in the last 6 minutes
    submissions = []
    submission = requests.get(
      'https://api.pushshift.io/reddit/search/submission',
      params = {
        'subreddit' : subreddit,
        'size' : 20,
        'after' : int(time.time()) - 660,
        'sort' : 'asc',
        'sort_type' : 'created_utc'
      }
    )
    submission = submission.json()['data']
    submissions.extend(submission)

    # Loop through all posts to the subreddit and check the titles to see if
    # it is the new chapter for the mangas we are looking for
    for submission in submissions:
      title = submission['title'].lower()

      for manga in mangas_list:
        manga_name = manga['name']
        if updated.get(manga_name):
          continue
        current_chapter = int(manga['most_recent_chapter']) + 1
        additional_filters = manga['additional_filters']
        additional_filters = additional_filters[subreddit] if additional_filters.get(subreddit) else {}
        # or filters are keywords where we want at least one to appear in the title
        or_filters = [manga_name]
        if additional_filters.get('or'):
          or_filters.extend([x['S'] for x in additional_filters['or']['L']])
        # and filters are keywords, where we want ALL the keywords in the list to appear in the title
        and_filters = [str(current_chapter)]
        if additional_filters.get('and'):
          and_filters.extend(x['S'] for x in additional_filters['and']['L'])
        # Exclude filters are keywords that tell us that the post is not the one we want
        exclude_filters = []
        if additional_filters.get('exclude'):
          exclude_filters = [x['S'] for x in additional_filters['exclude']['L']]

        # If any of the exclude filters are in the title, then this post is not the one we wnat
        # so continue
        exclude_found = False
        for exclude in exclude_filters:
          if exclude in title:
            exclude_found = True
            break

        # If any of the and filters are not in the title, continue
        and_found = False
        for a_filter in and_filters:
          if a_filter not in title:
            and_found = True
            break

        # If none of the or filters is in title, title isn't the one we want
        or_found = True
        for o_filter in or_filters:
          if o_filter in title:
            or_found = False
            break

        # If the title met all conditions, then it is the one we want
        if not exclude_found and not and_found and not or_found:
          updated[manga_name] = current_chapter
          links.append({
            'url' : submission['full_link'],
            'msg'  : manga_name + ' Chapter ' + str(current_chapter)
          })

  if len(links) > 0:
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
