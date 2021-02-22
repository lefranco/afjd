""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config

my_panel = html.DIV(id="games")

OPTIONS = ['join game', 'quit game', 'move player in game']


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")

def get_player_id(pseudo):
    """ get_player_id """

    player_id = None

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting player identifier: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting player identifier: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        nonlocal player_id
        player_id = int(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/player-identifiers/{pseudo}"

    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return player_id


def get_game_id(name):
    """ get_game_id """

    game_id = None

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting game identifier: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting game identifier: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        nonlocal game_id
        game_id = int(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-identifiers/{name}"

    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_id


def join_game():
    """ join_game """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    def join_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error joining game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem joining game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Game joined : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        player_id = get_player_id(pseudo)
        if player_id is None:
            return

        game_id = get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'game_id': game_id,
            'player_id': player_id,
            'pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)


    form = html.FORM()

    input_join_game = html.INPUT(type="submit", value="join game")
    input_join_game.bind("click", join_game_callback)
    form <= input_join_game

    my_sub_panel <= form















def quit_game():
    """ quit_game """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    def quit_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error quitting game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem quitting game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Game quitted : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        player_id = get_player_id(pseudo)
        if player_id is None:
            return

        game_id = get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'game_id': game_id,
            'player_id': player_id,
            'pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # should be a delete but body in delete requests is more or less forbidden
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)


    form = html.FORM()

    input_quit_game = html.INPUT(type="submit", value="quit game")
    input_quit_game.bind("click", quit_game_callback)
    form <= input_quit_game

    my_sub_panel <= form














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
    if item_name == 'quit game':
        quit_game()
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


def render(panel_middle):
    """ render """
    load_option(None, item_name_selected)
    panel_middle <= my_panel
