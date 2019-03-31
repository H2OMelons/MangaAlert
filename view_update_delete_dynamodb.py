import boto3
import asyncio
import aioboto3
import constants
import os
from utilities import validate_menu_selection, print_menu, terminal_colors
from utilities import print_line_sep, errors, success, get_terminal_dim
from utilities import validate_info_input

dynamodb = None
if os.environ.get('ENV') == 'PROD':
  dynamodb = aioboto3.client('dynamodb', region_name='us-west-2')
else:
  dynamodb = aioboto3.client('dynamodb', endpoint_url = 'http://localhost:8000')

async def main():
  selections = ["View", "Edit", "Delete", "Finish"]
  menu_selection = -1
  while menu_selection != len(selections):
    print_menu(selections, True, terminal_colors.GREEN)
    menu_selection = input("Choose one of the menu selections: ")
    menu_selection = validate_menu_selection(menu_selection, range(1, len(selections) + 1))
    if menu_selection == 1:
      # Get the total number of items in dynamodb db
      response = await dynamodb.scan(
        TableName = constants.TABLE_NAME,
        Select = 'COUNT'
      )
      num_items = response['Count']
      limit = 10
      # Scan for the first 10 items
      response = await dynamodb.scan(
        TableName = constants.TABLE_NAME,
        Limit = limit
      )
      mangas = response['Items']
      num_current_results = response['Count']
      print_manga_info(mangas)
      print('Displaying ' + str(num_current_results) + '/' + str(num_items) + ' results')

      load_more = True
      # Ask the user if they want to load more if there is still more to load
      while response.get('LastEvaluatedKey') and load_more and num_current_results < num_items:
        print_menu(['Load More', 'Finish'], True, terminal_colors.GREEN)
        menu_selection = input('Choose one of the menu selections: ')
        menu_selection = validate_menu_selection(menu_selection, range(1,3))
        if menu_selection == 1:
          load_more = True
          response = await dynamodb.scan(
            TableName = constants.TABLE_NAME,
            Limit = limit,
            ExclusiveStartKey = response['LastEvaluatedKey']
          )
          mangas = response['Items']
          num_current_results += response['Count']
          print_manga_info(mangas)
          print('Displaying ' + str(num_current_results) + '/' + str(num_items) + ' results')
        elif menu_selection == 2:
          load_more = False

    elif menu_selection == 2 or menu_selection == 3:
      manga_name = ''
      if menu_selection == 2:
        manga_name = input("Enter the name of the manga you want to edit (-1 to exit): ")
      elif menu_selection == 3:
        manga_name = input("Enter the name of the manga you want to delete (-1 to exit): ")
      if manga_name == '-1':
        continue
      print('Retrieving info...')
      # Query dyamodb for all entries that match the manga name
      mangas = await query_for_name(dynamodb, manga_name)
      # Display all the matches
      if len(mangas) > 0:
        print('Retrieved ' + str(len(mangas)) + ' matches...')
        # Print all the mangas that match the name the user searched for
        print_manga_info(mangas)
        # Print the 'Go Back' option
        print(str(len(mangas) + 1) + '. '+  terminal_colors.GREEN + 'Go Back' + terminal_colors.END)
        print_line_sep()
        # menu selection 2 is for editing while 3 is for deleting
        prompt = ''
        if menu_selection == 2:
          prompt = 'Select the manga you want to edit (Enter a number): '
        elif menu_selection == 3:
          prompt = 'Select the manga you want to delete (Enter a number): '
        # Keep asking for user selection until they enter a valid selection
        selection = None
        while selection == None:
          selection = input(prompt)
          selection = validate_menu_selection(selection, range(1, len(mangas) + 2))

        # If the user chose a manga, then delete it
        # len(mangas) + 1 is the 'Go Back' option. If it's chosen, don't do anything
        if selection != len(mangas) + 1:
          selection -= 1
          # Keep a copy of the old key before it is updated in case we need to delete
          # the related entry from dynamodb
          old_key = generate_db_key(mangas[selection])
          if menu_selection == 2:
            menu_items = [att['key'] for att in constants.dynamodb_attributes]
            menu_items.append('Finish')
            print_menu(menu_items, True, terminal_colors.GREEN)
            edit_selection = None
            changes = []
            # Keep asking the user for input as long as they don't select 'Finish'
            # or as long as they keep entering invalid input
            while edit_selection == None or edit_selection != len(menu_items):
              edit_selection = input('What would you like to edit (Enter a number): ')
              edit_selection = validate_menu_selection(edit_selection, range(1, len(menu_items) + 1))
              # If the user input was valid and was not the 'Finish' selection, update the
              # corresponding value if necessary
              if edit_selection != None and edit_selection != len(menu_items):
                edit_selection -= 1

                # Keep asking user for manga info until they enter a valid input
                edit_input = None
                while edit_input == None:
                  edit_input = input(constants.prompts[edit_selection])
                  edit_input = validate_info_input(edit_input, edit_selection)

                # The current value of the category that the user is editing
                hash_key = constants.dynamodb_attributes[edit_selection]['key']
                hash_type = constants.dynamodb_attributes[edit_selection]['type']
                current_val = mangas[selection].get(hash_key)

                if current_val != None:
                  current_val = current_val.get(hash_type)

                # Only apply the new value if it's necessary and if it's new
                if edit_input != None and current_val != edit_input:
                  # boto3 requires that all int values be stringified
                  if type(edit_input) == int:
                    edit_input = str(edit_input)
                  mangas[selection][hash_key] = {hash_type : edit_input}
                  changes.append(edit_selection)

            if len(changes) > 0:
              # If the user decided to change the manga name or the poster name, we need
              # to delete the item from dynamodb and put in a new item
              # (can't update the hash/range key in dynamodb)
              if constants.DB_HASH_KEY_INDEX in changes or constants.DB_RANGE_KEY_INDEX in changes:
                # Delete using `old_key` because the corresponding values in the mangas list was
                # overwritten with the new user inputted value. We need the old key to be able
                # to delete the old entry before inserting the new one
                response = await delete_from_db(dynamodb, old_key)
                response = await dynamodb.put_item(
                  TableName = constants.TABLE_NAME,
                  Item = mangas[selection]
                )
              # If the user didn't change the manga name or poster, can simply update
              # the item
              else:
                # Create a dictionary where the keys are the dynamodb att and the values are the new
                # corresponding values that the user edited
                expression_att_values = {}
                expression_att_names = {}
                update_expression = 'SET '
                for change in changes:
                  expression_att_names['#' + str(change)] = constants.dynamodb_attributes[change]['key']
                  value = mangas[selection][constants.dynamodb_attributes[change]['key']][constants.dynamodb_attributes[change]['type']]
                  if type(value) == list:
                    value = [{'S' : val} for val in value]
                  expression_att_values[':' + str(change)] = {
                    constants.dynamodb_attributes[change]['type'] : value
                  }
                  if update_expression != 'SET ':
                    update_expression += ','
                  update_expression += ' #' + str(change) + ' = :' + str(change)
                # Create an api call to update the item
                print(expression_att_values)
                print(expression_att_names)
                response = await dynamodb.update_item(
                  TableName = constants.TABLE_NAME,
                  Key = generate_db_key(mangas[selection]),
                  ExpressionAttributeNames = expression_att_names,
                  ExpressionAttributeValues = expression_att_values,
                  UpdateExpression = update_expression
                )
              success.print_success('Successfully edited ' + mangas[selection][constants.DB_HASH_KEY][constants.DB_HASH_TYPE])
            else:
              success.print_success('No changes detected...')
          elif menu_selection == 3:
            print('Deleting ' + mangas[selection]['manga_name']['S'] + ' ...')
            response = await delete_from_db(dynamodb, generate_db_key(mangas[selection]))
            success.print_success('Successfuly deleted ' + mangas[selection][constants.DB_HASH_KEY][constants.DB_HASH_TYPE])

      # If there are none, print that there are no matches
      else:
        errors.print_error('There are no mangas matching that name in the database')

  await dynamodb.close()

# Given a manga name, query dynamodb for all entries that has the same name and return them
async def query_for_name(dynamodb, manga_name):
  response = await dynamodb.query(
    ExpressionAttributeValues = {':m' : {'S' : manga_name}},
    KeyConditionExpression = 'manga_name = :m',
    TableName = constants.TABLE_NAME
  )
  mangas = response['Items']

  while response.get('LastEvaluatedKey'):
    response = await dynamodb.query(
      ExpressionAttributeValues = {':m' : {'S' : manga_name}},
      KeyConditionExpression = 'manga_name = :m',
      TableName = constants.TABLE_NAME,
      ExclusiveStartKey = response['LastKeyEvaluated']
    )
    mangas.extend(response['Items'])

  return mangas

async def delete_from_db(dynamodb, key):
  response = await dynamodb.delete_item(
    Key = key,
    TableName = constants.TABLE_NAME
  )

def generate_db_key(manga):
  key = {
    constants.DB_HASH_KEY : {
      constants.DB_HASH_TYPE : manga[constants.DB_HASH_KEY][constants.DB_HASH_TYPE]
    },
    constants.DB_RANGE_KEY : {
      constants.DB_RANGE_TYPE : manga[constants.DB_RANGE_KEY][constants.DB_RANGE_TYPE]
    }
  }
  return key

# Given a list of mangas retrieved from dynamodb, print all entries onto the terminal
def print_manga_info(mangas):
  for i in range(len(mangas)):
    print_line_sep()
    for att in constants.dynamodb_attributes:
      if mangas[i].get(att['key']):
        # If the attribute is the name, then add bolding and an index
        if att == constants.dynamodb_attributes[0]:
          print(str(i + 1) + '. ' + terminal_colors.BOLD + mangas[i].get(att['key'])[att['type']] + terminal_colors.END)
        # The additional filters list is a list of dictionaries. Turn it into a list of the values of the dictionaries
        # [{'S':'1'},{'S':'2'}] -> ['1', '2']
        elif att['type'] == 'L':
          arr = [item['S'] for item in mangas[i].get(att['key']).get(att['type'])]
          print('\t' + att['key'] + ': ' + str(arr))
        else:
          print('\t' + att['key'] + ': ' + str(mangas[i].get(att['key'])[att['type']]))
  print_line_sep()


if __name__ == '__main__':
  try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
  except Exception as e:
    print(e)
    loop.run_until_complete(dynamodb.close())
