import boto3
import sys

dynamodb = boto3.resource('dynamodb', endpoint_url = 'http://localhost:8000')
categories = [
  "Name",
  "User",
  "Upload Day",
  "Secondary Upload Day",
  "Most Recent Chapter",
  "Additional Filters"
]
upload_range = range(2,4)
category_types = [
  str, str, int, int, int, list
]
prompts = [
  "What is the name of the manga? ",
  "Who is the reddit user that posts the chapter? ",
  "Su=0,M=1,Tu=2,W=3,Th=4,F=5,Sa=6,unsure=-1 \nWhat day of the week is the chapter most often posted? ",
  "If it's not posted on the above day, what is the second most likely day? ",
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
  print_menu(main_menu)

  # Continue looping until user chooses 'Finish' option
  user_input = -1
  while user_input != FINISH:
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
  print_line_sep()

def edit_manga_list(manga_list):
  # Get a list of all the manga names that the user has added so far
  manga_names = [manga[categories[0]] for manga in manga_list]
  manga_names.append('Finish Editing')
  # Print a list of all the manga names
  manga_selection = -1
  # Keep asking for user input if user doesn't enter the index for 'Finish Editing'
  while manga_selection != len(manga_names):
    # Ask the user to enter the index of the manga that they want to edit
    print_menu(manga_names)
    manga_selection = input('Enter the number corresponding to the manga you want to edit: ')
    manga_selection = validate_menu_selection(manga_selection, range(1, len(manga_names) + 1))
    if manga_selection != None and manga_selection != len(manga_names):
      manga_selection -= 1
      category_selection = -1
      # List of manga info where each item is a string 'category: info'
      manga_info = [categories[i] + ': ' + str(manga_list[manga_selection - 1][categories[i]]) for i in range(len(categories))]
      manga_info.append('Go Back')
      while category_selection != len(manga_info):
        print_menu(manga_info)
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

def delete_from_manga_list(manga_list):
  # Get a list of all the manga names that the user has added to the list
  manga_names = [manga[categories[0]] for manga in manga_list]
  manga_names.append("Go Back")
  # Print them all as a menu
  manga_selection = -1
  while manga_selection != len(manga_names):
    print_menu(manga_names)
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


# Validates the (numeric) menu selection by trying to convert the
# given selection parameter into an int and checking if it is
# in the given range. If it doesn't satisfy both conditions, then an
# errors is printed and NONE is returned, otherwise, the selection casted
# into an int is returned
def validate_menu_selection(selection, selection_range):
  try:
    selection = int(selection)
    if selection not in selection_range:
      errors.print_error(errors.INV_SEL)
      selection = None
  except ValueError:
    errors.print_error(errors.NOT_NUM)
    selection = None
  return selection

# Validates the info that the user enters for a category
# If the category requires an int, checks that input is a number and makes sure
# it is in the right range
# If category requires a list, turns comma separated string into a list
def validate_info_input(info, category_index):
  if category_types[category_index] == int:
    try:
      info = int(info)
      # If the category is the update day, make sure its within range of -1 to 6
      if category_index == 2 or category_index == 3:
        if info not in range(-1, 7):
          errors.print_error(errors.INV_SEL)
          info = None
    except ValueError:
      errors.print_error(errors.NOT_NUM)
      info = None
  elif category_types[category_index] == list:
    info = info.split(',')
  return info

# Prints a menu on the terminal with the given menu items, with each
# item given an index in the order as in menu_items
#
# @param menu_items List of items that should be printed onto the
#                   terminal. Will be printed in the same order
#                   as they appear in the list.
def print_menu(menu_items):
  for i in range(len(menu_items)):
    print(str(i + 1) + '. ' + menu_items[i])

# Prints a 100 char width line of '-'
def print_line_sep():
  for i in range(100):
    print('-', end = '')
  print()

# Class to format the text printed onto the terminal
class terminal_colors:
  BLUE = '\033[94m'
  GREEN = '\033[92m'
  RED = '\033[91m'
  END = '\033[0m'

class errors:
  NOT_NUM = 'ERROR: Please enter a number'
  INV_SEL = 'ERROR: Please enter a valid selection'

  def print_error(error):
    print(terminal_colors.RED + error + terminal_colors.END)

class success:
  DELETE = "Manga was successfully deleted"

  def print_success(success):
    print(terminal_colors.GREEN + success + terminal_colors.END)

if __name__ == '__main__':
  main()
