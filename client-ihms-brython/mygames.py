""" home """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position


from json import loads, dumps
from time import time

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
import games

MY_PANEL = html.DIV()
MY_SUB_PANEL = html.DIV(id="page")
MY_SUB_PANEL.attrs['style'] = 'display: table-row'
MY_PANEL <= MY_SUB_PANEL

# warn because difference
DELTA_WARNING_THRESHOLD_SEC = 10


def get_suffering_games(games_dict, games_id_player, dict_role_id):
    """ get_suffering_games """

    suffering_games = []

    incomplete_games_list = get_incomplete_games()
    # there can be no message (if no game of failed to load)

    for game_id_str, data in games_dict.items():

        if data['current_state'] != 0:
            continue

        # do not display games players does not participate into
        game_id = int(game_id_str)
        if game_id not in games_id_player:
            continue

        # must be game master
        role_id = dict_role_id[str(game_id)]
        if role_id != 0:
            continue

        # game must not need players
        if game_id in incomplete_games_list:
            continue

        game_name = data['name']
        suffering_games.append(game_name)

    return suffering_games


def new_private_messages_received():
    """ new_private_messages_received """

    new_messages_loaded = 0

    def reply_callback(req):
        nonlocal new_messages_loaded
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement si des messages personnels : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement si des messages personnels : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        new_messages_loaded = req_result['new_messages']
        return

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/new-private-messages-received"

    # reading new private messages received : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return new_messages_loaded


def get_incomplete_games():
    """ get_incomplete_games : returns empty list if error or no game"""

    incomplete_games_list = []

    def reply_callback(req):
        nonlocal incomplete_games_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des parties qui sont prêtes : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des parties qui sont prêtes : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        incomplete_games_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games-incomplete"

    # getting incomplete games list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return incomplete_games_list


def get_all_roles_allocated_to_player():
    """ get all roles the player has in all the games : returns empty dict if problem"""

    dict_role_id = {}

    def reply_callback(req):
        nonlocal dict_role_id
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_role_id


def date_last_visit_load_all_games(visit_type):
    """ date_last_visit_load_all_games : returns empty dict if problem """

    dict_time_stamp = {}

    def reply_callback(req):
        nonlocal dict_time_stamp
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_time_stamp


def date_last_declarations():
    """ date_last_declarations : returns empty dict if problem """

    dict_time_stamp = {}

    def reply_callback(req):
        nonlocal dict_time_stamp
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_time_stamp


def date_last_messages():
    """ date_last_messages : returns empty dict if problem """

    dict_time_stamp = {}

    def reply_callback(req):
        nonlocal dict_time_stamp
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_time_stamp


def get_all_player_ongoing_votes():
    """ get_all_player_ongoing_votes : returns empty dict if problem """

    dict_voted_data = {}

    def reply_callback(req):
        nonlocal dict_voted_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération votes en cours pour toutes mes parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des votes en cours pour toutes mes parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        dict_voted_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-player-games-ongoing-votes"

    # get games with ongoing vote : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_voted_data


def get_all_player_games_roles_submitted_orders():
    """ get_all_player_games_roles_submitted_orders : returns empty dict if problem """

    dict_submitted_data = {}

    def reply_callback(req):
        nonlocal dict_submitted_data
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_submitted_data


def get_my_delays():
    """ get_my_delays """

    delays_list = None

    def reply_callback(req):
        nonlocal delays_list
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    delays_table = html.TABLE()

    # the display order
    fields = ['date', 'name', 'go_game', 'current_advancement', 'role_played', 'duration']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'date': 'date', 'name': 'nom', 'go_game': 'aller dans la partie', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'duration': 'durée'}[field]
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

            if field == 'go_game':

                if storage['GAME_ACCESS_MODE'] == 'button':

                    form = html.FORM()
                    input_jump_game = html.INPUT(type="image", src="./images/play.png", title="Cliquer pour aller dans la partie", Class='btn-inside')
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=None: select_game_callback(e, gn, gds, a))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png", title="Cliquer pour aller dans la partie")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'current_advancement':
                nb_max_cycles_to_play = data['nb_max_cycles_to_play']
                value = common.get_full_season(advancement_delay, variant_data, nb_max_cycles_to_play, False)

            if field == 'role_played':
                role = variant_data.roles[role_id]
                role_name = variant_data.role_name_table[role]
                role_icon_img = common.display_flag(variant_name_loaded, interface_chosen, role_id, role_name)
                value = role_icon_img

            if field == 'duration':
                value = duration_delay

            col = html.TD(value)

            row <= col

        delays_table <= row

    MY_SUB_PANEL.clear()
    MY_SUB_PANEL <= html.H2("Tous mes retards sur toutes mes parties")
    MY_SUB_PANEL <= delays_table
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Un retard signifie que le joueur (ou l'arbitre) a réalisé la transition 'pas d'accord pour la résolution' -> 'd'accord pour résoudre' après la date limite", Class='note')
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées", Class='note')


def get_my_dropouts():
    """ get_my_dropouts """

    dropouts_list = None

    def reply_callback(req):
        nonlocal dropouts_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des abandons pour toutes mes parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des abandons pour toutes mes parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        dropouts_list = req_result['dropouts']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/player-game-dropouts"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dropouts_list


def my_dropouts(ev):  # pylint: disable=invalid-name
    """ my_dropouts """

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

    dropouts_list = get_my_dropouts()

    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    dropouts_table = html.TABLE()

    # the display order
    fields = ['date', 'name', 'go_game', 'role_played']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'date': 'date', 'name': 'nom', 'go_game': 'aller dans la partie', 'role_played': 'rôle joué'}[field]
        col = html.TD(field_fr)
        thead <= col
    dropouts_table <= thead

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0

    for game_id, role_id, date_dropout in sorted(dropouts_list, key=lambda t: t[2], reverse=True):

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
                datetime_deadline_dropout = mydatetime.fromtimestamp(date_dropout)
                datetime_deadline_dropout_str = mydatetime.strftime2(*datetime_deadline_dropout)
                value = datetime_deadline_dropout_str

            if field == 'name':
                game_name = data['name']
                value = game_name

            if field == 'go_game':

                if storage['GAME_ACCESS_MODE'] == 'button':

                    form = html.FORM()
                    input_jump_game = html.INPUT(type="image", src="./images/play.png", title="Cliquer pour aller dans la partie", Class='btn-inside')
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=None: select_game_callback(e, gn, gds, a))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png", title="Cliquer pour aller dans la partie")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'role_played':
                role = variant_data.roles[role_id]
                role_name = variant_data.role_name_table[role]
                role_icon_img = common.display_flag(variant_name_loaded, interface_chosen, role_id, role_name)
                value = role_icon_img

            col = html.TD(value)

            row <= col

        dropouts_table <= row

    MY_SUB_PANEL.clear()
    MY_SUB_PANEL <= html.H2("Tous mes abandons sur toutes mes parties")
    MY_SUB_PANEL <= dropouts_table
    MY_SUB_PANEL <= html.BR()


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

    def edit_game_callback(ev, game_name):  # pylint: disable=invalid-name
        """ edit_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        common.info_dialog(f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page")
        allgames.show_game_selected()

        # action of going to edit game page
        PANEL_MIDDLE.clear()
        games.render(PANEL_MIDDLE)

    def start_game_callback(ev, game):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
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
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        my_games(state_name)

    def stop_game_callback(ev, game):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
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
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        my_games(state_name)

    def again(state_name):
        """ again """
        MY_SUB_PANEL.clear()
        my_games(state_name)

    def change_show_mode_callback(_):
        if storage['GAME_SHOW_MODE'] == 'complete':
            storage['GAME_SHOW_MODE'] = 'reduced'
        else:
            storage['GAME_SHOW_MODE'] = 'complete'
        MY_SUB_PANEL.clear()
        my_games(state_name)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_SUB_PANEL.clear()
        my_games(state_name)

    def change_action_mode_callback(_):
        if storage['ACTION_COLUMN_MODE'] == 'displayed':
            storage['ACTION_COLUMN_MODE'] = 'not_displayed'
        else:
            storage['ACTION_COLUMN_MODE'] = 'displayed'
        MY_SUB_PANEL.clear()
        my_games(state_name)

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by != storage['SORT_BY_MYGAMES']:
            storage['SORT_BY_MYGAMES'] = new_sort_by
            storage['REVERSE_NEEDED_MYGAMES'] = str(False)
        else:
            storage['REVERSE_NEEDED_MYGAMES'] = str(not bool(storage['REVERSE_NEEDED_MYGAMES'] == 'True'))

        MY_SUB_PANEL.clear()
        my_games(state_name)

    overall_time_before = time()

    # title
    MY_SUB_PANEL <= html.H2(f"Parties que je joue dans l'état : {state_name}")

    state = config.STATE_CODE_TABLE[state_name]

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    # get the day
    day_now = int(time()) // 3600

    # we check new private messages once a day
    day_notified = 0
    if 'DATE_NEW_MESSAGES_NOTIFIED' in storage:
        day_notified = int(storage['DATE_NEW_MESSAGES_NOTIFIED'])
    if day_now > day_notified:
        new_messages = new_private_messages_received()
        if new_messages:
            alert(f"Vous avez {new_messages} nouveau(x) message(s) personnel(s) ! Pour les lire : Accueil/Messages personnels.")
            storage['DATE_NEW_MESSAGES_NOTIFIED'] = str(day_now)

    dict_role_id = get_all_roles_allocated_to_player()
    if not dict_role_id:
        alert("Il semble que vous ne jouiez dans aucune partie... Quel dommage !")

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiant joueur")
        return

    player_games = common.get_player_games_playing_in(player_id)
    if player_games is None:
        alert("Erreur chargement liste parties joueés")
        return

    # little optim : we pass the state so front will only request games in that state
    games_dict = common.get_games_data(state)
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return

    # if state is current (arrival) we add the awaiting games
    if state == 1:

        state2 = 0
        games_dict2 = common.get_games_data(state2)
        if games_dict2 is None:
            alert("Erreur chargement dictionnaire parties (2)")
            return

        # join both dicts
        games_dict.update(games_dict2)

    dict_submitted_data = get_all_player_games_roles_submitted_orders()
    if not dict_submitted_data:
        alert("Erreur chargement des soumissions dans les parties")
        return

    dict_voted_data = get_all_player_ongoing_votes()
    if not dict_voted_data:
        alert("Erreur chargement des votes dans les parties")
        return

    dict_time_stamp_last_declarations = date_last_declarations()
    # may be empty

    dict_time_stamp_last_messages = date_last_messages()
    # may be empty

    dict_time_stamp_last_visits_declarations = date_last_visit_load_all_games(config.DECLARATIONS_TYPE)
    if dict_role_id and not dict_time_stamp_last_visits_declarations:
        alert("Erreur chargement dates visites dernières declarations des parties")
        return

    dict_time_stamp_last_visits_messages = date_last_visit_load_all_games(config.MESSAGES_TYPE)
    if dict_role_id and not dict_time_stamp_last_visits_messages:
        alert("Erreur chargement dates visites derniers messages des parties")
        return

    games_id_player = {int(n) for n in player_games.keys()}

    # need a default value
    suffering_games = []

    # we check suffering games once a day
    day_notified = 0
    if 'DATE_SUFFERING_NOTIFIED' in storage:
        day_notified = int(storage['DATE_SUFFERING_NOTIFIED'])
    if day_now > day_notified:
        suffering_games = get_suffering_games(games_dict, games_id_player, dict_role_id)
        if suffering_games:
            alert(f"Il faut démarrer la(les) partie(s) en attente {' '.join(suffering_games)} qui est(sont) complète(s) !")
            storage['DATE_SUFFERING_NOTIFIED'] = str(day_now)

    time_stamp_now = time()

    # button for switching mode (display)
    if 'GAME_SHOW_MODE' not in storage:
        storage['GAME_SHOW_MODE'] = 'complete'
    if storage['GAME_SHOW_MODE'] == 'complete':
        button = html.BUTTON("Mode restreint (affiche moins de colonnes)", Class='btn-inside')
    else:
        button = html.BUTTON("Mode complet (affiche toutes les colonnes)", Class='btn-inside')
    button.bind("click", change_show_mode_callback)
    MY_SUB_PANEL <= button

    # separator
    MY_SUB_PANEL <= " "

    # button for switching mode
    if 'GAME_ACCESS_MODE' not in storage:
        storage['GAME_ACCESS_MODE'] = 'button'
    if storage['GAME_ACCESS_MODE'] == 'button':
        button = html.BUTTON("Mode liens externes (plus lent mais conserve cette page)", Class='btn-inside')
    else:
        button = html.BUTTON("Mode boutons (plus rapide mais remplace cette page)", Class='btn-inside')
    button.bind("click", change_button_mode_callback)
    MY_SUB_PANEL <= button

    # separator
    MY_SUB_PANEL <= " "

    # button for switching mode (action)
    if 'ACTION_COLUMN_MODE' not in storage:
        storage['ACTION_COLUMN_MODE'] = 'not_displayed'
    if storage['ACTION_COLUMN_MODE'] == 'not_displayed':
        button = html.BUTTON("Mode avec les colonnes d'action (éditer+arrêter/démarrer)", Class='btn-inside')
    else:
        button = html.BUTTON("Mode sans les colonnes d'action (éditer+arrêter/démarrer)", Class='btn-inside')
    button.bind("click", change_action_mode_callback)
    MY_SUB_PANEL <= button

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    games_table = html.TABLE()

    # the display order
    fields = ['name', 'go_game', 'deadline', 'current_advancement', 'role_played', 'all_orders_submitted', 'all_agreed', 'orders_submitted', 'agreed', 'votes', 'new_declarations', 'new_messages', 'variant', 'used_for_elo', 'nopress_current', 'nomessage_current', 'game_type']

    if storage['GAME_SHOW_MODE'] == 'reduced':
        fields.remove('all_orders_submitted')
        fields.remove('all_agreed')
        fields.remove('votes')
        fields.remove('used_for_elo')
        fields.remove('nopress_current')
        fields.remove('nomessage_current')

    if storage['ACTION_COLUMN_MODE'] == 'displayed':
        fields.extend(['edit', 'startstop'])

    # header
    thead = html.THEAD()
    for field in fields:

        content = {'name': 'nom', 'go_game': 'aller dans la partie', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'orders_submitted': 'mes ordres', 'agreed': 'mon accord', 'all_orders_submitted': 'ordres de tous', 'all_agreed': 'accords de tous', 'votes': 'votes', 'new_declarations': 'déclarations', 'new_messages': 'messages', 'variant': 'variante', 'used_for_elo': 'elo', 'nopress_current': 'déclarations', 'nomessage_current': 'négociations', 'game_type': 'type de partie', 'edit': 'éditer', 'startstop': 'arrêter/démarrer'}[field]

        legend = {'name': "Le nom de la partie", 'go_game': "Un bouton aller se promener dans la partie", 'deadline': "Valeur temporelle et vision colorée de la date limite", 'current_advancement': "La saison qui est maintenant à jouer dans la partie", 'role_played': "Le rôle que vous jouez dans la partie", 'orders_submitted': "Le status de vos ordres", 'agreed': "Le statut de votre accord pour la résolution", 'all_orders_submitted': "Le statut global des ordres de tous les joueurs", 'all_agreed': "Le statut global des accords de tous les joueurs pour la résolution ('ma' pour 'maintenant' et 'dl' pour 'à la date limite')", 'votes': "Le nombrte de votes exprimés pour arrêter la partie", 'new_declarations': "Existe-t-il une presse (déclaration) non lue pour vous dans la partie", 'new_messages': "Existe-t-il un message de négociation non lu pour vous dans la partie", 'variant': "La variante de la partie", 'used_for_elo': "Est-ce que la partie compte pour le classement E.L.O ?", 'nopress_current': "Est-ce que les messages publics (déclarations) sont autorisés entre les joueurs actuellement", 'nomessage_current': "Est-ce que les messages privés (négociations) sont autorisés pour les joueurs actuellement", 'game_type': "Type de partie pour la communication en jeu", 'edit': "Pour éditer les paramètres de la partie", 'startstop': "Pour arrêter ou démarrer la partie"}[field]

        field = html.DIV(content, title=legend)
        col = html.TD(field)
        thead <= col

    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'deadline', 'current_advancement', 'role_played', 'variant', 'used_for_elo', 'nopress_current', 'nomessage_current', 'game_type']:

            if field == 'name':

                # button for sorting by creation date
                button = html.BUTTON("&lt;Date de création&gt;", Class='btn-inside')
                button.bind("click", lambda e, f='creation': sort_by_callback(e, f))
                buttons <= button

                # separator
                buttons <= " "

                # button for sorting by name
                button = html.BUTTON("&lt;Nom&gt;", Class='btn-inside')
                button.bind("click", lambda e, f='name': sort_by_callback(e, f))
                buttons <= button

            else:

                button = html.BUTTON("<>", Class='btn-inside')
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button
        col = html.TD(buttons)
        row <= col
    games_table <= row

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    # default
    if 'SORT_BY_MYGAMES' not in storage:
        storage['SORT_BY_MYGAMES'] = 'creation'
    if 'REVERSE_NEEDED_MYGAMES' not in storage:
        storage['REVERSE_NEEDED_MYGAMES'] = str(False)

    sort_by = storage['SORT_BY_MYGAMES']
    reverse_needed = bool(storage['REVERSE_NEEDED_MYGAMES'] == 'True')

    gameover_table = {int(game_id_str): data['soloed'] or data['finished'] for game_id_str, data in games_dict.items()}

    # conversion
    game_type_conv = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}

    if sort_by == 'creation':
        def key_function(g): return int(g[0])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'name':
        def key_function(g): return g[1]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'variant':
        def key_function(g): return g[1]['variant']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'used_for_elo':
        def key_function(g): return int(g[1]['used_for_elo'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_current':
        def key_function(g): return int(g[1]['nopress_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_current':
        def key_function(g): return int(g[1]['nomessage_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'game_type':
        def key_function(g): return int(g[1]['game_type'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'role_played':
        def key_function(g): return int(dict_role_id.get(g[0], -1))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'deadline':
        def key_function(g): return int(gameover_table[int(g[0])]), int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    startable_game_present = False

    games_list = []

    for game_id_str, data in sorted(games_dict.items(), key=key_function, reverse=reverse_needed):

        # can happen because we added awaiting games
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

        # add to game list
        game_name = data['name']
        games_list.append(game_name)

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
        data['votes'] = None
        data['new_declarations'] = None
        data['new_messages'] = None
        data['edit'] = None
        data['startstop'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None

            if field == 'name':

                value = game_name

                # highlite free available position
                if game_name in suffering_games:
                    colour = config.NEED_START

            if field == 'go_game':

                if storage['GAME_ACCESS_MODE'] == 'button':

                    form = html.FORM()
                    input_jump_game = html.INPUT(type="image", src="./images/play.png", title="Cliquer pour aller dans la partie", Class='btn-inside')
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=None: select_game_callback(e, gn, gds, a))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png", title="Cliquer pour aller dans la partie")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'deadline':

                deadline_loaded = value
                value = ""
                explanation = ""

                # game over
                if gameover_table[game_id]:

                    if data['soloed']:
                        stats = "(solo)"
                        colour = config.SOLOED_COLOUR
                    elif data['finished']:
                        stats = "(terminée)"
                        colour = config.FINISHED_COLOUR

                    # keep value only for game master
                    if role_id is None or role_id != 0:
                        explanation = "Pas de date limite : la partie est terminée parce qu'arrivée à échéance"
                    else:
                        explanation = "La date indiquée n'est pas une date limite, mais plutôt une date à laquelle il faudra agir sur cette partie que vous arbitrez"

                elif int(data['current_state']) == 1:

                    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                    datetime_deadline_loaded_str = mydatetime.strftime2(*datetime_deadline_loaded)
                    stats = datetime_deadline_loaded_str

                    if data['fast']:
                        factor = 60
                    else:
                        factor = 60 * 60

                    # we are after everything !
                    if time_stamp_now > deadline_loaded + factor * 24 * config.CRITICAL_DELAY_DAY:
                        colour = config.CRITICAL_COLOUR
                        explanation = "La date limite est fortement dépassée"
                    # we are after deadline + grace
                    elif time_stamp_now > deadline_loaded + factor * data['grace_duration']:
                        colour = config.PASSED_GRACE_COLOUR
                        explanation = "La date limite est dépassée"
                    # we are after deadline + slight
                    elif time_stamp_now > deadline_loaded + config.SLIGHT_DELAY_SEC:
                        colour = config.PASSED_DEADLINE_COLOUR
                        explanation = "La date limite est légèrement dépassée"
                    # we are slightly after deadline
                    elif time_stamp_now > deadline_loaded:
                        colour = config.SLIGHTLY_PASSED_DEADLINE_COLOUR
                        explanation = "La date limite est tout juste dépassée"
                    # deadline is today
                    elif time_stamp_now > deadline_loaded - config.APPROACH_DELAY_SEC:
                        colour = config.APPROACHING_DEADLINE_COLOUR
                        explanation = "La date limite est bientôt"

                    value = html.DIV(stats, title=explanation)

            if field == 'current_advancement':
                advancement_loaded = value
                nb_max_cycles_to_play = data['nb_max_cycles_to_play']
                value = common.get_full_season(advancement_loaded, variant_data, nb_max_cycles_to_play, False)

            if field == 'role_played':
                value = ""
                if role_id is None:
                    role_icon_img = html.IMG(src="./images/assigned.png", title="Affecté à la partie")
                else:
                    role = variant_data.roles[role_id]
                    role_name = variant_data.role_name_table[role]
                    role_icon_img = common.display_flag(variant_name_loaded, interface_chosen, role_id, role_name)
                value = role_icon_img

            if field == 'all_orders_submitted':
                value = "-"
                if not gameover_table[game_id]:
                    if role_id is not None:
                        if not data['anonymous'] or role_id == 0:
                            submitted_roles_list = submitted_data['submitted']
                            nb_submitted = len(submitted_roles_list)
                            needed_roles_list = submitted_data['needed']
                            nb_needed = len(needed_roles_list)
                            stats = f"{nb_submitted}/{nb_needed}"
                            value = html.DIV(stats, title="Combien de jeux d'ordres soumis / combien nécessaires")
                            if nb_submitted >= nb_needed:
                                # we have all orders : green
                                colour = config.ALL_ORDERS_IN_COLOUR

            if field == 'all_agreed':
                value = "-"
                if not gameover_table[game_id]:
                    if role_id is not None:
                        if not data['anonymous'] or role_id == 0:
                            agreed_now_roles_list = submitted_data['agreed_now']
                            nb_agreed_now = len(agreed_now_roles_list)
                            agreed_after_roles_list = submitted_data['agreed_after']
                            nb_agreed_after = len(agreed_after_roles_list)
                            stats = f"{nb_agreed_now} ma. {nb_agreed_after} dl"
                            value = html.DIV(stats, title="Abbréviations : ma : les accords pour résoudre maintenant, dl : les accords pour résoudre à la date limite")

            if field == 'orders_submitted':
                value = "-"
                if not gameover_table[game_id]:
                    if role_id is not None:
                        if role_id != 0:
                            submitted_roles_list = submitted_data['submitted']
                            needed_roles_list = submitted_data['needed']
                            if role_id in submitted_roles_list:
                                flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                                value = flag
                            elif role_id in needed_roles_list:
                                flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
                                value = flag

            if field == 'agreed':
                value = "-"
                if not gameover_table[game_id]:
                    if role_id is not None:
                        if role_id != 0:
                            submitted_roles_list = submitted_data['submitted']
                            agreed_now_roles_list = submitted_data['agreed_now']
                            agreed_after_roles_list = submitted_data['agreed_after']
                            if role_id in agreed_now_roles_list:
                                flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre maintenant")
                                value = flag
                            elif role_id in agreed_after_roles_list:
                                flag = html.IMG(src="./images/agreed_after.jpg", title="D'accord pour résoudre mais à la date limite")
                                value = flag
                            elif role_id in needed_roles_list:
                                flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")
                                value = flag

            if field == 'votes':
                value = ""
                if str(game_id) in dict_voted_data['dict_voted'] and dict_voted_data['dict_voted'][str(game_id)]:
                    stats = dict_voted_data['dict_voted'][str(game_id)]
                    value = html.DIV(stats, title="Compte les votes exprimés sur le vote d'arrêt de la partie (qu'ils soient pour ou contre)")

            if field == 'new_declarations':
                value = ""
                if role_id is not None:
                    if str(game_id) in dict_time_stamp_last_declarations and dict_time_stamp_last_declarations[str(game_id)] > dict_time_stamp_last_visits_declarations[str(game_id)]:

                        arrival = "declarations"
                        if storage['GAME_ACCESS_MODE'] == 'button':
                            form = html.FORM()
                            input_jump_game = html.INPUT(type="image", src="./images/press_published.jpg", title="Cliquer pour aller voir les nouvelles presses", Class='btn-inside')
                            input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=arrival: select_game_callback(e, gn, gds, a))
                            form <= input_jump_game
                            value = form
                        else:
                            img = html.IMG(src="./images/press_published.jpg", title="Cliquer pour aller voir les nouvelles presses")
                            link = html.A(href=f"?game={game_name}&arrival={arrival}", target="_blank")
                            link <= img
                            value = link

            if field == 'new_messages':
                value = ""
                if role_id is not None:
                    if str(game_id) in dict_time_stamp_last_messages and dict_time_stamp_last_messages[str(game_id)] > dict_time_stamp_last_visits_messages[str(game_id)]:

                        arrival = "messages"
                        if storage['GAME_ACCESS_MODE'] == 'button':
                            form = html.FORM()
                            input_jump_game = html.INPUT(type="image", src="./images/messages_received.jpg", title="Cliquer pour aller voir les nouveaux messages privés", Class='btn-inside')
                            input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=arrival: select_game_callback(e, gn, gds, a))
                            form <= input_jump_game
                            value = form
                        else:
                            img = html.IMG(src="./images/messages_received.jpg", title="Cliquer pour aller voir les nouveaux messages privés")
                            link = html.A(href=f"?game={game_name}&arrival={arrival}", target="_blank")
                            link <= img
                            value = link

            if field == 'used_for_elo':
                stats = "Oui" if value else "Non"
                value = html.DIV(stats, title="Indique si la partie compte pour le classement E.L.O. sur le site")

            if field == 'nopress_current':
                explanation = "Indique si les joueurs peuvent actuellement utiliser la messagerie publique"
                stats = "Non" if data['nopress_current'] else "Oui"
                value = html.DIV(stats, title=explanation)

            if field == 'nomessage_current':
                explanation = "Indique si les joueurs peuvent actuellement utiliser la messagerie privée"
                stats = "Non" if data['nomessage_current'] else "Oui"
                value = html.DIV(stats, title=explanation)

            if field == 'game_type':
                value = game_type_conv[value]

            if field == 'edit':
                value = ""
                if storage['ACTION_COLUMN_MODE'] == 'displayed':
                    if role_id == 0:
                        if storage['GAME_ACCESS_MODE'] == 'button':
                            form = html.FORM()
                            input_edit_game = html.INPUT(type="image", src="./images/edit_game.png", title="Pour éditer les paramètres de la partie", Class='btn-inside')
                            input_edit_game.bind("click", lambda e, g=game_name: edit_game_callback(e, g))
                            form <= input_edit_game
                            value = form
                        else:
                            img = html.IMG(src="./images/edit_game.png", title="Pour éditer les paramètres de la partie")
                            link = html.A(href=f"?edit_game={game_name}", target="_blank")
                            link <= img
                            value = link

            if field == 'startstop':
                value = ""
                if storage['ACTION_COLUMN_MODE'] == 'displayed':
                    if role_id == 0:
                        if state == 0:
                            form = html.FORM()
                            input_start_game = html.INPUT(type="image", src="./images/start_game.jpg", title="Cliquer pour démarrer la partie", Class='btn-inside')
                            input_start_game.bind("click", lambda e, g=game_name: start_game_callback(e, g))
                            form <= input_start_game
                            value = form
                            startable_game_present = True
                        if state == 1:
                            form = html.FORM()
                            input_stop_game = html.INPUT(type="image", src="./images/stop_game.png", title="Cliquer pour arrêter la partie", Class='btn-inside')
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

    # store the list of games
    storage['GAME_LIST'] = ' '.join(games_list)

    # get GMT date and time
    time_stamp_now = time()
    date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)

    MY_SUB_PANEL <= html.DIV(f"Pour information, date et heure actuellement sur votre horloge locale : {date_now_gmt_str}")
    MY_SUB_PANEL <= html.BR()

    # display shift with server
    delta_time_sec = int(storage['DELTA_TIME_SEC'])
    abs_delta_time_sec = abs(delta_time_sec)

    if abs_delta_time_sec > DELTA_WARNING_THRESHOLD_SEC:

        if delta_time_sec > 0:
            status = "en avance"
        else:
            status = "en retard"

        if abs_delta_time_sec > 60:
            abs_delta_time_sec //= 60
            unit = "minutes"
        else:
            unit = "secondes"

        # display
        MY_SUB_PANEL <= html.DIV(f"Attention ! Votre horloge locale est {status} de {abs_delta_time_sec} {unit} sur celle du serveur", Class='important')
        MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()
    if startable_game_present:
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.DIV("Si une partie n'a pas le bon nombre de joueurs, elle ne pourra pas être démarrée !", Class='important')
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time()
    elapsed = overall_time_after - overall_time_before

    number_games = len(games_list)
    stats = f"Temps de chargement de la page {elapsed:.2f} secs avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games:.2f} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')
    MY_SUB_PANEL <= html.BR()

    for other_state_name in config.STATE_CODE_TABLE:

        if other_state_name != state_name:

            input_change_state = html.INPUT(type="submit", value=other_state_name, Class='btn-inside')
            input_change_state.bind("click", lambda _, s=other_state_name: again(s))
            MY_SUB_PANEL <= input_change_state
            MY_SUB_PANEL <= "    "

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()
    input_my_delays = html.INPUT(type="submit", value="Consulter la liste de tous mes retards", Class='btn-inside')
    input_my_delays.bind("click", my_delays)
    MY_SUB_PANEL <= input_my_delays

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()
    input_my_dropouts = html.INPUT(type="submit", value="Consulter la liste de tous mes abandons", Class='btn-inside')
    input_my_dropouts.bind("click", my_dropouts)
    MY_SUB_PANEL <= input_my_dropouts


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    MY_SUB_PANEL.clear()
    my_games('en cours')
    panel_middle <= MY_SUB_PANEL
