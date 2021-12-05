""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time

from browser import html, alert, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import config

OPTIONS = ['créer les parties']

DESCRIPTION = "partie créée par batch"


def check_batch(current_pseudo, games_to_create):
    """ check_batch """

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return False
    games_dict = dict(games_dict)
    games_set = {d['name'] for d in games_dict.values()}

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return False
    players_dict = dict(players_dict)
    players_set = {d['pseudo'] for d in players_dict.values()}

    error = False

    # check the game does not exist
    for ligne, game_name in enumerate(games_to_create):

        if not game_name:
            alert(f"Il y a un nom de partie vide dans le fichier en ligne {ligne+1}")
            error = True

        if game_name in games_set:
            alert(f"Il semble que la partie '{game_name}' existe déjà")
            error = True

    # check the players exist
    already_warned = set()
    for ligne, allocations in enumerate(games_to_create.values()):
        for player_name in allocations.values():

            if not player_name:
                alert(f"Il y a un nom de joueur vide dans le fichier en ligne {ligne+1}")
                error = True

            if player_name not in players_set:

                if player_name not in already_warned:
                    alert(f"Il semble que le pseudo '{player_name}' n'existe pas")
                    already_warned.add(player_name)
                    error = True

    # check all games have same number of roles
    reference_size = None
    for game_name, allocations in games_to_create.items():
        size = len(allocations)
        if reference_size is None:
            reference_size = size
        elif size != reference_size:
            alert(f"Il semble que la partie {game_name} n'a pas le même nombre de joueurs que la première partie")
            error = True

    # check the players in games are not duplicated
    for game_name, allocations in games_to_create.items():
        if len(set(allocations.values())) != len(allocations.values()):
            alert(f"Il semble que la partie {game_name} n'a pas 8 joueurs différents")
            error = True

    # check players are in same number of games
    presence_table = dict()
    for allocations in games_to_create.values():
        for player_name in allocations.values():
            if player_name in presence_table:
                presence_table[player_name] += 1
            else:
                presence_table[player_name] = 1
    for player_name1 in presence_table:
        for player_name2 in presence_table:
            if player_name2 != player_name1 and presence_table[player_name2] != presence_table[player_name1]:
                alert(f"Il semble que {player_name1} et {player_name2} jouent dans un nombre de parties différent")
                error = True

    # game master does not have to be pseudo but still warning
    for game_name, allocations in games_to_create.items():
        if allocations[0] != current_pseudo:
            alert(f"Vous n'êtes pas l'arbitre désiré de la partie {game_name}. Il faudra demander à l'abitre désiré de venir prendre l'arbitrage de cette partie")

    return not error


def perform_batch(current_pseudo, current_game_name, games_to_create_data, description):
    """ perform_batch """

    def create_game(current_pseudo, current_game_name, game_to_create_name, description):
        """ create_game """

        create_status = None
        load_status = None
        parameters_loaded = None

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

            alert(f"Création de la partie {game_to_create_name} réalisée !")
            create_status = True

        def game_parameters_reload():
            """ game_parameters_reload """

            def local_noreply_callback(_):
                """ local_noreply_callback """
                nonlocal load_status
                alert("Problème (pas de réponse de la part du serveur)")
                load_status = False

            def reply_callback(req):
                nonlocal load_status
                nonlocal parameters_loaded
                req_result = json.loads(req.text)
                if req.status != 200:
                    if 'message' in req_result:
                        alert(f"Erreur à la récupération du paramètre de la partie modèle : {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à la récupération du paramètre de la partie modèle : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    load_status = False
                    return

                parameters_loaded = req_result
                load_status = True

            json_dict = dict()

            host = config.SERVER_CONFIG['GAME']['HOST']
            port = config.SERVER_CONFIG['GAME']['PORT']
            url = f"{host}:{port}/games/{current_game_name}"

            # getting game data : no need for token
            ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        game_parameters_reload()
        if not load_status:
            alert("Impossible de récupérer les paramètres de la partie modèle")
            return False

        # copy
        json_dict = dict()

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
                    alert(f"Problème putting player in game: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            alert(f"Le joueur {player_name} a été mis dans la partie {game_name} !")
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

            alert(f"Le joueur {player_pseudo} s'est vu attribuer le rôle {role_id} dans la partie {game_name}")
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

    def quit_mastering_game(current_pseudo, game_name):

        status = None

        def reply_callback(req):
            nonlocal status
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la démission de l'arbitrage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la démission de l'arbitrage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                return

            alert(f"Vous avez démissionné de l'arbitrage de la partie {game_name}")
            status = True

        game_id_int = common.get_game_id(game_name)
        if not game_id_int:
            alert(f"Erreur chargement identifiant partie {game_name}. Cette partie existe ?")
            return False

        json_dict = {
            'game_id': game_id_int,
            'role_id': 0,
            'player_pseudo': current_pseudo,
            'pseudo': current_pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # giving up game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return status

    # do the work using the three previous functions

    alert(f"Travail à faire : {games_to_create_data}")

    for game_to_create_name, game_to_create_data in games_to_create_data.items():

        alert(f"Partie {game_to_create_name}...")

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
                alert(f"Echec à l'attribution du role {role_id} à {player_name} dans la partie {game_to_create_name}")
                return

    # give up mastering for games not mastered
    for game_to_create_name, game_to_create_data in games_to_create_data.items():
        # game master already has its role
        game_master_expected = game_to_create_data[0]
        # I am game master
        if game_master_expected == current_pseudo:
            continue
        status = quit_mastering_game(current_pseudo, game_to_create_name)
        if not status:
            alert(f"Echec à la démission de l'arbitrage dans la partie {game_to_create_name}")
            return

    nb_parties = len(games_to_create_data)
    alert(f"Les {nb_parties} parties du tournoi on été créée. Tout s'est bien passé. Incroyable, non ?")


def create_games():
    """ ratings """

    def create_games_callback(_):
        """ create_games_callback """

        def onload_callback(_):
            """ onload_callback """

            games_to_create = dict()

            content = str(reader.result)
            lines = content.splitlines()

            if not len(lines) >= 1:
                alert("Votre fichier n'a pas de lignes")
                return

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

                # create dictionnary
                games_to_create[game_name] = {n: tab[n + 1] for n in range(len(tab) - 1)}

            global DESCRIPTION
            DESCRIPTION = input_description.value

            #  actual creation of all the games
            if check_batch(pseudo, games_to_create):
                perform_batch(pseudo, game, games_to_create, DESCRIPTION)

            # back to where we started
            my_sub_panel.clear()
            create_games()

        if not input_file.files:
            alert("Pas de fichier")

            # back to where we started
            my_sub_panel.clear()
            create_games()
            return

        file = input_file.files[0]
        # Create a new DOM FileReader instance
        reader = window.FileReader.new()
        # Read the file content as text
        reader.readAsBinaryString(file)
        reader.bind("load", onload_callback)

        # back to where we started
        my_sub_panel.clear()
        create_games()

    my_sub_panel <= html.H3("Création des parties")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter pour créer des parties")
        return

    pseudo = storage['PSEUDO']

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

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

    input_file = html.INPUT(type="file")
    form <= input_file
    form <= html.BR()

    form <= html.BR()

    input_create_games = html.INPUT(type="submit", value="créer les parties")
    input_create_games.bind("click", create_games_callback)
    form <= input_create_games

    my_sub_panel <= form


my_panel = html.DIV()
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="tournament")
my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'créer les parties':
        create_games()

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


def render(panel_middle):
    """ render """

    # always back to top
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

    load_option(None, item_name_selected)
    panel_middle <= my_panel
