""" create """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time

from browser import html, alert, ajax, window  # pylint: disable=import-error
from browser.widgets.dialog import Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common
import interface
import mapping


OPTIONS = ['Créer plusieurs parties', 'Les lâcheurs']

MAX_NUMBER_GAMES = 200

MAX_LEN_GAME_NAME = 50

INPUT_FILE = None


def check_creator(pseudo):
    """ check_creator """

    creator_list = common.get_creators()
    if pseudo not in creator_list:
        return False

    return True


def get_quitters_data():
    """ get_quitters_data : returns empty dict on error """

    quitters_data = {}

    def reply_callback(req):
        nonlocal quitters_data
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des abandons : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des abandons : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        quitters_data = req_result['dropouts']

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-game-dropouts"

    # getting allocations : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return quitters_data


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

    # Note : we do not check players are in same number of games because games may be split amongst several masters

    # game master has to be pseudo
    for game_name, allocations in games_to_create.items():
        if allocations[0] != current_pseudo:
            alert(f"Vous n'êtes pas l'arbitre indiqué dans le fichier pour la partie {game_name}. Il faudra donc demander à l'arbitre en question de venir lui-même sur le site réaliser la création de ses parties")
            error = True

    return not error


def perform_batch(current_pseudo, current_game_name, games_to_create_data):
    """ perform_batch """

    def create_game(current_pseudo, current_game_name, game_to_create_name):
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

        # obviously different deadline (set it to now)
        timestamp = time.time()
        deadline = int(timestamp)
        json_dict['deadline'] = deadline

        # obviously different state (starting)
        json_dict['current_state'] = 0
        json_dict['current_advancement'] = 0

        # logically : manual allocation (otherwise at start random allocation will spoil csv file allocation)
        json_dict['manual'] = int(True)

        # remove these two so that they get copied from their xxx_game clone
        del json_dict['nopress_current']
        del json_dict['nomessage_current']

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
        status = create_game(current_pseudo, current_game_name, game_to_create_name)
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
                role_name = variant_data.role_name_table[role]
                alert(f"Echec à l'attribution du role {role_name} à {player_name} dans la partie {game_to_create_name}")
                return

    nb_parties = len(games_to_create_data)
    alert(f"Les {nb_parties} parties du tournoi ont bien été créée. Tout s'est bien passé. Incroyable, non ?")


# so that we do not too much repeat the selected game
PREV_GAME = ""


def create_many_games():
    """ create_many_games """

    global PREV_GAME

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
                perform_batch(pseudo, game, games_to_create)

            games_to_create = {}

            content = reader.result
            lines = content.splitlines()

            if len(lines) > MAX_NUMBER_GAMES:
                alert(f"Il y a trop de parties dans le fichier. La limite est {MAX_NUMBER_GAMES}")
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

                # create players dict
                players_dict = {n: tab[n + 1] for n in range(len(tab) - 1)}

                # check for duplicated games
                if players_dict in games_to_create.values():
                    alert(f"La partie {game_name} est identique à une précédente")
                    return

                # create dictionnary
                games_to_create[game_name] = players_dict

            if not games_to_create:
                alert("Aucune partie dans le fichier")
                return

            #  actual creation of all the games
            if check_batch(pseudo, games_to_create):
                dialog = Dialog("On créé vraiment toutes ces parties ?", ok_cancel=True)
                dialog.ok_button.bind("click", lambda e, d=dialog: create_games_callback2(e, d))
                dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_create_games_callback(e, d))

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
        reader.bind("load", onload_callback)
        reader.readAsText(file_name)

        # back to where we started
        MY_SUB_PANEL.clear()
        create_many_games()

    MY_SUB_PANEL <= html.H3("Création des parties")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_creator(pseudo):
        alert("Pas le bon compte (pas créateur)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if game != PREV_GAME:
        alert(f"La partie modèle est le partie '{game}'. Vérifiez que cela convient !")
        PREV_GAME = game

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
    information <= "Les parties copieront un maximum de propriétés de la partie modèle que vous avez préalablement sélectionnée, dont la description - donc pensez bien à la modifier dans la partie modèle avant de créer les parties..."
    information <= "Cela créée les parties, pas le tournoi. Il faut se mettre sur une partie, puis créée le tournoi et enfin insérer dedans les autres parties."
    information <= html.BR()
    information <= "Note : Soit vous utilisez comme modèle une partie existante, soit vous la créez pour l'occasion et la supprimez à la fin"

    MY_SUB_PANEL <= information
    MY_SUB_PANEL <= html.BR()

    information2 = html.DIV(Class='important')
    information2 <= "Le site peut vous fournir une ressource pour vous aider à créer le fichier CSV pour votre tournoi. Si vous êtes intéressé, allez dans accueil/coin technique"
    MY_SUB_PANEL <= information2
    MY_SUB_PANEL <= html.BR()

    form = html.FORM()

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


def show_game_quitters():
    """ show_game_quitters """

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

    # get the quitters
    quitters_data = get_quitters_data()
    # there can be no quitters

    game_quitters_table = html.TABLE()

    fields = ['player', 'game', 'date']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'player': 'joueur', 'game': 'partie', 'date': 'date'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_quitters_table <= thead

    for game_id, _, player_id, time_stamp in quitters_data:

        row = html.TR()

        player_name = players_dict[str(player_id)]['pseudo']
        col = html.TD(player_name)
        row <= col

        game_name = games_dict[str(game_id)]['name']
        col = html.TD(game_name)
        row <= col

        date_now_gmt = mydatetime.fromtimestamp(time_stamp)
        date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
        col = html.TD(date_now_gmt_str)
        row <= col

        game_quitters_table <= row

    MY_SUB_PANEL <= html.H3("Les joueurs qui ont abandonné une partie")
    MY_SUB_PANEL <= game_quitters_table


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

MY_SUB_PANEL = html.DIV(id="create")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    global PREV_GAME

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    PREV_GAME = ""

    if item_name == 'Créer plusieurs parties':
        create_many_games()
    if item_name == 'Les lâcheurs':
        show_game_quitters()

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


# starts here


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
