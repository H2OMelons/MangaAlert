import boto3
import sys
import asyncio
import aioboto3
from utilities import print_menu, errors, success, terminal_colors
from utilities import print_line_sep, validate_menu_selection, validate_info_input
from constants import categories

upload_range = range(2,4)
prompts = [
  "What is the name of the manga? ",
  "Who is the reddit user that posts the chapter? ",
  "What is the most recent chapter number? ",
  "Enter any additional filters separated by commas (Press enter if none): "
]
main_menu = [
  'Add Manga', 'View All', 'Edit Additions', 'Delete an Addition', 'Finish'
]
ASK_FOR_INPUT = 'Choose one of the menu selections: '
# Selection options for the main menu
ADD = 1
VIEW = 2
EDIT= 3
DELETE = 4
FINISH = 5

def main():
  manga_list = []

  # Continue looping until user chooses 'Finish' option
  user_input = -1
  while user_input != FINISH:
    print_line_sep()
    print_menu(main_menu, True, terminal_colors.GREEN)
    user_input = input(ASK_FOR_INPUT)
    user_input = validate_menu_selection(user_input, range(1, len(main_menu) + 1))
    if user_input != None:
      # If user input isn't valid, print an error
      if user_input == ADD:
        add_manga(manga_list)
      elif user_input == VIEW:
        view_manga_list(manga_list)
      elif user_input == EDIT:
        edit_manga_list(manga_list)
      elif user_input == DELETE:
        delete_from_manga_list(manga_list)

  return manga_list

# Function performs asks user for info about the manga they want to add
# to the list
def add_manga(manga_list):
  manga_info = {}
  # Go through all the categories necessary and prompt the user for the info
  i = 0
  while i < len(categories):
    # Get the info for the category from the user
    manga_info[categories[i]] = input(prompts[i])
    manga_info[categories[i]] = validate_info_input(manga_info[categories[i]], i)

    if manga_info[categories[i]] != None:
      i += 1
  manga_list.append(manga_info)

# Prints out all the mangas and the related info that the user has added
# to the list in the current session to the terminal
def view_manga_list(manga_list):
  for manga in manga_list:
    print_line_sep()
    for category in manga:
      print(category + ': '  + str(manga[category]))

def edit_manga_list(manga_list):
  # Get a list of all the manga names that the user has added so far
  manga_names = [manga[categories[0]] for manga in manga_list]
  manga_names.append('Go Back')
  # Print a list of all the manga names
  manga_selection = -1
  # Keep asking for user input if user doesn't enter the index for 'Finish Editing'
  while manga_selection != len(manga_names):
    # Ask the user to enter the index of the manga that they want to edit
    print_menu(manga_names, True, terminal_colors.GREEN)
    manga_selection = input('Enter the number corresponding to the manga you want to edit: ')
    manga_selection = validate_menu_selection(manga_selection, range(1, len(manga_names) + 1))
    if manga_selection != None and manga_selection != len(manga_names):
      manga_selection -= 1
      category_selection = -1
      # List of manga info where each item is a string 'category: info'
      manga_info = [categories[i] + ': ' + str(manga_list[manga_selection - 1][categories[i]]) for i in range(len(categories))]
      manga_info.append('Go Back')
      while category_selection != len(manga_info):
        print_menu(manga_info, True, terminal_colors.GREEN)
        category_selection = input('Enter the number corresponding to what you want to edit: ')
        category_selection = validate_menu_selection(category_selection, range(1, len(manga_info) + 1))
        if category_selection != None and category_selection != len(manga_info):
          # Subtract one because indexing starts at one in the printed menu, but starts at 0 in arrays
          category_selection -= 1
          category_info = input(prompts[category_selection])
          category_info = validate_info_input(category_info, category_selection)
          if category_info != None:
            # Update manga_list to have the current info
            manga_list[manga_selection][categories[category_selection]] = category_info
            # Update manga info list for correct category selection menu
            manga_info[category_selection] = categories[category_selection] + ': ' + str(category_info)
            # If the user chose to update the name of the manga, also update the list containing
            # all the manga names that make up the selection menu for editing
            if category_selection == 0:
              manga_names[manga_selection] = category_info

# Displays the names of all the mangas that the user currently has on the list and prompts
# the user to choose one to delete
def delete_from_manga_list(manga_list):
  # Get a list of all the manga names that the user has added to the list
  manga_names = [manga[categories[0]] for manga in manga_list]
  manga_names.append("Go Back")
  # Print them all as a menu
  manga_selection = -1
  while manga_selection != len(manga_names):
    print_menu(manga_names, True, terminal_colors.GREEN)
    manga_selection = input('Enter the number corresponding to the manga you want to delete: ')
    manga_selection = validate_menu_selection(manga_selection, range(1, len(manga_names) + 1))
    # If user chooses 'Go Back' don't do anything
    if manga_selection == len(manga_names):
      continue
    if manga_selection != None:
      manga_selection -= 1
      confirmation = input('Are you sure you want to delete ' + manga_names[manga_selection] + ' (Y/N): ')
      confirmation = confirmation.lower()
      if confirmation == 'y' or confirmation == 'yes':
        # Remove the manga from the list of mangas and the list of manga names
        manga_list.pop(manga_selection)
        manga_names.pop(manga_selection)
        success.print_success(success.DELETE)

async def finish(manga_list):
  if len(manga_list) == 0:
    print('You didn\'t add any mangas. Ending program...')
  else:

    dynamodb = aioboto3.resource('dynamodb', endpoint_url = 'http://localhost:8000')
    #table = dynamo_resource.Table('manga_list')

    print('Preparing to insert into dynamodb...')
    # List of all batch write requests (each batch request is a list of at most 25 items)
    batch_write_list = []
    # List of items to write. Max length of 25 (dynamodb limit)
    batch_write_buffer = []
    for i in range(len(manga_list)):
      item = {}
      item['manga_name'] = manga_list[i][categories[0]]#{'S' : manga_list[i][categories[0]]}
      item['poster'] = manga_list[i][categories[1]]#{'S' : manga_list[i][categories[1]]}
      item['most_recent_chapter'] = manga_list[i][categories[2]]#{'N' : manga_list[i][categories[2]]}
      additional_filters = manga_list[i][categories[3]]
      if len(additional_filters) != 0:
        #filters = [{'S' : fil} for fil in manga_list[i][categories[3]]]
        item['additional_filters'] = additional_filters#{'L' : filters}
      item['ended'] = False #{'BOOL' : False}
      batch_write_buffer.append({'PutRequest' : {'Item' : item}})
      if len(batch_write_buffer) == 25:
        batch_write_list.append(batch_write_buffer)
        batch_write_buffer = []

    # If buffer is not empty, then add it to the list of requests
    if len(batch_write_buffer) != 0:
      batch_write_list.append(batch_write_buffer)
      batch_write_buffer = []


    # Write all the mangas in the list to dynamodb in batches of at most 25
    for batch in batch_write_list:
      response = await dynamodb.batch_write_item(RequestItems={'manga_list' : batch})
      unprocessed_items = response['UnprocessedItems']

      # Print all the mangas that were successfully added
      for put_request in batch:
        if not bool(unprocessed_items) or put_request not in unprocessed_items['manga_list']:
          success.print_success(put_request['PutRequest']['Item']['manga_name'] + success.ADD)

      # While there are still items not successfully inserted into dynamodb, sleep for 3 seconds then reattempt
      while len(unprocessed_items) > 0:
        errors.print_error(str(len(unprocessed_items)) + ' unsuccessfully added. Retrying in 3 seconds...')
        await asyncio.sleep(3)
        response = await dynamodb.batch_write_item(RequestItems=unprocessed_items)
        # Print all the mangas that were successfully added
        for put_request in unprocessed_items['manga_list']:
          if put_request not in response['UnprocessedItems']['manga_list']:
            success.print_success(put_request['PutRequest']['Item']['manga_name'] + success.ADD)
        unprocessed_items = response['UnprocessedItems']

    # Close the dynamodb connection
    await dynamodb.close()
    success.print_success("All mangas successfully added. Ending Program...")

if __name__ == '__main__':
  manga_list = main()
  loop = asyncio.get_event_loop()
  loop.run_until_complete(finish(manga_list))
