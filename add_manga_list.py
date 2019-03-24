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
prompts = [
  "What is the name of the manga? ",
  "Who is the reddit user that posts the chapter? ",
  "What day of the week is the chapter most often posted? ",
  "If it's not posted on the above day, what is the second most likely day? ",
  "What is the most recent chapter number? ",
  "Enter any additional filters separated by commas: "
]
main_menu = [
  'Add Manga', 'View All', 'Edit Additions', 'Finish'
]
ASK_FOR_INPUT = 'Choose one of the menu selections: '
MAIN_MENU_STOP_COND = len(main_menu)

def main():
  manga_list = []
  print_menu(main_menu)

  # Continue looping until user chooses 'Finish' option
  user_input = -1
  while user_input != MAIN_MENU_STOP_COND:
    user_input = input(ASK_FOR_INPUT)
    # Try to convert user input into an integer. If it doesn't work,
    # print an error
    try:
      user_input = int(user_input)

      # If user input isn't valid, print an error
      if user_input <= 0 or user_input > MAIN_MENU_STOP_COND:
        print(terminal_colors.RED + 'ERROR: Please enter a valid selection' + terminal_colors.END)
    except:
      print(terminal_colors.RED + 'ERROR: Please enter a number' + terminal_colors.END)

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

if __name__ == '__main__':
  main()
