import boto3
from utilities import print_menu, terminal_colors, validate_menu_selection
from utilities import print_line_sep

events = boto3.client('events')

def main():
  menu_choices = ['View', 'Edit', 'Delete', 'Finish']
  menu_selection = None
  while menu_selection == None or menu_selection != len(menu_choices):
    print_menu(menu_choices, True, terminal_colors.GREEN)
    menu_selection = input('Choose one of the menu selections: ')
    menu_selection = validate_menu_selection(menu_selection, range(1, len(menu_choices) + 1))

    if menu_selection == 1:
      view_cloudwatch_schedules()
    elif menu_selection == 2:
      edit_cloudwatch_schedules()
    elif menu_selection == 3:
      delete_cloudwatch_schedules()

def view_cloudwatch_schedules():
  rules = events.list_rules()
  rules = rules['Rules']
  print_rules(rules)

def edit_cloudwatch_schedules():
  print()

def delete_cloudwatch_schedules():
  print()

def print_rules(rules):
  for rule in rules:
    print_line_sep()
    print('Name: ' + rule['Name'])
    print('State: ' + rule['State'])
    print('Schedule: ' + rule['ScheduleExpression'])
  print_line_sep()

if __name__ == '__main__':
  main()
