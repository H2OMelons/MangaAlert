import boto3
from utilities import print_menu, terminal_colors, validate_menu_selection
from utilities import print_line_sep, success, errors

events = boto3.client('events')

def main():
  menu_choices = ['View', 'Add', 'Edit', 'Delete', 'Finish']
  menu_selection = None
  while menu_selection == None or menu_selection != len(menu_choices):
    print_menu(menu_choices, True, terminal_colors.GREEN)
    menu_selection = input('Choose one of the menu selections: ')
    menu_selection = validate_menu_selection(menu_selection, range(1, len(menu_choices) + 1))

    if menu_selection == 1:
      view_cloudwatch_schedules()
    elif menu_selection == 2:
      add_cloudwatch_schedules()
    elif menu_selection == 3:
      edit_cloudwatch_schedules()
    elif menu_selection == 4:
      delete_cloudwatch_schedules()

def view_cloudwatch_schedules():
  rules = events.list_rules()
  rules = rules['Rules']
  print_rules(rules)

def add_cloudwatch_schedules():
  rule_name = input('Enter the name of the rule: ')
  cron = input('Enter the cron expression (in the format (* * * * * *) with the parenthesis)')
  state = input('Enter the state of the rule (enabled/disabled): ')
  state = state.upper()
  while state != 'ENABLED' and state != 'DISABLED':
    errors.print_error('Please enter enabled or disabled')
    state = input('Enter the state of the rule (enabled/disabled): ')
  description = input('Enter a description (press enter to leave blank): ')
  target_id = input('Enter the id of the target: ')
  target_arn = input('Enter the arn of the target: ')

  response = events.put_rule(
    Name = rule_name,
    ScheduleExpression = 'cron' + cron,
    State = state,
    Description = description
  )

  response = events.put_targets(
    Rule = rule_name,
    Targets = [
      {
        'Id' : target_id,
        'Arn' : target_arn
      }
    ]
  )

def edit_cloudwatch_schedules():
  rule_name = input('Enter the name of the rule you want to delete: ')

def delete_cloudwatch_schedules():
  rule_name = input('Enter the name of the rule you want to delete: ')
  # Get a list of all the targets of the rule we want to delete
  response = events.list_targets_by_rule(
    Rule = rule_name
  )
  targets = [target['Id'] for target in response['Targets']]
  next_token = response.get('NextToken')
  while next_token != None:
    response = events.list_targets_by_rule(
      Rule = rule_name,
      NextToken = next_token
    )
    next_token = response.get('NextToken')
    targets.extend([target['Id'] for target in response['Targets']])

  # Remove all the targets of the rule
  if len(targets) > 0:
    response = events.remove_targets(
      Rule = rule_name,
      Ids = targets
    )

    num_failed = response['FailedEntryCount']
    while num_failed > 0:
      response = events.remove_targets(
        Rule = rule_name,
        Ids = [target['TargetId'] for target in response['FailedEntries']]
      )
      num_failed = response['FailedEntryCount']

  # Now that all the targets are removed, we can delete the rule
  events.delete_rule(
    Name = rule_name,
    Force = True
  )
  success.print_success('Successfully deleted ' + rule_name)

def print_rules(rules):
  for rule in rules:
    print_line_sep()
    print('Name: ' + rule['Name'])
    print('State: ' + rule['State'])
    print('Schedule: ' + rule['ScheduleExpression'])
  print_line_sep()

if __name__ == '__main__':
  main()
