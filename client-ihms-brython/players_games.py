""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error

import config

my_panel = html.DIV(id="players")

OPTIONS = ['players', 'games']


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


def get_player_list():
    """ get_player_list """

    players_dict = None

    def reply_callback(req):
        nonlocal players_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            alert(f"Problem : {req_result['msg']}")
            return

        req_result = json.loads(req.text)
        players_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players"

    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return players_dict


def show_player_list():
    """ show_player_list """

    players_dict = get_player_list()

    if not players_dict:
        return

    players_table = html.TABLE()
    players_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    # TODO : make it possible to sort etc...
    for pseudo in sorted(players_dict.values()):
        row = html.TR()
        row.style = {
            "border": "solid",
        }
        col = html.TD(pseudo)
        col.style = {
            "border": "solid",
        }
        row <= col
        players_table <= row


    my_sub_panel <= players_table


def get_game_list():
    """ get_game_list """

    games_dict = None

    def reply_callback(req):
        nonlocal games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            alert(f"Problem : {req_result['msg']}")
            return

        req_result = json.loads(req.text)
        games_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games"

    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return games_dict


def show_game_list():
    """ show_game_list """

    games_dict = get_game_list()

    if not games_dict:
        return

    games_table = html.TABLE()
    games_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    # TODO : make it possible to sort etc...
    for game_name in sorted(games_dict.values()):
        row = html.TR()
        row.style = {
            "border": "solid",
        }
        col = html.TD(game_name)
        col.style = {
            "border": "solid",
        }
        row <= col
        games_table <= row


    my_sub_panel <= games_table


my_panel = html.DIV(id="players_games")
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
    if item_name == 'players':
        show_player_list()
    if item_name == 'games':
        show_game_list()

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
