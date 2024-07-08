""" create """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from time import time

from browser import html, alert, ajax, window, timer  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import mydialog
import config
import common
import interface
import mapping
import memoize
import scoring


OPTIONS = {
    'Editer les glorieux': "Changer nouvelles du site pour le createur (les glorieux)",
    'Appariements de tournoi': "Créer un fichier CSV par exemple à partir d'une liste de joueurs",
    'Créer plusieurs parties': "Créer des parties à partir d'un fichier CSV",
    'Explications': "Explications sur la création de parties à partir d'un fichier CSV",
    'Résultats du tournoi': "Résultats détaillé du tournoi de la partie sélectionnée sans anonymat",
    'Mur de la honte': "Les joueurs qui ont abandonné une partie"
}

MAX_NUMBER_GAMES = 200

MAX_LEN_GAME_NAME = 50


def get_quitters_data():
    """ get_quitters_data : returns empty dict on error """

    quitters_data = {}

    def reply_callback(req):
        nonlocal quitters_data
        req_result = loads(req.text)
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

    # we do not really care if a hacker manages to get this information without being a creator
    # getting allocations : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return quitters_data


def get_tournament_players_data(tournament_id):
    """ get_tournament_players_data : can return empty dict  (all games anonymous) """

    tournament_players_dict = {}

    def reply_callback(req):
        nonlocal tournament_players_dict
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs des parties du tournoi : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs des partie du tournoi : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        tournament_players_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/tournament-allocations/{tournament_id}"

    # getting tournament allocation : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return tournament_players_dict


def change_glorious():
    """ change_glorious """

    def change_glorious_callback(ev):  # pylint: disable=invalid-name
        """ change_glorious_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du contenu des glorieux : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du contenu des glorieux : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Les glorieux ont été changées : {messages}")

        ev.preventDefault()

        glory_content = input_glory_content.value
        if not glory_content:
            alert("Contenu glorieux manquant")
            return

        json_dict = {
            'topic': 'glory',
            'content': glory_content
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/news"

        # changing news : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_glorious()

    MY_SUB_PANEL <= html.H3("Editer les glorieux")

    if not common.check_creator():
        alert("Pas le bon compte (pas créateur)")
        return

    news_content_table_loaded = common.get_news_content()
    if not news_content_table_loaded:
        return

    glory_content_loaded = news_content_table_loaded['glory']

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_glory_content = html.LEGEND("glorieux", title="Saisir le nouveau contenu des glorieux")
    fieldset <= legend_glory_content
    input_glory_content = html.TEXTAREA(type="text", rows=20, cols=100)
    input_glory_content <= glory_content_loaded
    fieldset <= input_glory_content
    form <= fieldset

    form <= html.BR()

    input_change_glory_content = html.INPUT(type="submit", value="Mettre à jour", Class='btn-inside')
    input_change_glory_content.bind("click", change_glorious_callback)
    form <= input_change_glory_content
    form <= html.BR()

    MY_SUB_PANEL <= form


def check_batch(current_pseudo, games_to_create, number_players_expected):
    """ check_batch """

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
                alert(f"Il y a un nom de joueur vide dans le fichier en ligne {ligne + 1}")
                return False

            if player_name not in players_set:

                if player_name not in already_warned:
                    alert(f"Il semble que le joueur '{player_name}' n'existe pas sur le site")
                    already_warned.add(player_name)
                    error = True

    # check all games have same number of roles as variant expects (fatal)
    for game_name, allocations in games_to_create.items():
        number_players = len(allocations) - 1
        if number_players != number_players_expected:
            alert(f"Il semble que la partie {game_name} n'a pas le nombre de joueurs attendu par la variante")
            return False

    # check the players in games are not duplicated (fatal)
    for game_name, allocations in games_to_create.items():
        if len(set(allocations.values())) != len(allocations.values()):
            alert(f"Il semble que la partie {game_name} n'a pas des joueurs tous différents")
            return False

    # Note : we do not check players are in same number of games

    # game master has to be pseudo
    for game_name, allocations in games_to_create.items():
        if allocations[0] != current_pseudo:
            alert(f"Vous n'êtes pas l'arbitre indiqué dans le fichier pour la partie {game_name}. Il faudra donc demander à l'arbitre en question de venir lui-même sur le site réaliser la création de ses parties")
            error = True

    return not error


# timer for repeating attemps to create game
CREATE_RETRY_PERIOD_MILLISEC = 500


def perform_batch(current_pseudo, current_game_name, games_to_create_data):
    """ perform_batch """

    games_created_so_far = 0

    def create_game(current_game_name, game_to_create_name):
        """ create_game """

        create_status = None

        def reply_callback(req):
            nonlocal create_status
            req_result = loads(req.text)
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
        time_stamp_now = time()
        deadline = int(time_stamp_now)
        json_dict['deadline'] = deadline

        # obviously different state (starting)
        json_dict['current_state'] = 0
        json_dict['current_advancement'] = 0

        # obviously different description
        time_stamp_now = time()
        time_creation = mydatetime.fromtimestamp(time_stamp_now)
        time_creation_str = mydatetime.strftime(*time_creation)
        variant = json_dict['variant']
        scoring_used = json_dict['scoring']
        description = f"Partie créée par batch (sur le modèle de {current_game_name}) le {time_creation_str} par {current_pseudo} variante {variant}. Scorage {scoring_used}."
        json_dict['description'] = description

        # logically : manual allocation (otherwise at start random allocation will spoil csv file allocation)
        json_dict['manual'] = int(True)

        # remove these two so that they get copied from their xxx_game clone
        del json_dict['nopress_current']
        del json_dict['nomessage_current']
        del json_dict['finished']
        del json_dict['soloed']

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games"

        # creating a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return create_status

    def put_player_in_game(game_name, player_name):
        """ put_player_in_game """

        put_player_in_game_status = None

        def reply_callback(req):
            nonlocal put_player_in_game_status
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la mise d'un joueur dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise d'un joueur dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                put_player_in_game_status = False
                return

            put_player_in_game_status = True

        game_id_int = common.get_game_id(game_name)
        if not game_id_int:
            alert(f"Erreur chargement identifiant partie {game_name}. Cette partie existe ?")
            return False

        json_dict = {
            'game_id': game_id_int,
            'player_pseudo': player_name,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # putting a player in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return put_player_in_game_status

    def allocate_role(game_name, player_pseudo, role_id):
        """ allocate_role """

        allocate_role_status = None

        def reply_callback(req):
            nonlocal allocate_role_status
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'allocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'allocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                allocate_role_status = False
                return

            allocate_role_status = True

        game_id_int = common.get_game_id(game_name)
        if not game_id_int:
            alert(f"Erreur chargement identifiant partie {game_name}. Cette partie existe ?")
            return False

        json_dict = {
            'game_id': game_id_int,
            'role_id': role_id,
            'player_pseudo': player_pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return allocate_role_status

    def create_one():
        """ will create a game : called on timer """

        nonlocal games_created_so_far

        # no more game : done
        if not games_to_create_data:
            timer.clear_interval(create_refresh_timer)
            if games_created_so_far == number_games:
                alert(f"Les {number_games} parties du tournoi ont bien été créée(s) et peuplée(s).\nTout s'est bien passé.\nIncroyable, non ?")
            return

        # pop a game
        game_to_create_name = list(games_to_create_data.keys())[0]
        game_to_create_data = games_to_create_data[game_to_create_name]
        del games_to_create_data[game_to_create_name]

        # create this game
        create_one_status = create_game(current_game_name, game_to_create_name)
        if not create_one_status:
            alert(f"Echec à la création de la partie {game_to_create_name}")
            timer.clear_interval(create_refresh_timer)
            return

        # put players in this game
        for role_id, player_name in game_to_create_data.items():
            # game master already there
            if role_id == 0:
                continue
            # put player
            create_one_status = put_player_in_game(game_to_create_name, player_name)
            if not create_one_status:
                alert(f"Echec à l'appariement de {player_name} dans la partie {game_to_create_name}")
                timer.clear_interval(create_refresh_timer)
                return

        # allocate roles to players
        for role_id, player_name in game_to_create_data.items():
            # game master already has its role
            if role_id == 0:
                continue
            create_one_status = allocate_role(game_to_create_name, player_name, role_id)
            if not create_one_status:
                alert(f"Echec à l'attribution du role numéro {role_id} à {player_name} dans la partie {game_to_create_name}")
                timer.clear_interval(create_refresh_timer)
                return

        # update progress bar
        games_created_so_far += 1
        # was not possible to have a progress bar for some reason
        mydialog.InfoDialog("Information", f"Partie {game_to_create_name} ({games_created_so_far}/{number_games}) créé et peuplée..")

    # will increment
    games_created_so_far = 0

    number_games = len(games_to_create_data)
    create_refresh_timer = timer.set_interval(create_one, CREATE_RETRY_PERIOD_MILLISEC)


def info_allocate():
    """ info_allocate """

    MY_SUB_PANEL <= html.H3("Problème de l'allocation des pays")

    information = ""
    information += "Le site peut vous fournir une ressource pour vous aider à créer le fichier CSV pour votre tournoi. "
    information += "Ce script permet de passer de la liste des joueurs (par exemple extraire de la page des inscriptions à l'événement) "
    information += "à un fichier à fournir en entrée à l'outil du site permettant la création automatique des parties..."

    MY_SUB_PANEL <= information

    MY_SUB_PANEL <= html.P()

    MY_SUB_PANEL <= "Prérequis : executer le script sur un ordinateur local disposant d'un interprêteur PYTHON"

    MY_SUB_PANEL <= html.P()

    link61 = html.A(href="./docs/Fichier_tournoi.pdf", target="_blank")
    link61 <= "Explications sur comment allouer les joueurs dans les parties d'un tournoi de taille quelconque"
    MY_SUB_PANEL <= link61

    MY_SUB_PANEL <= html.P()

    link62 = html.A(href="./scripts/allocate.py", target="_blank")
    link62 <= "Téléchargement du script PYTHON à utiliser pour réaliser cette allocation (lire le document au préalable)"
    MY_SUB_PANEL <= link62


# so that we do not too much repeat the selected game
WARNED = False


def create_many_games():
    """ create_many_games """

    global WARNED

    def create_games_callback(ev, input_file):  # pylint: disable=invalid-name
        """ create_games_callback """

        def onload_callback(_):
            """ onload_callback """

            def cancel_create_games_callback(_, dialog):
                """ cancel_create_games_callback """
                dialog.close(None)

            def create_games_callback2(_, dialog):
                """ create_games_callback2 """
                dialog.close(None)
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
            if check_batch(pseudo, games_to_create, number_players_expected):
                dialog = mydialog.Dialog("On créé vraiment toutes ces parties ?", ok_cancel=True)
                dialog.ok_button.bind("click", lambda e, d=dialog: create_games_callback2(e, d))
                dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_create_games_callback(e, d))

        ev.preventDefault()

        if not input_file.files:
            alert("Pas de fichier")

            # back to where we started
            MY_SUB_PANEL.clear()
            create_many_games()
            return

        # Create a new DOM FileReader instance
        reader = window.FileReader.new()
        # Extract the file
        file_name = input_file.files[0]
        # Read the file content as text
        reader.bind("load", onload_callback)
        reader.readAsText(file_name)

        # back to where we started
        MY_SUB_PANEL.clear()
        create_many_games()

    MY_SUB_PANEL <= html.H3("Création des parties")

    if not common.check_creator():
        alert("Pas le bon compte (pas créateur)")
        return

    pseudo = storage['PSEUDO']

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if not WARNED:
        alert(f"La partie modèle est le partie '{game}'. Vérifiez que cela convient !")
        WARNED = True

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("Ficher CSV")
    fieldset <= legend_name
    form <= fieldset

    input_file = html.INPUT(type="file", accept='.csv', Class='btn-inside')
    form <= input_file
    form <= html.BR()
    form <= html.BR()

    input_create_games = html.INPUT(type="submit", value="Créer les parties", Class='btn-inside')
    input_create_games.bind("click", lambda e, i=input_file: create_games_callback(e, i))
    form <= input_create_games

    MY_SUB_PANEL <= form

    # just to  get 'number_players_expected'
    variant_name_loaded = storage['GAME_VARIANT']
    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    number_players_expected = variant_content_loaded['roles']['number']


def explain_stuff():
    """ explain_stuff """

    if not common.check_creator():
        alert("Pas le bon compte (pas créateur)")
        return

    MY_SUB_PANEL <= html.H3("Spécifications  du fichier CSV")

    information1 = html.DIV()
    information1 <= "Vous devez composer un fichier CSV"
    information1 <= html.BR()
    information1 <= "Une ligne par partie"
    information1 <= html.BR()
    information1 <= "Sur chaque ligne, séparés pas des virgules (ou des points-virgules):"
    items = html.UL()
    items <= html.LI("le nom de la partie")
    items <= html.LI("l'arbitre de la partie (cette colonne est redondante : c'est forcément votre pseudo)")
    items <= html.LI("le premier joueur de la partie")
    items <= html.LI("le deuxième joueur de la partie")
    items <= html.LI("etc....")
    information1 <= items
    information1 <= "Utilisez l'ordre suivant pour la variante standard : Angleterre, France, Allemagne, Italie, Autriche, Russie, Turquie"
    information1 <= html.BR()
    information1 <= "Il est impossible d'attribuer l'arbitrage d'une partie à un autre joueur, donc vous pouvez mettre dans le fichier un arbitre différent à des fins de vérification mais la création des parties n'aura pas lieu."
    information1 <= html.BR()
    information1 <= "Les parties copieront un maximum de propriétés de la partie modèle que vous avez préalablement sélectionnée, dont la description - donc pensez bien à la modifier dans la partie modèle avant de créer les parties..."

    MY_SUB_PANEL <= information1

    MY_SUB_PANEL <= html.H3("Rappel de la procédure pour les arbitres assistants")

    information2 = html.DIV()
    modus = html.OL()
    modus <= html.LI("Vous avez dû recevoir un fichier csv avec les donnees de vos parties à importer.")
    modus <= html.LI("Allez sur le site. Choisissez le menu “Rejoindre une partie” sous menu “Sélectionner une partie”. Restreignez le choix dans la fenêtre “sélection de l'état” aux parties “distinguées”. Eventuellement filtrez aussi sur la variante. Sélectionnez finalement la partie modèle (T-BLITZ par exemple). Cette etape est pertinente, car c’est cette partie qui definira presque toutes les caracteristiques des parties que vous allez créer.")
    modus <= html.LI("Allez dans le menu “Création”. Si vous ne voyez pas le menu, demandez les droits à l'administrateur")
    modus <= html.LI("Cliquez sur “parcourir” pour choisir le fichier et selectionnez le fichier csv que vous avez reçu")
    modus <= html.LI("Confirmez la création des parties...")
    modus <= html.LI("Si votre connexion est lente, ignorez les messages bizarres comme par exemple “le navigateur attend une reponse du site”. C’est long, ça mouline, mais à la fin ça doit aboutir.")
    modus <= html.LI("Si les parties se sont créées normalement, un sympathique message comme quoi tout s'est bien passé apparaît.")
    modus <= html.LI("Les parties sont créés mais dans l'état “en attente”")
    modus <= html.LI("Allez dans le menu “mes parties”, cliquez sur “en attente”, cliquez sur le bouton “basculer en mode avec colonnes action” si besoin.")
    modus <= html.LI("Démarrez chacune des parties nouvelement créée une par une en cliquant sur les fusées.")
    modus <= html.LI("Les parties sont démarrées ! Félicitations !")
    modus <= html.LI("Vous pouvez mettre un message de bienvenue dans chaque partie en passant par le menu “Déclarer“")
    modus <= html.LI("En cas de souci contactez l'administateur")
    information2 <= modus

    MY_SUB_PANEL <= information2


def tournament_result():
    """ tournament_result """

    MY_SUB_PANEL <= html.H3("Résultats intermédiaires du tournoi")

    if not common.check_creator():
        alert("Pas le bon compte (pas créateur)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    tournament_dict = common.get_tournament_data(game)
    if not tournament_dict:
        alert("Pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    tournament_name = tournament_dict['name']
    tournament_id = tournament_dict['identifier']
    games_in = tournament_dict['games']

    MY_SUB_PANEL <= html.DIV("Attention : si des parties sont anonymes le classement est incomplet", Class='important')
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= f"Tournoi concerné : {tournament_name}"
    MY_SUB_PANEL <= html.BR()

    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement info joueurs")
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    tournament_players_dict = get_tournament_players_data(tournament_id)

    gamerole2pseudo = {(int(g), r): id2pseudo[int(p)] for g, d in tournament_players_dict.items() for p, r in d.items()}

    # =====
    # points
    # =====

    # build dict of positions
    positions_dict_loaded = common.tournament_position_reload(tournament_id)
    if not positions_dict_loaded:
        alert("Erreur chargement positions des parties du tournoi")
        return

    points = {}

    for game_id_str, data in games_dict.items():

        game_id = int(game_id_str)

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
        position_loaded = positions_dict_loaded[game_id_str]

        position_data = mapping.Position(position_loaded, variant_data)
        ratings = position_data.role_ratings()

        # scoring
        game_scoring = data['scoring']
        centers_variant = variant_data.number_centers()
        score_table = scoring.scoring(game_scoring, centers_variant, ratings)

        rolename2num = {variant_data.role_name_table[r]: n for n, r in variant_data.roles.items()}

        for role_name, score in score_table.items():
            role_num = rolename2num[role_name]
            pseudo = gamerole2pseudo.get((game_id, role_num), None)
            if pseudo:
                if pseudo not in points:
                    points[pseudo] = score
                else:
                    points[pseudo] += score

    # =====
    # incidents
    # =====

    # get the actual incidents of the tournament
    tournament_incidents = common.tournament_incidents_reload(tournament_id)
    # there can be no incidents (if no incident of failed to load)

    count = {}
    for game_id, role_num, _, duration, _ in tournament_incidents:
        pseudo = gamerole2pseudo.get((game_id, role_num), None)
        if pseudo:
            if pseudo not in count:
                count[pseudo] = []
            count[pseudo].append(duration)

    recap_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['rang', 'pseudo', 'score', 'retards']:
        col = html.TD(field)
        thead <= col
    recap_table <= thead

    rank = 1
    for pseudo, score in sorted(points.items(), key=lambda p: float(p[1]), reverse=True):
        row = html.TR()

        col = html.TD(rank)
        row <= col

        col = html.TD(pseudo)
        row <= col

        col = html.TD(f"{float(score):.2f}")
        row <= col

        incidents_list = count.get(pseudo, [])
        col = html.TD(" ".join([f"{i}" for i in incidents_list]))
        row <= col

        recap_table <= row
        rank += 1

    incident_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'retards']:
        col = html.TD(field)
        thead <= col
    incident_table <= thead

    for pseudo, incidents_list in sorted(count.items(), key=lambda p: len(p[1]), reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        incidents_list = count.get(pseudo, [])
        col = html.TD(" ".join([f"{i}" for i in incidents_list]))
        row <= col

        incident_table <= row

    # =====
    # incidents2
    # =====

    # get the actual incidents of the tournament
    tournament_incidents2 = common.tournament_incidents2_reload(tournament_id)
    # there can be no incidents (if no incident of failed to load)

    count = {}
    for game_id, role_num, _, _ in tournament_incidents2:
        pseudo = gamerole2pseudo.get((game_id, role_num), None)
        if pseudo:
            if pseudo not in count:
                count[pseudo] = 0
            count[pseudo] += 1

    incident_table2 = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'Nombre de Désordres Civils']:
        col = html.TD(field)
        thead <= col
    incident_table2 <= thead

    for pseudo in sorted(count, key=lambda p: count[p], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        nb_dc = count[pseudo]
        col = html.TD(nb_dc)
        row <= col

        incident_table2 <= row

    MY_SUB_PANEL <= html.H4("Classement")
    MY_SUB_PANEL <= recap_table

    MY_SUB_PANEL <= html.H4("Retards")
    MY_SUB_PANEL <= incident_table

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées", Class='note')

    MY_SUB_PANEL <= html.H4("Désordres Civils")
    MY_SUB_PANEL <= incident_table2


def show_game_quitters():
    """ show_game_quitters """

    if not common.check_creator():
        alert("Pas le bon compte (pas créateur)")
        return

    MY_SUB_PANEL <= html.H3("Les joueurs qui ont abandonné une partie")

    # get the games
    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

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

    for game_id, _, player_id, time_stamp in sorted(quitters_data, key=lambda i: i[3], reverse=True):

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

ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

MY_SUB_PANEL = html.DIV(id="create")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Editer les glorieux':
        change_glorious()
    if item_name == 'Appariements de tournoi':
        info_allocate()
    if item_name == 'Créer plusieurs parties':
        create_many_games()
    if item_name == 'Explications':
        explain_stuff()
    if item_name == 'Résultats du tournoi':
        tournament_result()
    if item_name == 'Mur de la honte':
        show_game_quitters()

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name, legend in OPTIONS.items():

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, title=legend, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item


# starts here


def render(panel_middle):
    """ render """

    global WARNED
    WARNED = False

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
