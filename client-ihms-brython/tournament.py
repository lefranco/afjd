""" tournament """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time

from browser import html, alert, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import mydialog
import common
import config
import interface
import mapping
import scoring
import memoize
import allgames
import play


OPTIONS = ['Parties du tournoi', 'Joueurs du tournoi', 'Classement du tournoi', 'Incidents du tournoi', 'Créer un tournoi', 'Editer le tournoi', 'Supprimer le tournoi', 'Les tournois du site']

MAX_LEN_TOURNAMENT_NAME = 50

TOURNAMENT_DICT = None


def get_tournament_players(tournament_id):
    """ get_tournament_players : returns empty list if problem """

    tournament_players = {}

    def reply_callback(req):
        nonlocal tournament_players
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs du tournoi : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs du tournoi : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        tournament_players = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/tournament-players/{tournament_id}"

    # getting tournament allocation : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return tournament_players


def show_games():
    """ show_games """

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
        allgames.show_game_selected()

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_SUB_PANEL.clear()
        show_games()

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by != storage['SORT_BY_TOURNAMENT']:
            storage['SORT_BY_TOURNAMENT'] = new_sort_by
            storage['REVERSE_NEEDED_TOURNAMENT'] = str(False)
        else:
            storage['REVERSE_NEEDED_TOURNAMENT'] = str(not bool(storage['REVERSE_NEEDED_TOURNAMENT'] == 'True'))

        MY_SUB_PANEL.clear()
        show_games()

    overall_time_before = time.time()

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if not TOURNAMENT_DICT:
        alert("Pas de partie sélectionnée ou pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    # title
    tournament_name = TOURNAMENT_DICT['name']
    title = html.H3(f"Parties du tournoi {tournament_name}")
    MY_SUB_PANEL <= title

    games_in = TOURNAMENT_DICT['games']

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

    fields = ['name', 'go_game', 'deadline', 'current_advancement', 'current_state', 'variant', 'used_for_elo', 'master', 'nopress_game', 'nomessage_game']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'go_game': 'aller dans la partie', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'current_state': 'état', 'variant': 'variante', 'used_for_elo': 'elo', 'master': 'arbitre', 'nopress_game': 'publics (act.)', 'nomessage_game': 'privés (act.)', }[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['name', 'deadline', 'current_advancement', 'current_state', 'variant', 'used_for_elo', 'master', 'nopress_game', 'nomessage_game']:

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

    # get advancement scale
    advancements = [data['current_advancement'] for game_id_str, data in games_dict.items() if int(game_id_str) in games_in]
    min_advancement = min(advancements)
    max_advancement = max(advancements)

    rev_state_code_table = {v: k for k, v in config.STATE_CODE_TABLE.items()}

    number_games = 0

    # default
    if 'SORT_BY_TOURNAMENT' not in storage:
        storage['SORT_BY_TOURNAMENT'] = 'creation'
    if 'REVERSE_NEEDED_TOURNAMENT' not in storage:
        storage['REVERSE_NEEDED_TOURNAMENT'] = str(False)

    sort_by = storage['SORT_BY_TOURNAMENT']
    reverse_needed = bool(storage['REVERSE_NEEDED_TOURNAMENT'] == 'True')

    gameover = {int(game_id_str): data['current_advancement'] % 5 == 4 and (data['current_advancement'] + 1) // 5 >= data['nb_max_cycles_to_play'] for game_id_str, data in games_dict.items()}

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
    elif sort_by == 'deadline':
        def key_function(g): return int(gameover[int(g[0])]), int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    # exception : games are sorted by name, not identifier
    for game_id_str, data in sorted(games_dict.items(), key=key_function, reverse=reverse_needed):

        if int(game_id_str) not in games_in:
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
        data['master'] = None
        data['all_orders_submitted'] = None
        data['all_agreed'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None
            fg_colour = None
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

            if field == 'deadline':

                deadline_loaded = value
                value = ""

                if int(data['current_state']) == 1:

                    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                    datetime_deadline_loaded_str = mydatetime.strftime2(*datetime_deadline_loaded)
                    value = datetime_deadline_loaded_str

                    if data['fast']:
                        factor = 60
                    else:
                        factor = 60 * 60

                    # game over
                    if gameover[game_id]:
                        colour = config.GAMEOVER_COLOUR
                        value = "(terminée)"

                    # we are after everything !
                    elif time_stamp_now > deadline_loaded + factor * 24 * config.CRITICAL_DELAY_DAY:
                        colour = config.CRITICAL_COLOUR
                    # we are after deadline + grace
                    elif time_stamp_now > deadline_loaded + factor * data['grace_duration']:
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

                # special : a colour to see how far games have got (cannot go up to 255 - not readable)
                delta = max(1, max_advancement - min_advancement)
                col_val_red = round(((max_advancement - advancement_loaded) / delta) * 168)
                col_val_green = round(((advancement_loaded - min_advancement) / delta) * 168)
                fg_colour = f"#{col_val_red:02x}{col_val_green:02x}00"

            if field == 'current_state':
                state_name = data[field]
                value = rev_state_code_table[state_name]

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
            if fg_colour is not None:
                col.style = {
                    'color': fg_colour
                }

            row <= col

        games_table <= row

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Les icônes suivants sont cliquables pour aller dans ou agir sur les parties :", Class='note')
    MY_SUB_PANEL <= html.IMG(src="./images/play.png", title="Pour aller dans la partie")
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed} avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')


def show_players():
    """ show_players """

    if not TOURNAMENT_DICT:
        alert("Pas de partie sélectionnée ou pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    # title
    tournament_name = TOURNAMENT_DICT['name']
    title = html.H3(f"Les participants du tournoi {tournament_name}")
    MY_SUB_PANEL <= title

    tournament_id = TOURNAMENT_DICT['identifier']

    players_list = get_tournament_players(tournament_id)
    if not players_list:
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    players_table = html.TABLE()

    fields = ['pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    for player_id in sorted(players_list, key=lambda p: num2pseudo[p].upper()):

        row = html.TR()
        col = html.TD(num2pseudo[player_id])
        row <= col

        players_table <= row

    MY_SUB_PANEL <= players_table


def show_ratings():
    """ show_ratings """

    overall_time_before = time.time()

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if not TOURNAMENT_DICT:
        alert("Pas de partie sélectionnée ou pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    # title
    tournament_name = TOURNAMENT_DICT['name']
    title = html.H3(f"Le classement du tournoi {tournament_name}")
    MY_SUB_PANEL <= title

    tournament_id = TOURNAMENT_DICT['identifier']
    games_in = TOURNAMENT_DICT['games']

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # build dict of positions
    positions_dict_loaded = common.tournament_position_reload(tournament_id)
    if not positions_dict_loaded:
        alert("Erreur chargement positions des parties du tournoi")
        return

    rating_dict = {}

    name2code = {v: k for k, v in config.SCORING_CODE_TABLE.items()}

    for game_id_str, data in games_dict.items():

        game_id = int(game_id_str)
        game_name = data['name']

        if game_id not in games_in:
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

        # position previously loaded
        position_loaded = positions_dict_loaded[str(game_id)]

        position_data = mapping.Position(position_loaded, variant_data)
        ratings = position_data.role_ratings()

        # scoring
        game_scoring = data['scoring']
        solo_threshold = variant_data.number_centers() // 2
        score_table = scoring.scoring(game_scoring, solo_threshold, ratings)

        # get scoring name
        scoring_name = name2code[game_scoring]

        for role_name, score in score_table.items():
            centers = ratings[role_name]
            rating_dict[(game_name, role_name)] = (score, centers, scoring_name)

    ratings_table = html.TABLE()

    fields = ['rank', 'points', 'centers', 'scoring', 'alias']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'rank': 'rang', 'points': 'points', 'centers': 'centres', 'scoring': 'scorage', 'alias': 'alias'}[field]
        col = html.TD(field_fr)
        thead <= col
    ratings_table <= thead

    rank = 1
    for (game, role), (points, centers, scoring_name) in sorted(rating_dict.items(), key=lambda i: (float(i[1][0]), -float(i[1][1])), reverse=True):

        row = html.TR()

        # rank
        col = html.TD(rank)
        row <= col

        # points
        col = html.TD(f"{float(points):.2f}")
        row <= col

        # centers
        col = html.TD(centers)
        row <= col

        # scoring
        col = html.TD(scoring_name)
        row <= col

        # player
        alias = f"{game}##{role}"
        col = html.TD(alias)
        row <= col

        ratings_table <= row
        rank += 1

    MY_SUB_PANEL <= ratings_table
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV("Les noms des joueurs sont remplacés par des alias &lt;nom de partie&gt;##&lt;nom du rôle&gt;", Class='note')
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed}"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')


def show_incidents():
    """ show_incidents """

    overall_time_before = time.time()

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    if not TOURNAMENT_DICT:
        alert("Pas de partie sélectionnée ou pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    # title
    tournament_name = TOURNAMENT_DICT['name']
    title = html.H3(f"Les incidents du tournoi {tournament_name}")
    MY_SUB_PANEL <= title

    tournament_id = TOURNAMENT_DICT['identifier']

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the actual incidents (civil disorders) of the tournament
    tournament_incidents2 = common.tournament_incidents2_reload(tournament_id)
    # there can be no incidents (if no incident of failed to load)

    tournament_incidents2_table = html.TABLE()

    fields = ['alias', 'season', 'date']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'alias': 'alias', 'season': 'saison', 'date': 'date'}[field]
        col = html.TD(field_fr)
        thead <= col
    tournament_incidents2_table <= thead

    for game_id, role_num, advancement, time_stamp in sorted(tournament_incidents2, key=lambda i: i[3]):

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

        row = html.TR()

        # player
        game_name = data['name']
        role = variant_data.roles[role_num]
        role_name = variant_data.role_name_table[role]
        alias = f"{game_name}##{role_name}"
        col = html.TD(alias)
        row <= col

        # season
        advancement_season, advancement_year = common.get_season(advancement, variant_data)
        advancement_season_readable = variant_data.season_name_table[advancement_season]
        game_season = f"{advancement_season_readable} {advancement_year}"
        col = html.TD(game_season)
        row <= col

        # date
        datetime_incident = mydatetime.fromtimestamp(time_stamp)
        datetime_incident_str = mydatetime.strftime2(*datetime_incident)
        col = html.TD(datetime_incident_str)
        row <= col

        tournament_incidents2_table <= row

    # get the actual incidents (delays) of the tournament
    tournament_incidents = common.tournament_incidents_reload(tournament_id)
    # there can be no incidents (if no incident of failed to load)

    tournament_incidents_table = html.TABLE()

    fields = ['alias', 'season', 'duration', 'date']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'alias': 'alias', 'season': 'saison', 'duration': 'durée', 'date': 'date'}[field]
        col = html.TD(field_fr)
        thead <= col
    tournament_incidents_table <= thead

    for game_id, role_num, advancement, duration, time_stamp in sorted(tournament_incidents, key=lambda i: i[4]):

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

        row = html.TR()

        # player
        game_name = data['name']
        role = variant_data.roles[role_num]
        role_name = variant_data.role_name_table[role]
        alias = f"{game_name}##{role_name}"
        col = html.TD(alias)
        row <= col

        # season
        advancement_season, advancement_year = common.get_season(advancement, variant_data)
        advancement_season_readable = variant_data.season_name_table[advancement_season]
        game_season = f"{advancement_season_readable} {advancement_year}"
        col = html.TD(game_season)
        row <= col

        # duration
        col = html.TD(f"{duration}")
        row <= col

        # date
        datetime_incident = mydatetime.fromtimestamp(time_stamp)
        datetime_incident_str = mydatetime.strftime(*datetime_incident)
        col = html.TD(datetime_incident_str)
        row <= col

        tournament_incidents_table <= row

    MY_SUB_PANEL <= html.DIV("Les noms des joueurs sont remplacés par des alias &lt;nom de partie&gt;##&lt;nom du rôle&gt;", Class='note')

    title2 = html.H4("Désordres civils du tournoi")
    MY_SUB_PANEL <= title2
    MY_SUB_PANEL <= tournament_incidents2_table

    title2 = html.H4("Retards du tournoi")
    MY_SUB_PANEL <= title2
    MY_SUB_PANEL <= tournament_incidents_table
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Les retards des joueurs qui depuis ont été remplacés n'apparaissent pas", Class='note')
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées", Class='note')
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed}"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')


def create_tournament():
    """ create_tournament """

    def create_tournament_callback(ev):  # pylint: disable=invalid-name
        """ create_tournament_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la création du tournoi : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la création du tournoi : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le tournoi a été créé : {messages}")

            # we may have just created so need to reload
            global TOURNAMENT_DICT
            TOURNAMENT_DICT = common.get_tournament_data(game)
            if not TOURNAMENT_DICT:
                alert("Impossible de retrouver le tournoi qui vient juste d'être créée.")

        ev.preventDefault()

        name = input_name.value

        if not name:
            alert("Nom de tournoi manquant")
            MY_SUB_PANEL.clear()
            create_tournament()
            return

        if len(name) > MAX_LEN_TOURNAMENT_NAME:
            alert("Nom de tournoi trop long")
            MY_SUB_PANEL.clear()
            create_tournament()
            return

        json_dict = {
            'name': name,
            'game_id': game_id,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/tournaments"

        # creating a tournament : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        create_tournament()

    MY_SUB_PANEL <= html.H3("Création de tournoi")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    game_id = storage['GAME_ID']

    information = html.DIV(Class='important')
    information <= f"Vous êtes sur le point de créer un tournoi qui contiendra (pour commencer) la partie sélectionnée ({game}) "
    MY_SUB_PANEL <= information

    form = html.FORM()

    legend_title_main = html.H3("Paramètres principaux du tournoi - ne peuvent plus être changés le tournoi crée")
    form <= legend_title_main

    form <= html.DIV("Pas d'espaces ni de tirets dans le nom du tournoi", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom du tournoi (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value="", size=MAX_LEN_TOURNAMENT_NAME)
    fieldset <= input_name
    form <= fieldset

    form <= html.BR()

    input_create_tournament = html.INPUT(type="submit", value="Créer le tournoi")
    input_create_tournament.bind("click", create_tournament_callback)
    form <= input_create_tournament

    MY_SUB_PANEL <= form


def edit_tournament():
    """ edit_tournament """

    def put_in_tournament_callback(ev):  # pylint: disable=invalid-name
        """ put_in_tournament_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la mise d'une partie dans le tournoi : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise d'une partie dans le tournoi : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                edit_tournament()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La partie a été mise dans le tournoi : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_tournament()

        ev.preventDefault()

        game_name = input_incomer.value
        game_id = common.get_game_id(game_name)
        if not game_id:
            alert("Erreur chargement identifiant partie")
            return

        json_dict = {
            'game_id': game_id,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/groupings/{tournament_id}"

        # putting a game in a tournament : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_from_tournament_callback(ev):  # pylint: disable=invalid-name
        """remove_from_tournament_callback"""

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au retrait d'une partie du tournoi : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au retrait d'une partie du tournoi : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                edit_tournament()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La partie a été retirée du tournoi : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_tournament()

        ev.preventDefault()

        game_name = input_outcomer.value

        game_id = common.get_game_id(game_name)
        if not game_id:
            alert("Erreur chargement identifiant partie")
            return

        json_dict = {
            'game_id': game_id,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/groupings/{tournament_id}"

        # removing a game from a tournament : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    # get the tournament_id

    # we probably just changed so need to reload
    global TOURNAMENT_DICT
    TOURNAMENT_DICT = common.get_tournament_data(game)
    if not TOURNAMENT_DICT:
        alert("Pas de partie sélectionnée ou pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    # title
    tournament_name = TOURNAMENT_DICT['name']
    title = html.H3(f"Mettre dans ou enlever des parties du tournoi {tournament_name}")
    MY_SUB_PANEL <= title

    tournament_id = TOURNAMENT_DICT['identifier']
    games_in = TOURNAMENT_DICT['games']

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    id2name = {int(k): v['name'] for k, v in games_dict.items()}

    # get the groupings
    groupings_dict = common.get_groupings_data()
    if not groupings_dict:
        alert("Pas de groupements ou erreur chargement dictionnaire groupements")
        return

    games_grouped_list = sum(groupings_dict.values(), [])

    form = html.FORM()

    # ---

    fieldset = html.FIELDSET()
    legend_incomer = html.LEGEND("Entrant", title="Sélectionner la partie à mettre dans le tournoi")
    fieldset <= legend_incomer

    # put the games not in any tournament
    # all games can come in
    possible_incomers = set(map(int, games_dict.keys()))

    # not those already in a tournament
    possible_incomers -= set(games_grouped_list)

    input_incomer = html.SELECT(type="select-one", value="")
    for game_name in sorted(map(lambda i: id2name[i], possible_incomers), key=lambda g: g.upper()):
        option = html.OPTION(game_name)
        input_incomer <= option

    fieldset <= input_incomer
    form <= fieldset

    form <= html.BR()

    input_put_in_tournament = html.INPUT(type="submit", value="Mettre dans le tournoi")
    input_put_in_tournament.bind("click", put_in_tournament_callback)
    form <= input_put_in_tournament

    form <= html.BR()
    form <= html.BR()

    # ---

    fieldset = html.FIELDSET()
    fieldset <= html.LEGEND("Sont dans le tournoi : ")
    fieldset <= html.DIV(" ".join(sorted(map(lambda i: id2name[i], games_in), key=lambda g: g.upper())), Class='note')
    form <= fieldset

    # ---
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_outcomer = html.LEGEND("Sortant", title="Sélectionner la partie à retirer du tournoi")
    fieldset <= legend_outcomer

    # put the games in the tournament
    possible_outcomers = games_in

    input_outcomer = html.SELECT(type="select-one", value="")
    for game_name in sorted(map(lambda i: id2name[i], possible_outcomers), key=lambda g: g.upper()):
        option = html.OPTION(game_name)
        input_outcomer <= option

    fieldset <= input_outcomer
    form <= fieldset

    form <= html.BR()

    input_remove_from_tournament = html.INPUT(type="submit", value="Retirer du tournoi")
    input_remove_from_tournament.bind("click", remove_from_tournament_callback)
    form <= input_remove_from_tournament

    MY_SUB_PANEL <= form


def delete_tournament():
    """ delete_tournament """

    def cancel_delete_tournament_callback(_, dialog):
        """ cancel_delete_tournament_callback """
        dialog.close(None)

    def delete_tournament_callback(ev, dialog):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppresssion du tournoi : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppresssion du tournoi : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Le tournoi a été supprimé : {messages}")

            global TOURNAMENT_DICT
            TOURNAMENT_DICT = common.get_tournament_data(game)
            if not TOURNAMENT_DICT:
                alert("Pas de partie sélectionnée ou pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
                return

        ev.preventDefault()

        dialog.close(None)

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/tournaments/{game}"

        # deleting tournament : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_tournament_callback_confirm(ev):  # pylint: disable=invalid-name
        """ delete_tournament_callback_confirm """

        ev.preventDefault()

        dialog = mydialog.Dialog("On supprime vraiment le tournoi ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog: delete_tournament_callback(e, d))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_delete_tournament_callback(e, d))

        # back to where we started
        MY_SUB_PANEL.clear()
        delete_tournament()

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    global TOURNAMENT_DICT
    TOURNAMENT_DICT = common.get_tournament_data(game)
    if not TOURNAMENT_DICT:
        alert("Pas de partie sélectionnée ou pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    # title
    tournament_name = TOURNAMENT_DICT['name']
    title = html.H3(f"Suppression du tournoi {tournament_name}")
    MY_SUB_PANEL <= title

    form = html.FORM()

    input_delete_tournament = html.INPUT(type="submit", value="Supprimer le tournoi")
    input_delete_tournament.bind("click", delete_tournament_callback_confirm)
    form <= input_delete_tournament

    MY_SUB_PANEL <= form


def show_tournaments_data():
    """ show_tournaments_data """

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
        allgames.show_game_selected()

        # action of going to game page
        PANEL_MIDDLE.clear()
        render(PANEL_MIDDLE)

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

    # get the tournaments
    tournaments_dict = common.get_tournaments_data()
    if not tournaments_dict:
        alert("Pas de tournoi ou erreur chargement dictionnaire tournois")
        return

    # get the assignments
    assignments_dict = common.get_assignments_data()
    if not assignments_dict:
        alert("Pas d'assignations ou erreur chargement dictionnaire assignations")
        return

    # get the groupings
    groupings_dict = common.get_groupings_data()
    if not groupings_dict:
        alert("Pas de groupements ou erreur chargement dictionnaire groupements")
        return

    tournaments_table = html.TABLE()

    fields = ['tournament', 'go_tournament', 'creator', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'tournament': 'tournoi', 'go_tournament': 'aller dans le tournoi', 'creator': 'créateur', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    tournaments_table <= thead

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    count = 0
    for tournament_id, data in sorted(tournaments_dict.items(), key=lambda m: int(m[0]), reverse=True):
        row = html.TR()
        for field in fields:
            if field == 'tournament':
                value = data['name']
            if field == 'go_tournament':
                games_ids = groupings_dict[str(tournament_id)]
                games_names = sorted([games_dict[str(i)]['name'] for i in games_ids], key=lambda m: m.upper())
                game_name = games_names[0]
                form = html.FORM()
                input_jump_game = html.INPUT(type="image", src="./images/look.png")
                input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                form <= input_jump_game
                value = form
            if field == 'creator':
                director_id = assignments_dict[str(tournament_id)]
                director_pseudo = players_dict[str(director_id)]['pseudo']
                value = director_pseudo
            if field == 'games':
                games_ids = groupings_dict[str(tournament_id)]
                games_names = sorted([games_dict[str(i)]['name'] for i in games_ids], key=lambda m: m.upper())
                value = ' '.join(games_names)
            col = html.TD(value)
            row <= col

        tournaments_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les tournois du site")
    MY_SUB_PANEL <= tournaments_table
    MY_SUB_PANEL <= html.DIV("Les icônes suivants sont cliquables pour aller dans les tournois :", Class='note')
    MY_SUB_PANEL <= html.IMG(src="./images/look.png", title="Pour aller dans le tournoi (en sélectionnant une partie du tournoi)")
    MY_SUB_PANEL <= html.P(f"Il y a {count} tournois")


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = OPTIONS[0]

MY_SUB_PANEL = html.DIV(id="tournament")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Parties du tournoi':
        show_games()
    if item_name == 'Joueurs du tournoi':
        show_players()
    if item_name == 'Classement du tournoi':
        show_ratings()
    if item_name == 'Incidents du tournoi':
        show_incidents()
    if item_name == 'Créer un tournoi':
        create_tournament()
    if item_name == 'Editer le tournoi':
        edit_tournament()
    if item_name == 'Supprimer le tournoi':
        delete_tournament()
    if item_name == 'Les tournois du site':
        show_tournaments_data()

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

    ITEM_NAME_SELECTED = 'Les tournois du site'

    if 'GAME' in storage:
        game = storage['GAME']
        global TOURNAMENT_DICT
        TOURNAMENT_DICT = common.get_tournament_data(game)
        if TOURNAMENT_DICT:
            ITEM_NAME_SELECTED = 'Parties du tournoi'

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
