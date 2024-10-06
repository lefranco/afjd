""" home """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import mydatetime
import mydialog


THRESHOLD_DRIFT_ALERT_SEC = 59


OPTIONS = {
    'Messages personnels': "Lire mes messages personnels et en envoyer",
}


def private_messages(dest_user_id, initial_content):
    """ private_messages """

    def answer_callback(ev, dest_id):  # pylint: disable=invalid-name
        """ answer_callback """
        ev.preventDefault()
        MY_SUB_PANEL.clear()
        private_messages(dest_id, "")

    def suppress_message_callback(ev, message_id):  # pylint: disable=invalid-name
        """ suppress_message_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression de message dans les messages privés : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression de message dans les messages privés : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le message privé a été supprimé ! {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            private_messages(None, "")

        ev.preventDefault()

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/private-messages/{message_id}"

        # deleting a message in a game : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def add_message_callback(ev):  # pylint: disable=invalid-name
        """ add_message_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de message dans les messages privés : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de message dans les messages privés : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le message privé a été envoyé ! {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            private_messages(None, content)

        ev.preventDefault()

        content = input_message.value
        dest_user_id = players_dict[input_addressed.value]

        if not content:
            alert("Pas de contenu pour ce message !")
            MY_SUB_PANEL.clear()
            private_messages(dest_user_id, content)
            return

        if not dest_user_id:
            alert("Pas de destinataire pour ce message !")
            MY_SUB_PANEL.clear()
            private_messages(dest_user_id, content)
            return

        json_dict = {
            'dest_user_id': dest_user_id,
            'content': content
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/private-messages"

        # sending private message : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def private_messages_reload():
        """ messages_reload """

        messages = []

        def reply_callback(req):
            nonlocal messages
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des messages privés : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des messages privés : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = req_result['messages_list']

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/private-messages"

        # extracting messages from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return messages

    MY_SUB_PANEL <= html.H3("Messagerie privée")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement info joueurs")
        return

    # all players can be addressed
    possible_addressed = set(players_dict.keys())

    id2pseudo = {v: k for k, v in players_dict.items()}
    pseudo_id = players_dict[pseudo]

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre message", title="Qu'avez vous à lui dire ?")
    fieldset <= legend_declaration
    input_message = html.TEXTAREA(type="text", rows=8, cols=80)
    input_message <= initial_content
    fieldset <= input_message
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_addressee = html.LEGEND("Destinataire", title="Et à qui ?")
    fieldset <= legend_addressee
    input_addressed = html.SELECT(type="select-one", value="", Class='btn-inside')
    for addressee_pseudo in sorted(possible_addressed, key=lambda pu: pu.upper()):
        option = html.OPTION(addressee_pseudo)
        input_addressed <= option
        if dest_user_id is not None and id2pseudo[dest_user_id] == addressee_pseudo:
            option.selected = True
    fieldset <= input_addressed
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Envoyer le message", Class='btn-inside')
    input_declare_in_game.bind("click", add_message_callback)
    form <= input_declare_in_game

    # now we display messages

    messages = private_messages_reload()
    # there can be no message (if no message of failed to load)

    # sort with all that was added
    messages.sort(key=lambda m: float(m[2]), reverse=True)

    messages_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Destinataire', 'Contenu', 'Répondre', 'Supprimer']:
        col = html.TD(html.B(title))
        thead <= col
    messages_table <= thead

    for id_, from_user_id, time_stamp, dest_user_id2, read, content in messages:

        class_ = 'text'

        row = html.TR()

        col = html.TD(str(id_), Class=class_)
        row <= col

        date_desc_gmt = mydatetime.fromtimestamp(time_stamp)
        date_desc_gmt_str = mydatetime.strftime(*date_desc_gmt)

        col = html.TD(f"{date_desc_gmt_str}", Class=class_)
        row <= col

        col = html.TD(Class=class_)
        pseudo_there = id2pseudo[from_user_id]
        col <= pseudo_there
        row <= col

        col = html.TD(Class=class_)
        pseudo_there = id2pseudo[dest_user_id2]
        col <= pseudo_there
        row <= col

        col = html.TD(Class=class_)

        for line in content.split('\n'):
            # new so put in bold
            if not read:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        col = html.TD()
        if dest_user_id2 == pseudo_id:
            button = html.BUTTON("Répondre", Class='btn-inside')
            button.bind("click", lambda e, d=from_user_id: answer_callback(e, d))
            col <= button
        row <= col

        col = html.TD()
        if dest_user_id2 == pseudo_id:
            button = html.BUTTON("Supprimer", Class='btn-inside')
            button.bind("click", lambda e, i=id_: suppress_message_callback(e, i))
            col <= button
        row <= col

        messages_table <= row

    # now we can display

    # form
    MY_SUB_PANEL <= form
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # messages already
    MY_SUB_PANEL <= messages_table
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()


MAX_LEN_GAME_NAME = 50
MAX_LEN_EMAIL = 100

MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

MY_SUB_PANEL = html.DIV(id="home")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Messages personnels':
        private_messages(None, "")

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


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
