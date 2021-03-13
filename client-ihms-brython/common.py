""" common """

import json

from browser import ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config


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

    # get player id : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

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

    # getting a game identifier : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return int(game_id)


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

    # getting players list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict(players_dict)


def get_games_data():
    """ get_games_data """

    games_dict = None

    def reply_callback(req):
        nonlocal games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting games list: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting games list: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        req_result = json.loads(req.text)
        games_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games"

    # getting games list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict(games_dict)


def game_variant_name_reload(game):
    """ game_variant_name_reload """

    variant_name_loaded = None

    def reply_callback(req):
        """ reply_callback """
        nonlocal variant_name_loaded

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error loading game variant name: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem loading game variant name: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        variant_name_loaded = req_result['variant']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games/{game}"

    # getting game data : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return variant_name_loaded


def game_variant_content_reload(variant_name):
    """ game_variant_content_reload """

    variant_content_loaded = None

    def reply_callback(req):
        """ reply_callback """
        nonlocal variant_content_loaded

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error loading game variant content: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem loading game variant content: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        variant_content_loaded = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/variants/{variant_name}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return variant_content_loaded


def game_position_reload(game):
    """ game_position_reload """

    position_loaded = None

    def reply_callback(req):
        """ reply_callback """
        nonlocal position_loaded

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error loading game position: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem loading game position: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        position_loaded = req_result

    game_id = get_game_id(game)
    if game_id is None:
        return None

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-positions/{game_id}"

    # getting game position : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return position_loaded


def game_report_reload(game):
    """ game_report_reload """

    report_loaded = None

    def reply_callback(req):
        """ reply_callback """
        nonlocal report_loaded

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error loading game report: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem loading game report: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        report_loaded = req_result['content']

    game_id = get_game_id(game)
    if game_id is None:
        return None

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-reports/{game_id}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return report_loaded


def game_orders_reload(game):
    """ game_orders_reload """

    orders_loaded = None

    def reply_callback(req):
        """ reply_callback """
        nonlocal orders_loaded

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error loading game orders: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem loading game orders: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        orders_loaded = dict(req_result)

    game_id = get_game_id(game)
    if game_id is None:
        return None

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders/{game_id}"

    # getting orders : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return orders_loaded


def game_parameters_reload(game):
    """ display_main_parameters_reload """

    game_parameters_loaded = None

    def reply_callback(req):
        """ reply_callback """
        nonlocal game_parameters_loaded

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error loading main parameters: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem loading main parameters: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        game_parameters_loaded = dict(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games/{game}"

    # getting game data : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_parameters_loaded
