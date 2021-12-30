""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time
import datetime

from browser import html, alert, ajax, window  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import config
import interface
import mapping
import selection
import scoring
import memoize
import index  # circular import


OPTIONS = ['parties du tournoi', 'classement du tournoi', 'retards du tournoi', 'créer un tournoi', 'éditer le tournoi', 'supprimer le tournoi', 'les tournois du site', 'créer plusieurs parties', 'tester un scorage']

DESCRIPTION = "partie créée par batch"

MAX_LEN_GAME_NAME = 50
MAX_LEN_TOURNAMENT_NAME = 50

INPUT_FILE = None

TOURNAMENT_DICT = None


def check_batch(current_pseudo, games_to_create):
    """ check_batch """

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return False
    games_dict = dict(games_dict)

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return False
    players_dict = dict(players_dict)
    players_set = {d['pseudo'] for d in players_dict.values()}

    error = False

    # check the players exist
    already_warned = set()
    for ligne, allocations in enumerate(games_to_create.values()):
        for player_name in allocations.values():

            # empty player (fatal)
            if not player_name:
                alert(f"Il y a un nom de joueur vide dans le fichier en ligne {ligne+1}")
                return False

            if player_name not in players_set:

                if player_name not in already_warned:
                    alert(f"Il semble que le joueur '{player_name}' n'existe pas sur le site")
                    already_warned.add(player_name)
                    error = True

    # check all games have same number of roles (fatal)
    reference_size = None
    for game_name, allocations in games_to_create.items():
        size = len(allocations)
        if reference_size is None:
            reference_size = size
        elif size != reference_size:
            alert(f"Il semble que la partie {game_name} n'a pas le même nombre de joueurs que la première partie")
            return False

    # check the players in games are not duplicated (fatal)
    for game_name, allocations in games_to_create.items():
        if len(set(allocations.values())) != len(allocations.values()):
            alert(f"Il semble que la partie {game_name} n'a pas des joueurs tous différents")
            return False

    # check players are in same number of games (fatal)
    presence_table = {}
    for allocations in games_to_create.values():
        for player_name in allocations.values():
            if player_name in presence_table:
                presence_table[player_name] += 1
            else:
                presence_table[player_name] = 1
    for player_name1, occurences_player1 in presence_table.items():
        for player_name2, occurences_player2 in presence_table.items():
            if player_name2 != player_name1 and occurences_player2 != occurences_player1:
                alert(f"Il semble que les joueurs '{player_name1}' et '{player_name2}' jouent dans un nombre de parties différent")
                return False

    # game master has to be pseudo
    for game_name, allocations in games_to_create.items():
        if allocations[0] != current_pseudo:
            alert(f"Vous n'êtes pas l'arbitre indiqué dans le fichier pour la partie {game_name}. Il faudra donc demander à l'arbitre en question de venir lui-même sur le site réaliser la création de ses parties")
            error = True

    return not error


def perform_batch(current_pseudo, current_game_name, games_to_create_data, description):
    """ perform_batch """

    def create_game(current_pseudo, current_game_name, game_to_create_name, description):
        """ create_game """

        create_status = None

        def reply_callback(req):
            nonlocal create_status
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la création de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la création de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                create_status = False
                return

            create_status = True

        parameters_loaded = common.game_parameters_reload(current_game_name)
        if not parameters_loaded:
            alert("Impossible de récupérer les paramètres de la partie modèle")
            return False

        # copy
        json_dict = {}

        json_dict.update(parameters_loaded)

        # but changes

        # obviously different name
        json_dict['name'] = game_to_create_name

        # obviously different description
        json_dict['description'] = description

        # can only be manual
        json_dict['manual'] = True

        # obviously different deadline - set it to now
        timestamp = time.time()
        deadline = int(timestamp)
        json_dict['deadline'] = deadline

        # obviously different state (starting)
        json_dict['current_state'] = 0
        json_dict['current_advancement'] = 0

        # and addition
        json_dict['pseudo'] = current_pseudo

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games"

        # creating a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return create_status

    def put_player_in_game(current_pseudo, game_name, player_name):
        """ put_player_in_game """

        status = None

        def reply_callback(req):
            nonlocal status
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la mise d'un joueur dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise d'un joueur dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            status = True

        game_id_int = common.get_game_id(game_name)
        if not game_id_int:
            alert(f"Erreur chargement identifiant partie {game_name}. Cette partie existe ?")
            return False

        json_dict = {
            'game_id': game_id_int,
            'player_pseudo': player_name,
            'pseudo': current_pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # putting a player in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return status

    def allocate_role(current_pseudo, game_name, player_pseudo, role_id):
        """ allocate_role """

        status = None

        def reply_callback(req):
            nonlocal status
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'allocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'allocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            status = True

        game_id_int = common.get_game_id(game_name)
        if not game_id_int:
            alert(f"Erreur chargement identifiant partie {game_name}. Cette partie existe ?")
            return False

        json_dict = {
            'game_id': game_id_int,
            'role_id': role_id,
            'player_pseudo': player_pseudo,
            'delete': 0,
            'pseudo': current_pseudo,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return status

    # just to display role correctly
    variant_name_loaded = storage['GAME_VARIANT']
    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    interface_chosen = interface.get_interface_from_variant(variant_name_loaded)
    parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    # do the work using the three previous functions

    for game_to_create_name, game_to_create_data in games_to_create_data.items():

        # create game
        status = create_game(current_pseudo, current_game_name, game_to_create_name, description)
        if not status:
            alert(f"Echec à la création de la partie {game_to_create_name}")
            return

        # put players in
        for role_id, player_name in game_to_create_data.items():
            # game master already there
            if role_id == 0:
                continue
            # put player
            status = put_player_in_game(current_pseudo, game_to_create_name, player_name)
            if not status:
                alert(f"Echec à l'appariement de {player_name} dans la partie {game_to_create_name}")
                return

        # allocate roles to players
        for role_id, player_name in game_to_create_data.items():
            # game master already has its role
            if role_id == 0:
                continue
            status = allocate_role(current_pseudo, game_to_create_name, player_name, role_id)
            if not status:
                role = variant_data.roles[role_id]
                role_name = variant_data.name_table[role]
                alert(f"Echec à l'attribution du role {role_name} à {player_name} dans la partie {game_to_create_name}")
                return

    nb_parties = len(games_to_create_data)
    alert(f"Les {nb_parties} parties du tournoi ont bien été créée. Tout s'est bien passé. Incroyable, non ?")


def show_games():
    """ show_games """

    def select_game_callback(_, game_name, game_data_sel):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        InfoDialog("OK", f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page", remove_after=config.REMOVE_AFTER)
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    overall_time_before = time.time()

    # title
    title = html.H3("Parties du tournoi")
    MY_SUB_PANEL <= title

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    global TOURNAMENT_DICT
    if not TOURNAMENT_DICT:
        TOURNAMENT_DICT = common.tournament_data(game)
        if not TOURNAMENT_DICT:
            alert("Pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
            return

    tournament_name = TOURNAMENT_DICT['name']
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

    games_table = html.TABLE()

    fields = ['jump_here', 'go_away', 'master', 'variant', 'deadline', 'current_advancement']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'jump_here': 'même onglet', 'go_away': 'nouvel onglet', 'master': 'arbitre', 'variant': 'variante', 'deadline': 'date limite', 'current_advancement': 'saison à jouer'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0
    for game_id_str, data in sorted(games_dict.items(), key=lambda g: int(g[0])):

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

        data['jump_here'] = None
        data['go_away'] = None
        data['master'] = None
        data['all_orders_submitted'] = None
        data['all_agreed'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None

            if field == 'jump_here':
                game_name = data['name']
                form = html.FORM()
                input_jump_game = html.INPUT(type="submit", value=game_name)
                input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                form <= input_jump_game
                value = form

            if field == 'go_away':
                link = html.A(href=f"?game={game_name}", target="_blank")
                link <= game_name
                value = link

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

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        games_table <= row

    MY_SUB_PANEL <= html.DIV(f"Tournoi {tournament_name}", Class='note')
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
    special_info = html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}", Class='note')
    MY_SUB_PANEL <= special_info
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed} avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')


def show_ratings():
    """ show_ratings """

    overall_time_before = time.time()

    # title
    title = html.H3("Classement du tournoi")
    MY_SUB_PANEL <= title

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    global TOURNAMENT_DICT
    if not TOURNAMENT_DICT:
        TOURNAMENT_DICT = common.tournament_data(game)
        if not TOURNAMENT_DICT:
            alert("Pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
            return

    tournament_name = TOURNAMENT_DICT['name']
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
        score_table = scoring.scoring(game_scoring, variant_data, ratings)

        # get scoring name
        scoring_name = name2code[game_scoring]

        for role_name, score in score_table.items():
            rating_dict[(game_name, role_name)] = (score, scoring_name)

    ratings_table = html.TABLE()

    fields = ['points', 'scoring', 'alias']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'points': 'points', 'scoring': 'scorage', 'alias': 'alias'}[field]
        col = html.TD(field_fr)
        thead <= col
    ratings_table <= thead

    for (game, role), (points, scoring_name) in sorted(rating_dict.items(), key=lambda i: i[1], reverse=True):

        row = html.TR()

        # points
        points_str = f"{points:.2f}"
        col = html.TD(points_str)
        row <= col

        # scoring
        col = html.TD(scoring_name)
        row <= col

        # player
        alias = f"{game}##{role}"
        col = html.TD(alias)
        row <= col

        ratings_table <= row

    MY_SUB_PANEL <= html.DIV(f"Tournoi {tournament_name}", Class='note')
    MY_SUB_PANEL <= html.BR()
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

    # title
    title = html.H3("Incidents du tournoi")
    MY_SUB_PANEL <= title

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    global TOURNAMENT_DICT
    if not TOURNAMENT_DICT:
        TOURNAMENT_DICT = common.tournament_data(game)
        if not TOURNAMENT_DICT:
            alert("Pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
            return

    tournament_name = TOURNAMENT_DICT['name']
    tournament_id = TOURNAMENT_DICT['identifier']

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the actual incidents of the tournament
    tournament_incidents = common.tournament_incidents_reload(tournament_id)
    # there can be no incidents (if no incident of failed to load)

    tournament_incidents_table = html.TABLE()

    fields = ['date', 'alias']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'date': 'date', 'alias': 'alias'}[field]
        col = html.TD(field_fr)
        thead <= col
    tournament_incidents_table <= thead

    for game_id, role_num, date_incident in sorted(tournament_incidents, key=lambda i: i[2]):

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

        # date
        datetime_incident = datetime.datetime.fromtimestamp(date_incident, datetime.timezone.utc)
        incident_day = f"{datetime_incident.year:04}-{datetime_incident.month:02}-{datetime_incident.day:02}"
        incident_hour = f"{datetime_incident.hour:02}:{datetime_incident.minute:02}"
        incident_str = f"{incident_day} {incident_hour} GMT"
        col = html.TD(incident_str)
        row <= col

        # player
        game_name = data['name']
        role = variant_data.roles[role_num]
        role_name = variant_data.name_table[role]
        alias = f"{game_name}##{role_name}"
        col = html.TD(alias)
        row <= col

        tournament_incidents_table <= row

    MY_SUB_PANEL <= html.DIV(f"Tournoi {tournament_name}", Class='note')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= tournament_incidents_table
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV("Les noms des joueurs sont remplacés par des alias &lt;nom de partie&gt;##&lt;nom du rôle&gt;", Class='note')
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed}"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')


def create_tournament():
    """ create_tournament """

    def create_tournament_callback(_):
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
            InfoDialog("OK", f"Le tournoi a été créé : {messages}", remove_after=config.REMOVE_AFTER)

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

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    game_id = storage['GAME_ID']

    form = html.FORM()

    legend_title_main = html.H3("Paramètres principaux du tournoi - ne peuvent plus être changés le tournoi crée")
    form <= legend_title_main

    form <= html.DIV("Pas d'espaces dans le nom du tournoi", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom du tournoi (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value="", size=MAX_LEN_TOURNAMENT_NAME)
    fieldset <= input_name
    form <= fieldset

    form <= html.BR()

    input_create_tournament = html.INPUT(type="submit", value="créer le tournoi")
    input_create_tournament.bind("click", create_tournament_callback)
    form <= input_create_tournament

    MY_SUB_PANEL <= form


def edit_tournament():
    """ edit_tournament """

    def put_in_tournament_callback(_):
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
            InfoDialog("OK", f"La partie a été mise dans le tournoi : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_tournament()

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

    def remove_from_tournament_callback(_):
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
            InfoDialog("OK", f"La partie a été retirée du tournoi : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_tournament()

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

    MY_SUB_PANEL <= html.H3("Mettre dans ou enlever des parties du tournoi")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    # get the tournament_id

    global TOURNAMENT_DICT
    if not TOURNAMENT_DICT:
        TOURNAMENT_DICT = common.tournament_data(game)
        if not TOURNAMENT_DICT:
            alert("Pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
            return

    tournament_name = TOURNAMENT_DICT['name']
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
    for game_name in sorted(map(lambda i: id2name[i], possible_incomers)):
        option = html.OPTION(game_name)
        input_incomer <= option

    fieldset <= input_incomer
    form <= fieldset

    form <= html.BR()

    input_put_in_tournament = html.INPUT(type="submit", value="mettre dans le tournoi")
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
    for game_name in sorted(map(lambda i: id2name[i], possible_outcomers)):
        option = html.OPTION(game_name)
        input_outcomer <= option

    fieldset <= input_outcomer
    form <= fieldset

    form <= html.BR()

    input_remove_from_tournament = html.INPUT(type="submit", value="retirer du tournoi")
    input_remove_from_tournament.bind("click", remove_from_tournament_callback)
    form <= input_remove_from_tournament

    MY_SUB_PANEL <= html.DIV(f"Tournoi {tournament_name}", Class='note')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= form


def delete_tournament():
    """ delete_tournament """

    def cancel_delete_tournament_callback(_, dialog):
        """ cancel_delete_tournament_callback """
        dialog.close()

    def delete_tournament_callback(_, dialog):

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
            InfoDialog("OK", f"Le tournoi a été supprimé : {messages}", remove_after=config.REMOVE_AFTER)

        dialog.close()

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/tournaments/{game}"

        # deleting tournament : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_tournament_callback_confirm(_):
        """ delete_tournament_callback_confirm """

        dialog = Dialog("On supprime vraiment le tournoi ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog: delete_tournament_callback(e, d))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_delete_tournament_callback(e, d))

        # back to where we started
        MY_SUB_PANEL.clear()
        delete_tournament()

    MY_SUB_PANEL <= html.H3("Suppression")

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    global TOURNAMENT_DICT
    if not TOURNAMENT_DICT:
        TOURNAMENT_DICT = common.tournament_data(game)
        if not TOURNAMENT_DICT:
            alert("Pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
            return

    tournament_name = TOURNAMENT_DICT['name']

    form = html.FORM()

    input_delete_tournament = html.INPUT(type="submit", value="supprimer le tournoi")
    input_delete_tournament.bind("click", delete_tournament_callback_confirm)
    form <= input_delete_tournament

    MY_SUB_PANEL <= html.DIV(f"Tournoi {tournament_name}", Class='note')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= form


def show_tournaments_data():
    """ show_tournaments_data """

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

    fields = ['tournament', 'director', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'tournament': 'tournoi', 'director': 'directeur', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    tournaments_table <= thead

    count = 0
    for tournament_id, data in sorted(tournaments_dict.items(), key=lambda m: m[0].upper()):
        row = html.TR()
        for field in fields:
            if field == 'tournament':
                value = data['name']
            if field == 'director':
                director_id = assignments_dict[str(tournament_id)]
                director_pseudo = players_dict[str(director_id)]['pseudo']
                value = director_pseudo
            if field == 'games':
                games_ids = groupings_dict[str(tournament_id)]
                games_names = sorted([games_dict[str(i)]['name'] for i in games_ids], key=lambda m: m.upper())
                value = '/'.join(games_names)
            col = html.TD(value)
            row <= col

        tournaments_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les tournois")
    MY_SUB_PANEL <= tournaments_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} tournois")


def create_many_games():
    """ create_many_games """

    def create_games_callback(_):
        """ create_games_callback """

        def onload_callback(_):
            """ onload_callback """

            def cancel_create_games_callback(_, dialog):
                """ cancel_create_games_callback """
                dialog.close()

            def create_games_callback2(_, dialog):
                """ create_games_callback2 """
                dialog.close()
                perform_batch(pseudo, game, games_to_create, DESCRIPTION)

            games_to_create = {}

            content = str(reader.result)
            lines = content.splitlines()

            for line in lines:

                # ignore empty lines
                if not line:
                    continue

                if line.find(',') != -1:
                    tab = line.split(',')
                elif line.find(';') != -1:
                    tab = line.split(';')
                else:
                    alert("Votre fichier n'est pas un CSV (il faut séparer les champs par des virgules ou des point-virgule)")
                    return

                # name of game is first column
                game_name = tab[0]

                if not game_name:
                    alert("Un nom de partie est vide dans le fichier")
                    return

                if not game_name.isidentifier():
                    alert(f"Le nom de partie '{game_name}' est incorrect pour le site")
                    return

                if len(game_name) > MAX_LEN_GAME_NAME:
                    alert(f"Le nom de partie '{game_name}' est trop long (limite : {MAX_LEN_GAME_NAME})")
                    return

                if game_name in games_to_create:
                    alert(f"La partie {game_name} est définie plusieurs fois dans le fichier")
                    return

                # create dictionnary
                games_to_create[game_name] = {n: tab[n + 1] for n in range(len(tab) - 1)}

            if not games_to_create:
                alert("Aucune partie dans le fichier")
                return

            global DESCRIPTION
            DESCRIPTION = input_description.value

            #  actual creation of all the games
            if check_batch(pseudo, games_to_create):
                dialog = Dialog("On créé vraiment toutes ces parties ?", ok_cancel=True)
                dialog.ok_button.bind("click", lambda e, d=dialog: create_games_callback2(e, d))
                dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_create_games_callback(e, d))

            # back to where we started
            MY_SUB_PANEL.clear()
            create_many_games()

        if not INPUT_FILE.files:
            alert("Pas de fichier")

            # back to where we started
            MY_SUB_PANEL.clear()
            create_many_games()
            return

        # Create a new DOM FileReader instance
        reader = window.FileReader.new()
        # Extract the file
        file_name = INPUT_FILE.files[0]
        # Read the file content as text
        reader.readAsBinaryString(file_name)
        reader.bind("load", onload_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        create_many_games()

    MY_SUB_PANEL <= html.H3("Création des parties")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    information = html.DIV(Class='note')
    information <= "Vous devez composer un fichier CSV"
    information <= html.BR()
    information <= "Une ligne par partie"
    information <= html.BR()
    information <= "Sur chaque ligne, séparés pas des virgules (ou des points-virgules):"
    items = html.UL()
    items <= html.LI("le nom de la partie")
    items <= html.LI("l'arbitre de la partie (cette colonne est redondante : c'est forcément votre pseudo)")
    items <= html.LI("le premier joueur de la partie")
    items <= html.LI("le deuxième joueur de la partie")
    items <= html.LI("etc....")
    information <= items
    information <= "Utiliser l'ordre suivant pour la variante standard : Angleterre, France, Allemagne, Italie, Autriche, Russie, Turquie"
    information <= html.BR()
    information <= "Il est impossible d'attribuer l'arbitrage d'une partie à un autre joueur, donc vous pouvez mettre un arbitre différent à des fins de vérification mais la création des parties n'aura pas lieu."
    information <= html.BR()
    information <= "Il faut remplir soigneusement la description qui s'appliquera à toutes les parties !"
    information <= html.BR()
    information <= "Les parties copieront un maximum de propriétés de la partie modèle que vous avez préalablement sélectionnée..."
    information <= html.BR()
    information <= "Note : Soit vous utilisez comme modèle une partie existante, soit vous la créez pour l'occasion et la supprimez à la fin"

    MY_SUB_PANEL <= information
    MY_SUB_PANEL <= html.BR()

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_description = html.LEGEND("description", title="Ce sera la description de toutes les parties créées")
    fieldset <= legend_description
    input_description = html.TEXTAREA(type="text", rows=5, cols=80)
    input_description <= DESCRIPTION
    fieldset <= input_description
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("Ficher CSV")
    fieldset <= legend_name
    form <= fieldset

    # need to make this global to keep it (only way it seems)
    global INPUT_FILE
    if INPUT_FILE is None:
        INPUT_FILE = html.INPUT(type="file", accept='.csv')
    form <= INPUT_FILE
    form <= html.BR()

    form <= html.BR()

    input_create_games = html.INPUT(type="submit", value="créer les parties")
    input_create_games.bind("click", create_games_callback)
    form <= input_create_games

    MY_SUB_PANEL <= form


RATING_TABLE = {}


def test_scoring():
    """ test_scoring """

    def test_scoring_callback(_, game_scoring, ratings_input):
        """ test_scoring_callback """

        for name, element in ratings_input.items():
            val = 0
            try:
                val = int(element.value)
            except:  # noqa: E722 pylint: disable=bare-except
                pass
            RATING_TABLE[name] = val

        # scoring
        score_table = scoring.scoring(game_scoring, variant_data, RATING_TABLE)

        score_desc = "\n".join([f"{k} : {v} points" for k, v in score_table.items()])
        alert(f"Dans cette configuration la marque est :\n{score_desc}")

        # back to where we started
        MY_SUB_PANEL.clear()
        test_scoring()

    # title
    title = html.H3("Test de scorage")
    MY_SUB_PANEL <= title

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    game_parameters_loaded = common.game_parameters_reload(game)

    variant_name_loaded = storage['GAME_VARIANT']

    # from variant name get variant content
    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)

    # selected interface (user choice)
    interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

    # from display chose get display parameters
    interface_parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, interface_parameters_read)

    # this comes from game
    game_scoring = game_parameters_loaded['scoring']

    form = html.FORM()

    title_enter_centers = html.H4("Entrer les nombre de centres")
    form <= title_enter_centers

    ratings_input = {}
    for num, role in variant_data.roles.items():

        if num == 0:
            continue

        role_name = variant_data.name_table[role]

        fieldset = html.FIELDSET()
        legend_centers = html.LEGEND(role_name, title="nombre de centres")
        fieldset <= legend_centers
        input_centers = html.INPUT(type="number", value=str(RATING_TABLE[role_name]) if role_name in RATING_TABLE else "")
        fieldset <= input_centers
        form <= fieldset

        ratings_input[role_name] = input_centers

    # get scoring name
    name2code = {v: k for k, v in config.SCORING_CODE_TABLE.items()}
    scoring_name = name2code[game_scoring]

    form <= html.DIV(f"Pour cette partie le scorage est {scoring_name}", Class='note')
    form <= html.BR()

    input_test_scoring = html.INPUT(type="submit", value="calculer le scorage")
    input_test_scoring.bind("click", lambda e, gs=game_scoring, ri=ratings_input: test_scoring_callback(e, gs, ri))
    form <= input_test_scoring

    MY_SUB_PANEL <= form


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
    if item_name == 'parties du tournoi':
        show_games()
    if item_name == 'classement du tournoi':
        show_ratings()
    if item_name == 'retards du tournoi':
        show_incidents()
    if item_name == 'créer un tournoi':
        create_tournament()
    if item_name == 'éditer le tournoi':
        edit_tournament()
    if item_name == 'supprimer le tournoi':
        delete_tournament()
    if item_name == 'les tournois du site':
        show_tournaments_data()
    if item_name == 'créer plusieurs parties':
        create_many_games()
    if item_name == 'tester un scorage':
        test_scoring()

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
        MENU_LEFT <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED

    ITEM_NAME_SELECTED = 'créer un tournoi'

    if 'GAME' in storage:
        game = storage['GAME']
        global TOURNAMENT_DICT
        TOURNAMENT_DICT = common.tournament_data(game)
        if TOURNAMENT_DICT:
            ITEM_NAME_SELECTED = 'parties du tournoi'

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
