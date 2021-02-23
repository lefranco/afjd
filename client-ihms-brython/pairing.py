""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config

my_panel = html.DIV(id="games")

OPTIONS = ['join game', 'quit game', 'move players in game']


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


def get_players():
    """ get_players """

    players_dict = None

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting players: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting players: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        req_result = json.loads(req.text)
        nonlocal players_dict
        players_dict = {v['pseudo']: int(k) for k, v in req_result.items()}

    json_dict = dict()

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players"

    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return players_dict


def get_game_allocated_players(game_id):
    """ get_available_players """

    players_dict = None

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting game allocated players: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting game allocated players: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        req_result = json.loads(req.text)
        nonlocal players_dict
        players_dict = [int(k) for k, v in req_result.items() if v != 0]

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-allocations/{game_id}"

    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return players_dict


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


def move_players_in_game():
    """ move_players_in_game """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    def put_in_game_callback(_):
        """ put_in_game_callback """

        def reply_callback(req):
            """ reply_callback """

            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error putting player in game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem putting player in game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Player was put in game: {req_result['msg']}", remove_after=config.REMOVE_AFTER)
            # back to where we started
            move_players_in_game()

        player_pseudo = input_incomer.value
        player_id = get_player_id(player_pseudo)
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

    def remove_from_game_callback(_):
        """remove_from_game_callback"""

        def reply_callback(req):
            """ reply_callback """

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error removing player from game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem removing player from game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Player was removed from game: {req_result['msg']}", remove_after=config.REMOVE_AFTER)
            # back to where we started
            move_players_in_game()

        player_pseudo = input_outcomer.value
        player_id = get_player_id(player_pseudo)
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

        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    players_dict = get_players()
    if players_dict is None:
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    game_id = get_game_id(game)
    if game_id is None:
        return

    players_allocated_id_list = get_game_allocated_players(game_id)
    if players_allocated_id_list is None:
        return

    players_allocated_list = [id2pseudo[i] for i in list(players_allocated_id_list)]

    form = html.FORM()

    # ---

    legend_incomer = html.LEGEND("Incoming", title="Select player to put in game")
    legend_incomer.style = {
        'color': 'red',
    }
    form <= legend_incomer

    possible_incomers = set(players_dict.keys()) - set(players_allocated_list)

    input_incomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_incomers):
        option = html.OPTION(play_pseudo)
        input_incomer <= option

    form <= input_incomer
    form <= html.BR()

    form <= html.BR()

    input_put_in_game = html.INPUT(type="submit", value="put in game")
    input_put_in_game.bind("click", put_in_game_callback)
    form <= input_put_in_game

    # ---
    form <= html.BR()
    form <= html.BR()

    legend_outcomer = html.LEGEND("Outcoming", title="Select player to remove from game")
    legend_outcomer.style = {
        'color': 'red',
    }
    form <= legend_outcomer

    input_outcomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(players_allocated_list):
        option = html.OPTION(play_pseudo)
        input_outcomer <= option

    form <= input_outcomer
    form <= html.BR()

    form <= html.BR()

    input_remove_from_game = html.INPUT(type="submit", value="remove from game")
    input_remove_from_game.bind("click", remove_from_game_callback)
    form <= input_remove_from_game

    my_sub_panel.clear()
    my_sub_panel <= form


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
    if item_name == 'move players in game':
        move_players_in_game()

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
