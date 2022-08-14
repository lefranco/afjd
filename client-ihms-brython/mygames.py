""" home """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import interface
import config
import mapping
import selection
import memoize
import play
import index  # circular import

MY_PANEL = html.DIV(id="mygames")
MY_PANEL.attrs['style'] = 'display: table'


def get_all_roles_allocated_to_player():
    """ get all roles the player has in all the games : returns empty dict if problem"""

    dict_role_id = {}

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

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-games-roles"

    # get players allocated to game : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_role_id


def date_last_visit_load_all_games(visit_type):
    """ date_last_visit_load_all_games : returns empty dct if problem """

    dict_time_stamp = {}

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

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-game-visits/{visit_type}"

    # getting last visit in a game : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_time_stamp


def date_last_declarations():
    """ date_last_declarations : returns empty dict if problem """

    dict_time_stamp = {}

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

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/date-last-declarations"

    # getting last game declaration : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_time_stamp


def date_last_messages():
    """ date_last_messages : returns empty dict if problem """

    dict_time_stamp = {}

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

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/date-last-game-messages"

    # getting last game message role : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_time_stamp


def get_all_player_games_roles_submitted_orders():
    """ get_all_player_games_roles_submitted_orders : retuens empty dict if problem """

    dict_submitted_data = {}

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

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-player-games-orders-submitted"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_submitted_data


def information_about_quitting():
    """ information_about_quitting """

    information = html.DIV(Class='note')
    information <= "Pour quitter une partie, utiliser le menu 'appariement / quitter la partie'"
    return information


def my_games(state_name):
    """ my_games """

    def select_game_callback(_, game_name, game_data_sel, arrival):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        InfoDialog("OK", f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page", remove_after=config.REMOVE_AFTER)
        selection.show_game_selected()

        # so that will go to proper page
        play.set_arrival(arrival)

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    def start_game_callback(_, game):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au démarrage de la partie {game}: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au démarrage de la partie {game}: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La partie a été démarrée : {messages}", remove_after=config.REMOVE_AFTER)

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'current_state': 1,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game state : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_PANEL.clear()
        my_games(state_name)

    def stop_game_callback(_, game):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'arrêt de la partie {game}: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'arrêt de la partie {game}: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La partie a été arrêtée : {messages}", remove_after=config.REMOVE_AFTER)

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'current_state': 2,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # changing game state : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_PANEL.clear()
        my_games(state_name)

    def again(state_name):
        """ again """
        MY_PANEL.clear()
        my_games(state_name)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_PANEL.clear()
        my_games(state_name)

    def change_action_mode_callback(_):
        if storage['ACTION_COLUMN_MODE'] == 'displayed':
            storage['ACTION_COLUMN_MODE'] = 'not_displayed'
        else:
            storage['ACTION_COLUMN_MODE'] = 'displayed'
        MY_PANEL.clear()
        my_games(state_name)

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by != storage['SORT_BY_MYGAMES']:
            storage['SORT_BY_MYGAMES'] = new_sort_by
            storage['REVERSE_NEEDED_MYGAMES'] = str(False)
        else:
            storage['REVERSE_NEEDED_MYGAMES'] = str(not bool(storage['REVERSE_NEEDED_MYGAMES'] == 'True'))

        MY_PANEL.clear()
        my_games(state_name)

    overall_time_before = time.time()

    # title
    MY_PANEL <= html.H2(f"Parties que je joue dans l'état : {state_name}")

    state = config.STATE_CODE_TABLE[state_name]

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    dict_role_id = get_all_roles_allocated_to_player()
    if not dict_role_id:
        alert("Il semble que vous ne jouiez dans aucune partie... Quel dommage !")
        return

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiant joueur")
        return

    player_games = common.get_player_games_playing_in(player_id)
    if player_games is None:
        alert("Erreur chargement liste parties joueés")
        return

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    dict_submitted_data = get_all_player_games_roles_submitted_orders()
    if not dict_submitted_data:
        alert("Erreur chargement des soumissions dans les parties")
        return

    dict_time_stamp_last_declarations = date_last_declarations()
    if not dict_time_stamp_last_declarations:
        alert("Erreur chargement dates dernières déclarations des parties")
        return

    dict_time_stamp_last_messages = date_last_messages()
    if not dict_time_stamp_last_messages:
        alert("Erreur chargement dates derniers messages des parties")
        return

    dict_time_stamp_last_visits_declarations = date_last_visit_load_all_games(config.DECLARATIONS_TYPE)
    if not dict_time_stamp_last_visits_declarations:
        alert("Erreur chargement dates visites dernières declarations des parties")
        return

    dict_time_stamp_last_visits_messages = date_last_visit_load_all_games(config.MESSAGES_TYPE)
    if not dict_time_stamp_last_visits_messages:
        alert("Erreur chargement dates visites derniers messages des parties")
        return

    time_stamp_now = time.time()

    # button for switching mode
    if 'GAME_ACCESS_MODE' not in storage:
        storage['GAME_ACCESS_MODE'] = 'button'
    if storage['GAME_ACCESS_MODE'] == 'button':
        button = html.BUTTON("Basculer en mode liens externes (plus lent mais conserve cette page)")
    else:
        button = html.BUTTON("Basculer en mode boutons (plus rapide mais remplace cette page)")
    button.bind("click", change_button_mode_callback)
    MY_PANEL <= button

    # separator
    MY_PANEL <= " "

    # button for switching mode (action)
    if 'ACTION_COLUMN_MODE' not in storage:
        storage['ACTION_COLUMN_MODE'] = 'not_displayed'
    if storage['ACTION_COLUMN_MODE'] == 'not_displayed':
        button = html.BUTTON("Basculer en mode avec colonne action")
    else:
        button = html.BUTTON("Basculer en mode sans colonne action")
    button.bind("click", change_action_mode_callback)
    MY_PANEL <= button

    MY_PANEL <= html.BR()
    MY_PANEL <= html.BR()

    games_table = html.TABLE()

    fields = ['variant', 'nopress_game', 'nomessage_game', 'deadline', 'current_advancement', 'role_played', 'all_orders_submitted', 'all_agreed', 'orders_submitted', 'agreed', 'new_declarations', 'new_messages', 'go_game']

    if storage['ACTION_COLUMN_MODE'] == 'displayed':
        fields.extend(['action'])

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'variant': 'variante', 'deadline': 'date limite', 'nopress_game': 'publics(*)', 'nomessage_game': 'privés(*)', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'orders_submitted': 'mes ordres', 'agreed': 'suis d\'accord', 'all_orders_submitted': 'ordres(**)', 'all_agreed': 'tous d\'accord', 'new_declarations': 'déclarations', 'new_messages': 'messages', 'go_game': 'aller dans la partie', 'action': 'action'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['variant', 'nopress_game', 'nomessage_game', 'deadline', 'current_advancement', 'role_played', 'go_game']:

            if field == 'go_game':

                # button for sorting by creation date
                button = html.BUTTON("&lt;date de création&gt;")
                button.bind("click", lambda e, f='creation': sort_by_callback(e, f))
                buttons <= button

                # separator
                buttons <= " "

                # button for sorting by name
                button = html.BUTTON("&lt;nom&gt;")
                button.bind("click", lambda e, f='name': sort_by_callback(e, f))
                buttons <= button

            else:

                button = html.BUTTON("<>")
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button
        col = html.TD(buttons)
        row <= col
    games_table <= row

    games_id_player = {int(n) for n in player_games}

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0

    # default
    if 'SORT_BY_MYGAMES' not in storage:
        storage['SORT_BY_MYGAMES'] = 'creation'
    if 'REVERSE_NEEDED_MYGAMES' not in storage:
        storage['REVERSE_NEEDED_MYGAMES'] = str(False)

    sort_by = storage['SORT_BY_MYGAMES']
    reverse_needed = bool(storage['REVERSE_NEEDED_MYGAMES'] == 'True')

    if sort_by == 'creation':
        def key_function(g): return int(g[0])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'name':
        def key_function(g): return g[1]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'variant':
        def key_function(g): return g[1]['variant']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_game':
        def key_function(g): return (g[1]['nopress_game'], g[1]['nopress_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_game':
        def key_function(g): return (g[1]['nomessage_game'], g[1]['nomessage_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'role_played':
        def key_function(g): return int(dict_role_id.get(g[0], -1))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    for game_id_str, data in sorted(games_dict.items(), key=key_function, reverse=reverse_needed):

        if data['current_state'] != state:
            continue

        # do not display games players does not participate into
        game_id = int(game_id_str)
        if game_id not in games_id_player:
            continue

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content
        if variant_name_loaded in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
            variant_content_loaded = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded]
        else:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                alert("Erreur chargement données variante de la partie")
                return
            memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded] = variant_content_loaded

        # selected display (user choice)
        interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

        # parameters

        if (variant_name_loaded, interface_chosen) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
            parameters_read = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)]
        else:
            parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)
            memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)] = parameters_read

        # build variant data

        if (variant_name_loaded, interface_chosen) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
            variant_data = memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)]
        else:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)] = variant_data

        number_games += 1

        role_id = dict_role_id[str(game_id)]
        if role_id == -1:
            role_id = None
        data['role_played'] = role_id

        submitted_data = {}
        submitted_data['needed'] = dict_submitted_data['dict_needed'][str(game_id)]
        submitted_data['submitted'] = dict_submitted_data['dict_submitted'][str(game_id)]
        submitted_data['agreed'] = dict_submitted_data['dict_agreed'][str(game_id)]

        data['orders_submitted'] = None
        data['agreed'] = None
        data['all_orders_submitted'] = None
        data['all_agreed'] = None
        data['new_declarations'] = None
        data['new_messages'] = None
        data['go_game'] = None
        data['action'] = None

        arrival = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None
            game_name = data['name']

            if field == 'nopress_game':
                value1 = value
                value2 = data['nopress_current']
                if value2 == value1:
                    value = "Non" if value1 else "Oui"
                else:
                    value1 = "Non" if value1 else "Oui"
                    value2 = "Non" if value2 else "Oui"
                    value = f"{value1} ({value2})"

            if field == 'nomessage_game':
                value1 = value
                value2 = data['nomessage_current']
                if value2 == value1:
                    value = "Non" if value1 else "Oui"
                else:
                    value1 = "Non" if value1 else "Oui"
                    value2 = "Non" if value2 else "Oui"
                    value = f"{value1} ({value2})"

            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
                deadline_loaded_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded_str

                time_unit = 60 if data['fast'] else 60 * 60
                approach_duration = 24 * 60 * 60

                # we are after deadline + grace
                if time_stamp_now > deadline_loaded + time_unit * data['grace_duration']:
                    colour = config.PASSED_GRACE_COLOUR
                # we are after deadline
                elif time_stamp_now > deadline_loaded:
                    colour = config.PASSED_DEADLINE_COLOUR
                # deadline is today
                elif time_stamp_now > deadline_loaded - approach_duration:
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
                    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{interface_chosen}/roles/{role_id}.jpg", title=role_name)
                value = role_icon_img

            if field == 'orders_submitted':
                value = ""
                if data['current_advancement'] % 5 == 4 and (data['current_advancement'] + 1) // 5 >= data['nb_max_cycles_to_play']:
                    flag = html.IMG(src="./images/game_over.png", title="Partie finie")
                    value = flag
                else:
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
                if data['current_advancement'] % 5 == 4 and (data['current_advancement'] + 1) // 5 >= data['nb_max_cycles_to_play']:
                    flag = html.IMG(src="./images/game_over.png", title="Partie finie")
                    value = flag
                else:
                    submitted_roles_list = submitted_data['submitted']
                    agreed_roles_list = submitted_data['agreed']
                    if role_id is not None:
                        if role_id in agreed_roles_list:
                            flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre")
                            value = flag
                        elif role_id in needed_roles_list:
                            flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
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
                        if not arrival:
                            arrival = "declarations"
                    value = popup

            if field == 'new_messages':
                value = ""
                if role_id is not None:
                    # popup if new
                    popup = ""
                    if dict_time_stamp_last_messages[str(game_id)] > dict_time_stamp_last_visits_messages[str(game_id)]:
                        popup = html.IMG(src="./images/messages_received.jpg", title="Nouveau(x) message(s) dans cette partie !")
                        if not arrival:
                            arrival = "messages"
                    value = popup

            if field == 'go_game':
                if storage['GAME_ACCESS_MODE'] == 'button':
                    form = html.FORM()
                    input_jump_game = html.INPUT(type="submit", value=game_name)
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=arrival: select_game_callback(e, gn, gds, a))
                    form <= input_jump_game
                    value = form
                else:
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= game_name
                    value = link

            if field == 'action':
                value = ""
                if storage['ACTION_COLUMN_MODE'] == 'displayed':
                    if role_id == 0:
                        if state == 0:
                            form = html.FORM()
                            input_start_game = html.INPUT(type="submit", value="démarrer")
                            input_start_game.bind("click", lambda e, g=game_name: start_game_callback(e, g))
                            form <= input_start_game
                            value = form
                        if state == 1:
                            form = html.FORM()
                            input_stop_game = html.INPUT(type="submit", value="arrêter")
                            input_stop_game.bind("click", lambda e, g=game_name: stop_game_callback(e, g))
                            form <= input_stop_game
                            value = form

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        games_table <= row

    MY_PANEL <= games_table
    MY_PANEL <= html.BR()

    MY_PANEL <= html.DIV("(*) Messagerie possible sur la partie, si le paramètre applicable actuellement est différent (partie terminée) il est indiqué entre parenthèses", Class='note')
    MY_PANEL <= html.BR()

    MY_PANEL <= html.DIV("(**) Parties anonymes : le statut des ordres des autres joueurs n'est pas accessible", Class='note')
    MY_PANEL <= html.BR()

    MY_PANEL <= information_about_quitting()
    MY_PANEL <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
    special_legend = html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}")
    MY_PANEL <= special_legend
    MY_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed} avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    MY_PANEL <= html.DIV(stats, Class='load')
    MY_PANEL <= html.BR()

    for other_state_name in config.STATE_CODE_TABLE:

        if other_state_name != state_name:

            input_change_state = html.INPUT(type="submit", value=other_state_name)
            input_change_state.bind("click", lambda _, s=other_state_name: again(s))

            MY_PANEL <= input_change_state
            MY_PANEL <= html.BR()
            MY_PANEL <= html.BR()


def render(panel_middle):
    """ render """
    MY_PANEL.clear()
    my_games('en cours')
    panel_middle <= MY_PANEL
