
categories = [
  "Name",
  "User",
  "Most Recent Chapter",
  "Additional Filters"
]
category_types = [
  str, str, int, list
]

dynamodb_attributes = [
  {'key' : 'manga_name', 'type' : 'S'},
  {'key' : 'poster', 'type' : 'S'},
  {'key' : 'most_recent_chapter', 'type' : 'N'},
  {'key' : 'additional_filters', 'type' : 'L'},
  {'key' : 'ended', 'type' : 'BOOL'}
]

DB_HASH_KEY = 0
DB_RANGE_KEY = 1
