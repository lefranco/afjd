""" technical """

# pylint: disable=pointless-statement, expression-not-assigned

import time
import json

from browser import html, alert, document, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common
import mapping
import interface
import memoize
import play

import index  # circular import


# sandbox must stay first
OPTIONS = ['Sélectionner une partie', 'Aller dans la partie sélectionnée', 'Rejoindre une partie', 'Toutes les parties', 'Appariement', 'Parties sans arbitres',]


def information_about_games():
    """ information_about_games """

    information = html.DIV(Class='note')
    information <= "Pour connaître tous les paramètres de la partie, cliquez sur le bouton de la partie dans la colonne 'aller dans la partie'"
    return information


def get_recruiting_games():
    """ get_recruiting_games : returns empty list if error or no game"""

    recruiting_games_list = []

    def reply_callback(req):
        nonlocal recruiting_games_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des parties qui recrutent : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des parties qui recrutent : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        recruiting_games_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games-recruiting"

    # getting recruiting games list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return recruiting_games_list


def my_opportunities():
    """ my_opportunities """

    def create_account_callback(_):
        """ create_account_callback """

        # go to create account page
        index.load_option(None, 'Mon compte')

    def select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        common.info_dialog(f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page")
        show_game_selected()

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    def quit_and_select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ quit_and_select_game_callback : the second way of quitting a game : by a button """

        def quit_game(game_name, game_data_sel):

            def reply_callback(req):

                req_result = json.loads(req.text)
                if req.status != 200:
                    if 'message' in req_result:
                        alert(f"Erreur à la désinscription à la partie : {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à la désinscription à la partie : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    return

                messages = "<br>".join(req_result['msg'].split('\n'))
                common.info_dialog(f"Vous avez quitté la partie (en utilisant la page 'rejoindre') : {messages}", True)

            game_id = game_data_sel[game_name][0]

            json_dict = {
                'game_id': game_id,
                'player_pseudo': pseudo,
                'delete': 1
            }

            host = config.SERVER_CONFIG['GAME']['HOST']
            port = config.SERVER_CONFIG['GAME']['PORT']
            url = f"{host}:{port}/allocations"

            # adding allocation : need a token
            ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        ev.preventDefault()

        # action of putting myself in game
        quit_game(game_name, game_data_sel)

        # action of going to the game
        select_game_callback(ev, game_name, game_data_sel)

    def join_and_select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ join_and_select_game_callback : the second way of joining a game : by a button """

        def join_game(game_name, game_data_sel):

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
                common.info_dialog(f"Vous avez rejoint la partie (en utilisant la page 'rejoindre') : {messages}<br>Attention, c'est un réel engagement à ne pas prendre à la légère.<br>Un abandon pourrait compromettre votre inscription à de futures parties sur le site...", True)

            game_id = game_data_sel[game_name][0]

            json_dict = {
                'game_id': game_id,
                'player_pseudo': pseudo,
                'delete': 0
            }

            host = config.SERVER_CONFIG['GAME']['HOST']
            port = config.SERVER_CONFIG['GAME']['PORT']
            url = f"{host}:{port}/allocations"

            # adding allocation : need a token
            ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        ev.preventDefault()

        # action of putting myself in game
        join_game(game_name, game_data_sel)

        # action of going to the game
        select_game_callback(ev, game_name, game_data_sel)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_SUB_PANEL.clear()
        my_opportunities()

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by != storage['SORT_BY_OPPORTUNITIES']:
            storage['SORT_BY_OPPORTUNITIES'] = new_sort_by
            storage['REVERSE_NEEDED_OPPORTUNITIES'] = str(False)
        else:
            storage['REVERSE_NEEDED_OPPORTUNITIES'] = str(not bool(storage['REVERSE_NEEDED_OPPORTUNITIES'] == 'True'))

        MY_SUB_PANEL.clear()
        my_opportunities()

    overall_time_before = time.time()

    # declared by safety but could be not used
    pseudo = None
    player_id = None

    # fallback value
    player_games = {}

    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']

        player_id = common.get_player_id(pseudo)
        if player_id is None:
            alert("Erreur chargement identifiant joueur")
            return

        player_games = common.get_player_games_playing_in(player_id)
        if player_games is None:
            alert("Erreur chargement liste parties jouées")
            return

    recruiting_games_list = get_recruiting_games()
    # there can be no message (if no game of failed to load)

    recruiting_games_dict = {tr[0]: {'allocated': tr[1], 'capacity': tr[2]} for tr in recruiting_games_list}

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    games_dict_recruiting = {k: v for k, v in games_dict.items() if int(k) in recruiting_games_dict}

    # get the players
    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']

    # gather game to master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            game_master_dict[game] = master

    # Title
    MY_SUB_PANEL <= html.H2("Parties qui recrutent des joueurs")

    MY_SUB_PANEL <= information_about_games()
    MY_SUB_PANEL <= html.BR()

    # button for creating account
    if 'PSEUDO' not in storage:
        # shortcut to create account
        button = html.BUTTON("Je n'ai pas de compte, je veux le créer !", Class='btn-menu')
        button.bind("click", create_account_callback)
        MY_SUB_PANEL <= button
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()

    # button for switching mode
    if 'GAME_ACCESS_MODE' not in storage:
        storage['GAME_ACCESS_MODE'] = 'button'
    if storage['GAME_ACCESS_MODE'] == 'button':
        button = html.BUTTON("Basculer en mode liens externes (plus lent mais conserve cette page)", Class='btn-menu')
    else:
        button = html.BUTTON("Basculer en mode boutons (plus rapide mais remplace cette page)", Class='btn-menu')
    button.bind("click", change_button_mode_callback)
    MY_SUB_PANEL <= button
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    games_table = html.TABLE()

    fields = ['name', 'go_game', 'join', 'deadline', 'current_state', 'current_advancement', 'last_season', 'allocated', 'variant', 'used_for_elo', 'master', 'description', 'nopress_game', 'nomessage_game']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'go_game': 'aller dans la partie', 'join': 'rejoindre', 'deadline': 'date limite', 'current_state': 'état', 'current_advancement': 'saison à jouer', 'last_season': 'dernière saison', 'allocated': 'alloué(**)', 'variant': 'variante', 'used_for_elo': 'elo', 'master': 'arbitre', 'description': 'description', 'nopress_game': 'publics(*)', 'nomessage_game': 'privés(*)'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'master', 'deadline', 'current_state', 'current_advancement', 'last_season', 'allocated', 'variant', 'used_for_elo', 'nopress_game', 'nomessage_game']:

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

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0

    # default
    if 'SORT_BY_OPPORTUNITIES' not in storage:
        storage['SORT_BY_OPPORTUNITIES'] = 'creation'
    if 'REVERSE_NEEDED_OPPORTUNITIES' not in storage:
        storage['REVERSE_NEEDED_OPPORTUNITIES'] = str(False)

    sort_by = storage['SORT_BY_OPPORTUNITIES']
    reverse_needed = bool(storage['REVERSE_NEEDED_OPPORTUNITIES'] == 'True')

    if sort_by == 'creation':
        def key_function(g): return int(g[0])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'name':
        def key_function(g): return g[1]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'variant':
        def key_function(g): return g[1]['variant']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'used_for_elo':
        def key_function(g): return int(g[1]['used_for_elo'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'master':
        def key_function(g): return game_master_dict.get(g[1]['name'], '').upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_game':
        def key_function(g): return (int(g[1]['nopress_game']), int(g[1]['nopress_current']))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_game':
        def key_function(g): return (int(g[1]['nomessage_game']), int(g[1]['nomessage_current']))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'last_season':
        def key_function(g): return g[1]['nb_max_cycles_to_play']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'allocated':
        def key_function(g): return - (recruiting_games_dict[int(g[0])]['capacity'] - recruiting_games_dict[int(g[0])]['allocated'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    for game_id_str, data in sorted(games_dict_recruiting.items(), key=key_function, reverse=reverse_needed):

        # ignore finished (or distinguished) games
        if data['current_state'] in [2, 3]:
            continue

        number_games += 1

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        # this is an optimisation

        # new code after optimization
        if variant_name_loaded in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
            variant_content_loaded = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded]
        else:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                return
            memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded] = variant_content_loaded

        # selected interface (user choice)
        interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

        parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)

        # build variant data

        variant_name_loaded_str = str(variant_name_loaded)
        if (variant_name_loaded_str, interface_chosen) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
            variant_data = memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)]
        else:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)] = variant_data

        data['go_game'] = None
        data['master'] = None
        data['join'] = None
        data['allocated'] = None
        data['last_season'] = None

        # highlite ongoing games (replacement)
        field = 'current_state'
        value = data[field]
        if value == 1:
            colour = config.NEED_REPLACEMENT
        else:
            colour = None

        row = html.TR()
        for field in fields:

            value = data[field]
            game_name = data['name']

            if field == 'name':
                value = game_name

            if field == 'go_game':
                if storage['GAME_ACCESS_MODE'] == 'button':
                    form = html.FORM()
                    input_jump_game = html.INPUT(type="image", src="./images/play.png")
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'join':
                if player_id is None:
                    value = "Pas identifié"
                elif game_id_str in player_games:
                    game_name = data['name']
                    form = html.FORM()
                    input_quit_game = html.INPUT(type="image", src="./images/leave.png")
                    input_quit_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: quit_and_select_game_callback(e, gn, gds))
                    form <= input_quit_game
                    value = form
                else:
                    game_name = data['name']
                    form = html.FORM()
                    input_join_game = html.INPUT(type="image", src="./images/join.png")
                    input_join_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: join_and_select_game_callback(e, gn, gds))
                    form <= input_join_game
                    value = form

            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                datetime_deadline_loaded_str = mydatetime.strftime2(*datetime_deadline_loaded)
                value = datetime_deadline_loaded_str

            if field == 'current_state':
                state_loaded = value
                for possible_state_code, possible_state_desc in config.STATE_CODE_TABLE.items():
                    if possible_state_desc == state_loaded:
                        state_loaded = possible_state_code
                        break
                value = state_loaded

            if field == 'current_advancement':
                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.season_name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'last_season':
                value = data['nb_max_cycles_to_play']
                advancement_max = value * 5 - 1
                advancement_season, advancement_year = common.get_season(advancement_max, variant_data)
                advancement_season_readable = variant_data.season_name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'allocated':
                allocated = recruiting_games_dict[int(game_id_str)]['allocated']
                capacity = recruiting_games_dict[int(game_id_str)]['capacity']
                value = f"{allocated}/{capacity}"
                if allocated == capacity:
                    colour = config.ALL_ORDERS_IN_COLOUR

            if field == 'used_for_elo':
                value = "Oui" if value else "Non"

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

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

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        games_table <= row

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Les icônes suivants sont cliquables pour aller dans ou agir sur les parties :", Class='note')
    MY_SUB_PANEL <= html.IMG(src="./images/play.png", title="Pour aller dans la partie")
    MY_SUB_PANEL <= " "
    MY_SUB_PANEL <= html.IMG(src="./images/join.png", title="Pour se mettre dans la partie")
    MY_SUB_PANEL <= " "
    MY_SUB_PANEL <= html.IMG(src="./images/leave.png", title="Pour s'enlever de la partie")
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("(*) Messagerie possible sur la partie, si le paramètre applicable actuellement est différent (partie terminée) il est indiqué entre parenthèses", Class='note')
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("(**) On prend en compte l'arbitre dans le nombre de joueurs", Class='note')
    MY_SUB_PANEL <= html.BR()

    # get GMT date and time
    time_stamp_now = time.time()
    date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)

    special_legend = html.DIV(f"Pour information, date et heure actuellement sur votre horloge locale : {date_now_gmt_str}")
    MY_SUB_PANEL <= special_legend

    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed}"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')
    MY_SUB_PANEL <= html.BR()


def all_games(state_name):
    """all_games """

    def select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        common.info_dialog(f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page")
        show_game_selected()

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    def again(state_name):
        """ again """
        MY_SUB_PANEL.clear()
        all_games(state_name)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_SUB_PANEL.clear()
        all_games(state_name)

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by != storage['SORT_BY_HOME']:
            storage['SORT_BY_HOME'] = new_sort_by
            storage['REVERSE_NEEDED_HOME'] = str(False)
        else:
            storage['REVERSE_NEEDED_HOME'] = str(not bool(storage['REVERSE_NEEDED_HOME'] == 'True'))

        MY_SUB_PANEL.clear()
        all_games(state_name)

    overall_time_before = time.time()

    # title
    title = html.H3(f"Parties dans l'état: {state_name}")
    MY_SUB_PANEL <= title

    state = config.STATE_CODE_TABLE[state_name]

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the players (masters)
    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire des joueurs")
        return

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return
    masters_alloc = allocations_data['game_masters_dict']

    # fill table game -> master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            game_master_dict[game] = master

    time_stamp_now = time.time()

    # button for switching mode
    if 'GAME_ACCESS_MODE' not in storage:
        storage['GAME_ACCESS_MODE'] = 'button'
    if storage['GAME_ACCESS_MODE'] == 'button':
        button = html.BUTTON("Basculer en mode liens externes (plus lent mais conserve cette page)", Class='btn-menu')
    else:
        button = html.BUTTON("Basculer en mode boutons (plus rapide mais remplace cette page)", Class='btn-menu')
    button.bind("click", change_button_mode_callback)
    MY_SUB_PANEL <= button
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    games_table = html.TABLE()

    fields = ['name', 'go_game', 'id', 'deadline', 'current_advancement', 'variant', 'used_for_elo', 'master', 'nopress_game', 'nomessage_game', 'game_over']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'go_game': 'aller dans la partie', 'id': 'id', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'variant': 'variante', 'used_for_elo': 'elo', 'master': 'arbitre', 'nopress_game': 'publics(*)', 'nomessage_game': 'privés(*)', 'game_over': 'game over'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'deadline', 'current_advancement', 'variant', 'used_for_elo', 'master', 'nopress_game', 'nomessage_game']:

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

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0

    # default
    if 'SORT_BY_HOME' not in storage:
        storage['SORT_BY_HOME'] = 'creation'
    if 'REVERSE_NEEDED_HOME' not in storage:
        storage['REVERSE_NEEDED_HOME'] = str(False)

    sort_by = storage['SORT_BY_HOME']
    reverse_needed = bool(storage['REVERSE_NEEDED_HOME'] == 'True')

    if sort_by == 'creation':
        def key_function(g): return int(g[0])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'name':
        def key_function(g): return g[1]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'variant':
        def key_function(g): return g[1]['variant']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'used_for_elo':
        def key_function(g): return int(g[1]['used_for_elo'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'master':
        def key_function(g): return game_master_dict.get(g[1]['name'], '').upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_game':
        def key_function(g): return (int(g[1]['nopress_game']), int(g[1]['nopress_current']))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_game':
        def key_function(g): return (int(g[1]['nomessage_game']), int(g[1]['nomessage_current']))  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    for game_id_str, data in sorted(games_dict.items(), key=key_function, reverse=reverse_needed):

        if data['current_state'] != state:
            continue

        number_games += 1

        game_id = int(game_id_str)

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        if variant_name_loaded in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
            variant_content_loaded = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded]
        else:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                return
            memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded] = variant_content_loaded

        # selected interface (user choice)
        interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

        # parameters

        if (variant_name_loaded, interface_chosen) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
            parameters_read = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)]
        else:
            parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)
            memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)] = parameters_read

        # build variant data

        variant_name_loaded_str = str(variant_name_loaded)
        if (variant_name_loaded_str, interface_chosen) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
            variant_data = memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)]
        else:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)] = variant_data

        data['go_game'] = None
        data['id'] = None
        data['master'] = None
        data['game_over'] = None

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
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'id':
                value = game_id

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

            if field == 'used_for_elo':
                value = "Oui" if value else "Non"

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

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

            if field == 'game_over':
                value = ''
                if data['current_advancement'] % 5 == 4 and (data['current_advancement'] + 1) // 5 >= data['nb_max_cycles_to_play']:
                    flag = html.IMG(src="./images/game_over.png", title="Partie finie")
                    value = flag

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        games_table <= row

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Les icônes suivants sont cliquables pour aller dans ou agir sur les parties :", Class='note')
    MY_SUB_PANEL <= html.IMG(src="./images/play.png", title="Pour aller dans la partie")
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("(*) Messagerie possible sur la partie, si le paramètre applicable actuellement est différent (partie terminée) il est indiqué entre parenthèses", Class='note')
    MY_SUB_PANEL <= html.BR()

    # get GMT date and time
    time_stamp_now = time.time()
    date_now_gmt = mydatetime.fromtimestamp(time_stamp_now)
    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
    special_info = html.DIV(f"Pour information, date et heure actuellement sur votre horloge locale : {date_now_gmt_str}")
    MY_SUB_PANEL <= special_info
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed} avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')
    MY_SUB_PANEL <= html.BR()

    for other_state_name in config.STATE_CODE_TABLE:

        if other_state_name != state_name:

            input_change_state = html.INPUT(type="submit", value=other_state_name)
            input_change_state.bind("click", lambda _, s=other_state_name: again(s))
            MY_SUB_PANEL <= input_change_state
            MY_SUB_PANEL <= "    "


def select_game(selected_variant, selected_state):
    """ select_game """

    def select_variant_callback(ev, input_state):  # pylint: disable=invalid-name
        """ select_game_callback """

        nonlocal selected_variant

        ev.preventDefault()

        sel_variant = input_state.value
        selected_variant = sel_variant

        # back to where we started
        MY_SUB_PANEL.clear()
        select_game(selected_variant, selected_state)

    def select_state_callback(ev, input_state):  # pylint: disable=invalid-name
        """ select_state_callback """

        nonlocal selected_state

        ev.preventDefault()

        sel_state = input_state.value
        selected_state = config.STATE_CODE_TABLE[sel_state]

        # back to where we started
        MY_SUB_PANEL.clear()
        select_game(selected_variant, selected_state)

    def select_game_callback(ev, input_game, game_data_sel):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        game_name = input_game.value
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        common.info_dialog(f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page")
        show_game_selected()

        # back to where we started
        MY_SUB_PANEL.clear()
        select_game(selected_variant, selected_state)

    games_data = common.get_games_data()
    if not games_data:
        alert("Erreur chargement dictionnaire parties")
        return

    # variant selector
    # ----------------

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_variant = html.LEGEND("Sélection de la variante", title="Sélection de la variante")
    fieldset <= legend_variant

    # list the variants we have
    variant_list = {d['variant'] for d in games_data.values()}

    input_variant = html.SELECT(type="select-one", value="")
    for variant in variant_list:
        option = html.OPTION(variant)
        if variant == selected_variant:
            option.selected = True
        input_variant <= option
    fieldset <= input_variant
    form <= fieldset

    input_select_variant = html.INPUT(type="submit", value="Sélectionner")
    input_select_variant.bind("click", lambda e, i=input_variant: select_variant_callback(e, i))
    form <= input_select_variant

    MY_SUB_PANEL <= form
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # state selector
    # ----------------

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_state = html.LEGEND("Sélection de l'état", title="Sélection de l'état")
    fieldset <= legend_state

    # list the states we have
    state_list = {d['current_state'] for d in games_data.values()}

    rev_state_code_table = {v: k for k, v in config.STATE_CODE_TABLE.items()}

    input_state = html.SELECT(type="select-one", value="")
    for current_state in state_list:
        current_state_str = rev_state_code_table[current_state]
        option = html.OPTION(current_state_str)
        if current_state == selected_state:
            option.selected = True
        input_state <= option
    fieldset <= input_state
    form <= fieldset

    input_select_state = html.INPUT(type="submit", value="Sélectionner")
    input_select_state.bind("click", lambda e, i=input_state: select_state_callback(e, i))
    form <= input_select_state

    MY_SUB_PANEL <= form
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # game selector
    # ----------------

    form = html.FORM()
    fieldset = html.FIELDSET()
    legend_game = html.LEGEND("Sélection de la partie", title="Sélection de la partie")
    fieldset <= legend_game

    # list the games we have
    game_list = sorted([g['name'] for g in games_data.values() if g['variant'] == selected_variant and g['current_state'] == selected_state], key=lambda n: n.upper())

    input_game = html.SELECT(type="select-one", value="")
    for game in game_list:
        option = html.OPTION(game)
        if 'GAME' in storage:
            if storage['GAME'] == game:
                option.selected = True
        input_game <= option
    fieldset <= input_game
    form <= fieldset

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_data.items()}

    input_select_game = html.INPUT(type="submit", value="Sélectionner")
    input_select_game.bind("click", lambda e, ig=input_game, gds=game_data_sel: select_game_callback(e, ig, gds))
    form <= input_select_game

    MY_SUB_PANEL <= form


def unselect_game():
    """ unselect_game """
    if 'GAME' in storage:
        del storage['GAME']
        show_game_selected()


def show_game_selected():
    """  show_game_selected """

    log_message = html.DIV()
    if 'GAME' in storage:
        log_message <= "La partie sélectionnée est "
        log_message <= html.B(storage['GAME'])
    else:
        log_message <= "Pas de partie sélectionnée..."

    show_game_selected_panel = html.DIV(id="show_game_selected")
    show_game_selected_panel.attrs['style'] = 'text-align: left'
    show_game_selected_panel <= log_message

    if 'show_game_selected' in document:
        del document['show_game_selected']

    document <= show_game_selected_panel


def pairing():
    """ pairing """

    def join_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'inscription à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Erreur à l'inscription à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                pairing()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez rejoint la partie (en utilisant la page 'appariement') : {messages}<br>Attention, c'est un réel engagement à ne pas prendre à la légère.<br>Un abandon pourrait compromettre votre inscription à de futures parties sur le site...", True)

            # back to where we started
            MY_SUB_PANEL.clear()
            pairing()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # adding allocation : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def quit_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la désinscription de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Erreur à la désinscription de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                pairing()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez quitté la partie : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            pairing()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # should be a delete but body in delete requests is more or less forbidden
        # quitting a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def take_mastering_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):

            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la prise de l'arbitrage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la prise de l'arbitrage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                pairing()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez pris l'arbitrage de la partie : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            pairing()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'role_id': 0,
            'player_pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # taking game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def quit_mastering_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la démission de l'arbitrage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la démission de l'arbitrage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                pairing()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez quitté l'arbitrage de la partie : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            pairing()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'role_id': 0,
            'player_pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # giving up game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    game_id = storage['GAME_ID']

    MY_SUB_PANEL <= html.H3("Se mettre dans la partie")

    # join game

    form = html.FORM()
    input_join_game = html.INPUT(type="submit", value="Rejoindre la partie sélectionnée")
    input_join_game.bind("click", join_game_callback)
    form <= input_join_game
    MY_SUB_PANEL <= form

    # quit game

    MY_SUB_PANEL <= html.H3("Se retirer de la partie")

    form = html.FORM()
    input_quit_game = html.INPUT(type="submit", value="Quitter la partie sélectionnée")
    input_quit_game.bind("click", quit_game_callback)
    form <= input_quit_game
    MY_SUB_PANEL <= form

    # take mastering

    MY_SUB_PANEL <= html.H3("Prendre l'arbitrage de la partie")

    form = html.FORM()
    input_join_game = html.INPUT(type="submit", value="Prendre l'arbitrage de la partie sélectionnée")
    input_join_game.bind("click", take_mastering_game_callback)
    form <= input_join_game
    MY_SUB_PANEL <= form

    # quit mastering

    MY_SUB_PANEL <= html.H3("Quitter l'arbitrage de la partie")

    form = html.FORM()
    input_join_game = html.INPUT(type="submit", value="Démissionner de l'arbitrage de la partie sélectionnée")
    input_join_game.bind("click", quit_mastering_game_callback)
    form <= input_join_game
    MY_SUB_PANEL <= form


def show_no_game_masters_data():
    """ show_no_game_masters_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the players (masters)
    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']
    games_with_master = []
    for load in masters_alloc.values():
        games_with_master += load

    no_game_masters_table = html.TABLE()

    fields = ['game']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'game': 'partie'}[field]
        col = html.TD(field_fr)
        thead <= col
    no_game_masters_table <= thead

    for identifier, data in sorted(games_dict.items(), key=lambda g: g[1]['name'].upper()):

        if int(identifier) in games_with_master:
            continue

        row = html.TR()
        value = data['name']
        col = html.TD(value)
        row <= col
        no_game_masters_table <= row

    MY_SUB_PANEL <= html.H3("Les parties sans arbitre")
    MY_SUB_PANEL <= no_game_masters_table


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = OPTIONS[0]

MY_SUB_PANEL = html.DIV(id='technical')
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Sélectionner une partie':
        select_game(config.FORCED_VARIANT_NAME, 1)
    if item_name == 'Aller dans la partie sélectionnée':
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)
    if item_name == 'Rejoindre une partie':
        my_opportunities()
    if item_name == 'Toutes les parties':
        all_games('en cours')
    if item_name == 'Appariement':
        pairing()
    if item_name == 'Parties sans arbitres':
        show_no_game_masters_data()

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


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
