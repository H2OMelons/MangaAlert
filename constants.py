TABLE_NAME = 'manga_list'

categories = [
  "Name",
  "Subreddits",
  "Most Recent Chapter",
  "Update Type",
  "Additional Filters"
]
category_types = [
  str, str, int, str, list, bool
]

dynamodb_attributes = [
  {'key' : 'manga_name', 'type' : 'S'},
  {'key' : 'subreddits', 'type' : 'L'},
  {'key' : 'most_recent_chapter', 'type' : 'N'},
  {'key' : 'update_type', 'type' : 'S'},
  {'key' : 'additional_filters', 'type' : 'L'},
  {'key' : 'ended', 'type' : 'BOOL'}
]

prompts = [
  'What is the name of the manga? ',
  'Which subreddits is the chapter posted to? ',
  'What is the most recent chapter number? ',
  'What is the update type? (daily, weekly, biweekly, monthly, or other): ',
  'Enter any additional filters separated by commas (Press enter if none): ',
  'Has the manga ended? (Enter True/False): '
]

DB_HASH_KEY_INDEX = 0
DB_RANGE_KEY_INDEX = 1
DB_HASH_KEY = dynamodb_attributes[DB_HASH_KEY_INDEX]['key']
DB_HASH_TYPE = dynamodb_attributes[DB_HASH_KEY_INDEX]['type']
DB_RANGE_KEY = dynamodb_attributes[DB_RANGE_KEY_INDEX]['key']
DB_RANGE_TYPE = dynamodb_attributes[DB_RANGE_KEY_INDEX]['type']
