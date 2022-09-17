""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, alert, ajax, window  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import config

OPTIONS = ['sélectionner un événement', 'm\'inscrire', 'participants à l\'événement', 'créer un événement', 'éditer l\'événement', 'supprimer l\'événement']


MAX_LEN_EVENT_NAME = 50

# global data below

# loaded in render()
EVENT_ID = None


def get_event_data(event_id):
    """ get_event_data : returns empty dict if problem """

    event_dict = {}

    def reply_callback(req):
        nonlocal event_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des informations de l'événement: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des informations de l'événement : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        event_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/events/{event_id}"

    # getting tournament data : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return event_dict


def get_events_data():
    """ get_events_data : returnes empty dict if problem """

    events_dict = {}

    def reply_callback(req):
        nonlocal events_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des événements : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des événements : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        events_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/events"

    # getting tournaments list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return events_dict


def select_event():
    """ select_event """

    def select_event_callback(_, input_event, event_data_sel):
        """ select_event_callback """

        event_name = input_event.value
        event_id = event_data_sel[event_name]
        storage['EVENT_ID'] = event_id

        InfoDialog("OK", f"Evenement sélectionné : {event_name}", remove_after=config.REMOVE_AFTER)

        # back to where we started
        MY_SUB_PANEL.clear()
        select_event()

    MY_SUB_PANEL <= html.H3("Sélection d'un événement")

    events_data = get_events_data()
    if not events_data:
        alert("Pas d'événement de prévu pour le moment")
        return

    select_table = html.TABLE()

    # create a table to pass information about selected game
    event_data_sel = {v['name']: k for k, v in events_data.items()}

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_event = html.LEGEND("nom", title="Sélection de l'événement")
    fieldset <= legend_event
    input_event = html.SELECT(type="select-one", value="")
    event_list = sorted([g['name'] for g in events_data.values()], key=lambda n: n.upper())
    for event in event_list:
        option = html.OPTION(event)
        event_id = event_data_sel[event]
        if 'EVENT_ID' in storage:
            if storage['EVENT_ID'] == event_id:
                option.selected = True
        input_event <= option
    fieldset <= input_event
    form <= fieldset

    form <= html.BR()

    input_select_event = html.INPUT(type="submit", value="sélectionner cet événement")
    input_select_event.bind("click", lambda e, ie=input_event, eds=event_data_sel: select_event_callback(e, ie, eds))
    form <= input_select_event

    col = html.TD()
    col <= form
    col <= html.BR()

    row = html.TR()
    row <= col

    select_table <= row

    sub_panel = html.DIV(id='sub_panel')
    sub_panel <= select_table

    MY_SUB_PANEL <= sub_panel


def register_event():
    """ register_event """

    def register_event_callback(_):
        """ register_event_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'inscription à l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'inscription à l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'inscription a été prise en compte : {messages}", remove_after=config.REMOVE_AFTER)

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/registrations/{event_id}"

        json_dict = {
            'delete': False,
        }

        # registrating to an event : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started (actually to joiners)
        MY_SUB_PANEL.clear()
        event_joiners()

    MY_SUB_PANEL <= html.H3("Inscription à un événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    if 'EVENT_ID' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    event_id = storage['EVENT_ID']
    event_dict = get_event_data(event_id)

    form = html.FORM()

    input_register_event = html.INPUT(type="submit", value="s'inscrire à l'événement")
    input_register_event.bind("click", register_event_callback)
    form <= input_register_event

    name = event_dict['name']
    MY_SUB_PANEL <= html.DIV(f"Evenement {name}", Class='note')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= form


def event_joiners():
    """ event_joiners """

    MY_SUB_PANEL <= html.H3("Participants à un événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    MY_SUB_PANEL <= "TODO"


def create_event():
    """ create_event """

    def create_event_callback(_):
        """ create_event_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la création de l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la création de l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'événement a été créé : {messages}", remove_after=config.REMOVE_AFTER)

        name = input_name.value

        if not name:
            alert("Nom d'événement manquant")
            MY_SUB_PANEL.clear()
            create_event()
            return

        if len(name) > MAX_LEN_EVENT_NAME:
            alert("Nom d'événement trop long")
            MY_SUB_PANEL.clear()
            create_event()
            return

        json_dict = {
            'name': name,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/events"

        # creating an event : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        create_event()

    MY_SUB_PANEL <= html.H3("Création d'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    form = html.FORM()

    form <= html.DIV("Pas d'espaces ni de tirets dans le nom de l'événement", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom de l'événement (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value="", size=MAX_LEN_EVENT_NAME)
    fieldset <= input_name
    form <= fieldset

    form <= html.BR()

    input_create_event = html.INPUT(type="submit", value="créer l'événement")
    input_create_event.bind("click", create_event_callback)
    form <= input_create_event

    MY_SUB_PANEL <= form


def edit_event():
    """ edit_event """

    MY_SUB_PANEL <= html.H3("Edition d'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    MY_SUB_PANEL <= "TODO"


def delete_event():
    """ delete_event """

    def cancel_delete_event_callback(_, dialog):
        """ cancel_delete_event_callback """
        dialog.close()

    def delete_event_callback(_, dialog):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppresssion de l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppresssion de l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'événement a été supprimé : {messages}", remove_after=config.REMOVE_AFTER)

            del storage['EVENT_ID']

            # back to where we started (actually to creation)
            MY_SUB_PANEL.clear()
            select_event()

        dialog.close()

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/events/{event_id}"

        # deleting event : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_event_callback_confirm(_):
        """ delete_event_callback_confirm """

        dialog = Dialog("On supprime vraiment l'événement ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog: delete_event_callback(e, d))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_delete_event_callback(e, d))

        # back to where we started
        MY_SUB_PANEL.clear()
        delete_event()

    MY_SUB_PANEL <= html.H3("Suppression de l'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    if 'EVENT_ID' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    event_id = storage['EVENT_ID']
    event_dict = get_event_data(event_id)

    form = html.FORM()

    input_delete_event = html.INPUT(type="submit", value="supprimer l'événement")
    input_delete_event.bind("click", delete_event_callback_confirm)
    form <= input_delete_event

    name = event_dict['name']
    MY_SUB_PANEL <= html.DIV(f"Evenement {name}", Class='note')
    MY_SUB_PANEL <= html.BR()
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

MY_SUB_PANEL = html.DIV(id="events")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'sélectionner un événement':
        select_event()
    if item_name == 'm\'inscrire':
        register_event()
    if item_name == 'participants à l\'événement':
        event_joiners()
    if item_name == 'créer un événement':
        create_event()
    if item_name == 'éditer l\'événement':
        edit_event()
    if item_name == 'supprimer l\'événement':
        delete_event()

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

    global EVENT_ID
    EVENT_ID = None
    if 'EVENT_ID' in storage:
        EVENT_ID = storage['EVENT_ID']

    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
