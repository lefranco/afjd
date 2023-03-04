""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common


OPTIONS = ['Appariement']


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

    if item_name == 'Appariement':
        pairing()

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
