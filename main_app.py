from trello import TrelloApi
from random import shuffle
import datetime
import re
import _config

# Initialize Variables 
app_key = _config.app_key
user_token = _config.user_token
board_id = _config.board_id
shopping_list_column_id = _config.shopping_list_column_id
today = datetime.datetime.today()

# Initialize Arrays
card_id_list = []
checklist_id_list = []
column_id_list = []
dinner_card_list = []
item_list = []
days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday_2']
days_of_week_ids = _config.days_of_week_ids

# Initialize the trello api with app key and user token for write access and get board via board id
trello = TrelloApi(app_key, user_token)
trello.boards.get(board_id)


def get_trello_elements(board_element, requested_object, parent_id): #Returns a list of data based on the given trello board element, requested data, and parent id of board element
    if board_element == 'card':
        card_object_list = []
        card_list = trello.lists.get_card(parent_id) #parent_id should be a column id in this instance
        for card in card_list:
            card_object_list.append(card.get(requested_object))
        return card_object_list

    elif board_element == 'column':
        column_object_list = []
        column_list = trello.boards.get_list(parent_id) #parent_id should be a board id in this instance
        for column in column_list:
            column_object_list.append(column.get(requested_object))
        return column_object_list
    
    elif board_element == 'checklist':
        checklist_object_list = []
        checklist_id_list = trello.cards.get_checklist(parent_id) #parent_id should be a card id in this instance
        for checklist in checklist_id_list:
            checklist_object_list.append(checklist.get(requested_object))
        return checklist_object_list
    

def dinner_randomizer():
    reset_week()
    column_ids = [_config.dinner_id, _config.breakfast_id]
    for column in column_ids:
        column_card_ids = get_trello_elements('card', 'id', column)
        shuffle(column_card_ids)
        weekly_meals = [column_card_ids[i] for i in (0, 1, 2, 3, 4, 5, 6)]
        count = 0
        for meal in weekly_meals:
            trello.cards.update_idList(meal, days_of_week_ids[count])
            count += 1


def reset_week():  # Resets weekly meals (if present) and returns them to Dinner column
    for column in days_of_week_ids:
        dinner_card_json = trello.lists.get_card(column)
        for dict_2 in dinner_card_json:
            card_id = dict_2.get('id')
            card_name = dict_2.get('name')
            #print(card_id, card_name)
            if card_id == "":
                delete_old_shopping_list()
            elif 'DINNER' in card_name.upper():
                trello.cards.update_idList(card_id, _config.dinner_id)
            elif 'BREAKFAST' in card_name.upper():
                trello.cards.update_idList(card_id, _config.breakfast_id)



def delete_old_shopping_list():  # Gets current shopping list card ID and delete it
    shopping_list_array = trello.lists.get_card(shopping_list_column_id)
    if len(shopping_list_array) > 0:
        shopping_list_dict = shopping_list_array[0]
        shopping_list_card_id = shopping_list_dict.get('id')
        trello.cards.delete(shopping_list_card_id)
    else:
        get_column_ids()


def get_column_ids():  # Gets the column ids in each list
    lists = trello.boards.get_list(board_id)
    for column in lists:
        column_name = column.get('name')
        if column_name in days_of_week:
            column_id = column.get('id')
            column_id_list.append(column_id)


def get_card_ids():  # Get the card ids in each list
    for cards in column_id_list:
        card = trello.lists.get_card(cards)
        card_dict = card[0]
        checklist_id = card_dict.get('idChecklists')
        checklist_id_list.append(checklist_id)


def ingredient_consolidator(ingredient_list):

    shopping_list_dict = {}
    
    for item in ingredient_list:

        ingredient_letters = re.findall(r'[a-zA-Z\\:\sa-zA-Z]', item)
        ingredient_amount = re.findall(r'\d+\.?\d*', item)
        print(ingredient_amount)

        ingredient = "".join(ingredient_letters)
        ingredient_number = "".join(ingredient_amount)
        ingredient_float = float(ingredient_number)

        if ingredient in shopping_list_dict:
            shopping_list_dict[ingredient] += ingredient_float
        else:
            shopping_list_dict[ingredient] = ingredient_float

    return shopping_list_dict


def create_shopping_checklist():  # Create new card for shopping list, create new checklist on new shopping list card

    card_name = 'Shopping List ' + str(today.strftime('%Y' + '.' + '%m' + '.' + '%d'))

    trello.lists.new_card(shopping_list_column_id, card_name)
    shopping_list_array = trello.lists.get_card(shopping_list_column_id)
    shopping_list_dict = shopping_list_array[0]
    shopping_list_card_id = shopping_list_dict.get('id')
    trello.cards.new_checklist(shopping_list_card_id, 'shopping list')
    shopping_list_checklist_array = trello.cards.get_checklist(shopping_list_card_id)
    shopping_list_checklist_dict = shopping_list_checklist_array[0]
    shopping_list_checklist_id = shopping_list_checklist_dict.get('id')
    return shopping_list_checklist_id


def populate_shopping_list():
    shopping_checklist_id = create_shopping_checklist()
    for checklist in checklist_id_list:
        for checklist_ID in checklist:
            checklist_dict_1 = trello.checklists.get(checklist_ID)
            checklist_list_1 = checklist_dict_1.get('checkItems')
            for checklist_item in checklist_list_1:
                item = checklist_item.get('name')
                item_list.append(item)

    sorted_item_list = sorted(item_list)
    final_sorted_list = ingredient_consolidator(sorted_item_list)

    for item, value in final_sorted_list.items():
        items = (str(value) + ' ' + item)
        print(items)
        trello.checklists.new_checkItem(shopping_checklist_id, items)


def main():
    dinner_randomizer()
    delete_old_shopping_list()
    get_column_ids()
    get_card_ids()
    populate_shopping_list()
    print('\n' + 'Shopping list complete!')


main()

