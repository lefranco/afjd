""" play """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import enum
import time
import random

from browser import document, html, ajax, alert, timer, window   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import scoring
import interface
import geometry
import mapping
import login
import sandbox
import memoize
import moderate
import index  # circular import


# how long between two consecutives refresh
SUPERVISE_REFRESH_PERIOD_SEC = 15

# how long between two consecutives refresh
OBSERVE_REFRESH_PERIOD_SEC = 60

LONG_DURATION_LIMIT_SEC = 1.0

OPTIONS = ['consulter', 'ordonner', 'taguer', 'négocier', 'déclarer', 'voter', 'noter', 'arbitrer', 'paramètres', 'retards', 'superviser', 'observer']


@enum.unique
class AutomatonStateEnum(enum.Enum):
    """ AutomatonStateEnum """

    SELECT_ACTIVE_STATE = enum.auto()
    SELECT_ORDER_STATE = enum.auto()
    SELECT_PASSIVE_UNIT_STATE = enum.auto()
    SELECT_DESTINATION_STATE = enum.auto()
    SELECT_BUILD_UNIT_TYPE_STATE = enum.auto()


# the idea is not to loose the content of a message if not destinee were specified
CONTENT_BACKUP = None


# global data below

# loaded in render()
GAME = None
GAME_ID = None
PSEUDO = None
ROLE_ID = None

# loaded in load_static_stuff
PLAYERS_DICT = None
VARIANT_NAME_LOADED = None
VARIANT_CONTENT_LOADED = None
INTERFACE_CHOSEN = None
INTERFACE_PARAMETERS_READ = None
VARIANT_DATA = None
INFORCED_VARIANT_DATA = None

# loaded in load_dynamic_stuff
GAME_PARAMETERS_LOADED = {}
GAME_STATUS = None
POSITION_LOADED = None
POSITION_DATA = None
REPORT_LOADED = {}

# loaded in load_special_stuff
GAME_PLAYERS_DICT = {}

ARRIVAL = None


def set_arrival(arrival):
    """ set_arrival """
    global ARRIVAL
    ARRIVAL = arrival


def readable_season(advancement):
    """ readable_season """
    advancement_season, advancement_year = common.get_season(advancement, VARIANT_DATA)
    advancement_season_readable = VARIANT_DATA.name_table[advancement_season]
    value = f"{advancement_season_readable} {advancement_year}"
    return value


def join_game():
    """ join_game_action : the third way of joining a game (by a link) """

    def reply_callback(req):

        req_result = json.loads(req.text)
        if req.status != 201:
            if 'message' in req_result:
                alert(f"Erreur à l'inscription à la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à l'inscription à la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        messages = "<br>".join(req_result['msg'].split('\n'))
        InfoDialog("OK", f"Vous avez rejoint la partie : {messages}", remove_after=config.REMOVE_AFTER)

    if PSEUDO is None:
        alert("Il faut se connecter au préalable")
        return

    pseudo = PSEUDO

    if GAME_ID is None:
        alert("Problème avec la partie")
        return

    game_id = GAME_ID

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


def game_incidents_reload(game_id):
    """ game_incidents_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents retards de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents retards de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result['incidents']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-incidents/{game_id}"

    # extracting incidents from a game : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incidents


def game_incidents2_reload(game_id):
    """ game_incidents2_reload """

    incidents = []

    def reply_callback(req):
        nonlocal incidents
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des incidents désordres civils  de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des incidents désordres civils de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incidents = req_result['incidents']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-incidents2/{game_id}"

    # extracting incidents from a game : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incidents


def game_report_reload(game_id):
    """ game_report_reload """

    report_loaded = {}

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

        report_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-reports/{game_id}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return report_loaded


def game_transition_reload(game_id, advancement):
    """ game_transition_reload : returns empty dict if problem (or no data) """

    transition_loaded = {}

    def reply_callback(req):
        nonlocal transition_loaded
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement de la transition de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement de la transition de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        transition_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-transitions/{game_id}/{advancement}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

        orders_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders/{game_id}"

    # getting orders : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

        orders_loaded = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-communication-orders/{game_id}"

    # getting orders : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return orders_loaded


def game_transitions_reload(game_id):
    """ game_transitions_reload : returns empty dict if problem (or no data) """

    transitions_loaded = {}

    def reply_callback(req):
        nonlocal transitions_loaded
        req_result = json.loads(req.text)
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

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return transitions_loaded


def make_rating_colours_window(variant_data, ratings, colours, game_scoring):
    """ make_rating_window """

    rating_table = html.TABLE()

    # roles
    rating_names_row = html.TR()
    rating_table <= rating_names_row
    col = html.TD(html.B("Rôles :"))
    rating_names_row <= col
    for role_name in ratings:
        col = html.TD()

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

        col <= canvas
        col <= f" {role_name}"
        rating_names_row <= col

    # centers
    rating_centers_row = html.TR()
    rating_table <= rating_centers_row
    col = html.TD(html.B("Centres :"))
    rating_centers_row <= col
    for ncenters in ratings.values():
        col = html.TD()
        col <= f"{ncenters}"
        rating_centers_row <= col

    # scoring
    solo_threshold = variant_data.number_centers() // 2
    score_table = scoring.scoring(game_scoring, solo_threshold, ratings)

    # get scoring name
    name2code = {v: k for k, v in config.SCORING_CODE_TABLE.items()}
    scoring_name = name2code[game_scoring]

    # scoring
    rating_scoring_row = html.TR()
    rating_table <= rating_scoring_row
    col = html.TD(html.B(f"{scoring_name} :"))
    rating_scoring_row <= col
    for role_name in ratings:
        score_dis = float(score_table[role_name])
        role_score = f"{score_dis:.2f}"
        col = html.TD(role_score)
        rating_scoring_row <= col

    rolename2role_id = {VARIANT_DATA.name_table[v]: k for k, v in VARIANT_DATA.roles.items()}
    id2pseudo = {v: k for k, v in PLAYERS_DICT.items()}
    role2pseudo = {v: k for k, v in GAME_PLAYERS_DICT.items()}

    # player
    players_row = html.TR()
    rating_table <= players_row
    col = html.TD(html.B("Joueurs :"))
    players_row <= col
    for role_name in ratings:
        role_id = rolename2role_id[role_name]
        pseudo_there = ""
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        col = html.TD(pseudo_there)
        players_row <= col

    return rating_table


def non_playing_information():
    """ non_playing_information """

    # need to be connected
    if PSEUDO is None:
        return None

    # is game anonymous
    if not(moderate.check_modo(PSEUDO) or ROLE_ID == 0 or not GAME_PARAMETERS_LOADED['anonymous']):
        return None

    id2pseudo = {v: k for k, v in PLAYERS_DICT.items()}

    dangling_players = [p for p, d in GAME_PLAYERS_DICT.items() if d == - 1]
    if not dangling_players:
        return None

    info = "Les pseudos suivants sont alloués à la partie sans rôle : "
    for dangling_player_id_str in dangling_players:
        dangling_player_id = int(dangling_player_id_str)
        dangling_player = id2pseudo[dangling_player_id]
        info += f"{dangling_player} "

    return html.EM(info)


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
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def game_votes_reload(game_id):
    """ game_votes_reload """

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

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-votes/{game_id}"

    # extracting vote from a game : need token (or not?)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return votes


def game_note_reload(game_id):
    """ game_note_reload """

    content = None

    def reply_callback(req):
        nonlocal content
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return content


def load_static_stuff():
    """ load_static_stuff : loads global data """

    # need to be first since used in get_game_status()
    # get the players (all players)
    global PLAYERS_DICT
    PLAYERS_DICT = common.get_players()
    if not PLAYERS_DICT:
        alert("Erreur chargement info joueurs")
        return

    # from game name get variant name

    if 'GAME_VARIANT' not in storage:
        alert("ERREUR : variante introuvable")
        return

    global VARIANT_NAME_LOADED
    VARIANT_NAME_LOADED = storage['GAME_VARIANT']

    # from variant name get variant content

    global VARIANT_CONTENT_LOADED

    # optimization
    if VARIANT_NAME_LOADED in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
        VARIANT_CONTENT_LOADED = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[VARIANT_NAME_LOADED]
    else:
        VARIANT_CONTENT_LOADED = common.game_variant_content_reload(VARIANT_NAME_LOADED)
        if not VARIANT_CONTENT_LOADED:
            alert("Erreur chargement contenu variante")
            return
        memoize.VARIANT_CONTENT_MEMOIZE_TABLE[VARIANT_NAME_LOADED] = VARIANT_CONTENT_LOADED

    # selected interface (user choice)
    global INTERFACE_CHOSEN
    INTERFACE_CHOSEN = interface.get_interface_from_variant(VARIANT_NAME_LOADED)

    # from display chose get display parameters

    global INTERFACE_PARAMETERS_READ

    # optimization
    if (VARIANT_NAME_LOADED, INTERFACE_CHOSEN) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
        INTERFACE_PARAMETERS_READ = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)]
    else:
        INTERFACE_PARAMETERS_READ = common.read_parameters(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
        memoize.PARAMETERS_READ_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)] = INTERFACE_PARAMETERS_READ

    # build variant data
    global VARIANT_DATA

    # optimization
    if (VARIANT_NAME_LOADED, INTERFACE_CHOSEN) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
        VARIANT_DATA = memoize.VARIANT_DATA_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)]
    else:
        VARIANT_DATA = mapping.Variant(VARIANT_NAME_LOADED, VARIANT_CONTENT_LOADED, INTERFACE_PARAMETERS_READ)
        memoize.VARIANT_DATA_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)] = VARIANT_DATA

    # now for official map

    # like above
    interface_inforced = interface.get_inforced_interface_from_variant(VARIANT_NAME_LOADED)

    # optimization
    if (VARIANT_NAME_LOADED, interface_inforced) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
        inforced_interface_parameters_read = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, interface_inforced)]
    else:
        inforced_interface_parameters_read = common.read_parameters(VARIANT_NAME_LOADED, interface_inforced)
        memoize.PARAMETERS_READ_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, interface_inforced)] = inforced_interface_parameters_read

    # build variant data
    global INFORCED_VARIANT_DATA

    # optimization
    if (VARIANT_NAME_LOADED, interface_inforced) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
        INFORCED_VARIANT_DATA = memoize.VARIANT_DATA_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, interface_inforced)]
    else:
        INFORCED_VARIANT_DATA = mapping.Variant(VARIANT_NAME_LOADED, VARIANT_CONTENT_LOADED, inforced_interface_parameters_read)
        memoize.VARIANT_DATA_MEMOIZE_TABLE[(VARIANT_NAME_LOADED, interface_inforced)] = INFORCED_VARIANT_DATA


def load_dynamic_stuff():
    """ load_dynamic_stuff : loads global data """

    # now game parameters (dynamic since advancement is dynamic)
    global GAME_PARAMETERS_LOADED
    GAME_PARAMETERS_LOADED = common.game_parameters_reload(GAME)
    if not GAME_PARAMETERS_LOADED:
        alert("Erreur chargement paramètres")
        return

    global GAME_STATUS
    GAME_STATUS = get_game_status()

    # get the position from server
    global POSITION_LOADED
    POSITION_LOADED = common.game_position_reload(GAME_ID)
    if not POSITION_LOADED:
        alert("Erreur chargement position")
        return

    # digest the position
    global POSITION_DATA
    POSITION_DATA = mapping.Position(POSITION_LOADED, VARIANT_DATA)

    # need to be after game parameters (advancement -> season)
    global REPORT_LOADED
    REPORT_LOADED = game_report_reload(GAME_ID)
    if not REPORT_LOADED:
        alert("Erreur chargement rapport")
        return


def load_special_stuff():
    """ load_special_stuff : loads global data """

    global GAME_PLAYERS_DICT
    GAME_PLAYERS_DICT = {}

    if PSEUDO is None:
        return

    if not (moderate.check_modo(PSEUDO) or ROLE_ID == 0 or not GAME_PARAMETERS_LOADED['anonymous']):
        return

    # get the players of the game
    # need a token for this
    GAME_PLAYERS_DICT = get_game_players_data(GAME_ID)
    if not GAME_PLAYERS_DICT:
        alert("Erreur chargement joueurs de la partie")
        return


def stack_clock(frame, period):
    """ stack_clock """

    clock_icon_img = html.IMG(src="./images/clock.png", title=f"Cette page est rafraichie périodiquement toutes les {period} secondes")
    frame <= clock_icon_img


def stack_role_flag(frame):
    """ stack_role_flag """

    # role flag
    role = VARIANT_DATA.roles[ROLE_ID]
    role_name = VARIANT_DATA.name_table[role]
    role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{ROLE_ID}.jpg", title=role_name)
    frame <= role_icon_img


def stack_role_retreats(frame):
    """ stack_role_retreats """
    if ROLE_ID != 0:
        role = VARIANT_DATA.roles[ROLE_ID]
        info_retreats = POSITION_DATA.role_retreats(role)
        for info_retreat in info_retreats:
            frame <= html.DIV(info_retreat, Class='note')
            frame <= html.BR()


def stack_role_builds(frame):
    """ stack_role_builds """
    if ROLE_ID != 0:
        role = VARIANT_DATA.roles[ROLE_ID]
        nb_builds, nb_ownerships, nb_units, nb_free_centers = POSITION_DATA.role_builds(role)
        frame <= html.DIV(f"Vous avez {nb_ownerships} centre(s) pour {nb_units} unité(s) et {nb_free_centers} emplacement(s) libre(s). Vous {'construisez' if nb_builds > 0 else 'détruisez'} donc {abs(nb_builds)} fois.", Class='note')


DEADLINE_COL = None
COUNTDOWN_COL = None


def countdown():
    """ countdown """

    deadline_loaded = GAME_PARAMETERS_LOADED['deadline']

    # calculate display colour for deadline and countdown

    time_unit = 60 if GAME_PARAMETERS_LOADED['fast'] else 60 * 60
    approach_duration = 24 * 60 * 60

    colour = None
    time_stamp_now = time.time()
    # we are after deadline + grace
    if time_stamp_now > deadline_loaded + time_unit * GAME_PARAMETERS_LOADED['grace_duration']:
        colour = config.PASSED_GRACE_COLOUR
    # we are after deadline
    elif time_stamp_now > deadline_loaded:
        colour = config.PASSED_DEADLINE_COLOUR
    # deadline is today
    elif time_stamp_now > deadline_loaded - approach_duration:
        colour = config.APPROACHING_DEADLINE_COLOUR

    # set the colour
    if colour is not None:
        DEADLINE_COL.style = {
            'background-color': colour
        }

    # calculate text value of countdown

    time_stamp_now = time.time()
    remains = int(deadline_loaded - time_stamp_now)

    if remains < 0:
        late = - remains
        if late < 60:
            countdown_text = f"passée de {late:02}s !"
        elif late < 3600:
            countdown_text = f"passée de {late // 60:02}mn {late % 60:02}s !"
        elif late < 24 * 3600:
            countdown_text = f"passée de ~ {late // 3600:02}h !"
        else:
            countdown_text = f"passée de ~ {late // (24 * 3600)}j !"
    elif remains < 60:
        countdown_text = f"{remains:02}s"
    elif remains < 3600:
        countdown_text = f"{remains // 60:02}mn {remains % 60:02}s"
    elif remains < 24 * 3600:
        countdown_text = f"~ {remains // 3600:02}h"
    else:
        countdown_text = f"~ {remains // (24 * 3600)}j"

    # insert text
    COUNTDOWN_COL.text = countdown_text

    # set the colour
    if colour is not None:
        COUNTDOWN_COL.style = {
            'background-color': colour
        }


def get_game_master(game_id):
    """ get_game_master """

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return None

    masters_alloc = allocations_data['game_masters_dict']

    # get the game it self
    for master_id, games_id in masters_alloc.items():
        if game_id in games_id:
            for pseudo, identifier in PLAYERS_DICT.items():
                if str(identifier) == master_id:
                    return pseudo

    return None


def get_game_status():
    """ get_game__status """

    game_name = GAME_PARAMETERS_LOADED['name']
    game_description = GAME_PARAMETERS_LOADED['description']
    game_variant = GAME_PARAMETERS_LOADED['variant']

    state_loaded = GAME_PARAMETERS_LOADED['current_state']
    for possible_state_code, possible_state_desc in config.STATE_CODE_TABLE.items():
        if possible_state_desc == state_loaded:
            game_state_readable = possible_state_code
            break

    advancement_loaded = GAME_PARAMETERS_LOADED['current_advancement']
    advancement_season, advancement_year = common.get_season(advancement_loaded, VARIANT_DATA)
    advancement_season_readable = VARIANT_DATA.name_table[advancement_season]
    game_season = f"{advancement_season_readable} {advancement_year}"

    nb_max_cycles_to_play = GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
    last_year_played = common.get_last_year(nb_max_cycles_to_play, VARIANT_DATA)

    deadline_loaded = GAME_PARAMETERS_LOADED['deadline']
    datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
    deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
    deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
    game_deadline_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"

    game_status_table = html.TABLE()

    row = html.TR()

    col = html.TD(f"Partie {game_name} ({game_variant})")
    row <= col
    col = html.TD(f"id={GAME_ID}")
    row <= col
    col = html.TD(f"Etat {game_state_readable}")
    row <= col
    col = html.TD(f"Saison {game_season}")
    row <= col
    col = html.TD(f"Fin {last_year_played}")
    row <= col

    global DEADLINE_COL
    DEADLINE_COL = html.TD(f"DL {game_deadline_str}")
    row <= DEADLINE_COL

    global COUNTDOWN_COL
    COUNTDOWN_COL = html.TD("")
    row <= COUNTDOWN_COL

    game_status_table <= row

    row = html.TR()

    col = html.TD(game_description, colspan="7")
    row <= col
    game_status_table <= row

    if GAME_PARAMETERS_LOADED['fast']:
        row = html.TR()
        specific_information = html.DIV("Partie en direct : utiliser le bouton 'recharger la partie' du menu 'consulter'", Class='note')
        col = html.TD(specific_information, colspan="6")
        row <= col
        game_status_table <= row

    return game_status_table


def get_game_status_histo(variant_data, advancement_selected):
    """ get_game_status_histo """

    advancement_selected_season, advancement_selected_year = common.get_season(advancement_selected, variant_data)
    advancement_selected_season_readable = variant_data.name_table[advancement_selected_season]
    game_season = f"{advancement_selected_season_readable} {advancement_selected_year}"

    game_status_table = html.TABLE()
    row = html.TR()
    col = html.TD(f"Saison {game_season}")
    row <= col
    game_status_table <= row

    return game_status_table


def get_game_players_data(game_id):
    """ get_game_players_data : returns empty dict if problem """

    game_players_dict = {}

    def reply_callback(req):
        nonlocal game_players_dict
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return game_players_dict


def get_roles_submitted_orders(game_id):
    """ get_roles_submitted_orders : returns empty dict if problem """

    submitted_data = {}

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

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders-submitted/{game_id}"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return submitted_data


def show_position():
    """ show_position """

    position_data = None
    adv_last_moves = None
    fake_report_loaded = None

    def callback_refresh(_):
        """ callback_refresh """

        game_parameters_loaded = common.game_parameters_reload(GAME)
        if not game_parameters_loaded:
            alert("Erreur chargement paramètres")
            return

        if game_parameters_loaded['current_advancement'] == GAME_PARAMETERS_LOADED['current_advancement']:
            # no change it seeems
            InfoDialog("OK", "Rien de nouveau sous le soleil !", remove_after=config.REMOVE_AFTER)
            return

        alert("La position de la partie a changé !")
        load_dynamic_stuff()
        MY_SUB_PANEL.clear()
        load_option(None, 'consulter')

    def callback_export_sandbox(_):
        """ callback_export_sandbox """

        # action on importing game
        sandbox.import_position(POSITION_DATA)

        # action of going to sandbox page
        index.load_option(None, 'bac à sable')

    def callback_export_game_json(_):
        """ callback_export_game_json """

        json_return_dict = None

        def reply_callback(req):
            nonlocal json_return_dict
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de l'export json de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de l'export json de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return
            json_return_dict = req_result['content']
            json_text = json.dumps(json_return_dict, indent=4, ensure_ascii=False)

            # needed too for some reason
            MY_SUB_PANEL <= html.A(id='download_link')

            # perform actual exportation
            text_file_as_blob = window.Blob.new([json_text], {'type': 'text/plain'})
            download_link = document['download_link']
            download_link.download = f"diplomania_{GAME}_{GAME_ID}_json.txt"
            download_link.href = window.URL.createObjectURL(text_file_as_blob)
            document['download_link'].click()

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-export/{GAME_ID}"

        # getting game json export : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return True

    def transition_display_callback(_, advancement_selected):

        nonlocal position_data
        nonlocal fake_report_loaded

        def callback_render(_):
            """ callback_render """

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the centers
            VARIANT_DATA.render(ctx)

            # put the position
            position_data.render(ctx)

            # put the orders (if history)
            if orders_data:
                orders_data.render(ctx)

            # put the legends at the end
            VARIANT_DATA.render_legends(ctx)

        # current position is default
        orders_loaded = None
        fake_report_loaded = REPORT_LOADED
        position_data = POSITION_DATA
        orders_data = None

        if advancement_selected != last_advancement:

            transition_loaded = game_transition_reload(GAME_ID, advancement_selected)

            if transition_loaded:

                # retrieve stuff from history
                time_stamp = transition_loaded['time_stamp']
                report_loaded = transition_loaded['report_txt']
                fake_report_loaded = {'time_stamp': time_stamp, 'content': report_loaded}

                # digest the position
                position_loaded = transition_loaded['situation']
                position_data = mapping.Position(position_loaded, VARIANT_DATA)

                # digest the orders
                orders_loaded = transition_loaded['orders']
                orders_data = mapping.Orders(orders_loaded, position_data)

            else:

                # to force current map to be displayed
                advancement_selected = last_advancement

        # now we can display
        MY_SUB_PANEL.clear()
        #  MY_SUB_PANEL.attrs['style'] = 'display:table-row'

        # title
        MY_SUB_PANEL <= GAME_STATUS
        MY_SUB_PANEL <= html.BR()

        # create left side
        display_left = html.DIV(id='display_left')
        display_left.attrs['style'] = 'display: table-cell; width:500px; vertical-align: top; table-layout: fixed;'

        # put it in
        MY_SUB_PANEL <= display_left

        # put stuff in left side

        if advancement_selected != last_advancement:
            # display only if from history
            game_status = get_game_status_histo(VARIANT_DATA, advancement_selected)
            display_left <= game_status
            display_left <= html.BR()

        # create canvas
        map_size = VARIANT_DATA.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        ctx = canvas.getContext("2d")
        if ctx is None:
            alert("Il faudrait utiliser un navigateur plus récent !")
            return

        # put background (this will call the callback that display the whole map)
        img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
        img.bind('load', callback_render)

        display_left <= canvas
        display_left <= html.BR()

        ratings = position_data.role_ratings()
        colours = position_data.role_colours()
        game_scoring = GAME_PARAMETERS_LOADED['scoring']
        rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, colours, game_scoring)

        display_left <= rating_colours_window
        display_left <= html.BR()

        report_non_playing = non_playing_information()
        if report_non_playing is not None:
            display_left <= report_non_playing
            display_left <= html.BR()
            display_left <= html.BR()

        report_window = common.make_report_window(fake_report_loaded)
        display_left <= report_window

        # create right part
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # put it in
        MY_SUB_PANEL <= buttons_right

        # put stuff in right side

        # role flag if applicable
        if ROLE_ID is not None:
            stack_role_flag(buttons_right)

        buttons_right <= html.H3("Position")

        input_refresh = html.INPUT(type="submit", value="recharger la partie")
        input_refresh.bind("click", callback_refresh)
        buttons_right <= input_refresh

        buttons_right <= html.H3("Historique")

        input_first = html.INPUT(type="submit", value="derniers mouvements")
        input_first.bind("click", lambda e, a=adv_last_moves: transition_display_callback(e, a))
        buttons_right <= input_first
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_first = html.INPUT(type="submit", value="||<<")
        input_first.bind("click", lambda e, a=0: transition_display_callback(e, a))
        buttons_right <= input_first
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_previous = html.INPUT(type="submit", value="<")
        input_previous.bind("click", lambda e, a=advancement_selected - 1: transition_display_callback(e, a))
        buttons_right <= input_previous
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_next = html.INPUT(type="submit", value=">")
        input_next.bind("click", lambda e, a=advancement_selected + 1: transition_display_callback(e, a))
        buttons_right <= input_next
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_last = html.INPUT(type="submit", value=">>||")
        input_last.bind("click", lambda e, a=last_advancement: transition_display_callback(e, a))
        buttons_right <= input_last
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        for adv_sample in range(4, last_advancement, 5):

            adv_sample_season, adv_sample_year = common.get_season(adv_sample, VARIANT_DATA)
            adv_sample_season_readable = VARIANT_DATA.name_table[adv_sample_season]

            input_last = html.INPUT(type="submit", value=f"{adv_sample_season_readable} {adv_sample_year}")
            input_last.bind("click", lambda e, a=adv_sample: transition_display_callback(e, a))
            buttons_right <= input_last
            if adv_sample + 5 < last_advancement:
                buttons_right <= html.BR()
                buttons_right <= html.BR()

        buttons_right <= html.H3("Divers")

        input_export_sandbox = html.INPUT(type="submit", value="exporter vers le bac à sable")
        input_export_sandbox.bind("click", callback_export_sandbox)
        buttons_right <= input_export_sandbox
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        input_download_game_json = html.INPUT(type="submit", value="télécharger la partie au format JSON")
        input_download_game_json.bind("click", callback_export_game_json)
        buttons_right <= input_download_game_json
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        url = f"https://diplomania-gen.fr?game={GAME}"
        buttons_right <= f"Pour inviter un joueur à consulter la partie, lui envoyer le lien : '{url}'"
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        url = f"https://diplomania-gen.fr?game={GAME}&arrival=rejoindre"
        buttons_right <= f"Pour inviter un joueur à rejoindre la partie, lui envoyer le lien : '{url}'"
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-export/{GAME_ID}"
        buttons_right <= f"Pour une extraction automatique depuis le back-end utiliser : '{url}'"
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    last_advancement = GAME_PARAMETERS_LOADED['current_advancement']
    adv_last_moves = last_advancement
    while True:
        adv_last_moves -= 1
        if adv_last_moves % 5 in [0, 2]:
            break

    # initiates callback
    transition_display_callback(None, last_advancement)

    return True


def submit_orders():
    """ submit_orders """

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    selected_build_unit_type = None
    selected_build_zone = None
    automaton_state = None

    stored_event = None
    down_click_time = None
    selected_hovered_object = None

    input_definitive = None

    def cancel_submit_orders_callback(_, dialog):
        dialog.close()

    def submit_orders_callback(_, warned=False, dialog2=None):
        """ submit_orders_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez soumis les ordres : {messages}", remove_after=config.REMOVE_AFTER)

            adjudicated = req_result['adjudicated']
            if adjudicated:
                # seems to be things not updated if back to orders
                alert("La position de la partie a changé !")
                load_dynamic_stuff()
                MY_SUB_PANEL.clear()
                load_option(None, 'consulter')

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            role = VARIANT_DATA.roles[ROLE_ID]
            nb_builds, _, _, _ = POSITION_DATA.role_builds(role)
            if nb_builds > 0:
                nb_builds_done = orders_data.number()
                if nb_builds_done < nb_builds:
                    if not warned:
                        dialog = Dialog(f"Vous construisez {nb_builds_done} unités alors que vous avez droit à {nb_builds} unités. Vous êtes sûr ?", ok_cancel=True)
                        dialog.ok_button.bind("click", lambda e, w=True, d=dialog: submit_orders_callback(e, w, d))
                        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_submit_orders_callback(e, d))
                        return

        if dialog2:
            dialog2.close()

        names_dict = VARIANT_DATA.extract_names()
        names_dict_json = json.dumps(names_dict)

        inforced_names_dict = INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = json.dumps(inforced_names_dict)

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        definitive_value = input_definitive.checked

        json_dict = {
            'role_id': ROLE_ID,
            'pseudo': PSEUDO,
            'orders': orders_list_dict_json,
            'definitive': definitive_value,
            'names': names_dict_json,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-orders/{GAME_ID}"

        # submitting orders : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # complete orders
        orders_data.rest_hold(ROLE_ID if ROLE_ID != 0 else None)

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        stack_role_flag(buttons_right)
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        # we are in spring or autumn
        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

        stack_orders(buttons_right)

        if not orders_data.empty():
            put_erase_all(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        orders_data.erase_orders()

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        stack_role_flag(buttons_right)
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (clic-long pour effacer)", Class='instruction')
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum:
                if order_type.compatible(advancement_season):
                    input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[order_type])
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)

        # do not put erase all
        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def select_built_unit_type_callback(_, build_unit_type):
        """ select_built_unit_type_callback """

        nonlocal selected_build_unit_type
        nonlocal automaton_state
        nonlocal buttons_right

        if automaton_state == AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE:

            selected_build_unit_type = build_unit_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            legend_select_active = html.DIV("Sélectionner la zone où construire (cliquer sous la légende)", Class='instruction')
            buttons_right <= legend_select_active

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            # it is a zone we need now
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de l'attaque (cliquer sous la légende)", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée offensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée defensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(POSITION_DATA, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.DIV("Sélectionner l'unité convoyée", Class='instruction')
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de la retraite (cliquer sous la légende)", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.DISBAND_ORDER:

                # insert disband order
                order = mapping.Order(POSITION_DATA, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:

                legend_select_active = html.DIV("Sélectionner le type d'unité à construire", Class='instruction')
                buttons_right <= legend_select_active

                for unit_type in mapping.UnitTypeEnum:
                    input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[unit_type])
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, u=unit_type: select_built_unit_type_callback(e, u))
                    buttons_right <= html.BR()
                    buttons_right <= input_select

                automaton_state = AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE

            if selected_order_type is mapping.OrderTypeEnum.REMOVE_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_active = html.DIV("Sélectionner l'unité à retirer", Class='instruction')
                buttons_right <= legend_select_active

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_click(event):
        """ called when there is a click down then a click up separated by less than 'LONG_DURATION_LIMIT_SEC' sec """

        nonlocal selected_order_type
        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal selected_passive_unit
        nonlocal selected_dest_zone
        nonlocal selected_build_zone
        nonlocal buttons_right

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # this is a shortcut
        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                selected_order_type = mapping.OrderTypeEnum.ATTACK_ORDER
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_order_type = mapping.OrderTypeEnum.RETREAT_ORDER
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            # passthru

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_active_unit = POSITION_DATA.closest_unit(pos, False)
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_active_unit = POSITION_DATA.closest_unit(pos, True)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            # gm can pass orders on archive games
            if ROLE_ID != 0 and selected_active_unit.role != VARIANT_DATA.roles[ROLE_ID]:

                alert("Bien essayé, mais cette unité ne vous appartient pas (ou vous n'avez pas d'ordre à valider).")

                selected_active_unit = None

                # switch back to initial state selecting unit
                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                    legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
                    buttons_right <= legend_select_unit

                    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    legend_select_unit = html.DIV("Sélectionner l'ordre d'ajustement (clic-long pour effacer)", Class='instruction')
                    buttons_right <= legend_select_unit
                    for order_type in mapping.OrderTypeEnum:
                        if order_type.compatible(advancement_season):
                            input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[order_type])
                            buttons_right <= html.BR()
                            input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                            buttons_right <= html.BR()
                            buttons_right <= input_select

                    automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            else:

                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:

                    legend_selected_unit = html.DIV(f"L'unité active sélectionnée est {selected_active_unit}")
                    buttons_right <= legend_selected_unit

                legend_select_order = html.DIV("Sélectionner l'ordre (ou directement la destination - sous la légende)", Class='instruction')
                buttons_right <= legend_select_order
                buttons_right <= html.BR()

                legend_select_order21 = html.I("Raccourcis clavier :")
                buttons_right <= legend_select_order21
                buttons_right <= html.BR()

                for info in ["(a)ttaquer", "soutenir (o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer", "(x)supprimer l'ordre"]:
                    legend_select_order22 = html.I(info)
                    buttons_right <= legend_select_order22
                    buttons_right <= html.BR()

                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(advancement_season):
                        input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[order_type])
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, None)
                    orders_data.insert_order(order)

                    # update map
                    callback_render(None)

                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_dest_zone = VARIANT_DATA.closest_zone(pos)
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                selected_build_zone = VARIANT_DATA.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.DISBAND_ORDER
                    selected_dest_zone = None
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:
                # create fake unit
                region = selected_build_zone.region
                center = region.center
                if center is not None:
                    deducted_role = center.owner_start
                    if deducted_role is not None:
                        if ROLE_ID in (0, deducted_role.identifier):
                            if selected_build_unit_type is mapping.UnitTypeEnum.ARMY_UNIT:
                                fake_unit = mapping.Army(POSITION_DATA, deducted_role, selected_build_zone, None)
                            if selected_build_unit_type is mapping.UnitTypeEnum.FLEET_UNIT:
                                fake_unit = mapping.Fleet(POSITION_DATA, deducted_role, selected_build_zone, None)
                            # create order
                            order = mapping.Order(POSITION_DATA, selected_order_type, fake_unit, None, None)
                            orders_data.insert_order(order)
                        else:
                            alert("Bien essayé, mais ce centre ne vous appartient pas !")
                    else:
                        alert("On ne peut pas construire sur ce centre !")
                else:
                    alert("Pas de centre à cet endroit !")

            # update map
            callback_render(None)

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                legend_select_unit = html.DIV("Sélectionner l'ordre d'ajustement (clic-long pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit
                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(advancement_season):
                        input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[order_type])
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = POSITION_DATA.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                stack_orders(buttons_right)
                if not orders_data.empty():
                    put_erase_all(buttons_right)
                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                    put_rest_hold(buttons_right)
                if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    buttons_right <= html.BR()
                    put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination de l'attaque soutenue (cliquer sous la légende)", Class='instruction')
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination du convoi (cliquer sous la légende)", Class='instruction')
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_canvas_long_click(event):
        """
        called when there is a click down then a click up separated by more than 'LONG_DURATION_LIMIT_SEC' sec
        or when pressing 'x' in which case a None is passed
        """

        nonlocal automaton_state
        nonlocal buttons_right

        # the aim is to give this variable a value
        selected_erase_unit = None

        # first : take from event
        if event:

            # where is the click
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

            # moves : select unit : easy case
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_erase_unit = POSITION_DATA.closest_unit(pos, False)

            # retreat : select dislodged unit : easy case
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_erase_unit = POSITION_DATA.closest_unit(pos, True)

            #  builds : tougher case : we take the build units into account
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                selected_erase_unit = orders_data.closest_unit_or_built_unit(pos)

        # event is None when coming from x pressed, then take 'selected_active_unit' (that can be None)
        if selected_erase_unit is None:
            selected_erase_unit = selected_active_unit

        # unit must be selected
        if selected_erase_unit is None:
            return

        # unit must have an order
        if not orders_data.is_ordered(selected_erase_unit):
            return

        # remove order
        orders_data.remove_order(selected_erase_unit)

        # update map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        stack_role_flag(buttons_right)
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (clic-long pour effacer)", Class='instruction')
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum:
                if order_type.compatible(advancement_season):
                    input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[order_type])
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)
        if not orders_data.empty():
            put_erase_all(buttons_right)
        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_mousedown(event):
        """ callback_mousedow : store event"""

        nonlocal down_click_time
        nonlocal stored_event

        down_click_time = time.time()
        stored_event = event

    def callback_canvas_mouseup(_):
        """ callback_mouseup : retrieve event and pass it"""

        nonlocal down_click_time

        if down_click_time is None:
            return

        # get click duration
        up_click_time = time.time()
        click_duration = up_click_time - down_click_time
        down_click_time = None

        # slow : call
        if click_duration > LONG_DURATION_LIMIT_SEC:
            callback_canvas_long_click(stored_event)
            return

        # normal : call s
        callback_canvas_click(stored_event)

    def callback_keypress(event):
        """ callback_keypress """

        char = chr(event.charCode).lower()

        # order removal : special
        if char == 'x':
            # pass to double click
            callback_canvas_long_click(None)
            return

        # order shortcut
        selected_order = mapping.OrderTypeEnum.shortcut(char)
        if selected_order is None:
            return

        select_order_type_callback(event, selected_order)

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

        if selected_hovered_object != prev_selected_hovered_object:

            helper.clear()

            # put back previous
            if prev_selected_hovered_object is not None:
                prev_selected_hovered_object.highlite(ctx, False)

            # hightlite object where mouse is
            if selected_hovered_object is not None:
                selected_hovered_object.highlite(ctx, True)
                if isinstance(selected_hovered_object, mapping.Highliteable):
                    helper <= selected_hovered_object.description()
                else:
                    helper <= "."
            else:
                helper <= "."

            # redraw all arrows
            if prev_selected_hovered_object is not None or selected_hovered_object is not None:
                orders_data.render(ctx)

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """

        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, False)
            # redraw all arrows
            orders_data.render(ctx)

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the orders
        orders_data.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

    def stack_orders(buttons_right):
        """ stack_orders """

        buttons_right <= html.P()
        lines = str(orders_data).split('\n')
        orders = html.DIV()
        for line in lines:
            orders <= html.B(line)
            orders <= html.BR()
        buttons_right <= orders

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="effacer tout")
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_rest_hold(buttons_right):
        """ put_rest_hold """

        input_rest_hold = html.INPUT(type="submit", value="tout le reste tient")
        input_rest_hold.bind("click", rest_hold_callback)
        buttons_right <= html.BR()
        buttons_right <= input_rest_hold
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        nonlocal input_definitive

        label_definitive = html.LABEL("D'accord pour la résolution ?")
        buttons_right <= label_definitive

        definitive_value = ROLE_ID in submitted_data['agreed']

        input_definitive = html.INPUT(type="checkbox", checked=definitive_value)
        buttons_right <= input_definitive
        buttons_right <= html.BR()

        input_submit = html.INPUT(type="submit", value="soumettre ces ordres")
        input_submit.bind("click", submit_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        buttons_right <= html.DIV("La soumission des ordres prend également en compte le fait d'être d\'accord pour la résolution", Class='instruction')
        buttons_right <= html.BR()
        buttons_right <= html.DIV("Le coche 'd\'accord pour la résolution' est obligatoire à un moment donné (de préférence avant la date limite)", Class='important')
        if GAME_PARAMETERS_LOADED['nomessage_current']:
            buttons_right <= html.BR()
            buttons_right <= html.DIV("Pour communiquer avec des ordres (ordres invalides) utilisez le sous menu 'taguer'", Class='Note')

    # need to be connected
    if PSEUDO is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'consulter')
        return False

    # need to have a role
    if ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    # cannot be game master unless archive game
    if ROLE_ID == 0 and not GAME_PARAMETERS_LOADED['archive']:
        alert("Ordonner pour un arbitre n'est possible que pour les parties archive")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not waiting
    if GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not finished
    if GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        load_option(None, 'consulter')
        return False

    # need to have orders to submit

    submitted_data = get_roles_submitted_orders(GAME_ID)
    if not submitted_data:
        alert("Erreur chargement données de soumission")
        load_option(None, 'consulter')
        return False

    if ROLE_ID == 0:
        if not submitted_data['needed']:
            alert("Il n'y a pas d'ordre à passer")
            load_option(None, 'consulter')
            return False
    else:
        if ROLE_ID not in submitted_data['needed']:
            alert("Vous n'avez pas d'ordre à passer")
            load_option(None, 'consulter')
            return False

    # check gameover
    # game over when adjustments to play
    # game over when last year
    current_advancement = GAME_PARAMETERS_LOADED['current_advancement']
    nb_max_cycles_to_play = GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
    if current_advancement % 5 == 4 and (current_advancement + 1) // 5 >= nb_max_cycles_to_play:
        alert("La partie est arrivée à échéance")
        load_option(None, 'consulter')
        return False

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # now we can display

    # header

    # game status
    MY_SUB_PANEL <= GAME_STATUS

    advancement_loaded = GAME_PARAMETERS_LOADED['current_advancement']
    advancement_season, _ = common.get_season(advancement_loaded, VARIANT_DATA)

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return True

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    # get the orders from server
    orders_loaded = game_orders_reload(GAME_ID)
    if not orders_loaded:
        alert("Erreur chargement ordres")
        load_option(None, 'consulter')
        return False

    # digest the orders
    orders_data = mapping.Orders(orders_loaded, POSITION_DATA)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', callback_render)

    ratings = POSITION_DATA.role_ratings()
    colours = POSITION_DATA.role_colours()
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, colours, game_scoring)

    report_window = common.make_report_window(REPORT_LOADED)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    helper = html.DIV(".")
    display_left <= helper
    display_left <= canvas
    display_left <= html.BR()
    display_left <= rating_colours_window
    display_left <= html.BR()

    # all reports until last moves
    advancement_selected = GAME_PARAMETERS_LOADED['current_advancement']

    while True:

        # one backwards
        advancement_selected -= 1

        # out of scope : done
        if advancement_selected < 0:
            break

        transition_loaded = game_transition_reload(GAME_ID, advancement_selected)
        if not transition_loaded:
            break

        time_stamp = transition_loaded['time_stamp']
        report_loaded = transition_loaded['report_txt']

        fake_report_loaded = {'time_stamp': time_stamp, 'content': report_loaded}
        report_window = common.make_report_window(fake_report_loaded)

        game_status = get_game_status_histo(VARIANT_DATA, advancement_selected)
        display_left <= game_status
        display_left <= report_window
        display_left <= html.BR()

        # just displayed last moves : done
        if advancement_selected % 5 in [0, 2]:
            break

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    stack_role_flag(buttons_right)
    buttons_right <= html.BR()
    buttons_right <= html.BR()

    # first time : we alert about retreat possibilities
    if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        stack_role_retreats(buttons_right)
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    # first time : we alert about build stat
    if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        stack_role_builds(buttons_right)
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (clic-long pour effacer)", Class='instruction')
        buttons_right <= legend_select_order
        for order_type in mapping.OrderTypeEnum:
            if order_type.compatible(advancement_season):
                input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[order_type])
                buttons_right <= html.BR()
                input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                buttons_right <= html.BR()
                buttons_right <= input_select
        automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

    stack_orders(buttons_right)
    if not orders_data.empty():
        put_erase_all(buttons_right)
    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
        put_rest_hold(buttons_right)
    if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        buttons_right <= html.BR()
        put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    MY_SUB_PANEL <= my_sub_panel2

    return True


def submit_communication_orders():
    """ submit_orders """

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    selected_build_zone = None
    automaton_state = None

    stored_event = None
    down_click_time = None
    selected_hovered_object = None

    def submit_orders_callback(_):
        """ submit_orders_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de communication : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de communication : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez déposé les ordres de communcation : {messages}", remove_after=config.REMOVE_AFTER)

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        json_dict = {
            'role_id': ROLE_ID,
            'pseudo': PSEUDO,
            'orders': orders_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-communication-orders/{GAME_ID}"

        # submitting orders : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        orders_data.erase_orders()

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        stack_role_flag(buttons_right)
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        buttons_right <= html.BR()
        put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de l'attaque (cliquer sous la légende)", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée offensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée defensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(POSITION_DATA, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.DIV("Sélectionner l'unité convoyée", Class='instruction')
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_click(event):
        """ called when there is a click down then a click up separated by less than 'LONG_DURATION_LIMIT_SEC' sec """

        nonlocal selected_order_type
        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal selected_passive_unit
        nonlocal selected_dest_zone
        nonlocal selected_build_zone
        nonlocal buttons_right

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # this is a shortcut
        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = mapping.OrderTypeEnum.ATTACK_ORDER
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            # passthru

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:

            selected_active_unit = POSITION_DATA.closest_unit(pos, None)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            # gm can pass orders on archive games
            if ROLE_ID != 0 and selected_active_unit.role != VARIANT_DATA.roles[ROLE_ID]:

                alert("Bien essayé, mais cette unité ne vous appartient pas (ou vous n'avez pas d'ordre à valider).")

                selected_active_unit = None

                # switch back to initial state selecting unit
                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            else:

                legend_selected_unit = html.DIV(f"L'unité active sélectionnée est {selected_active_unit}")
                buttons_right <= legend_selected_unit

                legend_select_order = html.DIV("Sélectionner l'ordre (ou directement la destination - sous la légende)", Class='instruction')
                buttons_right <= legend_select_order
                buttons_right <= html.BR()

                legend_select_order21 = html.I("Raccourcis clavier :")
                buttons_right <= legend_select_order21
                buttons_right <= html.BR()

                for info in ["(a)ttaquer", "soutenir (o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer", "(x)supprimer l'ordre"]:
                    legend_select_order22 = html.I(info)
                    buttons_right <= legend_select_order22
                    buttons_right <= html.BR()

                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(mapping.SeasonEnum.SPRING_SEASON):
                        input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[order_type])
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            selected_dest_zone = VARIANT_DATA.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone)
                orders_data.insert_order(order)

            # update map
            callback_render(None)

            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = POSITION_DATA.closest_unit(pos, None)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)
            buttons_right <= html.BR()
            buttons_right <= html.BR()

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                stack_orders(buttons_right)
                if not orders_data.empty():
                    put_erase_all(buttons_right)
                buttons_right <= html.BR()
                put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination de l'attaque soutenue (cliquer sous la légende)", Class='instruction')
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination du convoi (cliquer sous la légende)", Class='instruction')
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_canvas_long_click(event):
        """
        called when there is a click down then a click up separated by more than 'LONG_DURATION_LIMIT_SEC' sec
        or when pressing 'x' in which case a None is passed
        """

        nonlocal automaton_state
        nonlocal buttons_right

        # the aim is to give this variable a value
        selected_erase_unit = None

        # first : take from event
        if event:

            # where is the click
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

            # moves : select unit : easy case
            selected_erase_unit = POSITION_DATA.closest_unit(pos, None)

        # event is None when coming from x pressed, then take 'selected_active_unit' (that can be None)
        if selected_erase_unit is None:
            selected_erase_unit = selected_active_unit

        # unit must be selected
        if selected_erase_unit is None:
            return

        # unit must have an order
        if not orders_data.is_ordered(selected_erase_unit):
            return

        # remove order
        orders_data.remove_order(selected_erase_unit)

        # update map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        stack_role_flag(buttons_right)
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not orders_data.empty():
            put_erase_all(buttons_right)
        buttons_right <= html.BR()
        put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_mousedown(event):
        """ callback_mousedow : store event"""

        nonlocal down_click_time
        nonlocal stored_event

        down_click_time = time.time()
        stored_event = event

    def callback_canvas_mouseup(_):
        """ callback_mouseup : retrieve event and pass it"""

        nonlocal down_click_time

        if down_click_time is None:
            return

        # get click duration
        up_click_time = time.time()
        click_duration = up_click_time - down_click_time
        down_click_time = None

        # slow : call
        if click_duration > LONG_DURATION_LIMIT_SEC:
            callback_canvas_long_click(stored_event)
            return

        # normal : call s
        callback_canvas_click(stored_event)

    def callback_keypress(event):
        """ callback_keypress """

        char = chr(event.charCode).lower()

        # order removal : special
        if char == 'x':
            # pass to double click
            callback_canvas_long_click(None)
            return

        # order shortcut
        selected_order = mapping.OrderTypeEnum.shortcut(char)
        if selected_order is None:
            return

        select_order_type_callback(event, selected_order)

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

        if selected_hovered_object != prev_selected_hovered_object:

            helper.clear()

            # put back previous
            if prev_selected_hovered_object is not None:
                prev_selected_hovered_object.highlite(ctx, False)

            # hightlite object where mouse is
            if selected_hovered_object is not None:
                selected_hovered_object.highlite(ctx, True)
                if isinstance(selected_hovered_object, mapping.Highliteable):
                    helper <= selected_hovered_object.description()
                else:
                    helper <= "."
            else:
                helper <= "."

            # redraw all arrows
            if prev_selected_hovered_object is not None or selected_hovered_object is not None:
                orders_data.render(ctx)

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """

        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, False)
            # redraw all arrows
            orders_data.render(ctx)

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the orders
        orders_data.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

    def stack_orders(buttons_right):
        """ stack_orders """

        buttons_right <= html.P()
        lines = str(orders_data).split('\n')
        communication_orders = html.DIV()
        communication_orders.style = {
            'color': 'magenta',
        }
        for line in lines:
            communication_orders <= html.B(line)
            communication_orders <= html.BR()
        buttons_right <= communication_orders

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="effacer tout")
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="enregistrer ces ordres")
        input_submit.bind("click", submit_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        buttons_right <= html.DIV("ATTENTION ! Ce sont des ordres pour communiquer avec les autres joueurs, pas des ordres pour les unités. Ils seront publiés à la prochaine résolution pourvu que l'unité en question ait reçu l'ordre *réel* de rester en place ou de se disperser.", Class='important')

    # need to be connected
    if PSEUDO is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'consulter')
        return False

    # need to have a role
    if ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    # cannot be game master
    if ROLE_ID == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not waiting
    if GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not finished
    if GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        load_option(None, 'consulter')
        return False

    # need to have orders to submit

    submitted_data = get_roles_submitted_orders(GAME_ID)
    if not submitted_data:
        alert("Erreur chargement données de soumission")
        load_option(None, 'consulter')
        return False

    if ROLE_ID not in submitted_data['needed']:
        alert("Vous n'avez pas d'ordre à passer")
        load_option(None, 'consulter')
        return False

    # check gameover
    # game over when adjustments to play
    # game over when last year
    current_advancement = GAME_PARAMETERS_LOADED['current_advancement']
    nb_max_cycles_to_play = GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
    if current_advancement % 5 == 4 and (current_advancement + 1) // 5 >= nb_max_cycles_to_play:
        alert("La partie est arrivée à échéance")
        load_option(None, 'consulter')
        return False

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # now we can display

    # header

    # game status
    MY_SUB_PANEL <= GAME_STATUS

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return True

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    # get the orders from server
    communication_orders_loaded = game_communication_orders_reload(GAME_ID)
    if not communication_orders_loaded:
        alert("Erreur chargement ordres communication")
        load_option(None, 'consulter')
        return False

    # digest the orders
    orders_data = mapping.Orders(communication_orders_loaded, POSITION_DATA)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', callback_render)

    ratings = POSITION_DATA.role_ratings()
    colours = POSITION_DATA.role_colours()
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, colours, game_scoring)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    helper = html.DIV(".")
    display_left <= helper
    display_left <= canvas
    display_left <= html.BR()
    display_left <= rating_colours_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    stack_role_flag(buttons_right)
    buttons_right <= html.BR()
    buttons_right <= html.BR()

    legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long pour effacer)", Class='instruction')
    buttons_right <= legend_select_unit
    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    stack_orders(buttons_right)
    if not orders_data.empty():
        put_erase_all(buttons_right)
    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    MY_SUB_PANEL <= my_sub_panel2

    return True


def negotiate():
    """ negotiate """

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

    def add_message_callback(_):
        """ add_message_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de message dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de message dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le message a été envoyé ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            global CONTENT_BACKUP
            CONTENT_BACKUP = None
            MY_SUB_PANEL.clear()
            negotiate()

        dest_role_ids = ' '.join([str(role_num) for (role_num, button) in selected.items() if button.checked])

        content = input_message.value

        # keep a backup
        global CONTENT_BACKUP
        CONTENT_BACKUP = content

        if not content:
            alert("Pas de contenu pour ce message !")
            MY_SUB_PANEL.clear()
            negotiate()
            return

        if not dest_role_ids:
            alert("Pas de destinataire pour ce message !")
            MY_SUB_PANEL.clear()
            negotiate()
            return

        json_dict = {
            'dest_role_ids': dest_role_ids,
            'role_id': ROLE_ID,
            'pseudo': PSEUDO,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{GAME_ID}"

        # adding a message in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def messages_reload(game_id):
        """ messages_reload """

        messages = []

        def reply_callback(req):
            nonlocal messages
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des messages dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des messages dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = req_result['messages_list']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{game_id}"

        # extracting messages from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return messages

    if ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(GAME_ID, config.MESSAGES_TYPE)

    # put time stamp of last visit of declarations as now
    date_last_visit_update(GAME_ID, PSEUDO, ROLE_ID, config.MESSAGES_TYPE)

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre message", title="Qu'avez vous à lui/leur dire ?")
    fieldset <= legend_declaration
    input_message = html.TEXTAREA(type="text", rows=8, cols=80)
    if CONTENT_BACKUP is not None:
        input_message <= CONTENT_BACKUP
    fieldset <= input_message
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_destinees = html.LEGEND("Destinataire(s)", title="Et à qui ?")
    fieldset <= legend_destinees

    table = html.TABLE()
    row = html.TR()
    selected = {}
    for role_id_dest in range(VARIANT_CONTENT_LOADED['roles']['number'] + 1):

        # dest only if allowed
        if GAME_PARAMETERS_LOADED['nomessage_current']:
            if not (ROLE_ID == 0 or role_id_dest == 0):
                continue

        role_dest = VARIANT_DATA.roles[role_id_dest]
        role_name = VARIANT_DATA.name_table[role_dest]
        role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id_dest}.jpg", title=role_name)

        # the alternative
        input_dest = html.INPUT(type="checkbox", id=str(role_id_dest), name="destinees")
        col = html.TD()
        col <= input_dest

        # necessary to link flag with button
        label_dest = html.LABEL(role_icon_img, for_=str(role_id_dest))
        col <= label_dest

        row <= col

        selected[role_id_dest] = input_dest

    table <= row
    fieldset <= table
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="envoyer le message")
    input_declare_in_game.bind("click", add_message_callback)
    form <= input_declare_in_game

    # now we display messages

    messages = messages_reload(GAME_ID)
    # there can be no message (if no message of failed to load)

    # insert new field 'synchro'
    messages = [(False, 0, i, f, t, d, c) for (i, f, t, d, c) in messages]

    # get the transition table
    game_transitions = game_transitions_reload(GAME_ID)

    # add fake messages (game transitions) and sort
    fake_messages = [(True, int(k), -1, -1, v, [], readable_season(int(k))) for k, v in game_transitions.items()]
    messages.extend(fake_messages)
    messages.sort(key=lambda d: (d[4], d[1]), reverse=True)

    messages_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Destinataire(s)', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    messages_table <= thead

    game_master_pseudo = get_game_master(int(GAME_ID))
    role2pseudo = {v: k for k, v in GAME_PLAYERS_DICT.items()}
    id2pseudo = {v: k for k, v in PLAYERS_DICT.items()}

    for synchro, _, id_, from_role_id_msg, time_stamp, dest_role_id_msgs, content in messages:

        if synchro:
            class_ = 'synchro'
        else:
            class_ = 'text'

        row = html.TR()

        id_txt = str(id_) if id_ != -1 else ""
        col = html.TD(id_txt, Class=class_)
        row <= col

        date_desc_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
        date_desc_gmt_str = datetime.datetime.strftime(date_desc_gmt, "%d-%m-%Y %H:%M:%S")

        col = html.TD(f"{date_desc_gmt_str} GMT", Class=class_)
        row <= col

        col = html.TD(Class=class_)

        if from_role_id_msg != -1:

            role = VARIANT_DATA.roles[from_role_id_msg]
            role_name = VARIANT_DATA.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{from_role_id_msg}.jpg", title=role_name)
            col <= role_icon_img

            # player
            pseudo_there = ""
            if from_role_id_msg == 0:
                if game_master_pseudo:
                    pseudo_there = game_master_pseudo
            elif from_role_id_msg in role2pseudo:
                player_id_str = role2pseudo[from_role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]

            if pseudo_there:
                col <= html.BR()
                col <= pseudo_there

        row <= col

        col = html.TD(Class=class_)

        for dest_role_id_msg in dest_role_id_msgs:

            role = VARIANT_DATA.roles[dest_role_id_msg]
            role_name = VARIANT_DATA.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{dest_role_id_msg}.jpg", title=role_name)

            # player
            pseudo_there = ""
            if dest_role_id_msg == 0:
                if game_master_pseudo:
                    pseudo_there = game_master_pseudo
            elif dest_role_id_msg in role2pseudo:
                player_id_str = role2pseudo[dest_role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]

            col <= role_icon_img
            if pseudo_there:
                col <= html.BR()
                col <= pseudo_there

            # separator
            col <= html.BR()

        row <= col

        col = html.TD(Class=class_)

        for line in content.split('\n'):
            # new so put in bold
            if time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        messages_table <= row

    # now we can display

    # header

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return False

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', callback_render)

    MY_SUB_PANEL <= canvas
    MY_SUB_PANEL <= html.BR()

    # ratings
    ratings = POSITION_DATA.role_ratings()
    colours = POSITION_DATA.role_colours()
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, colours, game_scoring)
    MY_SUB_PANEL <= rating_colours_window
    MY_SUB_PANEL <= html.BR()

    # role
    stack_role_flag(MY_SUB_PANEL)
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # form
    MY_SUB_PANEL <= form
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # advice to report
    label_unsuitable_content = html.DIV(Class="important")
    label_unsuitable_content <= "Attention, les messages sont privés entre émetteur et destinataire(s) mais doivent respecter la charte. L'administrateur peut sur demande les lire pour vérifier. Si cela ne vous convient pas, quittez le site. Contenu inaproprié ? Déclarez un incident ! (reperez le message par son id)"
    MY_SUB_PANEL <= label_unsuitable_content
    MY_SUB_PANEL <= html.BR()

    # messages already
    MY_SUB_PANEL <= messages_table
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    information = html.DIV(Class='note')
    information <= "Le pseudo affiché est celui du joueur en cours, pas forcément celui de l'auteur réel du message"
    MY_SUB_PANEL <= information

    return True


def declare():
    """ declare """

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

    def add_declaration_callback(_):
        """ add_declaration_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de déclaration dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de déclaration dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La déclaration a été faite ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            declare()

        anonymous = input_anonymous.checked

        content = input_declaration.value

        if not content:
            alert("Pas de contenu pour cette déclaration !")
            MY_SUB_PANEL.clear()
            declare()
            return

        json_dict = {
            'role_id': ROLE_ID,
            'pseudo': PSEUDO,
            'anonymous': anonymous,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{GAME_ID}"

        # adding a declaration in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def declarations_reload(game_id):
        """ declarations_reload """

        declarations = []

        def reply_callback(req):
            nonlocal declarations
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de déclarations dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de déclarations dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            declarations = req_result['declarations_list']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{game_id}"

        # extracting declarations from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return declarations

    if ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(GAME_ID, config.DECLARATIONS_TYPE)

    # put time stamp of last visit of declarations as now
    date_last_visit_update(GAME_ID, PSEUDO, ROLE_ID, config.DECLARATIONS_TYPE)

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre déclaration", title="Qu'avez vous à déclarer à tout le monde ?")
    fieldset <= legend_declaration
    input_declaration = html.TEXTAREA(type="text", rows=8, cols=80)
    fieldset <= input_declaration
    form <= fieldset

    fieldset = html.FIELDSET()
    label_anonymous = html.LABEL("En restant anonyme ? (pas anonyme auprès de l'arbitre cependant)")
    fieldset <= label_anonymous
    input_anonymous = html.INPUT(type="checkbox")
    fieldset <= input_anonymous
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="déclarer dans la partie")
    input_declare_in_game.bind("click", add_declaration_callback)
    form <= input_declare_in_game

    # now we display declarations

    declarations = declarations_reload(GAME_ID)
    # there can be no message (if no declaration of failed to load)

    # insert new field 'synchro'
    declarations = [(False, 0, i, a, r, t, c) for (i, a, r, t, c) in declarations]

    # get the transition table
    game_transitions = game_transitions_reload(GAME_ID)

    # add fake declarations (game transitions) and sort
    fake_declarations = [(True, int(k), -1, False, -1, v, readable_season(int(k))) for k, v in game_transitions.items()]
    declarations.extend(fake_declarations)
    declarations.sort(key=lambda d: (d[5], d[1]), reverse=True)

    declarations_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    declarations_table <= thead

    game_master_pseudo = get_game_master(int(GAME_ID))
    role2pseudo = {v: k for k, v in GAME_PLAYERS_DICT.items()}
    id2pseudo = {v: k for k, v in PLAYERS_DICT.items()}

    for synchro, _, id_, anonymous, role_id_msg, time_stamp, content in declarations:

        if synchro:
            class_ = 'synchro'
        elif anonymous:
            class_ = 'text_anonymous'
        else:
            class_ = 'text'

        row = html.TR()

        id_txt = str(id_) if id_ != -1 else ""
        col = html.TD(id_txt, Class=class_)
        row <= col

        date_desc_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
        date_desc_gmt_str = datetime.datetime.strftime(date_desc_gmt, "%d-%m-%Y %H:%M:%S")

        col = html.TD(f"{date_desc_gmt_str} GMT", Class=class_)
        row <= col

        role_icon_img = ""
        pseudo_there = ""
        if role_id_msg != -1:

            role = VARIANT_DATA.roles[role_id_msg]
            role_name = VARIANT_DATA.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id_msg}.jpg", title=role_name)

            # player
            if role_id_msg == 0:
                if game_master_pseudo:
                    pseudo_there = game_master_pseudo
            elif role_id_msg in role2pseudo:
                player_id_str = role2pseudo[role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]

        col = html.TD(Class=class_)

        col <= role_icon_img
        if pseudo_there:
            col <= html.BR()
            col <= pseudo_there

        row <= col

        col = html.TD(Class=class_)

        for line in content.split('\n'):
            # new so put in bold
            if time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        declarations_table <= row

    # now we can display

    # header

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return False

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', callback_render)

    MY_SUB_PANEL <= canvas
    MY_SUB_PANEL <= html.BR()

    # ratings
    ratings = POSITION_DATA.role_ratings()
    colours = POSITION_DATA.role_colours()
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, colours, game_scoring)
    MY_SUB_PANEL <= rating_colours_window
    MY_SUB_PANEL <= html.BR()

    # role
    stack_role_flag(MY_SUB_PANEL)
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # form only if allowed
    if GAME_PARAMETERS_LOADED['nopress_current'] and ROLE_ID != 0:
        MY_SUB_PANEL <= html.P("Cette partie est sans presse des joueurs")
    else:
        # form
        MY_SUB_PANEL <= form
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()

    # advice to report
    label_unsuitable_content = html.DIV(Class="important")
    label_unsuitable_content <= "Attention, les déclarations sont privées entre joueurs de la partie mais doivent respecter la charte. L'administrateur peut les lire pour vérifier. Si cela ne vous convient pas, quittez le site. Contenu inaproprié ? Déclarez un incident ! (reperez la déclaration par son id)"
    MY_SUB_PANEL <= label_unsuitable_content
    MY_SUB_PANEL <= html.BR()

    # declarations already
    MY_SUB_PANEL <= declarations_table
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    information = html.DIV(Class='note')
    information <= "Le pseudo affiché est celui du joueur en cours, pas forcément celui de l'auteur réel du message"
    MY_SUB_PANEL <= information

    return True


def vote():
    """ vote """

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

    def add_vote_callback(_):
        """ add_vote_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de vote d'arrêt dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de vote d'arrêt dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le vote a été enregistré ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            vote()

        vote_value = input_vote.checked

        json_dict = {
            'role_id': ROLE_ID,
            'pseudo': PSEUDO,
            'value': vote_value
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-votes/{GAME_ID}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        vote()

    # from game id and token get role_id of player

    if ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    if ROLE_ID == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not waiting
    if GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not finished
    if GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        load_option(None, 'consulter')
        return False

    votes = game_votes_reload(GAME_ID)
    if votes is None:
        alert("Erreur chargement votes")
        load_option(None, 'consulter')
        return False
    votes = list(votes)

    vote_value = False
    for _, role, vote_val in votes:
        if role == ROLE_ID:
            vote_value = bool(vote_val)
            break

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_vote = html.LEGEND("Cochez pour voter l'arrêt", title="Etes vous d'accord pour terminer la partie en l'état ?")
    fieldset <= legend_vote
    form <= fieldset
    input_vote = html.INPUT(type="checkbox", checked=vote_value)
    fieldset <= input_vote
    form <= fieldset

    form <= html.BR()

    input_vote_in_game = html.INPUT(type="submit", value="voter dans la partie")
    input_vote_in_game.bind("click", add_vote_callback)
    form <= input_vote_in_game

    # now we can display

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return False

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', callback_render)

    MY_SUB_PANEL <= canvas
    MY_SUB_PANEL <= html.BR()

    # ratings
    ratings = POSITION_DATA.role_ratings()
    colours = POSITION_DATA.role_colours()
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, colours, game_scoring)
    MY_SUB_PANEL <= rating_colours_window
    MY_SUB_PANEL <= html.BR()

    # role
    stack_role_flag(MY_SUB_PANEL)
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # form
    MY_SUB_PANEL <= form

    return True


def note():
    """ note """

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

    def add_note_callback(_):
        """ add_note_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de la note dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de la note dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La note a été enregistrée ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            note()

        content = input_note.value

        json_dict = {
            'role_id': ROLE_ID,
            'pseudo': PSEUDO,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-notes/{GAME_ID}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        note()

    # from game id and token get role_id of player

    if ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    content_loaded = game_note_reload(GAME_ID)
    if content_loaded is None:
        alert("Erreur chargement note")
        load_option(None, 'consulter')
        return False

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_note = html.LEGEND("Prendre des notes", title="Notez ce dont vous avez besoin de vous souvenir au sujet de cette partie")
    fieldset <= legend_note
    form <= fieldset
    input_note = html.TEXTAREA(type="text", rows=20, cols=80)
    input_note <= content_loaded
    fieldset <= input_note
    form <= fieldset

    form <= html.BR()

    input_vote_in_game = html.INPUT(type="submit", value="enregistrer dans la partie")
    input_vote_in_game.bind("click", add_note_callback)
    form <= input_vote_in_game

    # now we can display

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return False

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', callback_render)

    MY_SUB_PANEL <= canvas
    MY_SUB_PANEL <= html.BR()

    # ratings
    ratings = POSITION_DATA.role_ratings()
    colours = POSITION_DATA.role_colours()
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, colours, game_scoring)
    MY_SUB_PANEL <= rating_colours_window
    MY_SUB_PANEL <= html.BR()

    # role
    stack_role_flag(MY_SUB_PANEL)
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # form
    MY_SUB_PANEL <= form

    return True


def game_master():
    """ game_master """

    def change_deadline_reload():
        """ change_deadline_reload """

        deadline_loaded = None

        def reply_callback(req):
            nonlocal deadline_loaded
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la date limite de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la date limite de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            deadline_loaded = req_result['deadline']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{GAME}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return deadline_loaded

    def push_deadline_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au report de date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au report de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La date limite a été reportée : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            load_dynamic_stuff()
            game_master()

        # get deadline from server
        deadline_loaded = change_deadline_reload()

        # add one day - if fast game change to one minute
        time_unit = 60 if GAME_PARAMETERS_LOADED['fast'] else 24 * 60 * 60
        deadline_forced = deadline_loaded + time_unit

        # push on server
        json_dict = {
            'pseudo': PSEUDO,
            'name': GAME,
            'deadline': deadline_forced,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{GAME}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_recall_orders_email_callback(_, role_id):
        """ send_recall_orders_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de rappel (ordres manquants) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de rappel (ordres manquants) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", f"Message de rappel (manque ordres) émis vers : {pseudo_there}", remove_after=config.REMOVE_AFTER)

        deadline_loaded = GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time.time()
        if not time_stamp_now > deadline_loaded:
            alert("Attendez que la date limite soit passée pour réclamer les ordres, sinon le joueur va crier à l'injustice :-)")
            return

        subject = f"Message de la part de l'arbitre de la partie {GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]

        body = "Bonjour !"
        body += "\n"
        body += "Il manque vos ordres et la date limite est passée. Merci d'aviser rapidement !"
        body += "\n"
        body += f"Pour rappel votre rôle est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = id2pseudo[player_id]

        addressed_id = PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': PSEUDO,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_recall_agreed_email_callback(_, role_id):
        """ send_recall_agreed_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de rappel (manque accord pour résoudre) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de rappel (manque accord pour résoudre) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", f"Message de rappel (manque d'accord pour résoudre) émis vers : {pseudo_there}", remove_after=config.REMOVE_AFTER)

        deadline_loaded = GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time.time()
        if not time_stamp_now > deadline_loaded:
            alert("Attendez que la date limite soit passée pour réclamer l'accord, sinon le joueur va crier à l'injustice :-)")
            return

        subject = f"Message de la part de l'arbitre de la partie {GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]

        body = "Bonjour !"
        body += "\n"
        body += "Il manque votre confirmation d'être d'accord pour résoudre et la date limite est passée. Merci d'aviser rapidement !"
        body += "\n"
        body += f"Pour rappel votre rôle est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = id2pseudo[player_id]

        addressed_id = PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': PSEUDO,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_welcome_email_callback(_, role_id):
        """ send_welcome_email_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de bienvenue : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de bienvenue: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", f"Message de bienvenue émis vers : {pseudo_there}", remove_after=config.REMOVE_AFTER)

        subject = f"Message de la part de l'arbitre de la partie {GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]

        body = "Bonjour !"
        body += "\n"
        body += "J'ai l'immense honneur de vous informer que vous avez été mis dans la partie et pouvez donc commencer à jouer !"
        body += "\n"
        body += f"Le rôle qui vous a été attribué est {role_name}."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={GAME}"

        player_id_str = role2pseudo[role_id]
        player_id = int(player_id_str)
        pseudo_there = id2pseudo[player_id]

        addressed_id = PLAYERS_DICT[pseudo_there]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': PSEUDO,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def send_need_replacement_callback(_, role_id):
        """ send_need_replacement_callback """

        pseudo_there = None

        def reply_callback(req):
            nonlocal pseudo_there
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique message de demande de remplacement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique message de demande de remplacement: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", "Message de demande de remplacement émis vers les remplaçants potentiels", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            game_master()

        subject = f"Message de la part de l'arbitre de la partie {GAME} sur le site https://diplomania-gen.fr (AFJD)"

        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]

        body = "Bonjour !"
        body += "\n"
        body += "Cette partie a besoin d'un remplaçant. Vous aves demandé à être notifié dans un tel cas. Son arbitre vous sollicite !"
        body += "\n"
        body += f"Le rôle qui est libre est {role_name}."
        body += "\n"
        body += "Comment s'y prendre ? Aller sur le site, onglet 'Rejoindre une partie', bouton 'j'en profite' de la ligne de la partie en rose (Il peut être judicieux d'aller tâter un peu la partie au préalable)"
        body += "\n"
        body += "Si ces notifications vous agacent, allez sur le site modifier votre compte..."
        body += "\n"
        body += "Pour se rendre directement sur la partie :\n"
        body += f"https://diplomania-gen.fr?game={GAME}"

        players_dict = common.get_players_data()
        if not players_dict:
            alert("Erreur chargement dictionnaire joueurs")
            return
        addressees = [p for p in players_dict if players_dict[str(p)]['replace']]

        json_dict = {
            'pseudo': PSEUDO,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def civil_disorder_callback(_, role_id):
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu infligé des ordres de désordre civil: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            game_master()

        names_dict = VARIANT_DATA.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': PSEUDO,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{GAME_ID}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(_, role_id):
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu imposé un accord pour résoudre: {messages}", remove_after=config.REMOVE_AFTER)

            adjudicated = req_result['adjudicated']
            if adjudicated:
                alert("La position de la partie a changé !")

            # back to where we started
            MY_SUB_PANEL.clear()
            load_dynamic_stuff()
            load_special_stuff()
            game_master()

        inforced_names_dict = INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = json.dumps(inforced_names_dict)

        definitive_value = True

        json_dict = {
            'role_id': role_id,
            'pseudo': PSEUDO,
            'definitive': definitive_value,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{GAME_ID}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def unallocate_role_callback(_, pseudo_removed, role_id):
        """ unallocate_role_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la désallocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème Erreur à la désallocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu retirer le rôle dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            load_special_stuff()
            game_master()

        json_dict = {
            'game_id': GAME_ID,
            'role_id': role_id,
            'player_pseudo': pseudo_removed,
            'delete': 1,
            'pseudo': PSEUDO,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def allocate_role_callback(_, input_for_role, role_id):
        """ allocate_role_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'allocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'allocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu attribuer le rôle dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            load_special_stuff()
            game_master()

        player_pseudo = input_for_role.value

        json_dict = {
            'game_id': GAME_ID,
            'role_id': role_id,
            'player_pseudo': player_pseudo,
            'delete': 0,
            'pseudo': PSEUDO,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def get_list_pseudo_allocatable_game(id2pseudo):
        """ get_list_pseudo_allocatable_game """

        pseudo_list = None

        def reply_callback(req):
            nonlocal pseudo_list
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la liste des joueurs allouables dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la liste des joueurs allouables dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return None

            pseudo_list = [id2pseudo[int(k)] for k, v in req_result.items() if v == -1]
            return pseudo_list

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{GAME_ID}"

        # get roles that are allocated to game : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return pseudo_list

    # need to be connected
    if PSEUDO is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'consulter')
        return False

    # need to be game master
    if ROLE_ID != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not waiting
    if GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not finished
    if GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        load_option(None, 'consulter')
        return False

    # now we can display

    # header

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    stack_role_flag(MY_SUB_PANEL)
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    id2pseudo = {v: k for k, v in PLAYERS_DICT.items()}
    role2pseudo = {v: k for k, v in GAME_PLAYERS_DICT.items()}

    submitted_data = get_roles_submitted_orders(GAME_ID)
    if not submitted_data:
        alert("Erreur chargement données de soumission")
        load_option(None, 'consulter')
        return False

    # who can I put in this role
    possible_given_role = get_list_pseudo_allocatable_game(id2pseudo)

    # votes

    votes = game_votes_reload(GAME_ID)
    if votes is None:
        alert("Erreur chargement votes")
        load_option(None, 'consulter')
        return False
    votes = list(votes)

    vote_values_table = {}
    for _, role, vote_val in votes:
        vote_values_table[role] = bool(vote_val)

    submitted_roles_list = submitted_data['submitted']
    agreed_roles_list = submitted_data['agreed']
    needed_roles_list = submitted_data['needed']

    game_admin_table = html.TABLE()

    thead = html.THEAD()
    for field in ['drapeau', 'rôle', 'joueur', 'communiquer la bienvenue', '', 'ordres du joueur', 'demander les ordres', 'mettre en désordre civil', '', 'accord du joueur', 'demander l\'accord', 'forcer l\'accord', '', 'vote du joueur', '', 'retirer le rôle', 'attribuer le rôle']:
        col = html.TD(field)
        thead <= col
    game_admin_table <= thead

    for role_id in VARIANT_DATA.roles:

        # discard game master
        if role_id == 0:
            continue

        row = html.TR()

        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]

        # flag
        col = html.TD()
        role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)
        col <= role_icon_img
        row <= col

        # role name
        col = html.TD()
        col <= role_name
        row <= col

        # player
        col = html.TD()
        pseudo_there = ""
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        col <= pseudo_there
        row <= col

        col = html.TD()
        input_send_welcome_email = ""
        if pseudo_there:
            input_send_welcome_email = html.INPUT(type="submit", value="courriel bienvenue", title="Ceci enverra un courriel de bienvenue au joueur. A utiliser pour un nouveau joueur ou au démarrage de la partie")
            input_send_welcome_email.bind("click", lambda e, r=role_id: send_welcome_email_callback(e, r))
        col <= input_send_welcome_email
        row <= col

        # separator
        col = html.TD()
        row <= col

        col = html.TD()
        flag = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
            else:
                flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
        col <= flag
        row <= col

        col = html.TD()
        input_send_recall_email = ""
        if role_id in needed_roles_list:
            if role_id not in submitted_roles_list:
                if pseudo_there:
                    input_send_recall_email = html.INPUT(type="submit", value="courriel rappel ordres", title="Ceci enverra un courriel pour rappeler au joueur d'entrer des ordres dans le système")
                    input_send_recall_email.bind("click", lambda e, r=role_id: send_recall_orders_email_callback(e, r))
        col <= input_send_recall_email
        row <= col

        col = html.TD()
        input_civil_disorder = ""
        if role_id in needed_roles_list:
            if role_id not in submitted_roles_list:
                if pseudo_there:
                    input_civil_disorder = html.INPUT(type="submit", value="désordre civil", title="Ceci forcera des ordres de désordre civil pour le joueur dans le système")
                    input_civil_disorder.bind("click", lambda e, r=role_id: civil_disorder_callback(e, r))
        col <= input_civil_disorder
        row <= col

        # separator
        col = html.TD()
        row <= col

        col = html.TD()
        flag = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id in agreed_roles_list:
                    flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre")
                else:
                    flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
        col <= flag
        row <= col

        col = html.TD()
        input_send_recall_email = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id not in agreed_roles_list:
                    input_send_recall_email = html.INPUT(type="submit", value="courriel rappel accord", title="Ceci enverra un courriel demandant au joueur de manifester son accord pour résoudre la partie")
                    input_send_recall_email.bind("click", lambda e, r=role_id: send_recall_agreed_email_callback(e, r))
        col <= input_send_recall_email
        row <= col

        col = html.TD()
        input_force_agreement = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id not in agreed_roles_list:
                    input_force_agreement = html.INPUT(type="submit", value="forcer accord", title="Ceci forcera l'accord pour résoudre du joueur, déclenchant éventuellement la résolution")
                    input_force_agreement.bind("click", lambda e, r=role_id: force_agreement_callback(e, r))
        col <= input_force_agreement
        row <= col

        # separator
        col = html.TD()
        row <= col
        col = html.TD()

        flag = ""
        if role_id in vote_values_table:
            if vote_values_table[role_id]:
                flag = html.IMG(src="./images/stop.png", title="Le joueur a voté pour arrêter la partie")
            else:
                flag = html.IMG(src="./images/continue.jpg", title="Le joueur a voté pour continuer la partie")
        col <= flag
        row <= col

        # separator
        col = html.TD()
        row <= col

        col = html.TD()
        input_unallocate_role = ""
        if pseudo_there:
            input_unallocate_role = html.INPUT(type="submit", value="retirer le rôle", title="Ceci enlèvera le rôle au joueur")
            input_unallocate_role.bind("click", lambda e, p=pseudo_there, r=role_id: unallocate_role_callback(e, p, r))
        col <= input_unallocate_role
        row <= col

        col = html.TD()
        form = ""
        if not pseudo_there:
            form = html.FORM()

            if not possible_given_role:

                input_contact_replacers = html.INPUT(type="submit", value="contacter les remplaçants", title="Ceci contactera tous les remplaçants déclarés volontaires du site", display='inline')
                input_contact_replacers.bind("click", lambda e, r=role_id: send_need_replacement_callback(e, r))
                form <= input_contact_replacers

            else:

                input_for_role = html.SELECT(type="select-one", value="", display='inline')
                for play_role_pseudo in sorted(possible_given_role, key=lambda p: p.upper()):
                    option = html.OPTION(play_role_pseudo)
                    input_for_role <= option
                form <= input_for_role
                form <= " "
                input_put_in_role = html.INPUT(type="submit", value="attribuer le rôle", title="Ceci attribuera le rôle au joueur", display='inline')
                input_put_in_role.bind("click", lambda e, i=input_for_role, r=role_id: allocate_role_callback(e, i, r))
                form <= input_put_in_role

        col <= form
        row <= col

        game_admin_table <= row

    MY_SUB_PANEL <= html.DIV("Pour bénéficier du bouton premettant de contacter tous les remplaçants, il faut retirer le rôle au joueur (ci-dessous) puis éjecter le joueur de la partie (dans le menu appariement.)", Class='note')
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= game_admin_table
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Le bouton ci-dessous repousse la date limite d'une journée (une minute pour une partie en direct). Pour une gestion plus fine de cette date limite vous devez éditer la partie.", Class='note')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    input_push_deadline = html.INPUT(type="submit", value="Reporter la date limite")
    input_push_deadline.bind("click", push_deadline_game_callback)
    MY_SUB_PANEL <= input_push_deadline

    return True


SUPERVISE_REFRESH_TIMER = None


class Logger(list):
    """ Logger """

    def insert(self, message):
        """ insert """

        # insert datation
        time_stamp = time.time()
        date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
        date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")

        # put in stack (limited height)
        log_line = html.DIV(f"{date_now_gmt_str} : {message}", Class='important')
        self.append(log_line)

    def display(self, log_window):
        """ display """

        for log_line in reversed(self):
            log_window <= log_line


def show_game_parameters():
    """ show_game_parameters """

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    game_params_table = html.TABLE()

    # table header
    thead = html.THEAD()
    for field_name in "Nom du paramètre", "Valeur pour la partie", "Explication sommaire", "Effet (ce qui change concrètement)", "Implémenté ?":
        col = html.TD(field_name)
        thead <= col
    game_params_table <= thead

    for key, value in GAME_PARAMETERS_LOADED.items():

        if key in ['name', 'description', 'variant', 'deadline', 'current_state', 'current_advancement']:
            continue

        row = html.TR()

        parameter_name, explanation, effect, implemented = {
            'archive': ("archive", "la partie n'est pas jouée, elle est juste consultable", "L'arbitre peut passer des ordres, les dates limites ne sont pas gérées, le système autorise les résolutions sans tenir compte des soumissions des joueurs, le système ne réalise pas l'attribution des roles au démarrage de la partie, pas de courriel de notification aux joueurs", "OUI"),
            'used_for_elo': ("utilisée pour le calcul du élo", "oui ou non", "Le résultat de la partie est pris en compte dans le calcul du élo des joueurs du site", "OUI"),
            'anonymous': ("anonyme", "on sait pas qui joue quel rôle dans la partie - cette valeur est modifiable pendant la partie", "Seul l'arbitre peut savoir qui joue et les joueurs ne savent pas qui a passé les ordres  - effacé à la fin de la partie", "OUI"),
            'nomessage_game': ("blocage des messages privés (négociation) pour la partie", "si oui on ne peut pas négocier - sauf avec l'arbitre", "Tout message privé joueur vers joueur est impossible", "OUI"),
            'nopress_game': ("blocage des messages publics (déclaration) pour la partie", "si oui on ne peut pas déclarer - sauf l'arbitre", "Tout message public de joueur est impossible", "OUI"),
            'nomessage_current': ("blocage des messages privés (négociation) pour le moment", "si oui on ne peut pas négocier - valeur utilisée pour accorder l'accès ou pas - cette valeur est modifiable pendant la partie", "effacé en fin de partie", "OUI"),
            'nopress_current': ("blocage des messages publics (déclaration) pour le moment", "si oui on ne peut pas déclarer - valeur utilisée pour accorder l'accès ou pas - cette valeur est modifiable pendant la partie", "effacé en fin de partie", "OUI"),
            'fast': ("en direct", "la partie est jouée comme sur un plateau", "Les paramètres de calcul des dates limites sont en minutes et non en heures, pas de courriel de notification aux joueurs", "OUI"),
            'manual': ("attribution manuelle des rôle", "L'arbitre doit attribuer les roles", "Le système ne réalise pas l'attribution des roles au démarrage de la partie", "OUI"),
            'scoring': ("code du scorage", "le système de scorage appliqué", "Se reporter à Accueil/Coin technique pour le détail des scorages implémentés. Note : Le calcul est réalisé dans l'interface", "OUI"),
            'deadline_hour': ("heure de la date limite", "entre 0 et 23", "Heure à laquelle le système placera la date limite dans la journée si la synchronisation est souhaitée", "OUI"),
            'deadline_sync': ("synchronisation de la date limite", "oui ou non", "Le système synchronise la date limite à une heure précise dans la journée", "OUI"),
            'grace_duration': ("durée de la grâce", "en heures", "L'arbitre tolère un retard d'autant d'heures avant de placer des désordres civils", "OUI"),
            'speed_moves': ("vitesse pour les mouvements", "en heures", "Le système ajoute autant d'heures avant une résolution de mouvement pour une date limite", "OUI"),
            'speed_retreats': ("vitesse pour les retraites", "en heures", "Le système ajoute autant d'heures avant une résolution de retraites pour une date limite", "OUI"),
            'speed_adjustments': ("vitesse pour les ajustements", "en heures", "Le système ajoute autant d'heures avant une résolution d'ajustements pour une date limite", "OUI"),
            'cd_possible_moves': ("désordre civil possible pour les mouvements", "oui ou non", "L'arbitre est en mesure d'imposer un désordre civil pour une phase de mouvements", "OUI"),
            'cd_possible_retreats': ("désordre civil possible pour les retraites", "oui ou non", "L'arbitre est en mesure d'imposer un désordre civil pour une phase de retraites", "OUI"),
            'cd_possible_builds': ("désordre civil possible pour les constructions", "oui ou non", "L'arbitre est en mesure d'imposer un désordre civil pour une phase d'ajustements", "OUI"),
            'play_weekend': ("on joue le week-end", "oui ou non", "Le système pourra placer une date limite pendant le week-end", "OUI"),
            'access_code': ("code d'accès pour la partie", "(code de quatre chiffres)", "Le système demande un code pour rejoindre la partie", "NON - c'est pourquoi le code apparaît ici en clair !"),
            'access_restriction_reliability': ("restriction d'accès sur la fiabilité", "(valeur)", "Un seuil de fiabilité est exigé pour rejoindre la partie", "NON"),
            'access_restriction_regularity': ("restriction d'accès sur la régularité", "(valeur)", "Un seuil de régularité est exigé pour rejoindre la partie", "OUI"),
            'access_restriction_performance': ("restriction d'accès sur la performance", "(valeur)", "Un seuil de performance est exigé pour rejoindre la partie", "OUI"),
            'nb_max_cycles_to_play': ("nombre maximum de cycles (années) à jouer", "(valeur)", "L'arbitre déclare la partie terminée si autant de cycles ont été joués", "-"),
            'victory_centers': ("nombre de centres pour la victoire", "(valeur)", "L'arbitre déclare la partie gagnée si un joueur possède autant de centres", "-")
        }[key]

        col1 = html.TD(html.B(parameter_name))
        row <= col1

        if value is False:
            parameter_value = "Non"
        elif value is True:
            parameter_value = "Oui"
        else:
            parameter_value = value

        col2 = html.TD(html.B(parameter_value), Class='important')
        row <= col2

        # some more info

        col3 = html.TD(explanation)
        row <= col3

        col4 = html.TD(effect)
        row <= col4

        col5 = html.TD(implemented)
        row <= col5

        game_params_table <= row

    MY_SUB_PANEL <= game_params_table

    return True


def show_events_in_game():
    """ show_events_in_game """

    def cancel_remove_incident_callback(_, dialog, ):
        """ cancel_remove_incident_callback """
        dialog.close()

    def remove_incident_callback(_, dialog, role_id, advancement):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression de l'incident : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression de l'incident : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'incident a été supprimé : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            show_events_in_game()

        dialog.close()

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-incidents-manage/{GAME_ID}/{role_id}/{advancement}"

        # deleting incident : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_incident_callback_confirm(_, role_id, advancement, text):
        """ remove_incident_callback_confirm """

        dialog = Dialog(f"On supprime vraiment cet incident pour {text} ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, r=role_id, a=advancement: remove_incident_callback(e, d, r, a))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_remove_incident_callback(e, d))

        # back to where we started
        MY_SUB_PANEL.clear()
        show_events_in_game()

    # game status
    MY_SUB_PANEL <= GAME_STATUS
    MY_SUB_PANEL <= html.BR()

    # game master
    MY_SUB_PANEL <= html.H3("Arbitre")

    game_master_pseudo = get_game_master(int(GAME_ID))
    if game_master_pseudo is None:
        MY_SUB_PANEL <= html.DIV("Pas d'arbitre pour cette partie ou erreur au chargement de l'arbitre de la partie", Class='important')
    else:

        game_master_table = html.TABLE()

        fields = ['flag', 'role', 'player']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'flag': 'drapeau', 'player': 'joueur', 'role': 'rôle'}[field]
            col = html.TD(field_fr)
            thead <= col
        game_master_table <= thead

        role_id = 0

        row = html.TR()

        # role flag
        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        # role name
        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]

        col = html.TD(role_name)
        row <= col

        # player
        pseudo_there = game_master_pseudo
        col = html.TD(pseudo_there)
        row <= col

        game_master_table <= row

        MY_SUB_PANEL <= game_master_table

    # orders
    MY_SUB_PANEL <= html.H3("Ordres")

    # if user identified ?
    if PSEUDO is None:
        MY_SUB_PANEL <= html.DIV("Il faut se connecter au préalable", Class='important')

    # is player in game ?
    elif not(moderate.check_modo(PSEUDO) or ROLE_ID is not None):
        MY_SUB_PANEL <= html.DIV("Seuls les participants à une partie (ou un modérateur du site) peuvent voir le statut des ordres", Class='important')

    # game anonymous
    elif not(moderate.check_modo(PSEUDO) or ROLE_ID == 0 or not GAME_PARAMETERS_LOADED['anonymous']):
        MY_SUB_PANEL <= html.DIV("Seul l'arbitre (ou un modérateur du site) peut voir le statut des ordres  pour une partie anonyme", Class='important')

    else:

        # you will at least get your own role
        submitted_data = get_roles_submitted_orders(GAME_ID)
        if not submitted_data:
            alert("Erreur chargement données de soumission")
            load_option(None, 'consulter')
            return False

        role2pseudo = {v: k for k, v in GAME_PLAYERS_DICT.items()}

        id2pseudo = {v: k for k, v in PLAYERS_DICT.items()}

        game_players_table = html.TABLE()

        fields = ['flag', 'role', 'player', 'orders', 'agreement']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'flag': 'drapeau', 'role': 'rôle', 'player': 'joueur', 'orders': 'ordres', 'agreement': 'accord'}[field]
            col = html.TD(field_fr)
            thead <= col
        game_players_table <= thead

        for role_id in VARIANT_DATA.roles:

            row = html.TR()

            if role_id <= 0:
                continue

            # role flag
            role = VARIANT_DATA.roles[role_id]
            role_name = VARIANT_DATA.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

            if role_icon_img:
                col = html.TD(role_icon_img)
            else:
                col = html.TD()
            row <= col

            role = VARIANT_DATA.roles[role_id]
            role_name = VARIANT_DATA.name_table[role]

            col = html.TD(role_name)
            row <= col

            # player
            pseudo_there = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]
            col = html.TD(pseudo_there)
            row <= col

            # orders are in
            submitted_roles_list = submitted_data['submitted']
            needed_roles_list = submitted_data['needed']
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                else:
                    flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
            else:
                flag = ""
            col = html.TD(flag)
            row <= col

            # agreed
            col = html.TD()
            flag = ""
            submitted_roles_list = submitted_data['submitted']
            agreed_roles_list = submitted_data['agreed']
            needed_roles_list = submitted_data['needed']
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id in agreed_roles_list:
                        flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre")
                    else:
                        flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
            col <= flag
            row <= col

            game_players_table <= row

        MY_SUB_PANEL <= game_players_table

    # incidents2
    MY_SUB_PANEL <= html.H3("Désordres civils")

    # get the actual incidents of the game
    game_incidents2 = game_incidents2_reload(GAME_ID)
    # there can be no incidents (if no incident of failed to load)

    game_incidents2_table = html.TABLE()

    fields = ['flag', 'role', 'season', 'date']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'rôle', 'season': 'saison', 'date': 'date'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_incidents2_table <= thead

    for role_id, advancement, date_incident in sorted(game_incidents2, key=lambda i: i[2]):

        row = html.TR()

        # role flag
        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]

        col = html.TD(role_name)
        row <= col

        # season
        advancement_season, advancement_year = common.get_season(advancement, VARIANT_DATA)
        advancement_season_readable = VARIANT_DATA.name_table[advancement_season]
        game_season = f"{advancement_season_readable} {advancement_year}"
        col = html.TD(game_season)
        row <= col

        # date
        datetime_incident = datetime.datetime.fromtimestamp(date_incident, datetime.timezone.utc)
        incident_day = f"{datetime_incident.year:04}-{datetime_incident.month:02}-{datetime_incident.day:02}"
        incident_hour = f"{datetime_incident.hour:02}:{datetime_incident.minute:02}"
        incident_str = f"{incident_day} {incident_hour} GMT"
        col = html.TD(incident_str)
        row <= col

        game_incidents2_table <= row

    MY_SUB_PANEL <= game_incidents2_table

    if game_incidents2:
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV("Un désordre civil signifie que l'arbitre a forcé des ordres pour le joueur", Class='note')

    # incidents
    MY_SUB_PANEL <= html.H3("Retards")

    # get the actual incidents of the game
    game_incidents = game_incidents_reload(GAME_ID)
    # there can be no incidents (if no incident of failed to load)

    game_incidents_table = html.TABLE()

    fields = ['flag', 'role', 'season', 'duration', 'date']

    if ROLE_ID == 0:
        fields.extend(['remove'])

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'rôle', 'season': 'saison', 'duration': 'durée', 'date': 'date', 'remove': 'supprimer'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_incidents_table <= thead

    for role_id, advancement, player_id, duration, date_incident in sorted(game_incidents, key=lambda i: i[4]):

        row = html.TR()

        # role flag
        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]

        col = html.TD(role_name)
        row <= col

        # season
        advancement_season, advancement_year = common.get_season(advancement, VARIANT_DATA)
        advancement_season_readable = VARIANT_DATA.name_table[advancement_season]
        game_season = f"{advancement_season_readable} {advancement_year}"
        col = html.TD(game_season)
        row <= col

        # duration
        col = html.TD(f"{duration}")
        row <= col

        # date
        datetime_incident = datetime.datetime.fromtimestamp(date_incident, datetime.timezone.utc)
        incident_day = f"{datetime_incident.year:04}-{datetime_incident.month:02}-{datetime_incident.day:02}"
        incident_hour = f"{datetime_incident.hour:02}:{datetime_incident.minute:02}"
        incident_str = f"{incident_day} {incident_hour} GMT"
        col = html.TD(incident_str)
        row <= col

        # remove
        if ROLE_ID == 0:
            form = html.FORM()
            input_remove_incident = html.INPUT(type="submit", value="supprimer")
            text = f"Rôle {role_name} en saison {game_season}"
            input_remove_incident.bind("click", lambda e, r=role_id, a=advancement, t=text: remove_incident_callback_confirm(e, r, a, t))
            form <= input_remove_incident
            col = html.TD(form)
            row <= col

        game_incidents_table <= row

    MY_SUB_PANEL <= game_incidents_table
    MY_SUB_PANEL <= html.BR()

    count = {}

    for role_id, advancement, player_id, duration, date_incident in game_incidents:
        if role_id not in count:
            count[role_id] = []
        count[role_id].append(duration)

    recap_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['rang', 'role', 'retards']:
        col = html.TD(field)
        thead <= col
    recap_table <= thead

    rank = 1
    for role_id in sorted(count.keys(), key=lambda r: len(count[r]), reverse=True):
        row = html.TR()

        # rank
        col = html.TD(rank)
        row <= col

        # role flag
        role = VARIANT_DATA.roles[role_id]
        role_name = VARIANT_DATA.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        # incidents
        incidents_list = count.get(role_id, [])
        col = html.TD(" ".join([f"{i}" for i in incidents_list]))
        row <= col

        recap_table <= row
        rank += 1

    MY_SUB_PANEL <= recap_table
    MY_SUB_PANEL <= html.BR()

    # a bit of humour !
    if game_incidents:

        MY_SUB_PANEL <= html.DIV("Un retard signifie que le joueur (ou l'arbitre) ont réalisé la transition 'pas d'accord -> 'd'accord pour résoudre' après la date limite", Class='note')
        MY_SUB_PANEL <= html.BR()

        MY_SUB_PANEL <= html.DIV("Les retards des joueurs qui depuis ont été remplacés apparaissent", Class='note')
        MY_SUB_PANEL <= html.BR()

        MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées (sauf pour les parties en direct - en minutes).  Un retard de 1 par exemple signifie un retard entre 1 seconde et 59 minutes, 59 secondes.", Class='note')
        MY_SUB_PANEL <= html.BR()

        humour_img = html.IMG(src="./images/goudrons_plumes.gif", title="Du goudron et des plumes pour les retardataires !")
        MY_SUB_PANEL <= humour_img

    return True


def supervise():
    """ supervise """

    def civil_disorder_callback(_, role_id):
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

        names_dict = VARIANT_DATA.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': PSEUDO,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{GAME_ID}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(_, role_id):
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            adjudicated = req_result['adjudicated']
            if adjudicated:
                InfoDialog("OK", "La résolution a été forcée..", remove_after=config.REMOVE_AFTER)
                message = "Résolution forcée par la console suite forçage accord"
                log_stack.insert(message)

        inforced_names_dict = INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = json.dumps(inforced_names_dict)

        definitive_value = True

        json_dict = {
            'role_id': role_id,
            'pseudo': PSEUDO,
            'definitive': definitive_value,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{GAME_ID}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def reload_game_admin_table(submitted_data, votes):
        """ reload_game_admin_table """

        vote_values_table = {}
        for _, role, vote_val in votes:
            vote_values_table[role] = bool(vote_val)

        submitted_roles_list = submitted_data['submitted']
        agreed_roles_list = submitted_data['agreed']
        needed_roles_list = submitted_data['needed']

        game_admin_table = html.TABLE()

        for role_id in VARIANT_DATA.roles:

            # discard game master
            if role_id == 0:
                continue

            row = html.TR()

            role = VARIANT_DATA.roles[role_id]
            role_name = VARIANT_DATA.name_table[role]

            # flag
            col = html.TD()
            role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{role_id}.jpg", title=role_name)
            col <= role_icon_img
            row <= col

            # role name
            col = html.TD()
            col <= role_name
            row <= col

            # player
            col = html.TD()
            pseudo_there = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]
            col <= pseudo_there
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                else:
                    flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
            col <= flag
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id in agreed_roles_list:
                        flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre")
                    else:
                        flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
            col <= flag
            row <= col

            col = html.TD()
            flag = ""
            if role_id in vote_values_table:
                if vote_values_table[role_id]:
                    flag = html.IMG(src="./images/stop.png", title="Arrêter la partie")
                else:
                    flag = html.IMG(src="./images/continue.jpg", title="Continuer la partie")
            col <= flag
            row <= col

            game_admin_table <= row

        return game_admin_table

    def refresh():
        """ refresh """

        submitted_data = {}
        votes = None

        def refresh_subroutine():

            # reload from server to see what changed from outside
            load_dynamic_stuff()
            nonlocal submitted_data
            submitted_data = get_roles_submitted_orders(GAME_ID)
            if not submitted_data:
                alert("Erreur chargement données de soumission")
                return

            # votes
            nonlocal votes
            votes = game_votes_reload(GAME_ID)
            if votes is None:
                alert("Erreur chargement votes")
                return
            votes = list(votes)

            MY_SUB_PANEL.clear()

            # clock
            stack_clock(MY_SUB_PANEL, SUPERVISE_REFRESH_PERIOD_SEC)
            MY_SUB_PANEL <= html.BR()

            # game status
            MY_SUB_PANEL <= GAME_STATUS
            MY_SUB_PANEL <= html.BR()

            stack_role_flag(MY_SUB_PANEL)
            MY_SUB_PANEL <= html.BR()

        # changed from outside
        refresh_subroutine()

        # calculate deadline + grace
        time_unit = 60 if GAME_PARAMETERS_LOADED['fast'] else 24 * 60 * 60
        deadline_loaded = GAME_PARAMETERS_LOADED['deadline']
        grace_duration_loaded = GAME_PARAMETERS_LOADED['grace_duration']
        force_point = deadline_loaded + time_unit * grace_duration_loaded
        time_stamp_now = time.time()

        # are we past ?
        if time_stamp_now > force_point:

            submitted_roles_list = submitted_data['submitted']
            agreed_roles_list = submitted_data['agreed']
            needed_roles_list = submitted_data['needed']

            missing_orders = []
            for role_id in VARIANT_DATA.roles:
                if role_id in needed_roles_list and role_id not in submitted_roles_list:
                    missing_orders.append(role_id)

            alterated = False
            if missing_orders:
                role_id = random.choice(missing_orders)
                civil_disorder_callback(None, role_id)
                role = VARIANT_DATA.roles[role_id]
                role_name = VARIANT_DATA.name_table[role]
                message = f"Désordre civil pour {role_name}"
                alterated = True
            else:
                missing_agreements = []
                for role_id in VARIANT_DATA.roles:
                    if role_id in submitted_roles_list and role_id not in agreed_roles_list:
                        missing_agreements.append(role_id)
                if missing_agreements:
                    role_id = random.choice(missing_agreements)
                    force_agreement_callback(None, role_id)
                    role = VARIANT_DATA.roles[role_id]
                    role_name = VARIANT_DATA.name_table[role]
                    message = f"Forçage accord pour {role_name}"
                    alterated = True

            if alterated:

                log_stack.insert(message)

                # changed from myself
                refresh_subroutine()

        game_admin_table = reload_game_admin_table(submitted_data, votes)
        MY_SUB_PANEL <= game_admin_table
        MY_SUB_PANEL <= html.BR()

        # put stack in log window
        log_window = html.DIV(id="log")
        log_stack.display(log_window)

        # display
        MY_SUB_PANEL <= log_window

    def cancel_supervise_callback(_, dialog):
        """ cancel_supervise_callback """

        dialog.close()

        load_option(None, 'consulter')

    def supervise_callback(_, dialog):
        """ supervise_callback """

        dialog.close()

        nonlocal id2pseudo
        id2pseudo = {v: k for k, v in PLAYERS_DICT.items()}

        nonlocal role2pseudo
        role2pseudo = {v: k for k, v in GAME_PLAYERS_DICT.items()}

        nonlocal log_stack
        log_stack = Logger()

        # initiates refresh
        refresh()

        # repeat
        global SUPERVISE_REFRESH_TIMER
        if SUPERVISE_REFRESH_TIMER is None:
            SUPERVISE_REFRESH_TIMER = timer.set_interval(refresh, SUPERVISE_REFRESH_PERIOD_SEC * 1000)  # refresh every x seconds

    id2pseudo = {}
    role2pseudo = {}
    log_stack = None

    # need to be connected
    if PSEUDO is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'consulter')
        return False

    # need to be game master
    if ROLE_ID != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not waiting
    if GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not finished
    if GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        load_option(None, 'consulter')
        return False

    # game needs to be fast
    if not GAME_PARAMETERS_LOADED['fast']:
        alert("Cette partie n'est pas une partie rapide")
        load_option(None, 'consulter')
        return False

    # since touchy, this requires a confirmation
    dialog = Dialog("On supervise vraiment la partie (cela peut entrainer des désordres civils) ?", ok_cancel=True)
    dialog.ok_button.bind("click", lambda e, d=dialog: supervise_callback(e, d))
    dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_supervise_callback(e, d))

    return True


OBSERVE_REFRESH_TIMER = None


def observe():
    """ observe """

    ctx = None
    img = None

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

    def refresh():
        """ refresh """

        # reload from server to see what changed from outside
        load_dynamic_stuff()
        MY_SUB_PANEL.clear()

        # clock
        stack_clock(MY_SUB_PANEL, OBSERVE_REFRESH_PERIOD_SEC)
        MY_SUB_PANEL <= html.BR()

        # game status
        MY_SUB_PANEL <= GAME_STATUS

        # create canvas
        map_size = VARIANT_DATA.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        nonlocal ctx
        ctx = canvas.getContext("2d")
        if ctx is None:
            alert("Il faudrait utiliser un navigateur plus récent !")
            return

        # put background (this will call the callback that display the whole map)
        nonlocal img
        img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
        img.bind('load', callback_render)

        ratings = POSITION_DATA.role_ratings()
        colours = POSITION_DATA.role_colours()
        game_scoring = GAME_PARAMETERS_LOADED['scoring']
        rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, colours, game_scoring)

        report_window = common.make_report_window(REPORT_LOADED)

        # left side

        MY_SUB_PANEL <= canvas
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= rating_colours_window
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= report_window

    # game needs to be ongoing - not waiting
    if GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'consulter')
        return False

    # game needs to be ongoing - not finished
    if GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà terminée")
        load_option(None, 'consulter')
        return False

    # initiates refresh
    refresh()

    # repeat
    global OBSERVE_REFRESH_TIMER
    if OBSERVE_REFRESH_TIMER is None:
        OBSERVE_REFRESH_TIMER = timer.set_interval(refresh, OBSERVE_REFRESH_PERIOD_SEC * 1000)  # refresh every x seconds

    return True


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = None

MY_SUB_PANEL = html.DIV(id="play")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'consulter':
        status = show_position()
    if item_name == 'ordonner':
        status = submit_orders()
    if item_name == 'taguer':
        status = submit_communication_orders()
    if item_name == 'négocier':
        status = negotiate()
    if item_name == 'déclarer':
        status = declare()
    if item_name == 'voter':
        status = vote()
    if item_name == 'arbitrer':
        status = game_master()
    if item_name == 'noter':
        status = note()
    if item_name == 'superviser':
        status = supervise()
    if item_name == 'paramètres':
        status = show_game_parameters()
    if item_name == 'retards':
        status = show_events_in_game()
    if item_name == 'observer':
        status = observe()

    if not status:
        return

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item

    # quitting superviser : clear timer
    global SUPERVISE_REFRESH_TIMER
    if ITEM_NAME_SELECTED != 'superviser':
        if SUPERVISE_REFRESH_TIMER is not None:
            timer.clear_interval(SUPERVISE_REFRESH_TIMER)
            SUPERVISE_REFRESH_TIMER = None

    # quitting observer : clear timer
    global OBSERVE_REFRESH_TIMER
    if ITEM_NAME_SELECTED != 'observer':
        if OBSERVE_REFRESH_TIMER is not None:
            timer.clear_interval(OBSERVE_REFRESH_TIMER)
            OBSERVE_REFRESH_TIMER = None


COUNTDOWN_TIMER = None


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    global GAME
    GAME = storage['GAME']

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    global GAME_ID
    GAME_ID = storage['GAME_ID']

    # Connected but not player
    # Not connected
    ITEM_NAME_SELECTED = 'consulter'

    global PSEUDO
    PSEUDO = None
    if 'PSEUDO' in storage:
        PSEUDO = storage['PSEUDO']

    # from game_id and token get role

    global ROLE_ID
    ROLE_ID = None
    if PSEUDO is not None:
        ROLE_ID = common.get_role_allocated_to_player_in_game(GAME_ID)

    load_static_stuff()
    load_dynamic_stuff()
    load_special_stuff()

    # initiates new countdown
    countdown()

    # start countdown (must not be inside a timed function !)
    global COUNTDOWN_TIMER
    if COUNTDOWN_TIMER is None:
        COUNTDOWN_TIMER = timer.set_interval(countdown, 1000)

    # this means user wants to join game
    if ARRIVAL == 'rejoindre':
        join_game()

    if ROLE_ID is not None:

        # we have a player here

        if ARRIVAL == 'declarations':
            # set page for press
            ITEM_NAME_SELECTED = 'déclarer'
        elif ARRIVAL == 'messages':
            # set page for messages
            ITEM_NAME_SELECTED = 'négocier'
        else:
            if ROLE_ID == 0:
                # game master
                ITEM_NAME_SELECTED = 'arbitrer'
            else:
                # player
                ITEM_NAME_SELECTED = 'ordonner'

    else:

        # moderator wants to see whose orders are missing
        if moderate.check_modo(PSEUDO):
            # Admin
            ITEM_NAME_SELECTED = 'retards'

    set_arrival(None)
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
