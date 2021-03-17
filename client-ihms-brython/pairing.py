""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common

my_panel = html.DIV(id="pairing")

OPTIONS = ['rejoindre une partie', 'quitter une partie', 'déplacer des joueurs']


def get_game_allocated_players(game_id):
    """ get_available_players returns a tuple game_master + players """

    game_master_id = None
    players_allocated_list = None
    players_assigned_list = None

    def reply_callback(req):
        nonlocal game_master_id
        nonlocal players_allocated_list
        nonlocal players_assigned_list
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
        game_masters_list = [int(k) for k, v in req_result.items() if v == 0]
        game_master_id = game_masters_list.pop()
        players_allocated_list = [int(k) for k, v in req_result.items() if v == -1]
        players_assigned_list = [int(k) for k, v in req_result.items() if v > 0]

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-allocations/{game_id}"

    # get players allocated to game : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return game_master_id, players_allocated_list, players_assigned_list


def join_game():
    """ join_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
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
            InfoDialog("OK", f"Vous avez rejoint la partie : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # adding allocation : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    form = html.FORM()

    input_join_game = html.INPUT(type="submit", value="rejoindre la partie")
    input_join_game.bind("click", join_game_callback)
    form <= input_join_game

    my_sub_panel <= form


def quit_game():
    """ quit_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
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
            InfoDialog("OK", f"Vous avez quitté la partie : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # should be a delete but body in delete requests is more or less forbidden
        # quitting a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    form = html.FORM()

    input_quit_game = html.INPUT(type="submit", value="quitter la partie")
    input_quit_game.bind("click", quit_game_callback)
    form <= input_quit_game

    my_sub_panel <= form


def move_players_in_game():
    """ move_players_in_game """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
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
            InfoDialog("OK", f"Le joueur a été mis dans la partie: {req_result['msg']}", remove_after=config.REMOVE_AFTER)
            # back to where we started
            move_players_in_game()

        player_pseudo = input_incomer.value

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'game_id': game_id,
            'player_pseudo': player_pseudo,
            'pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # putting a player in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
            InfoDialog("OK", f"Le joueur a été retiré de la partie: {req_result['msg']}", remove_after=config.REMOVE_AFTER)
            # back to where we started
            move_players_in_game()

        player_pseudo = input_outcomer.value

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'game_id': game_id,
            'player_pseudo': player_pseudo,
            'pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # removing a player from a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    players_dict = common.get_players()
    if players_dict is None:
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    game_id = common.get_game_id(game)
    if game_id is None:
        return

    allocated = get_game_allocated_players(game_id)
    if allocated is None:
        return
    game_master_id, players_allocated_ids_list, players_assigned_ids_list = allocated

    players_allocated_list = [id2pseudo[i] for i in list(players_allocated_ids_list)]
    players_assigned_list = [id2pseudo[i] for i in list(players_assigned_ids_list)]

    form = html.FORM()

    # ---

    legend_incomer = html.LEGEND("Entrant", title="Sélectionner le joueur à mettre dans la partie")
    legend_incomer.style = {
        'color': 'red',
    }
    form <= legend_incomer

    # all players can come in
    possible_incomers = set(players_dict.keys())

    # not those already in
    possible_incomers -= set(players_allocated_list)
    possible_incomers -= set(players_assigned_list)

    # not the operator
    possible_incomers -= set([pseudo])

    # not the gm of the game
    possible_incomers -= set([game_master_id])

    input_incomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_incomers):
        option = html.OPTION(play_pseudo)
        input_incomer <= option

    form <= input_incomer
    form <= html.BR()

    form <= html.BR()

    input_put_in_game = html.INPUT(type="submit", value="mettre dans la partie")
    input_put_in_game.bind("click", put_in_game_callback)
    form <= input_put_in_game

    # ---
    form <= html.BR()
    form <= html.BR()

    legend_outcomer = html.LEGEND("Sortant", title="Sélectionner le joueur à retirer de la partie")
    legend_outcomer.style = {
        'color': 'red',
    }
    form <= legend_outcomer

    # players can come out are the ones not assigned
    possible_outcomers = players_allocated_list

    input_outcomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_outcomers):
        option = html.OPTION(play_pseudo)
        input_outcomer <= option

    form <= input_outcomer
    form <= html.BR()

    form <= html.BR()

    input_remove_from_game = html.INPUT(type="submit", value="retirer de la partie")
    input_remove_from_game.bind("click", remove_from_game_callback)
    form <= input_remove_from_game

    my_sub_panel.clear()
    my_sub_panel <= form


my_panel = html.DIV(id="pairing")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
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
    if item_name == 'rejoindre une partie':
        join_game()
    if item_name == 'quitter une partie':
        quit_game()
    if item_name == 'déplacer des joueurs':
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
