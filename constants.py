categories = [
  "Name",
  "User",
  "Most Recent Chapter",
  "Additional Filters"
]
category_types = [
  str, str, int, list, bool
]

dynamodb_attributes = [
  {'key' : 'manga_name', 'type' : 'S'},
  {'key' : 'poster', 'type' : 'S'},
  {'key' : 'most_recent_chapter', 'type' : 'N'},
  {'key' : 'additional_filters', 'type' : 'L'},
  {'key' : 'ended', 'type' : 'BOOL'}
]

prompts = [
  'What is the name of the manga? ',
  'Who is the reddit user that posts the chapter? ',
  'What is the most recent chapter number? ',
  'Enter any additional filters separated by commas (Press enter if none): ',
  'Has the manga ended? (Enter True/False): '
]

DB_HASH_KEY = 0
DB_RANGE_KEY = 1
