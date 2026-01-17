""" allgames """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from time import time

from browser import html, alert, ajax  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common
import mapping
import interface
import memoize
import play
import allgames
import mydialog


import index  # circular import


MY_PANEL = html.DIV()
MY_SUB_PANEL = html.DIV(id="page")
MY_SUB_PANEL.attrs['style'] = 'display: table-row'
MY_PANEL <= MY_SUB_PANEL


def get_recruiting_games():
    """ get_recruiting_games : returns empty list if error or no game"""

    recruiting_games_list = []

    def reply_callback(req):
        nonlocal recruiting_games_list
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return recruiting_games_list


def recruiting_games():
    """ recruiting_games """

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

        allgames.show_game_selected()

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    def quit_and_select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ quit_and_select_game_callback : the second way of quitting a game : by a button """

        def quit_game(game_name, game_data_sel):

            def reply_callback(req):

                req_result = loads(req.text)
                if req.status != 200:
                    if 'message' in req_result:
                        alert(f"Erreur à la désinscription à la partie : {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à la désinscription à la partie : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    return

                messages = "<br>".join(req_result['msg'].split('\n'))
                mydialog.info_go(f"Vous avez quitté la partie (en utilisant la page 'rejoindre') : {messages}")

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
            ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        ev.preventDefault()

        # action of putting myself in game
        quit_game(game_name, game_data_sel)

        # action of going to the game
        select_game_callback(ev, game_name, game_data_sel)

    def join_and_select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ join_and_select_game_callback : the second way of joining a game : by a button """

        ev.preventDefault()

        # action of going to the game
        select_game_callback(ev, game_name, game_data_sel)

        play.set_arrival('rejoindre')
        play.render(PANEL_MIDDLE)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_SUB_PANEL.clear()
        recruiting_games()

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by != storage['SORT_BY_OPPORTUNITIES']:
            storage['SORT_BY_OPPORTUNITIES'] = new_sort_by
            storage['REVERSE_NEEDED_OPPORTUNITIES'] = str(False)
        else:
            storage['REVERSE_NEEDED_OPPORTUNITIES'] = str(not bool(storage['REVERSE_NEEDED_OPPORTUNITIES'] == 'True'))

        MY_SUB_PANEL.clear()
        recruiting_games()

    overall_time_before = time()

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

    games_dict = common.get_games_data(0, 1)  # awaiting or ongoing
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data(0, 1)  # awaiting or ongoing
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']
    # merge 'masters_alloc2' into 'masters_alloc'
    for master, his_games in masters_alloc.items():
        if master in masters_alloc:
            masters_alloc[master] += his_games
        else:
            masters_alloc[master] = his_games

    games_dict_recruiting = {k: v for k, v in games_dict.items() if int(k) in recruiting_games_dict}

    # get the players
    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # fill table game -> master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            if str(game_id) in games_dict:
                game = games_dict[str(game_id)]['name']
                game_master_dict[game] = master

    # Title
    MY_SUB_PANEL <= html.H3("Parties qui recrutent des joueurs")

    # button for creating account
    if 'PSEUDO' not in storage:
        # shortcut to create account
        button = html.BUTTON("Je n'ai pas de compte, je veux le créer !", Class='btn-inside')
        button.bind("click", create_account_callback)
        MY_SUB_PANEL <= button
        MY_SUB_PANEL <= html.BR()

    # button for switching mode
    if 'GAME_ACCESS_MODE' not in storage:
        storage['GAME_ACCESS_MODE'] = 'button'
    if storage['GAME_ACCESS_MODE'] == 'button':
        button = html.BUTTON("Mode liens externes (plus lent mais conserve cette page)", Class='btn-inside')
    else:
        button = html.BUTTON("Mode boutons (plus rapide mais remplace cette page)", Class='btn-inside')
    button.bind("click", change_button_mode_callback)
    MY_SUB_PANEL <= button
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    games_table = html.TABLE()

    fields = ['name', 'join', 'deadline', 'current_state', 'current_advancement', 'allocated', 'variant', 'used_for_elo', 'master', 'description', 'nopress_current', 'nomessage_current', 'game_type']

    # header
    thead = html.THEAD()
    for field in fields:

        content = {'name': 'nom', 'join': 'rejoindre la partie (pour jouer dedans)', 'deadline': 'date limite', 'current_state': 'état', 'current_advancement': 'saison à jouer', 'allocated': 'alloué (dont arbitre)', 'variant': 'variante', 'used_for_elo': 'elo', 'master': 'arbitre', 'description': 'description', 'nopress_current': 'presse', 'nomessage_current': 'messagerie', 'game_type': 'type de partie'}[field]

        legend = {'name': "Le nom de la partie", 'join': "Un bouton pour rejoindre la partie (pour jouer dedans)", 'deadline': "La date limite de la partie", 'current_state': "L'état actuel de la partie", 'current_advancement': "La  saison qui est maintenant à jouer dans la partie", 'allocated': "Combien de joueurs sont alloué à la partie (arbitre compris) ?", 'variant': "La variante de la partie", 'used_for_elo': "Est-ce que la partie compte pour le classement E.L.O ?", 'master': "L'arbitre de la partie", 'description': "Une petite description de la partie", 'nopress_current': "Est-ce que les messages publics (presse) sont autorisés pour les joueurs actuellement", 'nomessage_current': "Est-ce que les messages privés (messagerie) sont autorisés pour les joueurs actuellement", 'game_type': "Type de partie pour la communication en jeu"}[field]

        field = html.DIV(content, title=legend)
        col = html.TD(field)
        thead <= col

    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'master', 'deadline', 'current_state', 'current_advancement', 'allocated', 'variant', 'used_for_elo', 'nopress_current', 'nomessage_current', 'game_type']:

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

    number_games = 0

    # default
    if 'SORT_BY_OPPORTUNITIES' not in storage:
        storage['SORT_BY_OPPORTUNITIES'] = 'creation'
    if 'REVERSE_NEEDED_OPPORTUNITIES' not in storage:
        storage['REVERSE_NEEDED_OPPORTUNITIES'] = str(False)

    sort_by = storage['SORT_BY_OPPORTUNITIES']
    reverse_needed = bool(storage['REVERSE_NEEDED_OPPORTUNITIES'] == 'True')

    gameover_table = {int(game_id_str): data['soloed'] or data['end_voted'] or data['finished'] for game_id_str, data in games_dict.items()}

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
    elif sort_by == 'master':
        def key_function(g): return game_master_dict.get(g[1]['name'], '').upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_current':
        def key_function(g): return int(g[1]['nopress_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_current':
        def key_function(g): return int(g[1]['nomessage_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'game_type':
        def key_function(g): return int(g[1]['game_type'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'last_season':
        def key_function(g): return g[1]['nb_max_cycles_to_play']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'allocated':
        def key_function(g): return - (recruiting_games_dict[int(g[0])]['capacity'] - recruiting_games_dict[int(g[0])]['allocated'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'deadline':
        def key_function(g): return int(gameover_table[int(g[0])]), int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    time_stamp_now = time()

    games_list = []

    for game_id_str, data in sorted(games_dict_recruiting.items(), key=key_function, reverse=reverse_needed):

        # ignore finished (or distinguished) games
        if data['current_state'] in [2, 3]:
            continue

        number_games += 1

        game_id = int(game_id_str)

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

        # add to game list
        game_name = data['name']
        games_list.append(game_name)

        data['master'] = None
        data['join'] = None
        data['allocated'] = None

        row = html.TR()
        for field in fields:

            colour = None
            arriving = False

            value = data[field]
            game_name = data['name']

            if field == 'name':
                if storage['GAME_ACCESS_MODE'] == 'button':
                    button = html.BUTTON(game_name, title="Cliquer pour aller dans la partie", Class='btn-inside')
                    button.bind("click", lambda e, gn=game_name, gds=game_data_sel, a=None: select_game_callback(e, gn, gds))
                    value = button
                else:
                    link = html.A(game_name, href=f"?game={game_name}", title="Cliquer pour aller dans la partie", target="_blank")
                    value = link

            if field == 'join':
                if player_id is None:
                    value = "Pas identifié"
                elif game_id_str in player_games:
                    button = html.BUTTON("quitter", title="Cliquer pour quitter dans la partie (ne plus y jouer)", Class='btn-inside')
                    button.bind("click", lambda e, gn=game_name, gds=game_data_sel: quit_and_select_game_callback(e, gn, gds))
                    value = button
                else:
                    button = html.BUTTON("rejoindre", title="Cliquer pour rejoindre dans la partie (y jouer)", Class='btn-inside')
                    button.bind("click", lambda e, gn=game_name, gds=game_data_sel: join_and_select_game_callback(e, gn, gds))
                    value = button
                    # highlite free available position
                    colour = config.CAN_JOIN

            if field == 'deadline':

                deadline_loaded = value
                value = ""

                if int(data['current_state']) == 0:

                    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                    datetime_deadline_loaded_str = mydatetime.strftime(*datetime_deadline_loaded, year_first=True)
                    value = datetime_deadline_loaded_str

                    if time_stamp_now > deadline_loaded:
                        colour = config.EXPIRED_WAIT_START_COLOUR

                elif int(data['current_state']) == 1:

                    if data['soloed']:
                        colour = config.SOLOED_COLOUR
                        value = "(solo)"
                    elif data['end_voted']:
                        colour = config.END_VOTED_COLOUR
                        value = "(fin votée)"
                    elif data['finished']:
                        colour = config.FINISHED_COLOUR
                        value = "(terminée)"

                    else:
                        datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                        datetime_deadline_loaded_str = mydatetime.strftime(*datetime_deadline_loaded, year_first=True)
                        value = datetime_deadline_loaded_str

            if field == 'current_state':
                state_loaded = value
                for possible_state_code, possible_state_desc in config.STATE_CODE_TABLE.items():
                    if possible_state_desc == state_loaded:
                        state_loaded = possible_state_code
                        break
                value = state_loaded
                # highlite ongoing games (replacement)
                if value == 'en cours':
                    colour = config.NEED_REPLACEMENT

            if field == 'current_advancement':
                advancement_loaded = value
                nb_max_cycles_to_play = data['nb_max_cycles_to_play']
                value = common.get_full_season(advancement_loaded, variant_data, nb_max_cycles_to_play, False)
                if advancement_loaded > (nb_max_cycles_to_play - 1) * 5 - 1:
                    arriving = True

            if field == 'allocated':
                allocated = recruiting_games_dict[int(game_id_str)]['allocated']
                capacity = recruiting_games_dict[int(game_id_str)]['capacity']
                stats = f"{allocated}/{capacity}"
                value = html.DIV(stats, title="L'arbitre est compté dans le calcul")
                if allocated >= capacity:
                    colour = config.READY_TO_START_COLOUR

            if field == 'used_for_elo':
                stats = "Oui" if value else "Non"
                value = html.DIV(stats, title="Indique si la partie compte pour le classement E.L.O. sur le site")

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

            if field == 'nopress_current':
                explanation = "Indique si les joueurs peuvent actuellement utiliser la messagerie publique"
                stats = "Non" if data['nopress_current'] else "Oui"
                value = html.DIV(stats, title=explanation)

            if field == 'nomessage_current':
                explanation = "Indique si les joueurs peuvent actuellement utiliser la messagerie privée"
                stats = "Non" if data['nomessage_current'] else "Oui"
                value = html.DIV(stats, title=explanation)

            if field == 'game_type':
                explanation = common.TYPE_GAME_EXPLAIN_CONV[value]
                stats = game_type_conv[value]
                value = html.DIV(stats, title=explanation)

            col = html.TD(value)

            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            if arriving:
                col.style = {
                    'background-color': config.LAST_YEAR
                }

            row <= col

        games_table <= row

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()

    # store the list of games
    storage['GAME_LIST'] = ' '.join(games_list)

    MY_SUB_PANEL <= html.DIV("Pour les parties en attente, la date limite est pour le démarrage de la partie (pas le rendu des ordres)", Class='note')
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed:.2f} secs"
    if number_games:
        stats += f" soit {elapsed / number_games:.2f} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')
    MY_SUB_PANEL <= html.BR()


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    MY_SUB_PANEL.clear()
    recruiting_games()
    panel_middle <= MY_SUB_PANEL
