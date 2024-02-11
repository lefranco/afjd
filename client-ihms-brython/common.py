""" common """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position


from json import load, loads, dumps
from time import time

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import mydialog
import mapping
import config


PERSIST_TIME_SEC = 5


TYPE_GAME_EXPLAIN_CONV = {
    0: "Négo : pas de restriction, tout est possible !",
    1: "Blitz : pas de communication, tout est fermé !",
    2: "NégoPublique : communication publique uniquement...",
    3: "BlitzOuverte : comme Blitz avec ouverture du canal public (déclarations) pour parler d'autre chose que la partie"
}


def noreply_callback(_):
    """ noreply_callback """
    alert("Problème (pas de réponse de la part du serveur)")


def info_dialog(mess, important=False):
    """ info_dialog """

    if important:
        mydialog.InfoDialog("Information", mess, remove_after=None, ok="Ok")
    else:
        mydialog.InfoDialog("Information", mess, remove_after=PERSIST_TIME_SEC)


def check_creator():
    """ check_creator """

    if 'PSEUDO' not in storage:
        return False

    pseudo = storage['PSEUDO']

    priviledged = PRIVILEDGED
    if not priviledged:
        return False
    creator_list = priviledged['creators']
    if pseudo not in creator_list:
        return False

    return True


def check_modo():
    """ check_modo """

    if 'PSEUDO' not in storage:
        return False

    pseudo = storage['PSEUDO']

    priviledged = PRIVILEDGED
    if not priviledged:
        return False
    moderators_list = priviledged['moderators']
    if pseudo not in moderators_list:
        return False

    return True


def check_admin():
    """ check_admin """

    if 'PSEUDO' not in storage:
        return False

    pseudo = storage['PSEUDO']

    priviledged = PRIVILEDGED
    if not priviledged:
        return False
    admin_pseudo = priviledged['admin']
    if pseudo != admin_pseudo:
        return False

    return True


class Random:
    """ Random provider """

    def __init__(self):
        self._next = int(time())

    def choice(self, values):
        """ chooses an element """

        self._next *= 1103515245
        self._next + 12345
        self._next //= 65536

        position = self._next % len(values)

        return values[position]


class MessageTypeEnum:
    """ MessageTypeEnum """

    TEXT = 1
    SEASON = 2
    DROPOUT = 3


def get_players():
    """ get_players returns an empy dict on error """

    players_dict = {}

    def reply_callback(req):
        nonlocal players_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        players_dict = {v['pseudo']: int(k) for k, v in req_result.items()}

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players-short"

    # getting players list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return players_dict


def get_players_data():
    """ get_players_data """

    players_dict = None

    def reply_callback(req):
        nonlocal players_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs et leurs données : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs et leurs données : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        players_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players"

    # getting players list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict(players_dict)


def get_games_data(current_state=None):
    """ get_games_data : returns None if problem """

    games_dict = None

    def reply_callback(req):
        nonlocal games_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        games_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']

    if current_state is not None:
        url = f"{host}:{port}/games-in-state/{current_state}"
    else:
        url = f"{host}:{port}/games"

    # getting games list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return games_dict


def game_variant_content_reload(variant_name):
    """ game_variant_content_reload """

    variant_content_loaded = {}

    def reply_callback(req):
        nonlocal variant_content_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement du contenu de la variante de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement du contenu de la variante de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        variant_content_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/variants/{variant_name}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return variant_content_loaded


def game_position_reload(game_id):
    """ game_position_reload """

    position_loaded = None

    def reply_callback(req):
        nonlocal position_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement de la position de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement de la position de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        position_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-positions/{game_id}"

    # getting game position : do not need a token if not fog_of_war
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return position_loaded


def game_position_empty():
    """ game_position_empty """

    return {
        'ownerships': {},
        'dislodged_ones': {},
        'units': {},
        'forbiddens': {},
        'imagined_units_zones': [],
    }


def game_position_fog_of_war_reload(game_id, role_id):
    """ game_position_fog_of_war_reload """

    position_loaded = None

    def reply_callback(req):
        nonlocal position_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement de la position (brouillard) de la partie  : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement de la position (brouillard) de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        position_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-fog-of-war-positions/{game_id}/{role_id}"

    # getting game position : need a token if fog_of_war
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return position_loaded


def tournament_position_reload(tournament_id):
    """ tournament_position_reload : returns empty dict on error """

    positions_loaded = {}

    def reply_callback(req):
        nonlocal positions_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des positions des parties du tournoi : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des positions des parties du tournoi : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        positions_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/tournament-positions/{tournament_id}"

    # getting game position : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return positions_loaded


def display_flag(variant_name, interface, role_id, role_name):
    """ display_flag """

    return html.IMG(src=f"./variants/{variant_name}/{interface}/roles/{role_id}.jpg", title=role_name)


DIPLOMACY_SEASON_CYCLE = [1, 2, 1, 2, 3]


def get_short_season(advancement, variant):
    """ get_short_season """

    len_season_cycle = len(DIPLOMACY_SEASON_CYCLE)
    advancement_season_num = advancement % len_season_cycle + 1
    advancement_season = mapping.SeasonEnum.from_code(advancement_season_num)

    advancement_play_year = ((advancement // len_season_cycle) + 1) * variant.increment + variant.year_zero

    return advancement_season, advancement_play_year


def readable_season(advancement, variant):
    """ readable_season """

    advancement_season, advancement_year = get_short_season(advancement, variant)
    advancement_season_readable = variant.season_name_table[advancement_season]
    description = f"{advancement_season_readable} {advancement_year}"
    return description


def get_full_season(advancement, variant, nb_max_cycles_to_play, full_info):
    """ get_full_season """

    advancement_season, advancement_year = get_short_season(advancement, variant)
    advancement_season_readable = variant.season_name_table[advancement_season]

    len_season_cycle = len(DIPLOMACY_SEASON_CYCLE)
    real_year = advancement // len_season_cycle + 1
    real_last_year = nb_max_cycles_to_play

    full_season = f"{advancement_season_readable} {advancement_year} ({real_year}/{real_last_year})"

    if full_info:
        play_last_year = nb_max_cycles_to_play * variant.increment + variant.year_zero
        full_season = f"{full_season} [fin {play_last_year}]"

    return full_season


def get_role_allocated_to_player_in_game(game_id):
    """ get_role the player has in this game """

    role_id = None

    def reply_callback(req):
        nonlocal role_id
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return role_id


def date_last_visit_load(game_id, visit_type):
    """ date_last_visit_load """

    time_stamp = None

    def reply_callback(req):
        nonlocal time_stamp
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la dernière visite de la partie : ({visit_type}): {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la dernière visite de la partie : ({visit_type=}): {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        time_stamp = req_result['time_stamp']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-visits/{game_id}/{visit_type}"

    # getting last visit in a game : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return time_stamp


def make_report_window(report_loaded):
    """ make_report_window """

    report_table = html.TABLE()

    if not report_loaded:
        return report_table

    content = report_loaded['content']
    columns = 3
    lines = content.split('\n')
    split_size = (len(lines) + columns) // columns
    report_row = html.TR()
    report_table <= report_row
    for chunk_num in range(columns):
        report_col = html.TD()
        chunk_content = lines[chunk_num * split_size: (chunk_num + 1) * split_size]
        for line in chunk_content:
            if line == "":
                report_col <= html.DIV("&nbsp", Class='code_info')
            elif line.find("(échec)") != -1 or line.find("(coupé)") != -1 or line.find("(délogée)") != -1 or line.find("(détruite)") != -1 or line.find("(invalide)") != -1:
                report_col <= html.DIV(line, Class='code_failed')
            elif line.find(":") != -1:
                report_col <= html.DIV(line, Class='code_info')
            elif line.startswith("*"):
                report_col <= html.DIV(line, Class='code_communication')
            else:
                report_col <= html.DIV(line, Class='code_success')
        report_row <= report_col

    time_stamp = report_loaded['time_stamp']
    date_report_gmt = mydatetime.fromtimestamp(time_stamp)
    date_report_gmt_str = mydatetime.strftime(*date_report_gmt)
    report_elem = html.B(date_report_gmt_str)
    caption = html.CAPTION(report_elem)
    report_table <= caption

    return report_table


def read_parameters(variant_name_loaded, interface_chosen):
    """ read_parameters """

    parameters_file_name = f"./variants/{variant_name_loaded}/{interface_chosen}/parameters.json"
    with open(parameters_file_name, "r", encoding="utf-8") as read_file2:
        parameters_read = load(read_file2)

    return parameters_read


def read_image(variant_name_loaded, interface_chosen):
    """ read_image """

    # create image
    # change version 12345 in map.png?v=12345 to force refreseh
    image = html.IMG(src=f"./variants/{variant_name_loaded}/{interface_chosen}/map.png?v=123456")

    # it must not move on screen !
    image.attrs['style'] = 'position: absolute;'

    return image


def get_allocations_data(current_state=None):
    """ get_allocations_data : returns empty dict on error """

    allocation_data = {}

    def reply_callback(req):
        nonlocal allocation_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des allocations : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des allocations : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        allocation_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']

    if current_state is not None:
        url = f"{host}:{port}/allocations-games-in-state/{current_state}"
    else:
        url = f"{host}:{port}/allocations"

    # getting allocations : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return allocation_data


def get_game_data(game):
    """ get_game_data : returns empty dict if problem """

    game_data = {}

    def reply_callback(req):
        nonlocal game_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des données de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des données de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        game_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games/{game}"

    # getting game data : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_data


def get_game_id(name):
    """ get_game_id """

    game_id = None

    def reply_callback(req):
        nonlocal game_id
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de l'identifiant de partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de l'identifiant de partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        game_id = int(req_result)

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-identifiers/{name}"

    # getting a game identifier : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_id


def get_tournaments_data():
    """ get_tournaments_data : returnes empty dict if problem """

    tournaments_dict = {}

    def reply_callback(req):
        nonlocal tournaments_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des tournois : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des tournois : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        tournaments_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/tournaments"

    # getting tournaments list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return tournaments_dict


def get_assignments_data():
    """ get_assignments_data : returns empty dict on error """

    assignment_data = {}

    def reply_callback(req):
        nonlocal assignment_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des assignations : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des assignations : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        assignment_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/assignments"

    # getting allocations : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return assignment_data


def get_groupings_data():
    """ get_groupings_data : returns empty dict on error """

    grouping_data = {}

    def reply_callback(req):
        nonlocal grouping_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des regroupements : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des regroupements : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        grouping_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/groupings"

    # getting allocations : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return grouping_data


def game_parameters_reload(game):
    """ game_parameters_reload : returns empty dict if error"""

    game_parameters_loaded = {}

    def reply_callback(req):
        nonlocal game_parameters_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des paramètres de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des paramètres de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        game_parameters_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games/{game}"

    # getting game data : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_parameters_loaded


def get_tournament_data(game):
    """ get_tournament_data : returns empty dict if problem """

    tournament_dict = {}

    def reply_callback(req):
        nonlocal tournament_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des informations du tournoi : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des informations du tournoi : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        tournament_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/tournaments/{game}"

    # getting tournament data : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return tournament_dict


def tournament_incidents_reload(tournament_id):
    """ tournament_incidents_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents retards du tournoi : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents retards du tournoi : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/tournament-incidents/{tournament_id}"

    # extracting incidents from a tournament : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return incidents


def tournament_incidents2_reload(tournament_id):
    """ tournament_incidents2_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents désordres civils du tournoi : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents désordre civils du tournoi : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/tournament-incidents2/{tournament_id}"

    # extracting incidents from a tournament : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return incidents


def get_player_id(pseudo):
    """ get_player_id """

    player_id = None

    def reply_callback(req):
        nonlocal player_id
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération d'identifiant de joueur : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération d'identifiant de joueur : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        player_id = int(req_result)

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/player-identifiers/{pseudo}"

    # get player id : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return player_id


def get_player_games_playing_in(player_id):
    """ get_player_games_playing_in """

    player_games_dict = None

    def reply_callback(req):
        nonlocal player_games_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récuperation de la liste des parties du joueur : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récuperation de la liste des parties du joueur : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        player_games_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/player-allocations/{player_id}"

    # getting player games playing in list : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return player_games_dict


def get_events_data():
    """ get_events_data : returnes empty dict if problem """

    events_dict = {}

    def reply_callback(req):
        nonlocal events_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des événements : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des événements : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        events_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/events"

    # getting tournaments list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return events_dict


def get_all_emails():
    """ get_all_emails returns empty dict if error """

    emails_dict = {}

    def reply_callback(req):
        nonlocal emails_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des courriels : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des courriels : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        emails_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players-emails"

    # changing news : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return emails_dict


def send_ip_address():
    """ send_ip_address """

    def reply_callback(req):
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à l'envoi de l'adresse IP : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à l'envoi de l'adresse IP : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

    # must be identified
    if 'PSEUDO' not in storage:
        return

    # must have an IP (should be the case)
    if 'IPADDRESS' not in storage:
        return

    ip_value = storage['IPADDRESS']
    json_dict = {
        'ip_value': ip_value
    }

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/ip_address"

    # store ip : do need token
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)


def get_ip_submission_table():
    """ get_ip_submission_table """

    ip_sub_list = {}

    def reply_callback(req):
        nonlocal ip_sub_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des addresses IP et dernières soumissions : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des addresses IP et dernières soumissions : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        ip_sub_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/ip_address"

    # getting ip addresses or last submissions : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dict(ip_sub_list)


def verification_code(pseudo):
    """ verification_code """
    code = int(sum(map(lambda c: ord(c) ** 3.5, pseudo))) % 1000000
    return code


def get_priviledged():
    """ get_priviledged : returns empty list if problem """

    priviledged = {}

    def reply_callback(req):
        nonlocal priviledged
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des privilégiés : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des privilégiés : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        priviledged = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/priviledged"

    # getting moderators list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return priviledged


def get_news_content():
    """ get_news_content """

    news_content = {}

    def reply_callback(req):
        nonlocal news_content
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du contenu des nouvelles : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du contenu des nouvelles : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        news_content = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/news"

    # get news : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return news_content


def get_game_players_data(game_id):
    """ get_game_players_data : returns empty dict if problem """

    game_players_dict = {}

    def reply_callback(req):
        nonlocal game_players_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        game_players_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-allocations/{game_id}"

    # getting game allocation : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return game_players_dict


def get_game_master(game_id):
    """ get_game_master """

    master_loaded = None

    def reply_callback(req):
        nonlocal master_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement de l'arbitre de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement de l'arbitre de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        master_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-master/{game_id}"

    # getting master : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return master_loaded


def game_dropouts_reload(game_id):
    """ game_dropouts_reload """

    dropouts = []

    def reply_callback(req):
        nonlocal dropouts
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des abandons de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des abandons de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        dropouts = req_result['dropouts']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-dropouts/{game_id}"

    # extracting dropouts from a game : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return dropouts


def game_transitions_reload(game_id):
    """ game_transitions_reload : returns empty dict if problem (or no data) """

    transitions_loaded = {}

    def reply_callback(req):
        nonlocal transitions_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des transitions de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des transitions de la partie: {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        transitions_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-transitions/{game_id}"

    # getting transitions : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return transitions_loaded


def game_note_reload(game_id):
    """ game_note_reload """

    content = None

    def reply_callback(req):
        nonlocal content
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des notes de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des notes de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        content = req_result['content']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-notes/{game_id}"

    # extracting vote from a game : need token (or not?)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return content


# stored for usage
PRIVILEDGED = get_priviledged()
