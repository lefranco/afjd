""" home """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import interface
import config
import mapping
import selection
import index  # circular import

my_panel = html.DIV(id="mygames")
my_panel.attrs['style'] = 'display: table'


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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_role_id


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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_time_stamp


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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_time_stamp


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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_submitted_data


def get_player_games_playing_in(player_id):
    """ get_player_games_playing_in """

    player_games_dict = None

    def reply_callback(req):
        nonlocal player_games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récuperation de la liste des parties du joueur : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récuperation de la liste des parties du joueur : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        player_games_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/player-allocations/{player_id}"

    # getting player games playing in list : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict(player_games_dict)


def my_games(state_name):
    """ my_games """

    def select_game_callback(_, game):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    overall_time_before = time.time()

    my_panel.clear()

    # title
    my_panel <= html.H2(f"Parties que je joue dans l'état : {state_name}")

    state = config.STATE_CODE_TABLE[state_name]

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiants joueurs")
        return

    player_games = get_player_games_playing_in(player_id)
    if player_games is None:
        alert("Erreur chargement liste parties joueés")
        return

    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement données des parties")
        return

    dict_role_id = get_all_roles_allocated_to_player()
    if dict_role_id is None:
        alert("Erreur chargement des roles dans les parties")
        return
    dict_role_id = dict(dict_role_id)

    dict_submitted_data = get_all_player_games_roles_submitted_orders()
    if dict_submitted_data is None:
        alert("Erreur chargement des soumissions dans les parties")
        return
    dict_submitted_data = dict(dict_submitted_data)

    dict_time_stamp_last_declarations = date_last_declarations()
    if dict_time_stamp_last_declarations is None:
        alert("Erreur chargement dates dernières déclarations des parties")
        return
    dict_time_stamp_last_declarations = dict(dict_time_stamp_last_declarations)

    dict_time_stamp_last_messages = date_last_messages()
    if dict_time_stamp_last_messages is None:
        alert("Erreur chargement dates derniers messages des parties")
        return
    dict_time_stamp_last_messages = dict(dict_time_stamp_last_messages)

    dict_time_stamp_last_visits_declarations = date_last_visit_load_all_games(config.DECLARATIONS_TYPE)
    if dict_time_stamp_last_visits_declarations is None:
        alert("Erreur chargement dates visites dernières declarations des parties")
        return
    dict_time_stamp_last_visits_declarations = dict(dict_time_stamp_last_visits_declarations)

    dict_time_stamp_last_visits_messages = date_last_visit_load_all_games(config.MESSAGES_TYPE)
    if dict_time_stamp_last_visits_messages is None:
        alert("Erreur chargement dates visites derniers messages des parties")
        return
    dict_time_stamp_last_visits_messages = dict(dict_time_stamp_last_visits_messages)

    time_stamp_now = time.time()

    games_table = html.TABLE()

    fields = ['name', 'variant', 'deadline', 'current_advancement', 'role_played', 'all_orders_submitted', 'all_agreed', 'orders_submitted', 'agreed', 'new_declarations', 'new_messages', 'jump_here', 'go_away']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'variant': 'variante', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'orders_submitted': 'mes ordres', 'agreed': 'mon accord', 'all_orders_submitted': 'ordres', 'all_agreed': 'accords', 'new_declarations': 'déclarations', 'new_messages': 'messages', 'jump_here': 'partie', 'go_away': 'partie (nouvel onglet)'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    games_id_player = {int(n) for n in player_games.keys()}

    # for optimization
    variant_content_memoize_table = dict()
    parameters_read_memoize_table = dict()
    variant_data_memoize_table = dict()

    number_games = 0

    for game_id_str, data in sorted(games_dict.items(), key=lambda g: int(g[0])):

        # do not display finished games
        if data['current_state'] != state:
            continue

        # do not display games players does not participate into
        game_id = int(game_id_str)
        if game_id not in games_id_player:
            continue

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content
        if variant_name_loaded not in variant_content_memoize_table:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                alert("Erreur chargement données variante de la partie")
                return
            variant_content_memoize_table[variant_name_loaded] = variant_content_loaded
        else:
            variant_content_loaded = variant_content_memoize_table[variant_name_loaded]

        # selected display (user choice)
        display_chosen = interface.get_display_from_variant(variant_name_loaded)

        # parameters

        if (variant_name_loaded, display_chosen) in parameters_read_memoize_table:
            parameters_read = parameters_read_memoize_table[(variant_name_loaded, display_chosen)]
        else:
            parameters_read = common.read_parameters(variant_name_loaded, display_chosen)
            parameters_read_memoize_table[(variant_name_loaded, display_chosen)] = parameters_read

        # build variant data

        if variant_name_loaded not in variant_data_memoize_table:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            variant_data_memoize_table[variant_name_loaded] = variant_data
        else:
            variant_data = variant_data_memoize_table[variant_name_loaded]

        number_games += 1

        role_id = dict_role_id[str(game_id)]
        if role_id == -1:
            role_id = None
        data['role_played'] = role_id

        submitted_data = dict()
        submitted_data['needed'] = dict_submitted_data['dict_needed'][str(game_id)]
        submitted_data['submitted'] = dict_submitted_data['dict_submitted'][str(game_id)]
        submitted_data['agreed'] = dict_submitted_data['dict_agreed'][str(game_id)]

        data['orders_submitted'] = None
        data['agreed'] = None
        data['all_orders_submitted'] = None
        data['all_agreed'] = None
        data['new_declarations'] = None
        data['new_messages'] = None
        data['jump_here'] = None
        data['go_away'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None

            if field == 'deadline':

                deadline_loaded = value
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
                deadline_loaded_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded_str

                time_unit = 60 if data['fast'] else 24 * 60 * 60

                # we are after deadline + grace
                if time_stamp_now > deadline_loaded + time_unit * data['grace_duration']:
                    colour = config.PASSED_GRACE_COLOUR
                # we are after deadline
                elif time_stamp_now > deadline_loaded:
                    colour = config.PASSED_DEADLINE_COLOUR
                # deadline is today
                elif time_stamp_now > deadline_loaded - time_unit:
                    colour = config.APPROACHING_DEADLINE_COLOUR

            if field == 'current_advancement':

                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'role_played':

                value = ""
                if role_id is None:
                    role_icon_img = html.IMG(src="./images/assigned.png", title="Affecté à la partie")
                else:
                    role = variant_data.roles[role_id]
                    role_name = variant_data.name_table[role]
                    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
                value = role_icon_img

            if field == 'orders_submitted':

                value = ""
                submitted_roles_list = submitted_data['submitted']
                needed_roles_list = submitted_data['needed']
                if role_id is not None:
                    if role_id in submitted_roles_list:
                        flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                        value = flag
                    elif role_id in needed_roles_list:
                        flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
                        value = flag

            if field == 'agreed':

                value = ""
                submitted_roles_list = submitted_data['submitted']
                agreed_roles_list = submitted_data['agreed']
                if role_id is not None:
                    if role_id in agreed_roles_list:
                        flag = html.IMG(src="./images/ready.jpg", title="Prêt pour résoudre")
                        value = flag
                    elif role_id in needed_roles_list:
                        flag = html.IMG(src="./images/not_ready.jpg", title="Pas prêt pour résoudre")
                        value = flag

            if field == 'all_orders_submitted':

                value = ""
                if role_id is not None:
                    submitted_roles_list = submitted_data['submitted']
                    nb_submitted = len(submitted_roles_list)
                    needed_roles_list = submitted_data['needed']
                    nb_needed = len(needed_roles_list)
                    stats = f"{nb_submitted}/{nb_needed}"
                    value = stats
                    if nb_submitted >= nb_needed:
                        # we have all orders : green
                        colour = config.ALL_ORDERS_IN_COLOUR

            if field == 'all_agreed':

                value = ""
                if role_id is not None:
                    agreed_roles_list = submitted_data['agreed']
                    nb_agreed = len(agreed_roles_list)
                    submitted_roles_list = submitted_data['submitted']
                    nb_submitted = len(submitted_roles_list)
                    stats = f"{nb_agreed}/{nb_submitted}"
                    value = stats
                    if nb_agreed >= nb_submitted:
                        # we have all agreements : green
                        colour = config.ALL_AGREEMENTS_IN_COLOUR

            if field == 'new_declarations':

                value = ""
                if role_id is not None:

                    # popup if new
                    popup = ""
                    if dict_time_stamp_last_declarations[str(game_id)] > dict_time_stamp_last_visits_declarations[str(game_id)]:
                        popup = html.IMG(src="./images/press_published.jpg", title="Nouvelle(s) déclaration(s) dans cette partie !")
                    value = popup

            if field == 'new_messages':

                value = ""
                if role_id is not None:

                    # popup if new
                    popup = ""
                    if dict_time_stamp_last_messages[str(game_id)] > dict_time_stamp_last_visits_messages[str(game_id)]:
                        popup = html.IMG(src="./images/messages_received.jpg", title="Nouveau(x) message(s) dans cette partie !")
                    value = popup

            if field == 'jump_here':

                game_name = data['name']
                form = html.FORM()
                input_jump_game = html.INPUT(type="submit", value="sauter")
                input_jump_game.bind("click", lambda e, g=game_name: select_game_callback(e, g))
                form <= input_jump_game
                value = form

            if field == 'go_away':

                link = html.A(href=f"?game={game_name}", target="_blank")
                link <= "y aller"
                value = link

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        games_table <= row

    my_panel <= games_table
    my_panel <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
    special_legend = html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}", Class='note')
    my_panel <= special_legend
    my_panel <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed} avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    my_panel <= html.DIV(stats, Class='load')
    my_panel <= html.BR()

    for other_state_name in config.STATE_CODE_TABLE:

        if other_state_name != state_name:

            input_change_state = html.INPUT(type="submit", value=other_state_name)
            input_change_state.bind("click", lambda _, s=other_state_name: my_games(s))

            my_panel <= input_change_state
            my_panel <= html.BR()
            my_panel <= html.BR()


def render(panel_middle):
    """ render """
    my_games('en cours')
    panel_middle <= my_panel
