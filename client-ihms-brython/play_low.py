""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

import json

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import profiler

import mydatetime
import config
import common
import scoring
import interface
import mapping
import memoize
import moderate

import play  # circular import


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


def make_rating_colours_window(variant_data, ratings, units, colours, game_scoring):
    """ make_rating_window """

    rating_table = html.TABLE()

    # roles
    rating_names_row = html.TR()
    rating_table <= rating_names_row
    col = html.TD(html.B("Rôles :"))
    rating_names_row <= col
    for role_name in ratings:
        col = html.TD()

        canvas2 = html.CANVAS(id="rect", width=15, height=15, alt=role_name)
        ctx2 = canvas2.getContext("2d")

        colour = colours[role_name]

        outline_colour = colour.outline_colour()
        ctx2.strokeStyle = outline_colour.str_value()
        ctx2.lineWidth = 2
        ctx2.beginPath()
        ctx2.rect(0, 0, 14, 14)
        ctx2.stroke()
        ctx2.closePath()  # no fill

        ctx2.fillStyle = colour.str_value()
        ctx2.fillRect(1, 1, 13, 13)

        col <= canvas2
        col <= f" {role_name}"
        rating_names_row <= col

    # centers
    rating_centers_row = html.TR()
    rating_table <= rating_centers_row
    col = html.TD(html.B("Centres (unités) :"))
    rating_centers_row <= col
    for role, ncenters in ratings.items():
        nunits = units[role]
        col = html.TD()
        if nunits != ncenters:
            col <= f"{ncenters} ({nunits})"
        else:
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

    rolename2role_id = {VARIANT_DATA.role_name_table[v]: k for k, v in VARIANT_DATA.roles.items()}
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


def load_static_stuff():
    """ load_static_stuff : loads global data """

    profiler.PROFILER.start_mes("get players...")

    # need to be first since used in get_game_status()
    # get the players (all players)
    global PLAYERS_DICT
    PLAYERS_DICT = common.get_players()
    if not PLAYERS_DICT:
        alert("Erreur chargement info joueurs")
        profiler.PROFILER.stop_mes()
        return

    profiler.PROFILER.stop_mes()

    profiler.PROFILER.start_mes("get the rest (memo)...")

    # from game name get variant name

    if 'GAME_VARIANT' not in storage:
        alert("ERREUR : variante introuvable")
        profiler.PROFILER.stop_mes()
        return

    global VARIANT_NAME_LOADED
    VARIANT_NAME_LOADED = storage['GAME_VARIANT']

    # from variant name get variant content

    global VARIANT_CONTENT_LOADED

    # optimization
    if VARIANT_NAME_LOADED in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
        VARIANT_CONTENT_LOADED = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[VARIANT_NAME_LOADED]
    else:
        profiler.PROFILER.start_mes("get variant...")
        VARIANT_CONTENT_LOADED = common.game_variant_content_reload(VARIANT_NAME_LOADED)
        profiler.PROFILER.stop_mes()
        if not VARIANT_CONTENT_LOADED:
            alert("Erreur chargement contenu variante")
            profiler.PROFILER.stop_mes()
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

    profiler.PROFILER.stop_mes()


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


def stack_last_moves_button(frame):
    """ stack_last_moves_button """

    input_last_moves = html.INPUT(type="submit", value="derniers mouvements")
    input_last_moves.bind("click", lambda e: play.load_option(e, 'Consulter', True))
    frame <= input_last_moves
    frame <= html.BR()
    frame <= html.BR()


def stack_role_flag(frame):
    """ stack_role_flag """

    # role flag
    role = VARIANT_DATA.roles[ROLE_ID]
    role_name = VARIANT_DATA.role_name_table[role]
    role_icon_img = html.IMG(src=f"./variants/{VARIANT_NAME_LOADED}/{INTERFACE_CHOSEN}/roles/{ROLE_ID}.jpg", title=role_name)
    frame <= role_icon_img
    frame <= html.BR()
    frame <= html.BR()


DEADLINE_COL = None
COUNTDOWN_COL = None


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
    advancement_season_readable = VARIANT_DATA.season_name_table[advancement_season]
    game_season = f"{advancement_season_readable} {advancement_year}"

    nb_max_cycles_to_play = GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
    last_year_played = common.get_last_year(nb_max_cycles_to_play, VARIANT_DATA)

    deadline_loaded = GAME_PARAMETERS_LOADED['deadline']
    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
    datetime_deadline_loaded_str = mydatetime.strftime(*datetime_deadline_loaded)

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
    DEADLINE_COL = html.TD(f"DL {datetime_deadline_loaded_str}")
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
        specific_information = html.DIV("Partie en direct : utiliser le bouton 'recharger la partie' du menu 'Consulter'", Class='note')
        col = html.TD(specific_information, colspan="6")
        row <= col
        game_status_table <= row

    return game_status_table


def get_game_status_histo(variant_data, advancement_selected):
    """ get_game_status_histo """

    advancement_selected_season, advancement_selected_year = common.get_season(advancement_selected, variant_data)
    advancement_selected_season_readable = variant_data.season_name_table[advancement_selected_season]
    game_season = f"{advancement_selected_season_readable} {advancement_selected_year}"

    game_status_table = html.TABLE()
    row = html.TR()
    col = html.TD(f"Saison {game_season}")
    row <= col
    game_status_table <= row

    return game_status_table


def show_board(panel):
    """ map and ratings """

    def callback_render(_):
        """ callback_render """

        # since orders are not involved not save/restore context

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

        # do not put the orders here

    # create canvas
    map_size = VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    panel <= canvas
    panel <= html.BR()

    # ratings
    ratings = POSITION_DATA.role_ratings()
    units = POSITION_DATA.role_units()
    colours = POSITION_DATA.role_colours()
    game_scoring = GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = make_rating_colours_window(VARIANT_DATA, ratings, units, colours, game_scoring)
    panel <= rating_colours_window
    panel <= html.BR()


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


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION


MY_SUB_PANEL = html.DIV(id="play")
MY_PANEL <= MY_SUB_PANEL