""" games """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config

my_panel = html.DIV(id="games")

OPTIONS = ['join game', 'move player in game']


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


def join_game():
    """ join_game """

    dummy = html.P("join game")
    my_sub_panel <= dummy


def move_player_in_game():
    """ move_player_in_game """

    dummy = html.P("move_player_in_game")
    my_sub_panel <= dummy


my_panel = html.DIV(id="pairing")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:25%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'join game':
        join_game()
    if item_name == 'move player in game':
        move_player_in_game()
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


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
