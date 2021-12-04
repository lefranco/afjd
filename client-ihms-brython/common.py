""" common """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import mapping


def noreply_callback(_):
    """ noreply_callback """
    alert("Problème (pas de réponse de la part du serveur)")


def get_news_content():
    """ get_news_content """

    news_content = None

    def reply_callback(req):
        nonlocal news_content
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du contenu des nouvelles : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du contenu des nouvelles : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        news_content = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/news"

    # get news : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return news_content


def get_player_id(pseudo):
    """ get_player_id """

    player_id = None

    def reply_callback(req):
        nonlocal player_id
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération d'identifiant de joueur : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération d'identifiant de joueur : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        player_id = int(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/player-identifiers/{pseudo}"

    # get player id : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return player_id


def get_players():
    """ get_players """

    players_dict = None

    def reply_callback(req):
        nonlocal players_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        players_dict = {v['pseudo']: int(k) for k, v in req_result.items()}

    json_dict = dict()

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players"

    # getting players list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return players_dict


def get_players_data():
    """ get_players_data """

    players_dict = None

    def reply_callback(req):
        nonlocal players_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs et leurs données : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs et leurs données : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        players_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players"

    # getting players list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict(players_dict)


def get_games_data():
    """ get_games_data """

    games_dict = None

    def reply_callback(req):
        nonlocal games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        games_dict = dict(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games"

    # getting games list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return games_dict


def game_variant_content_reload(variant_name):
    """ game_variant_content_reload """

    variant_content_loaded = None

    def reply_callback(req):
        nonlocal variant_content_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement du contenu de la variante de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement du contenu de la variante de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        variant_content_loaded = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/variants/{variant_name}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return variant_content_loaded


def game_position_reload(game_id):
    """ game_position_reload """

    position_loaded = None

    def reply_callback(req):
        nonlocal position_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement de la position de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement de la position de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        position_loaded = dict(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-positions/{game_id}"

    # getting game position : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return position_loaded


DIPLOMACY_SEASON_CYCLE = [1, 2, 1, 2, 3]


def get_season(advancement, variant) -> None:
    """ store season """

    len_season_cycle = len(DIPLOMACY_SEASON_CYCLE)
    advancement_season_num = advancement % len_season_cycle + 1
    advancement_season = mapping.SeasonEnum.from_code(advancement_season_num)
    advancement_year = (advancement // len_season_cycle) + 1 + variant.year_zero
    return advancement_season, advancement_year


def get_role_allocated_to_player_in_game(game_id):
    """ get_role the player has in this game """

    role_id = None

    def reply_callback(req):
        nonlocal role_id
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du rôle alloué au joueur dans la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du rôle alloué au joueur dans la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        # a player has never more than one role
        role_id = req_result

    json_dict = {
        'game_id': game_id,
    }

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-role/{game_id}"

    # get players allocated to game : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return role_id


def date_last_visit_load(game_id, visit_type):
    """ date_last_visit_load """

    time_stamp = None

    def reply_callback(req):
        nonlocal time_stamp
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la dernière visite de la partie : ({visit_type}): {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la dernière visite de la partie : ({visit_type=}): {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        time_stamp = req_result['time_stamp']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-visits/{game_id}/{visit_type}"

    # getting last visit in a game : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return time_stamp


def make_report_window(report_loaded):
    """ make_report_window """

    columns = 3

    lines = report_loaded.split('\n')
    split_size = (len(lines) + columns) // columns
    report_table = html.TABLE()
    report_row = html.TR()
    report_table <= report_row
    for chunk_num in range(columns):
        report_col = html.TD()
        chunk_content = lines[chunk_num * split_size: (chunk_num + 1) * split_size]
        for line in chunk_content:
            if line.find("(échec)") != -1 or line.find("(coupé)") != -1 or line.find("(délogée)") != -1 or line.find("(détruite)") != -1 or line.find("(invalide)") != -1:
                report_col <= html.DIV(line, Class='code_failed')
            elif line.find(":") != -1:
                report_col <= html.DIV(line, Class='code_info')
            elif line.startswith("*"):
                report_col <= html.DIV(line, Class='code_communication')
            else:
                report_col <= html.DIV(line, Class='code_success')
        report_row <= report_col
    return report_table


def read_parameters(variant_name_loaded, interface_chosen):
    """ read_parameters """

    parameters_file_name = f"./variants/{variant_name_loaded}/{interface_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file2:
        parameters_read = json.load(read_file2)

    return parameters_read


def read_image(variant_name_loaded, interface_chosen):
    """ read_image """

    return html.IMG(src=f"./variants/{variant_name_loaded}/{interface_chosen}/map.png")


def get_allocations_data():
    """ get_allocations_data """

    allocation_data = None

    def reply_callback(req):
        nonlocal allocation_data
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des listes parties avec les arbitres : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des listes parties avec les arbitres : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        allocation_data = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/allocations"

    # getting allocations : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return allocation_data


def get_game_data(game):
    """ get_game_data """

    game_data = None

    def reply_callback(req):
        nonlocal game_data
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des données de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des données de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        game_data = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games/{game}"

    # getting game data : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_data
