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
    # Try to convert user input into an integer. If it doesn't work,
    # print an error
    try:
      user_input = int(user_input)

      # If user input isn't valid, print an error
      if user_input <= 0 or user_input > FINISH:
        errors.print_error(errors.INV_SEL)
      elif user_input == ADD:
        manga_info = {}
        # Go through all the categories necessary and prompt the user for the info
        i = 0
        while i < len(categories):
          # Get the info for the category from the user
          manga_info[categories[i]] = input(prompts[i])
          # If the category requires a number input, check to make sure the user
          # entered a number
          if category_types[i] == int:
            try:
              manga_info[categories[i]] = int(manga_info[categories[i]])
              # If the user enters something not between -1 and 6 for the upload
              # day then print an error and decrement the counter
              if i in upload_range and manga_info[categories[i]] not in range(-1, 7):
                errors.print_error(errors.INV_SEL)
                i -= 1
            except:
              # If the input was not a number, then print an error and decrement
              # the counter
              errors.print_error(errors.NOT_NUM)
              i -= 1
          # If the category requires a list, convert the comma separated
          # string into a list
          if category_types[i] == list:
            manga_info[categories[i]] = manga_info[categories[i]].split(',')
          i += 1
        manga_list.append(manga_info)
    except:
      errors.print_error(errors.NOT_NUM)

# Prints a menu on the terminal with the given menu items, with each
# item given an index in the order as in menu_items
#
# @param menu_items List of items that should be printed onto the
#                   terminal. Will be printed in the same order
#                   as they appear in the list.
def print_menu(menu_items):
  for i in range(len(menu_items)):
    print(str(i + 1) + '. ' + menu_items[i])

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

if __name__ == '__main__':
  main()
