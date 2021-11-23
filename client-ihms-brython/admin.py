""" admin """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time
import datetime

from browser import document, html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import tools
import login
import mapping
import geometry
import selection
import index  # circular import


OPTIONS = ['changer nouvelles', 'usurper', 'toutes les parties', 'dernières connexions', 'connexions manquées', 'rectifier la position', 'emails non confirmés', 'remplaçants', 'envoyer un mail', 'récupérer un téléphone']

LONG_DURATION_LIMIT_SEC = 1.0


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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_submitted_data


def get_last_logins():
    """ get_last_logins """

    logins_list = None

    def reply_callback(req):
        nonlocal logins_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des connexions : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des connexions : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        logins_list = req_result['login_list']

    json_dict = dict()

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/logins_list"

    # logins list : need token
    # note : since we access directly to the user server, we present the token in a slightly different way
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return logins_list


def get_last_failures():
    """ get_last_failures """

    failures_list = None

    def reply_callback(req):
        nonlocal failures_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des connexions manquées : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des connexions manquées : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        failures_list = req_result['failure_list']

    json_dict = dict()

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/failures_list"

    # failures_list list : need token
    # note : since we access directly to the user server, we present the token in a slightly different way
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return failures_list


def get_all_games():
    """ get_all_games """

    games_dict = None

    def reply_callback(req):
        nonlocal games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste de toutes les parties : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste de toutes les parties : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        games_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games"

    # getting player games playing in list : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return games_dict.keys()


def check_admin(pseudo):
    """ check_admin """

    # TODO improve this with real admin account
    if pseudo != "Palpatine":
        alert("Pas le bon compte (pas admin)")
        return False

    return True


def change_news():
    """ change_news """

    def change_news_callback(_):
        """ change_news_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du contenu des nouvelles : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du contenu des nouvelles : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Les nouvelles ont été changées : {messages}", remove_after=config.REMOVE_AFTER)

        news_content = input_news_content.value
        if not news_content:
            alert("Contenu nouvelles manquant")
            return

        json_dict = {
            'pseudo': pseudo,
            'content': news_content,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/news"

        # changing news : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        change_news()

    my_sub_panel <= html.H3("Editer les nouvelles")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    news_content_loaded = common.get_news_content()
    if news_content_loaded is None:
        return

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_news_content = html.LEGEND("nouvelles", title="Saisir le nouveau contenu de nouvelles")
    fieldset <= legend_news_content
    input_news_content = html.TEXTAREA(type="text", rows=20, cols=100)
    input_news_content <= news_content_loaded
    fieldset <= input_news_content
    form <= fieldset

    form <= html.BR()

    input_change_news_content = html.INPUT(type="submit", value="mettre à jour")
    input_change_news_content.bind("click", change_news_callback)
    form <= input_change_news_content
    form <= html.BR()

    my_sub_panel <= form


def usurp():
    """ usurp """

    def usurp_callback(_):
        """ usurp_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'usurpation : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'usurpation : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            storage['PSEUDO'] = usurped_user_name
            storage['JWT_TOKEN'] = req_result['AccessToken']
            time_stamp = time.time()
            storage['LOGIN_TIME'] = str(time_stamp)

            InfoDialog("OK", f"Vous usurpez maintenant : {usurped_user_name}", remove_after=config.REMOVE_AFTER)
            login.show_login()

        usurped_user_name = input_usurped.value
        if not usurped_user_name:
            alert("User name usurpé manquant")
            return

        json_dict = {
            'usurped_user_name': usurped_user_name,
        }

        host = config.SERVER_CONFIG['USER']['HOST']
        port = config.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/usurp"

        # usurping : need token
        # note : since we access directly to the user server, we present the token in a slightly different way
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    my_sub_panel <= html.H3("Usurper un inscrit")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    players_dict = common.get_players()
    if players_dict is None:
        return

    # all players can be usurped
    possible_usurped = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_usurped = html.LEGEND("Usurpé", title="Sélectionner le joueur à usurper")
    fieldset <= legend_usurped
    input_usurped = html.SELECT(type="select-one", value="")
    for usurped_pseudo in sorted(possible_usurped, key=lambda pu: pu.upper()):
        option = html.OPTION(usurped_pseudo)
        input_usurped <= option
    fieldset <= input_usurped
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="usurper")
    input_select_player.bind("click", usurp_callback)
    form <= input_select_player

    my_sub_panel <= form


def all_games(state_name):
    """all_games """

    def select_game_callback(_, game):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    overall_time_before = time.time()

    my_sub_panel.clear()

    # title
    title = html.H3(f"Parties dans l'état: {state_name}")
    my_sub_panel <= title

    state = config.STATE_CODE_TABLE[state_name]

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiants des joueurs")
        return

    player_games = get_all_games()
    if player_games is None:
        alert("Erreur chargement joueurs des parties")
        return

    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return

    # avoids a warning
    games_dict = dict(games_dict)

    # get the players (masters)
    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire des joueurs")
        return

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data()
    if allocations_data is None:
        alert("Erreur chargement allocations")
        return
    allocations_data = dict(allocations_data)
    masters_alloc = allocations_data['game_masters_dict']

    dict_submitted_data = get_all_games_roles_submitted_orders()
    if dict_submitted_data is None:
        alert("Erreur chargement des soumissions dans les parties")
        return
    dict_submitted_data = dict(dict_submitted_data)

    # fill table game -> master
    game_master_dict = dict()
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            game_master_dict[game] = master

    time_stamp_now = time.time()

    games_table = html.TABLE()

    fields = ['name', 'master', 'variant', 'deadline', 'current_advancement', 'all_orders_submitted', 'all_agreed', 'jump_here', 'go_away']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'master': 'arbitre', 'variant': 'variante', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'all_orders_submitted': 'ordres', 'all_agreed': 'accords', 'jump_here': 'partie', 'go_away': 'partie (nouvel onglet)'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    # for optimization
    variant_data_memoize_table = dict()
    parameters_read_memoize_table = dict()
    variant_content_memoize_table = dict()

    number_games = 0
    for game_id_str, data in sorted(games_dict.items(), key=lambda g: int(g[0])):

        if data['current_state'] != state:
            continue

        number_games += 1

        game_id = int(game_id_str)

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        if variant_name_loaded not in variant_content_memoize_table:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                return
            variant_content_memoize_table[variant_name_loaded] = variant_content_loaded
        else:
            variant_content_loaded = variant_content_memoize_table[variant_name_loaded]

        # selected display (user choice)
        display_chosen = tools.get_display_from_variant(variant_name_loaded)

        # parameters

        if (variant_name_loaded, display_chosen) in parameters_read_memoize_table:
            parameters_read = parameters_read_memoize_table[(variant_name_loaded, display_chosen)]
        else:
            parameters_read = common.read_parameters(variant_name_loaded, display_chosen)
            parameters_read_memoize_table[(variant_name_loaded, display_chosen)] = parameters_read

        # build variant data

        variant_name_loaded_str = str(variant_name_loaded)
        variant_content_loaded_str = str(variant_content_loaded)
        parameters_read_str = str(parameters_read)
        if (variant_name_loaded_str, variant_content_loaded_str, parameters_read_str) not in variant_data_memoize_table:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            variant_data_memoize_table[(variant_name_loaded_str, variant_content_loaded_str, parameters_read_str)] = variant_data
        else:
            variant_data = variant_data_memoize_table[(variant_name_loaded_str, variant_content_loaded_str, parameters_read_str)]

        submitted_data = dict()
        submitted_data['needed'] = dict_submitted_data['dict_needed'][str(game_id)]
        submitted_data['submitted'] = dict_submitted_data['dict_submitted'][str(game_id)]
        submitted_data['agreed'] = dict_submitted_data['dict_agreed'][str(game_id)]

        data['master'] = None
        data['all_orders_submitted'] = None
        data['all_agreed'] = None
        data['jump_here'] = None
        data['go_away'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

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

            if field == 'all_orders_submitted':
                submitted_roles_list = submitted_data['submitted']
                nb_submitted = len(submitted_roles_list)
                needed_roles_list = submitted_data['needed']
                nb_needed = len(needed_roles_list)
                value = f"{nb_submitted}/{nb_needed}"
                if nb_submitted >= nb_needed:
                    # we have all orders : green
                    colour = config.ALL_ORDERS_IN_COLOUR

            if field == 'all_agreed':
                agreed_roles_list = submitted_data['agreed']
                nb_agreed = len(agreed_roles_list)
                submitted_roles_list = submitted_data['submitted']
                nb_submitted = len(submitted_roles_list)
                value = f"{nb_agreed}/{nb_submitted}"
                if nb_agreed >= nb_submitted:
                    # we have all agreements : green
                    colour = config.ALL_AGREEMENTS_IN_COLOUR

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

    my_sub_panel <= games_table
    my_sub_panel <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
    special_info = html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}", Class='note')
    my_sub_panel <= special_info
    my_sub_panel <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed}"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    my_sub_panel <= html.DIV(stats, Class='load')
    my_sub_panel <= html.BR()

    for other_state_name in config.STATE_CODE_TABLE:

        if other_state_name != state_name:

            input_change_state = html.INPUT(type="submit", value=other_state_name)
            input_change_state.bind("click", lambda _, s=other_state_name: all_games(s))

            my_sub_panel <= input_change_state
            my_sub_panel <= html.BR()
            my_sub_panel <= html.BR()


def last_logins():
    """ logins """

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    my_sub_panel <= html.H3("Liste des dernières connexions")

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    logins_list = get_last_logins()

    logins_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'date']:
        col = html.TD(field)
        thead <= col
    logins_table <= thead

    for pseudo, date in sorted(logins_list, key=lambda l: l[1], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        date_now_gmt = datetime.datetime.fromtimestamp(date, datetime.timezone.utc)
        date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
        col = html.TD(date_now_gmt_str)
        row <= col

        logins_table <= row

    my_sub_panel <= logins_table


def last_failures():
    """ failures """

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    my_sub_panel <= html.H3("Liste des connexions manquées")

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    failures_list = get_last_failures()

    failures_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'date']:
        col = html.TD(field)
        thead <= col
    failures_table <= thead

    for pseudo, date in sorted(failures_list, key=lambda l: l[1], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        date_now_gmt = datetime.datetime.fromtimestamp(date, datetime.timezone.utc)
        date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
        col = html.TD(date_now_gmt_str)
        row <= col

        failures_table <= row

    my_sub_panel <= failures_table


def rectify():
    """rectify """

    stored_event = None
    down_click_time = None

    def submit_callback(_):
        """ submit_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission de rectification de position : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission de rectification de position : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez rectifié la position : {messages}", remove_after=config.REMOVE_AFTER)

        # units
        units_list_dict = position_data.save_json()
        units_list_dict_json = json.dumps(units_list_dict)

        # ownerships
        ownerships_list_dict = position_data.save_json2()
        ownerships_list_dict_json = json.dumps(ownerships_list_dict)

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'pseudo': pseudo,
            'units': units_list_dict_json,
            'ownerships': ownerships_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-positions/{game_id}"

        # submitting position (units ownerships) for rectification : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def callback_canvas_short_click(event):
        """ callback_canvas_short_click """

        # the aim is to give this variable a value
        selected_erase_ownership = None

        # where is the click
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # select unit
        selected_erase_ownership = position_data.closest_ownership(pos)

        # center must be selected
        if selected_erase_ownership is None:
            return

        # remove center
        position_data.remove_ownership(selected_erase_ownership)

        # update map
        callback_render(None)

    def callback_canvas_long_click(event):
        """
        called when there is a click down then a click up separated by more than 'LONG_DURATION_LIMIT_SEC' sec
        or when pressing 'x' in which case a None is passed
        """

        # the aim is to give this variable a value
        selected_erase_unit = None

        # where is the click
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # select unit (cannot be dislodged - issue - maybe later)
        selected_erase_unit = position_data.closest_unit(pos, None)

        # unit must be selected
        if selected_erase_unit is None:
            return

        # remove unit
        position_data.remove_unit(selected_erase_unit)

        # update map
        callback_render(None)

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

        callback_canvas_short_click(stored_event)
        return

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        variant_data.render(ctx)

        # put the position
        position_data.render(ctx)

        # put the legends at the end
        variant_data.render_legends(ctx)

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="rectifier la position")
        input_submit.bind("click", submit_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit

    # callbacks pour le glisser / deposer

    def mouseover(event):
        """Quand la souris passe sur l'objet déplaçable, changer le curseur."""
        event.target.style.cursor = "pointer"

    def dragstart(event):
        """Fonction appelée quand l'utilisateur commence à déplacer l'objet."""

        # associer une donnée au processus de glissement
        event.dataTransfer.setData("text", event.target.id)
        # permet à l'object d'être déplacé dans l'objet destination
        event.dataTransfer.effectAllowed = "move"

    def dragover(event):
        event.data.dropEffect = 'move'
        event.preventDefault()

    def drop(event):
        """Fonction attachée à la zone de destination.
        Elle définit ce qui se passe quand l'objet est déposé, c'est-à-dire
        quand l'utilisateur relâche la souris alors que l'objet est au-dessus de
        la zone.
        """

        # récupère les données stockées dans drag_start (l'id de l'objet déplacé)
        src_id = event.dataTransfer.getData("text")
        elt = document[src_id]

        # enlever la fonction associée à mouseover
        elt.unbind("mouseover")
        elt.style.cursor = "auto"
        event.preventDefault()

        if src_id in unit_info_table:

            # put unit there
            # get unit dragged
            (type_unit, role) = unit_info_table[src_id]

            # get zone
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
            selected_drop_zone = variant_data.closest_zone(pos)

            # get region
            selected_drop_region = selected_drop_zone.region

            # prevent putting armies in sea
            if type_unit is mapping.UnitTypeEnum.ARMY_UNIT and selected_drop_zone.region.region_type is mapping.RegionTypeEnum.SEA_REGION:
                type_unit = mapping.UnitTypeEnum.FLEET_UNIT

            # prevent putting fleets inland
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT and selected_drop_zone.region.region_type is mapping.RegionTypeEnum.LAND_REGION:
                type_unit = mapping.UnitTypeEnum.ARMY_UNIT

            if selected_drop_zone.coast_type is not None:
                # prevent putting army on specific coasts
                if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
                    type_unit = mapping.UnitTypeEnum.FLEET_UNIT
            else:
                # we are not on a specific cosat
                if len([z for z in variant_data.zones.values() if z.region == selected_drop_region]) > 1:
                    # prevent putting fleet on non specific coasts if exists
                    if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                        type_unit = mapping.UnitTypeEnum.ARMY_UNIT

            # create unit
            if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
                new_unit = mapping.Army(position_data, role, selected_drop_zone, None)
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                new_unit = mapping.Fleet(position_data, role, selected_drop_zone, None)

            # remove previous occupant if applicable
            if selected_drop_region in position_data.occupant_table:
                previous_unit = position_data.occupant_table[selected_drop_region]
                position_data.remove_unit(previous_unit)

            # add to position
            position_data.add_unit(new_unit)

        if src_id in ownership_info_table:

            # put ownership there
            # get ownership dragged
            (role, ) = ownership_info_table[src_id]

            # get center
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
            selected_drop_center = variant_data.closest_center(pos)

            # create ownership
            new_ownership = mapping.Ownership(position_data, role, selected_drop_center)

            # remove previous ownership if applicable
            if selected_drop_center in position_data.owner_table:
                previous_ownership = position_data.owner_table[selected_drop_center]
                position_data.remove_ownership(previous_ownership)

            # add to position
            position_data.add_ownership(new_ownership)

        # refresh
        callback_render(ctx)

    # starts here

    my_sub_panel <= html.H3("Rectifier une position")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # selected display (user choice)
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    game_id = common.get_game_id(game)
    if game_id is None:
        return

    # get the position from server
    position_loaded = common.game_position_reload(game_id)
    if not position_loaded:
        return

    # digest the position
    position_data = mapping.Position(position_loaded, variant_data)

    # finds data about the dragged unit
    unit_info_table = dict()

    # finds data about the dragged ownership
    ownership_info_table = dict()

    reserve_table = html.TABLE()

    num = 1
    for role in variant_data.roles.values():

        # ignore GM
        if role.identifier == 0:
            continue

        row = html.TR()

        # country name
        col = html.TD()
        col <= html.B(variant_data.name_table[role])
        row <= col

        for type_unit in mapping.UnitTypeEnum:

            col = html.TD()

            if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
                draggable_unit = mapping.Army(position_data, role, None, None)
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                draggable_unit = mapping.Fleet(position_data, role, None, None)

            identifier = f"unit_{num}"
            unit_canvas = html.CANVAS(id=identifier, width=32, height=32, alt="Draguez moi!")
            unit_info_table[identifier] = (type_unit, role)
            num += 1

            unit_canvas.draggable = True
            unit_canvas.bind("mouseover", mouseover)
            unit_canvas.bind("dragstart", dragstart)

            ctx = unit_canvas.getContext("2d")
            draggable_unit.render(ctx)

            col <= unit_canvas
            row <= col

        col = html.TD()

        draggable_ownership = mapping.Ownership(position_data, role, None)

        identifier = f"center_{num}"
        ownership_canvas = html.CANVAS(id=identifier, width=32, height=32, alt="Draguez moi!")
        ownership_info_table[identifier] = (role, )
        num += 1

        ownership_canvas.draggable = True
        ownership_canvas.bind("mouseover", mouseover)
        ownership_canvas.bind("dragstart", dragstart)

        ctx = ownership_canvas.getContext("2d")
        draggable_ownership.render(ctx)

        col <= ownership_canvas
        row <= col

        reserve_table <= row

    display_very_left = html.DIV(id='display_very_left')
    display_very_left.attrs['style'] = 'display: table-cell; width=40px; vertical-align: top; table-layout: fixed;'

    display_very_left <= reserve_table

    display_very_left <= html.BR()

    display_very_left <= html.DIV("Glissez/déposez ces unités ou ces centres sur la carte", Class='instruction')

    map_size = variant_data.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # dragging related events
    canvas.bind('dragover', dragover)
    canvas.bind("drop", drop)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(variant_name_loaded, display_chosen)
    img.bind('load', callback_render)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    legend_select_unit = html.DIV("Clic-long sur une unité pour l'effacer, clic-court sur une possession pour l'effacer", Class='instruction')
    buttons_right <= legend_select_unit

    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_very_left
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= my_sub_panel2


def show_non_confirmed_data():
    """ show_non_confirmed_data """

    my_sub_panel <= html.H3("Liste des inscrits non confirmés")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    players_dict = common.get_players_data()

    if not players_dict:
        return

    players_table = html.TABLE()

    # TODO : make it possible to sort etc...
    fields = ['pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    for data in sorted(players_dict.values(), key=lambda p: p['pseudo'].upper()):

        if data['email_confirmed']:
            continue

        row = html.TR()
        for field in fields:
            value = data[field]

            col = html.TD(value)
            row <= col

        players_table <= row

    my_sub_panel <= players_table


def show_replacement_data():
    """ show_replacement_data """

    my_sub_panel <= html.H3("Liste des candidats au remplacement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    players_dict = common.get_players_data()

    if not players_dict:
        return

    players_table = html.TABLE()

    # TODO : make it possible to sort etc...
    fields = ['pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    for data in sorted(players_dict.values(), key=lambda p: p['pseudo'].upper()):

        if not data['replace']:
            continue

        row = html.TR()
        for field in fields:
            value = data[field]

            col = html.TD(value)
            row <= col

        players_table <= row

    my_sub_panel <= players_table


def sendmail():
    """ sendmail """

    def sendmail_callback(_):
        """ sendmail_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", f"Message émis vers : {addressed_user_name}", remove_after=config.REMOVE_AFTER)

        addressed_user_name = input_addressed.value
        if not addressed_user_name:
            alert("User name destinataire manquant")
            return

        subject = "Message de la part de l'administrateur du site https://diplomania-gen.fr (AFJD)"

        if not input_message.value:
            alert("Contenu du message vide")
            return

        body = input_message.value

        addressed_id = players_dict[addressed_user_name]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': pseudo,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        sendmail()

    my_sub_panel <= html.H3("Envoyer un e-mail")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    players_dict = common.get_players()
    if players_dict is None:
        return

    # clears a warnng
    players_dict = dict(players_dict)

    # all players can be usurped
    possible_addressed = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_addressee = html.LEGEND("Destinataire", title="Sélectionner le joueur à contacter par email")
    fieldset <= legend_addressee
    input_addressed = html.SELECT(type="select-one", value="")
    for addressee_pseudo in sorted(possible_addressed, key=lambda pu: pu.upper()):
        option = html.OPTION(addressee_pseudo)
        input_addressed <= option
    fieldset <= input_addressed
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_message = html.LEGEND("Votre message", title="Qu'avez vous à lui dire ?")
    fieldset <= legend_message
    input_message = html.TEXTAREA(type="text", rows=5, cols=80)
    fieldset <= input_message
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="contacter")
    input_select_player.bind("click", sendmail_callback)
    form <= input_select_player

    my_sub_panel <= form


def get_phone_number():
    """ get_phone_number """

    def get_phone_number_callback(_):
        """ get_phone_number_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de numéro de téléphone : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de numéro de téléphone : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            telephone = req_result['telephone']
            if telephone:
                alert(f"Son numéro est '{telephone}'")
            else:
                alert("Pas de numéro entré !")

        contact_user_name = input_contact.value
        if not contact_user_name:
            alert("User name à contacter manquant")
            return

        json_dict = dict()

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-telephone/{contact_user_name}"

        # getting private phone number : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        my_sub_panel.clear()
        get_phone_number()

    my_sub_panel <= html.H3("Un numéro de téléphone")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        return

    players_dict = common.get_players()
    if players_dict is None:
        return

    # clears a warnng
    players_dict = dict(players_dict)

    # all players can be usurped
    possible_contacts = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_contact = html.LEGEND("Contact", title="Sélectionner le joueur à contacter par téléphone")
    fieldset <= legend_contact
    input_contact = html.SELECT(type="select-one", value="")
    for contact_pseudo in sorted(possible_contacts, key=lambda pu: pu.upper()):
        option = html.OPTION(contact_pseudo)
        input_contact <= option
    fieldset <= input_contact
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="récupérer son numéro de téléphone")
    input_select_player.bind("click", get_phone_number_callback)
    form <= input_select_player

    my_sub_panel <= form


my_panel = html.DIV()
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="admin")
my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'changer nouvelles':
        change_news()
    if item_name == 'usurper':
        usurp()
    if item_name == 'toutes les parties':
        all_games('en cours')
    if item_name == 'dernières connexions':
        last_logins()
    if item_name == 'connexions manquées':
        last_failures()
    if item_name == 'rectifier la position':
        rectify()
    if item_name == 'emails non confirmés':
        show_non_confirmed_data()
    if item_name == 'remplaçants':
        show_replacement_data()
    if item_name == 'envoyer un mail':
        sendmail()
    if item_name == 'récupérer un téléphone':
        get_phone_number()

    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


# starts here


def render(panel_middle):
    """ render """

    # always back to top
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

    load_option(None, item_name_selected)
    panel_middle <= my_panel
