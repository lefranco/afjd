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


def get_game_id(name):
    """ get_game_id """

    game_id = None

    def reply_callback(req):
        nonlocal game_id
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de l'identifiant de partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de l'identifiant de partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        game_id = int(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-identifiers/{name}"

    # getting a game identifier : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_id


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


def game_variant_name_reload(game):
    """ game_variant_name_reload """

    variant_name_loaded = None

    def reply_callback(req):
        nonlocal variant_name_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement du nom de la variante de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement du nom de la variante de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
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


def game_report_reload(game_id):
    """ game_report_reload """

    report_loaded = None

    def reply_callback(req):
        nonlocal report_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement du rapport de résolution de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement du rapport de résolution de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        report_loaded = req_result['content']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-reports/{game_id}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return report_loaded


def game_transition_reload(game_id, advancement):
    """ game_transition_reload """

    transition_loaded = None

    def reply_callback(req):
        nonlocal transition_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement de la transition de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Résolution introuvable: {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        transition_loaded = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-transitions/{game_id}/{advancement}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return transition_loaded


def game_orders_reload(game_id):
    """ game_orders_reload """

    orders_loaded = None

    def reply_callback(req):
        nonlocal orders_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des ordres de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des ordres de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        orders_loaded = dict(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders/{game_id}"

    # getting orders : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return orders_loaded


def game_communication_orders_reload(game_id):
    """ game_communication_orders_reload """

    orders_loaded = None

    def reply_callback(req):
        nonlocal orders_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des ordres de communication la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des ordres de communication la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        orders_loaded = dict(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-communication-orders/{game_id}"

    # getting orders : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return orders_loaded


def game_parameters_reload(game):
    """ display_main_parameters_reload """

    game_parameters_loaded = None

    def reply_callback(req):
        nonlocal game_parameters_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des paramètres de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des paramètres de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        game_parameters_loaded = dict(req_result)

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games/{game}"

    # getting game data : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_parameters_loaded


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


def get_all_roles_allocated_to_player():
    """ get all roles the player has in all the games """

    dict_role_id = None

    def reply_callback(req):
        nonlocal dict_role_id
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des rôles alloué au joueur dans toutes les parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des rôles alloué au joueur dans toutes les parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        # a player has never more than one role
        dict_role_id = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-games-roles"

    # get players allocated to game : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict_role_id


def get_roles_submitted_orders(game_id):
    """ get_roles_submitted_orders """

    submitted_data = None

    def reply_callback(req):
        nonlocal submitted_data
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des rôles qui ont soumis des ordres pour la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des rôles qui ont soumis des ordres pour la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        submitted_data = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders-submitted/{game_id}"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return submitted_data


def get_all_player_games_roles_submitted_orders():
    """ get_all_player_games_roles_submitted_orders """

    dict_submitted_data = None

    def reply_callback(req):
        nonlocal dict_submitted_data
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des rôles qui ont soumis des ordres pour toutes mes parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des rôles qui ont soumis des ordres pour toutes mes parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        dict_submitted_data = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-player-games-orders-submitted"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict_submitted_data


def get_all_games_roles_submitted_orders():
    """ get_all_games_roles_submitted_orders """

    dict_submitted_data = None

    def reply_callback(req):
        nonlocal dict_submitted_data
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des rôles qui ont soumis des ordres pour toutes les parties possibles : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des rôles qui ont soumis des ordres pour toutes les parties possibles : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        dict_submitted_data = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-games-orders-submitted"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict_submitted_data


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


def date_last_visit_load_all_games(visit_type):
    """ date_last_visit_load_all_games """

    dict_time_stamp = None

    def reply_callback(req):
        nonlocal dict_time_stamp
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la dernière visite de la partie : ({visit_type}): {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la dernière visite de la partie : ({visit_type=}): {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        dict_time_stamp = req_result['dict_time_stamp']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-game-visits/{visit_type}"

    # getting last visit in a game : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict_time_stamp


def date_last_visit_update(game_id, pseudo, role_id, visit_type):
    """ date_last_visit_update """

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 201:
            if 'message' in req_result:
                alert(f"Erreur à la mise à jour de la dernière visite de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la mise à jour de la dernière visite de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

    json_dict = {
        'role_id': role_id,
        'pseudo': pseudo,
    }

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-visits/{game_id}/{visit_type}"

    # putting visit in a game : need token
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)


def date_last_declarations():
    """ date_last_declarations """

    dict_time_stamp = None

    def reply_callback(req):
        nonlocal dict_time_stamp
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des dates de dernières déclarations des parties jouées : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des dates de dernières déclarations de parties joueées : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        dict_time_stamp = req_result['dict_time_stamp']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/date-last-declarations"

    # getting last game declaration : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict_time_stamp


def date_last_messages():
    """ date_last_messages """

    dict_time_stamp = None

    def reply_callback(req):
        nonlocal dict_time_stamp
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des dates des derniers messages des parties jouées : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des dates des derniers messages des partie jouées : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        dict_time_stamp = req_result['dict_time_stamp']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/date-last-game-messages"

    # getting last game message role : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict_time_stamp


def make_rating_colours_window(ratings, colours):
    """ make_rating_window """

    rating_table = html.TABLE()
    rating_row = html.TR()
    rating_table <= rating_row
    for role_name, ncenters in ratings.items():
        rating_col = html.TD()

        canvas = html.CANVAS(id="rect", width=15, height=15, alt=role_name)
        ctx = canvas.getContext("2d")

        colour = colours[role_name]

        outline_colour = colour.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.rect(0, 0, 14, 14)
        ctx.stroke()
        ctx.closePath()  # no fill

        ctx.fillStyle = colour.str_value()
        ctx.fillRect(1, 1, 13, 13)

        rating_col <= canvas
        rating_col <= f" {role_name} {ncenters}"
        rating_row <= rating_col

    return rating_table


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
                report_col <= html.B(html.CODE(line, style={'color': 'grey'}))
            elif line.find(":") != -1:
                report_col <= html.B(html.CODE(line, style={'color': 'blue'}))
            elif line.startswith("*"):
                report_col <= html.B(html.CODE(line, style={'color': 'pink'}))
            else:
                report_col <= html.B(html.CODE(line, style={'color': 'red'}))
            report_col <= html.BR()
        report_row <= report_col
    return report_table


def vote_reload(game_id):
    """ vote_reload """

    votes = None

    def reply_callback(req):
        nonlocal votes
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des votes d'arrêt de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des votes d'arrêt de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        votes = req_result['votes']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-votes/{game_id}"

    # extracting vote from a game : need token (or not?)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return votes


def read_parameters(variant_name_loaded, display_chosen):
    """ read_parameters """

    parameters_file_name = f"./variants/{variant_name_loaded}/{display_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file2:
        parameters_read = json.load(read_file2)

    return parameters_read


def read_image(variant_name_loaded, display_chosen):
    """ read_image """

    return html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/map.png")


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
