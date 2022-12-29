""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common


OPTIONS = ['Rejoindre la partie', 'Quitter la partie', 'Déplacer des joueurs', 'Prendre l\'arbitrage', 'Démissionner de l\'arbitrage']


def get_game_allocated_players(game_id):
    """ get_available_players returns a tuple game_master + players """

    game_master_id = None
    players_allocated_list = None
    players_assigned_list = None

    def reply_callback(req):
        nonlocal game_master_id
        nonlocal players_allocated_list
        nonlocal players_assigned_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        game_masters_list = [int(k) for k, v in req_result.items() if v == 0]
        game_master_id = game_masters_list.pop()
        players_allocated_list = [int(k) for k, v in req_result.items() if v == -1]
        players_assigned_list = [int(k) for k, v in req_result.items() if v > 0]

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-allocations/{game_id}"

    # get players allocated to game : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return game_master_id, players_allocated_list, players_assigned_list


def join_game():
    """ join_game : the first way of joining a game """

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
                join_game()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez rejoint la partie : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            join_game()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # adding allocation : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Se mettre dans la partie")

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

    form = html.FORM()

    input_join_game = html.INPUT(type="submit", value="Rejoindre la partie sélectionnée")
    input_join_game.bind("click", join_game_callback)
    form <= input_join_game

    MY_SUB_PANEL <= form


def quit_game():
    """ quit_game """

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
                quit_game()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez quitté la partie : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            quit_game()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # should be a delete but body in delete requests is more or less forbidden
        # quitting a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Se retirer de la partie")

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

    form = html.FORM()

    input_quit_game = html.INPUT(type="submit", value="Quitter la partie sélectionnée")
    input_quit_game.bind("click", quit_game_callback)
    form <= input_quit_game

    MY_SUB_PANEL <= form


def move_players_in_game():
    """ move_players_in_game """

    def put_in_game_callback(ev):  # pylint: disable=invalid-name
        """ put_in_game_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la mise d'un joueur dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise d'un joueur dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                move_players_in_game()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur a été mis dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            move_players_in_game()

        ev.preventDefault()

        player_pseudo = input_incomer.value

        json_dict = {
            'game_id': game_id,
            'player_pseudo': player_pseudo,
            'pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # putting a player in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_from_game_callback(ev):  # pylint: disable=invalid-name
        """remove_from_game_callback"""

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au retrait d'un joueur de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au retrait d'un joueur de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                move_players_in_game()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur a été retiré de la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            move_players_in_game()

        ev.preventDefault()

        player_pseudo = input_outcomer.value

        json_dict = {
            'game_id': game_id,
            'player_pseudo': player_pseudo,
            'pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # removing a player from a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Mettre dans ou enlever des joueurs de la partie")

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

    players_dict = common.get_players()
    if not players_dict:
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    # from game id and token get role_id of player

    role_id = common.get_role_allocated_to_player_in_game(game_id)
    if role_id != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        return

    allocated = get_game_allocated_players(game_id)
    if allocated is None:
        return
    game_master_id, players_allocated_ids_list, players_assigned_ids_list = allocated

    players_allocated_list = [id2pseudo[i] for i in list(players_allocated_ids_list)]
    players_assigned_list = [id2pseudo[i] for i in list(players_assigned_ids_list)]

    form = html.FORM()

    # ---

    fieldset = html.FIELDSET()
    legend_incomer = html.LEGEND("Entrant", title="Sélectionner le joueur à mettre dans la partie")
    fieldset <= legend_incomer

    # all players can come in
    possible_incomers = set(players_dict.keys())

    # not those already in
    possible_incomers -= set(players_allocated_list)
    possible_incomers -= set(players_assigned_list)

    # not the operator
    possible_incomers -= set([pseudo])

    # not the gm of the game
    possible_incomers -= set([game_master_id])

    input_incomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_incomers, key=lambda pi: pi.upper()):
        option = html.OPTION(play_pseudo)
        input_incomer <= option

    fieldset <= input_incomer
    form <= fieldset

    form <= html.BR()

    input_put_in_game = html.INPUT(type="submit", value="Mettre dans la partie sélectionnée")
    input_put_in_game.bind("click", put_in_game_callback)
    form <= input_put_in_game

    form <= html.BR()
    form <= html.BR()

    # ---

    fieldset = html.FIELDSET()
    fieldset <= html.LEGEND("Ont un rôle : ")
    fieldset <= html.DIV(" ".join(sorted(list(set(players_assigned_list)), key=lambda p: p.upper())), Class='note')
    form <= fieldset

    form <= html.BR()

    fieldset = html.FIELDSET()
    fieldset <= html.LEGEND("Sont en attente : ")
    fieldset <= html.DIV(" ".join(sorted(list(set(players_allocated_list)), key=lambda p: p.upper())), Class='note')
    form <= fieldset

    # ---
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_outcomer = html.LEGEND("Sortant", title="Sélectionner le joueur à retirer de la partie")
    fieldset <= legend_outcomer

    # players can come out are the ones not assigned
    possible_outcomers = players_allocated_list

    input_outcomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_outcomers):
        option = html.OPTION(play_pseudo)
        input_outcomer <= option

    fieldset <= input_outcomer
    form <= fieldset

    form <= html.BR()

    input_remove_from_game = html.INPUT(type="submit", value="Retirer de la partie sélectionnée")
    input_remove_from_game.bind("click", remove_from_game_callback)
    form <= input_remove_from_game

    MY_SUB_PANEL <= form


def take_mastering_game():
    """ take_mastering_game """

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
                take_mastering_game()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez pris l'arbitrage de la partie : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            take_mastering_game()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'role_id': 0,
            'player_pseudo': pseudo,
            'pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # taking game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Prendre l'arbitrage de la partie")

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

    form = html.FORM()

    input_join_game = html.INPUT(type="submit", value="Prendre l'arbitrage de la partie sélectionnée")
    input_join_game.bind("click", take_mastering_game_callback)
    form <= input_join_game

    MY_SUB_PANEL <= form


def quit_mastering_game():
    """ quit_mastering_game """

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
                quit_mastering_game()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez quitté l'arbitrage de la partie : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            quit_mastering_game()

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'role_id': 0,
            'player_pseudo': pseudo,
            'pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # giving up game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Quitter l'arbitrage de la partie")

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

    form = html.FORM()

    input_join_game = html.INPUT(type="submit", value="Démissionner de l'arbitrage de la partie sélectionnée")
    input_join_game.bind("click", quit_mastering_game_callback)
    form <= input_join_game

    MY_SUB_PANEL <= form
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    warning = html.DIV("Attention : Créer une partie anonyme, se retirer de l'arbitrage après avoir consulté la liste des joueurs et ensuite jouer dans cette partie... est considéré comme tricher !", Class='note')
    MY_SUB_PANEL <= warning


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

MY_SUB_PANEL = html.DIV(id="pairing")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Rejoindre la partie':
        join_game()
    if item_name == 'Quitter la partie':
        quit_game()
    if item_name == 'Déplacer des joueurs':
        move_players_in_game()
    if item_name == 'Prendre l\'arbitrage':
        take_mastering_game()
    if item_name == 'Démissionner de l\'arbitrage':
        quit_mastering_game()

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


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
