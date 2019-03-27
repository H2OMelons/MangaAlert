import boto3
import asyncio
import aioboto3
import constants
from utilities import validate_menu_selection, print_menu, terminal_colors
from utilities import print_line_sep, errors, success

async def main():
  selections = ["View", "Edit", "Delete", "Finish"]
  menu_selection = -1
  dynamodb = aioboto3.client('dynamodb', endpoint_url = 'http://localhost:8000')
  while menu_selection != len(selections):
    print_menu(selections, True, terminal_colors.GREEN)
    menu_selection = input("Choose one of the menu selections: ")
    menu_selection = validate_menu_selection(menu_selection, range(1, len(selections) + 1))
    if menu_selection == 1:
      print(1)
    elif menu_selection == 2:
      manga_name = input("Enter the name of the manga you want to edit (-1 to exit): ")
    elif menu_selection == 3:
      manga_name = input("Enter the name of the manga you want to delete (-1 to exit): ")
      print('Retrieving info...')
      # Query dyamodb for all entries that match the manga name
      response = await dynamodb.query(
        ExpressionAttributeValues = {':m' : {'S' : manga_name}},
        KeyConditionExpression = 'manga_name = :m',
        TableName = 'manga_list'
      )
      mangas = response['Items']

      while response.get('LastEvaluatedKey'):
        response = await dynamodb.query(
          ExpressionAttributeValues = {':m' : {'S' : manga_name}},
          KeyConditionExpression = 'manga_name = :m',
          TableName = 'manga_list',
          ExclusiveStartKey = response['LastKeyEvaluated']
        )
        mangas.extend(response['Items'])
      # Display all the matches
      if len(mangas) > 0:
        print('Retrieved ' + str(len(mangas)) + ' matches...')
        # Prompt user to choose one
        for i in range(len(mangas)):
          print_line_sep()
          for att in constants.dynamodb_attributes:
            if mangas[i].get(att['key']):
              # If the attribute is the name, then add bolding and an index
              if att == constants.dynamodb_attributes[0]:
                print(str(i + 1) + '. ' + terminal_colors.BOLD + mangas[i].get(att['key'])[att['type']] + terminal_colors.END)
              else:
                print('\t' + att['key'] + ': ' + str(mangas[i].get(att['key'])[att['type']]))
        print_line_sep()
        print(str(len(mangas) + 1) + '. '+  terminal_colors.GREEN + 'Go Back' + terminal_colors.END)
        print_line_sep()

        # Keep asking for user selection until they enter a valid selection
        delete_selection = None
        while delete_selection == None:
          delete_selection = input('Select the manga you want to delete (Enter a number): ')
          delete_selection = validate_menu_selection(delete_selection, range(1, len(mangas) + 2))

        # If the user chose a manga, then delete it
        if delete_selection != len(mangas) + 1:
          delete_selection -= 1
          print('Deleting ' + mangas[delete_selection]['manga_name']['S'] + ' ...')
          hash_key = constants.dynamodb_attributes[constants.DB_HASH_KEY]['key']
          hash_type = constants.dynamodb_attributes[constants.DB_HASH_KEY]['type']
          range_key = constants.dynamodb_attributes[constants.DB_RANGE_KEY]['key']
          range_type = constants.dynamodb_attributes[constants.DB_RANGE_KEY]['type']
          response = await dynamodb.delete_item(
            Key={
              hash_key : {
                hash_type: mangas[delete_selection][hash_key][hash_type]
              },
              range_key : {
                range_type : mangas[delete_selection][range_key][range_type]
              }
            },
            TableName = 'manga_list'
          )
          success.print_success('Successfuly deleted ' + mangas[delete_selection][hash_key][hash_type])

      # If there are none, print that there are no matches
      else:
        errors.print_error('There are no mangas matching that name in the database')

  await dynamodb.close()


if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())
