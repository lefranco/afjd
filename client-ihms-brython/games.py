""" games """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

my_panel = html.DIV(id="games")

OPTIONS = ['create', 'join', 'add player', 'remove player', 'edit', 'delete']


def create_game():
    """ create_game """

    dummy = html.P("create game")
    my_sub_panel <= dummy


def join_game():
    """ join_game """

    dummy = html.P("join game")
    my_sub_panel <= dummy


def put_player_in_game():
    """ put_player_in_game """

    dummy = html.P("put player in game")
    my_sub_panel <= dummy


def remove_player_from_game():
    """ remove_player_from_game """

    dummy = html.P("remove player from game")
    my_sub_panel <= dummy


def edit_game():
    """ edit game """

    dummy = html.P("edit game")
    my_sub_panel <= dummy


def delete_game():
    """ delete_game """

    dummy = html.P("delete game")
    my_sub_panel <= dummy


my_panel = html.DIV(id="account")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:20%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel


def load_option(_, item_name) -> None:
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'create':
        create_game()
    if item_name == 'join':
        join_game()
    if item_name == 'add player':
        put_player_in_game()
    if item_name == 'remove player':
        remove_player_from_game()
    if item_name == 'edit':
        edit_game()
    if item_name == 'delete':
        delete_game()
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not)
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


# starts here
load_option(None, item_name_selected)


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
