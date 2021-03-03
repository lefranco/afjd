""" common """

import json

from browser import ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


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
