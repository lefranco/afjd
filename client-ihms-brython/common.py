""" common """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import mapping


DECLARATIONS_TYPE = 0
MESSAGES_TYPE = 1


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


def get_news_content():
    """ get_news_content """

    news_content = None

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting news content: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting news content: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        nonlocal news_content
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

    # getting players list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return players_dict


def get_players_data():
    """ get_players_data """

    players_dict = None

    def reply_callback(req):
        nonlocal players_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting players list: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting players list: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        req_result = json.loads(req.text)
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
                alert(f"Error getting games list: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting games list: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        req_result = json.loads(req.text)
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

        position_loaded = dict(req_result)

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


def game_transition_reload(game, advancement):
    """ game_transition_reload """

    transition_loaded = None

    def reply_callback(req):
        """ reply_callback """
        nonlocal transition_loaded

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error loading game transition: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Résolution introuvable: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        transition_loaded = req_result

    game_id = get_game_id(game)
    if game_id is None:
        return None

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-transitions/{game_id}/{advancement}"

    # getting variant : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return transition_loaded


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


def game_communication_orders_reload(game):
    """ game_communication_orders_reload """

    orders_loaded = None

    def reply_callback(req):
        """ reply_callback """
        nonlocal orders_loaded

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error loading game communication orders: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem loading game communication orders: {req_result['msg']}")
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
    url = f"{host}:{port}/game-communication-orders/{game_id}"

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


DIPLOMACY_SEASON_CYCLE = [1, 2, 1, 2, 3]


def get_season(advancement, variant) -> None:
    """ store season """

    len_season_cycle = len(DIPLOMACY_SEASON_CYCLE)
    advancement_season_num = advancement % len_season_cycle + 1
    advancement_season = mapping.SeasonEnum.from_code(advancement_season_num)
    advancement_year = (advancement // len_season_cycle) + 1 + variant.year_zero
    return advancement_season, advancement_year


def get_role_allocated_to_player(game_id):
    """ get_role the player has in the game """

    role_id = None

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting role allocated to player: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting role allocated to player: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        req_result = json.loads(req.text)
        nonlocal role_id
        # TODO : consider if a player has more than one role
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


def get_roles_submitted_orders(game_id):
    """ get_roles_submitted_orders """

    submitted_data = None

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting roles submitted orders: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting roles submitted orders: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        req_result = json.loads(req.text)
        nonlocal submitted_data
        submitted_data = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders-submitted/{game_id}"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return submitted_data


def last_visit_load(game_id, visit_type):
    """ last_visit_load """

    time_stamp = None

    def reply_callback(req):
        """ reply_callback """

        nonlocal time_stamp

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting last visit in game ({visit_type}): {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting last visit in game ({visit_type=}): {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        time_stamp = req_result['time_stamp']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-visits/{game_id}/{visit_type}"

    # getting last visit in a game : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return time_stamp


def last_visit_update(game_id, pseudo, role_id, visit_type):
    """ last_visit_update """

    def reply_callback(req):
        """ reply_callback """

        req_result = json.loads(req.text)
        if req.status != 201:
            if 'message' in req_result:
                alert(f"Error putting last visit in game: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem putting last visit in game: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
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


def last_game_declaration(game_id):
    """ last_game_declaration """

    time_stamp = None

    def reply_callback(req):
        """ reply_callback """

        nonlocal time_stamp

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting last game declaration: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting last game declaration: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        time_stamp = req_result['time_stamp']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/date-last-game-declaration/{game_id}"

    # getting last game declaration : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return time_stamp


def last_game_message(game_id, role_id):
    """ last_game_message """

    time_stamp = None

    def reply_callback(req):
        """ reply_callback """

        nonlocal time_stamp

        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting last game message : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting last game message: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        time_stamp = req_result['time_stamp']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/date-last-game-message/{game_id}/{role_id}"

    # getting last game message role : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return time_stamp


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
                report_col <= html.B(html.CODE(line, style={'color': 'red'}))
            elif line.find(":") != -1:
                report_col <= html.B(html.CODE(line, style={'color': 'blue'}))
            elif line.startswith("*"):
                report_col <= html.B(html.CODE(line, style={'color': 'pink'}))
            else:
                report_col <= html.B(html.CODE(line, style={'color': 'black'}))
            report_col <= html.BR()
        report_row <= report_col
    return report_table


def definitive_reload(game_id):
    """ definitive_reload """

    definitives = None

    def reply_callback(req):
        """ reply_callback """

        nonlocal definitives

        req_result = json.loads(req.text)

        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error extracting definitive from game: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem extracting definitive in game: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        definitives = req_result['definitives']

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-definitives/{game_id}"

    # extracting definitive from a game : need token (or not?)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return definitives


def vote_reload(game_id):
    """ vote_reload """

    votes = None

    def reply_callback(req):
        """ reply_callback """

        nonlocal votes

        req_result = json.loads(req.text)

        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error extracting vote from game: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem extracting vote in game: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
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
    with open(parameters_file_name, "r") as read_file:
        parameters_read = json.load(read_file)

    return parameters_read


def read_image(variant_name_loaded, display_chosen):
    """ read_image """

    return html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/map.png")
