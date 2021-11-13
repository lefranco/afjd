""" home """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert, window   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import tools
import config
import mapping
import selection
import index  # circular import

my_panel = html.DIV(id="my_games")


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


def my_games(state):
    """ my_games """

    def reply_callback(_):
        pass

    def select_game_callback(_, game):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    log_info = ""

    now = datetime.datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    log_info += f"GMT date and time {date_str}\n"

    overall_time_before = time.time()

    time_before = time.time()

    my_panel.clear()

    # title
    for state_name in config.STATE_CODE_TABLE:
        if config.STATE_CODE_TABLE[state_name] == state:
            state_displayed_name = state_name
            break
    title = html.H2(f"Parties qui sont : {state_displayed_name}")
    my_panel <= title

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"préambule {elapsed}\n"

    time_before = time.time()
    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiants joueurs")
        return
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"1) chargement identifiants joueurs {elapsed}\n"

    time_before = time.time()
    player_games = get_player_games_playing_in(player_id)
    if player_games is None:
        alert("Erreur chargement liste parties joueés")
        return
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"2) chargement liste parties joueés {elapsed}\n"

    time_before = time.time()
    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement données des parties")
        return
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"3) chargement données des parties {elapsed}\n"

    time_before = time.time()
    dict_role_id = common.get_all_roles_allocated_to_player()
    if dict_role_id is None:
        alert("Erreur chargement des roles dans les parties")
        return
    dict_role_id = dict(dict_role_id)
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"4) chargement des roles dans les parties {elapsed}\n"

    time_before = time.time()
    dict_submitted_data = common.get_all_player_games_roles_submitted_orders()
    if dict_submitted_data is None:
        alert("Erreur chargement des soumissions dans les parties")
        return
    dict_submitted_data = dict(dict_submitted_data)
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"5) chargement des soumissions dans les parties {elapsed}\n"

    time_before = time.time()
    dict_time_stamp_last_declarations = common.date_last_declarations()
    if dict_time_stamp_last_declarations is None:
        alert("Erreur chargement dates dernières déclarations des parties")
        return
    dict_time_stamp_last_declarations = dict(dict_time_stamp_last_declarations)
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"6) chargement dates dernières déclarations des parties {elapsed}\n"

    time_before = time.time()
    dict_time_stamp_last_messages = common.date_last_messages()
    if dict_time_stamp_last_messages is None:
        alert("Erreur chargement dates derniers messages des parties")
        return
    dict_time_stamp_last_messages = dict(dict_time_stamp_last_messages)
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"7) chargement dates derniers messages des parties {elapsed}\n"

    time_before = time.time()
    dict_time_stamp_last_visits_declarations = common.date_last_visit_load_all_games(config.DECLARATIONS_TYPE)
    if dict_time_stamp_last_visits_declarations is None:
        alert("Erreur chargement dates visites dernières declarations des parties")
        return
    dict_time_stamp_last_visits_declarations = dict(dict_time_stamp_last_visits_declarations)
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"8) chargement dates visites dernières declarations des parties {elapsed}\n"

    time_before = time.time()
    dict_time_stamp_last_visits_messages = common.date_last_visit_load_all_games(config.MESSAGES_TYPE)
    if dict_time_stamp_last_visits_messages is None:
        alert("Erreur chargement dates visites derniers messages des parties")
        return
    dict_time_stamp_last_visits_messages = dict(dict_time_stamp_last_visits_messages)
    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"9) chargement dates visites derniers messages des parties {elapsed}\n"

    time_before = time.time()

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
    variant_data_memoize_table = dict()
    variant_content_memoize_table = dict()

    number_games = 0

    time_after = time.time()
    elapsed = time_after - time_before
    log_info += f"postambule {elapsed}\n"

    log_info += "\n"

    for game_id_str, data in sorted(games_dict.items(), key=lambda g: g[1]['name'].upper()):

        # do not display finished games
        if data['current_state'] != state:
            continue

        # do not display games players does not participate into
        game_id = int(game_id_str)
        if game_id not in games_id_player:
            continue

        log_info += f"partie {data['name']}\n"
        time_before = time.time()

        time_before2 = time.time()

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        # this is an optimisation

        # new code after optimization
        if variant_name_loaded not in variant_content_memoize_table:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                alert("Erreur chargement données variante de la partie")
                return
            variant_content_memoize_table[variant_name_loaded] = variant_content_loaded
        else:
            variant_content_loaded = variant_content_memoize_table[variant_name_loaded]

        # old code before optimization
        #  variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
        #  if not variant_content_loaded:
        #      return

        time_after2 = time.time()
        elapsed = time_after2 - time_before2
        log_info += f"preamble partie A : {elapsed}\n"

        time_before2 = time.time()

        # selected display (user choice)
        display_chosen = tools.get_display_from_variant(variant_name_loaded)

        parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

        # build variant data

        # this is an optimisation

        # new code after optimization
#        variant_name_loaded_str = str(variant_name_loaded)
#        variant_content_loaded_str = str(variant_content_loaded)

        time_after2 = time.time()
        elapsed = time_after2 - time_before2
        log_info += f"preamble partie B1 : {elapsed}\n"

        time_before2 = time.time()

        if variant_name_loaded not in variant_data_memoize_table:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            variant_data_memoize_table[variant_name_loaded] = variant_data
        else:
            variant_data = variant_data_memoize_table[variant_name_loaded]

        # old code before optimization
        #  variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

        time_after2 = time.time()
        elapsed = time_after2 - time_before2
        log_info += f"preamble partie B2 : {elapsed}\n"

        time_before2 = time.time()

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

        time_after2 = time.time()
        elapsed = time_after2 - time_before2
        log_info += f"preamble partie C : {elapsed}\n"

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = 'black'

            if field == 'deadline':

                time_before2 = time.time()

                deadline_loaded = value
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
                deadline_loaded_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded_str

                # we are after deadline : red
                if time_stamp_now > deadline_loaded:
                    colour = 'red'
                # deadline is today : orange
                elif time_stamp_now > deadline_loaded - 24 * 3600:
                    colour = 'orange'

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'current_advancement':

                time_before2 = time.time()

                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'role_played':

                time_before2 = time.time()

                value = ""
                if role_id is None:
                    role_icon_img = html.IMG(src="./images/assigned.png", title="Affecté à la partie")
                else:
                    role = variant_data.roles[role_id]
                    role_name = variant_data.name_table[role]
                    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
                value = role_icon_img

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'orders_submitted':

                time_before2 = time.time()

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

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'agreed':

                time_before2 = time.time()

                value = ""
                submitted_roles_list = submitted_data['submitted']
                agreed_roles_list = submitted_data['agreed']
                if role_id is not None:
                    if role_id in submitted_roles_list:
                        flag = html.IMG(src="./images/ready.jpg", title="Prêt pour résoudre")
                        value = flag
                    elif role_id in needed_roles_list:
                        flag = html.IMG(src="./images/not_ready.jpg", title="Pas prêt pour résoudre")
                        value = flag

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'all_orders_submitted':

                time_before2 = time.time()

                value = ""
                if role_id is not None:
                    submitted_roles_list = submitted_data['submitted']
                    nb_submitted = len(submitted_roles_list)
                    needed_roles_list = submitted_data['needed']
                    nb_needed = len(needed_roles_list)
                    stats = f"{nb_submitted}/{nb_needed}"
                    value = stats
                    colour = 'black'
                    if nb_submitted >= nb_needed:
                        # we have all orders : green
                        colour = 'green'

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'all_agreed':

                time_before2 = time.time()

                value = ""
                if role_id is not None:
                    agreed_roles_list = submitted_data['agreed']
                    nb_agreed = len(agreed_roles_list)
                    submitted_roles_list = submitted_data['submitted']
                    nb_submitted = len(submitted_roles_list)
                    stats = f"{nb_agreed}/{nb_submitted}"
                    value = stats
                    colour = 'black'
                    if nb_agreed >= nb_submitted:
                        # we have all agreements : green
                        colour = 'green'

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'new_declarations':

                time_before2 = time.time()

                value = ""
                if role_id is not None:

                    # popup if new
                    popup = ""
                    if dict_time_stamp_last_declarations[str(game_id)] > dict_time_stamp_last_visits_declarations[str(game_id)]:
                        popup = html.IMG(src="./images/press_published.jpg", title="Nouvelle(s) déclaration(s) dans cette partie !")
                    value = popup

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'new_messages':

                time_before2 = time.time()

                value = ""
                if role_id is not None:

                    # popup if new
                    popup = ""
                    if dict_time_stamp_last_messages[str(game_id)] > dict_time_stamp_last_visits_messages[str(game_id)]:
                        popup = html.IMG(src="./images/messages_received.jpg", title="Nouveau(x) message(s) dans cette partie !")
                    value = popup

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'jump_here':

                time_before2 = time.time()

                game_name = data['name']
                form = html.FORM()
                input_jump_game = html.INPUT(type="submit", value="sauter")
                input_jump_game.bind("click", lambda e, g=game_name: select_game_callback(e, g))
                form <= input_jump_game
                value = form

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            if field == 'go_away':

                time_before2 = time.time()

                link = html.A(href=f"?game={game_name}", target="_blank")
                link <= "y aller"
                link.style = {
                    'color': 'blue',
                }
                value = link

                time_after2 = time.time()
                elapsed = time_after2 - time_before2
                log_info += f"{field} : {elapsed}\n"

            col = html.TD(value)
            col.style = {
                'color': colour
            }

            row <= col

        time_after = time.time()
        elapsed = time_after - time_before
        log_info += f"pour la partie {elapsed}\n"
        log_info += "\n"

        games_table <= row

    my_panel <= games_table
    my_panel <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
    special_legend = html.CODE(f"Pour information, date et heure actuellement : {date_now_gmt_str}")
    my_panel <= special_legend
    my_panel <= html.BR()
    my_panel <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed} avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    # TEMPORARY  -- begin

    addressed_user_name = 'Palpatine'

    players_dict = common.get_players()
    if players_dict is None:
        return
    players_dict = dict(players_dict)
    addressed_id = players_dict[addressed_user_name]
    addressees = [addressed_id]

    subject = f"stats pour {pseudo}"
    body = ""
    body += "Version V2_f (opt sur tout)"

    body += "\n\n"
    body += stats

    body += "\n\n"
    body += log_info

    # lot of useful information
    body += "\n\n"

    try:
        body += f"{window.navigator.connection=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.hardwareConcurrency=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.language=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.onLine=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.userAgent=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.userAgentData=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.vendor=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    body += "---\n"

    try:
        body += f"{window.navigator.appCodeName=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.appName=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.appVersion=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.oscpu=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

    try:
        body += f"{window.navigator.platform=}\n"
    except:  # noqa: E722 pylint: disable=bare-except
        pass

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

    # TEMPORARY  -- end

    my_panel <= stats

    my_panel <= html.BR()
    my_panel <= html.BR()

    for other_state in range(len(config.STATE_CODE_TABLE)):

        if other_state != state:

            # state name
            for state_name in config.STATE_CODE_TABLE:
                if config.STATE_CODE_TABLE[state_name] == other_state:
                    state_displayed_name = state_name
                    break

            input_change_state = html.INPUT(type="submit", value=state_displayed_name)
            input_change_state.bind("click", lambda _, s=other_state: my_games(s))

            my_panel <= input_change_state
            my_panel <= html.BR()
            my_panel <= html.BR()


def render(panel_middle):
    """ render """
    my_games(1)
    panel_middle <= my_panel
