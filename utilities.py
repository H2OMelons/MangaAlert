import os
from constants import categories, category_types

# Prints a menu on the terminal with the given menu items, with each
# item given an index in the order as in menu_items
#
# @param menu_items List of items that should be printed onto the
#                   terminal. Will be printed in the same order
#                   as they appear in the list.
# @param highlight_last If True, then the last item in the list will be
#                       highlighted when printed
# @param color The color of the hihglighted text
def print_menu(menu_items, highlight_last, color):
  for i in range(len(menu_items)):
    if i == len(menu_items) - 1 and highlight_last:
      print(color + str(i + 1) + '. ' + menu_items[i] + terminal_colors.END)
    else:
      print(str(i + 1) + '. ' + menu_items[i])

# Class to format the text printed onto the terminal
class terminal_colors:
  BLUE = '\033[94m'
  GREEN = '\033[92m'
  RED = '\033[91m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'
  END = '\033[0m'

class errors:
  NOT_NUM = 'ERROR: Please enter a number'
  INV_SEL = 'ERROR: Please enter a valid selection'

  def print_error(error):
    print(terminal_colors.RED + error + terminal_colors.END)

class success:
  DELETE = "Manga was successfully deleted"
  ADD = " was successfully added"

  def print_success(success):
    print(terminal_colors.GREEN + success + terminal_colors.END)
  END = '\033[0m'

# Returns a tuple where the first item is the number of rows and the
# second item is the number of columns of the terminal
def get_terminal_dim():
  (rows, cols) = os.popen('stty size', 'r').read().split()
  return (rows, cols)

# Prints a 100 char width line of '-'
def print_line_sep():
  cols = get_terminal_dim()[1]
  for i in range(int(cols)):
    print('-', end='')
  print()

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
    except ValueError:
      errors.print_error(errors.NOT_NUM)
      info = None
  elif category_types[category_index] == list:
    if info != '':
      info = info.split(',')
    else:
      info = []
  elif category_types[category_index] == bool:
    if info.lower() == 't' or info.lower() == 'true':
      info = True
    elif info.lower() == 'f' or info.lower() == 'false':
      info = False
    else:
      info = None
  return info

