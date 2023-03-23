""" home """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position


import json
import time

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import common
import config
import mapping
import interface
import memoize
import play
import allgames


MY_PANEL = html.DIV(id="mygames")
MY_PANEL.attrs['style'] = 'display: table-row'


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
    """ date_last_visit_load_all_games : returns empty dict if problem """

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
    information <= "Pour quitter une partie, utiliser le menu “Parties“ sous menu “Appariement“"
    return information


def get_my_delays():
    """ get_my_delays """

    delays_list = None

    def reply_callback(req):
        nonlocal delays_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des retards pour toutes mes parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des retards pour toutes mes parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        delays_list = req_result['incidents']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/player-game-incidents"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return delays_list


def my_delays(ev):  # pylint: disable=invalid-name
    """ my_delays """

    def select_game_callback(ev, game_name, game_data_sel, arrival):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        common.info_dialog(f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page")
        allgames.show_game_selected()

        # so that will go to proper page
        play.set_arrival(arrival)

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    ev.preventDefault()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    delays_list = get_my_delays()

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    delays_table = html.TABLE()

    # the display order
    fields = ['date', 'name', 'used_for_elo', 'go_game', 'current_advancement', 'role_played', 'duration']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'date': 'date', 'name': 'nom', 'used_for_elo': 'elo', 'go_game': 'aller dans la partie', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'duration': 'durée'}[field]
        col = html.TD(field_fr)
        thead <= col
    delays_table <= thead

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0

    for game_id, role_id, advancement_delay, duration_delay, date_delay in sorted(delays_list, key=lambda t: t[4], reverse=True):

        data = games_dict[str(game_id)]

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

        row = html.TR()
        for field in fields:

            if field == 'date':
                datetime_deadline_delay = mydatetime.fromtimestamp(date_delay)
                datetime_deadline_delay_str = mydatetime.strftime2(*datetime_deadline_delay)
                value = datetime_deadline_delay_str

            if field == 'name':
                game_name = data['name']
                value = game_name

            if field == 'used_for_elo':
                value = "Oui" if data['used_for_elo'] else "Non"

            if field == 'go_game':

                if storage['GAME_ACCESS_MODE'] == 'button':

                    form = html.FORM()
                    input_jump_game = html.INPUT(type="image", src="./images/play.png")
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=None: select_game_callback(e, gn, gds, a))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'current_advancement':
                advancement_season, advancement_year = common.get_season(advancement_delay, variant_data)
                advancement_season_readable = variant_data.season_name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'role_played':
                role = variant_data.roles[role_id]
                role_name = variant_data.role_name_table[role]
                role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{interface_chosen}/roles/{role_id}.jpg", title=role_name)
                value = role_icon_img

            if field == 'duration':
                value = duration_delay

            col = html.TD(value)

            row <= col

        delays_table <= row

    MY_PANEL.clear()
    MY_PANEL <= html.H2("Tous mes retards sur toutes mes parties")
    MY_PANEL <= delays_table
    MY_PANEL <= html.BR()

    MY_PANEL <= html.DIV("Un retard signifie que le joueur (ou l'arbitre) a réalisé la transition 'pas d'accord -> 'd'accord pour résoudre' après la date limite", Class='note')
    MY_PANEL <= html.BR()

    MY_PANEL <= html.DIV("Les retards sont en heures entamées", Class='note')


def my_games(state_name):
    """ my_games """

    def select_game_callback(ev, game_name, game_data_sel, arrival):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        common.info_dialog(f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page")
        allgames.show_game_selected()

        # so that will go to proper page
        play.set_arrival(arrival)

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    def start_game_callback(ev, game):  # pylint: disable=invalid-name

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
            common.info_dialog(f"La partie a été démarrée : {messages}")

        ev.preventDefault()

        json_dict = {
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

    def stop_game_callback(ev, game):  # pylint: disable=invalid-name

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
            common.info_dialog(f"La partie a été arrêtée : {messages}")

        ev.preventDefault()

        json_dict = {
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
        button = html.BUTTON("Basculer en mode liens externes (plus lent mais conserve cette page)", Class='btn-menu')
    else:
        button = html.BUTTON("Basculer en mode boutons (plus rapide mais remplace cette page)", Class='btn-menu')
    button.bind("click", change_button_mode_callback)
    MY_PANEL <= button

    # separator
    MY_PANEL <= " "

    # button for switching mode (action)
    if 'ACTION_COLUMN_MODE' not in storage:
        storage['ACTION_COLUMN_MODE'] = 'not_displayed'
    if storage['ACTION_COLUMN_MODE'] == 'not_displayed':
        button = html.BUTTON("Basculer en mode avec colonne action", Class='btn-menu')
    else:
        button = html.BUTTON("Basculer en mode sans colonne action", Class='btn-menu')
    button.bind("click", change_action_mode_callback)
    MY_PANEL <= button

    MY_PANEL <= html.BR()
    MY_PANEL <= html.BR()

    games_table = html.TABLE()

    # the display order
    fields = ['name', 'go_game', 'deadline', 'current_advancement', 'role_played', 'all_orders_submitted', 'all_agreed', 'orders_submitted', 'agreed', 'new_declarations', 'new_messages', 'variant', 'used_for_elo', 'nopress_game', 'nomessage_game']

    if storage['ACTION_COLUMN_MODE'] == 'displayed':
        fields.extend(['action'])

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'go_game': 'aller dans la partie', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'orders_submitted': 'mes ordres', 'agreed': 'mon accord', 'all_orders_submitted': 'ordres de tous', 'all_agreed': 'accords de tous(*)', 'new_declarations': 'déclarations', 'new_messages': 'messages', 'variant': 'variante', 'used_for_elo': 'elo', 'nopress_game': 'publics(**)', 'nomessage_game': 'privés(**)', 'action': 'action'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'deadline', 'current_advancement', 'role_played', 'variant', 'used_for_elo', 'nopress_game', 'nomessage_game']:

            if field == 'name':

                # button for sorting by creation date
                button = html.BUTTON("&lt;Date de création&gt;", Class='btn-menu')
                button.bind("click", lambda e, f='creation': sort_by_callback(e, f))
                buttons <= button

                # separator
                buttons <= " "

                # button for sorting by name
                button = html.BUTTON("&lt;Nom&gt;", Class='btn-menu')
                button.bind("click", lambda e, f='name': sort_by_callback(e, f))
                buttons <= button

            else:

                button = html.BUTTON("<>", Class='btn-menu')
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
    elif sort_by == 'used_for_elo':
        def key_function(g): return int(g[1]['used_for_elo'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_game':
        def key_function(g): return (int(g[1]['nopress_game']), int(g[1]['nopress_current']))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_game':
        def key_function(g): return (int(g[1]['nomessage_game']), int(g[1]['nomessage_current']))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
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
        submitted_data['agreed_now'] = dict_submitted_data['dict_agreed_now'][str(game_id)]
        submitted_data['agreed_after'] = dict_submitted_data['dict_agreed_after'][str(game_id)]

        data['go_game'] = None
        data['orders_submitted'] = None
        data['agreed'] = None
        data['all_orders_submitted'] = None
        data['all_agreed'] = None
        data['new_declarations'] = None
        data['new_messages'] = None
        data['action'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None
            game_name = data['name']

            if field == 'name':
                value = game_name

            if field == 'go_game':

                if storage['GAME_ACCESS_MODE'] == 'button':

                    form = html.FORM()
                    input_jump_game = html.INPUT(type="image", src="./images/play.png")
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=None: select_game_callback(e, gn, gds, a))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                datetime_deadline_loaded_str = mydatetime.strftime2(*datetime_deadline_loaded)
                value = datetime_deadline_loaded_str

                if data['fast']:
                    if time_stamp_now > deadline_loaded:
                        colour = config.PASSED_DEADLINE_COLOUR
                else:
                    # we are after everything !
                    if time_stamp_now > deadline_loaded + 60 * 60 * 24 * config.CRITICAL_DELAY_DAY:
                        colour = config.CRITICAL_COLOUR
                    # we are after deadline + grace
                    elif time_stamp_now > deadline_loaded + 60 * 60 * data['grace_duration']:
                        colour = config.PASSED_GRACE_COLOUR
                    # we are after deadline + slight
                    elif time_stamp_now > deadline_loaded + config.SLIGHT_DELAY_SEC:
                        colour = config.PASSED_DEADLINE_COLOUR
                    # we are slightly after deadline
                    elif time_stamp_now > deadline_loaded:
                        colour = config.SLIGHTLY_PASSED_DEADLINE_COLOUR
                    # deadline is today
                    elif time_stamp_now > deadline_loaded - config.APPROACH_DELAY_SEC:
                        colour = config.APPROACHING_DEADLINE_COLOUR

            if field == 'current_advancement':
                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.season_name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'role_played':
                value = ""
                if role_id is None:
                    role_icon_img = html.IMG(src="./images/assigned.png", title="Affecté à la partie")
                else:
                    role = variant_data.roles[role_id]
                    role_name = variant_data.role_name_table[role]
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
                    agreed_now_roles_list = submitted_data['agreed_now']
                    agreed_after_roles_list = submitted_data['agreed_after']
                    if role_id is not None:
                        if role_id in agreed_now_roles_list:
                            flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre maintenant")
                            value = flag
                        elif role_id in agreed_after_roles_list:
                            flag = html.IMG(src="./images/agreed_after.jpg", title="D'accord pour résoudre mais à la date limite")
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
                value = "-"
                if role_id is not None:
                    if not data['anonymous'] or role_id == 0:
                        agreed_now_roles_list = submitted_data['agreed_now']
                        nb_agreed_now = len(agreed_now_roles_list)
                        agreed_after_roles_list = submitted_data['agreed_after']
                        nb_agreed_after = len(agreed_after_roles_list)
                        stats = f"{nb_agreed_now}m+{nb_agreed_after}a"
                        value = stats

            if field == 'new_declarations':
                value = ""
                if role_id is not None:
                    if dict_time_stamp_last_declarations[str(game_id)] > dict_time_stamp_last_visits_declarations[str(game_id)]:

                        arrival = "declarations"
                        if storage['GAME_ACCESS_MODE'] == 'button':
                            form = html.FORM()
                            input_jump_game = html.INPUT(type="image", src="./images/press_published.jpg")
                            input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=arrival: select_game_callback(e, gn, gds, a))
                            form <= input_jump_game
                            value = form
                        else:
                            img = html.IMG(src="./images/press_published.jpg")
                            link = html.A(href=f"?game={game_name}&arrival={arrival}", target="_blank")
                            link <= img
                            value = link

            if field == 'new_messages':
                value = ""
                if role_id is not None:
                    if dict_time_stamp_last_messages[str(game_id)] > dict_time_stamp_last_visits_messages[str(game_id)]:

                        arrival = "messages"
                        if storage['GAME_ACCESS_MODE'] == 'button':
                            form = html.FORM()
                            input_jump_game = html.INPUT(type="image", src="./images/messages_received.jpg")
                            input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=arrival: select_game_callback(e, gn, gds, a))
                            form <= input_jump_game
                            value = form
                        else:
                            img = html.IMG(src="./images/messages_received.jpg")
                            link = html.A(href=f"?game={game_name}&arrival={arrival}", target="_blank")
                            link <= img
                            value = link

            if field == 'used_for_elo':
                value = "Oui" if value else "Non"

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

            if field == 'action':
                value = ""
                if storage['ACTION_COLUMN_MODE'] == 'displayed':
                    if role_id == 0:
                        if state == 0:
                            form = html.FORM()
                            input_start_game = html.INPUT(type="image", src="./images/start_game.jpg")
                            input_start_game.bind("click", lambda e, g=game_name: start_game_callback(e, g))
                            form <= input_start_game
                            value = form
                        if state == 1:
                            form = html.FORM()
                            input_stop_game = html.INPUT(type="image", src="./images/stop_game.png")
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

    MY_PANEL <= html.DIV("Les icônes suivants sont cliquables pour aller dans ou agir sur les parties :", Class='note')
    MY_PANEL <= html.IMG(src="./images/play.png", title="Pour aller dans la partie")
    MY_PANEL <= " "
    MY_PANEL <= html.IMG(src="./images/messages_received.jpg", title="Pour aller voir les nouveaux messages privés")
    MY_PANEL <= " "
    MY_PANEL <= html.IMG(src="./images/press_published.jpg", title="Pour aller voir les nouvelles presses")
    MY_PANEL <= " "
    MY_PANEL <= html.IMG(src="./images/start_game.jpg", title="Pour démarrer la partie")
    MY_PANEL <= " "
    MY_PANEL <= html.IMG(src="./images/stop_game.png", title="Pour arrêter la partie")
    MY_PANEL <= html.BR()
    MY_PANEL <= html.BR()

    MY_PANEL <= html.DIV("(*) Accords : m=maintenant et a=à la D.L.", Class='note')
    MY_PANEL <= html.BR()

    MY_PANEL <= html.DIV("(**) Messagerie possible sur la partie, si le paramètre applicable actuellement est différent (partie terminée) il est indiqué entre parenthèses", Class='note')
    MY_PANEL <= html.BR()

    MY_PANEL <= information_about_quitting()
    MY_PANEL <= html.BR()

    # get GMT date and time
    time_stamp_now = time.time()
    date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
    special_legend = html.DIV(f"Pour information, date et heure actuellement sur votre horloge locale : {date_now_gmt_str}")
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
            MY_PANEL <= "    "

    MY_PANEL <= html.BR()
    MY_PANEL <= html.BR()
    input_my_delays = html.INPUT(type="submit", value="Consulter la liste de tous mes retards")
    input_my_delays.bind("click", my_delays)
    MY_PANEL <= input_my_delays


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    MY_PANEL.clear()
    my_games('en cours')
    panel_middle <= MY_PANEL
