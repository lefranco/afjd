""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, alert, ajax, window  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import config

OPTIONS = ['sélectionner un événement', 'participants à l\'événement', 'm\'inscrire', 'créer un événement', 'éditer l\'événement', 'supprimer l\'événement']


MAX_LEN_EVENT_NAME = 50
MAX_LEN_EVENT_LOCATION = 20

DEFAULT_EVENT_LOCATION = "Diplomania"

ARRIVAL = False


def set_arrival():
    """ set_arrival """
    global ARRIVAL
    ARRIVAL = True


def get_registrations(event_id):
    """ get_registrations  """

    registrations_list = []

    def reply_callback(req):
        nonlocal registrations_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des inscriptions à l'événement: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des inscriptions à l'événement : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        registrations_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/registrations/{event_id}"

    # getting registrations: no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return registrations_list


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

    # getting event data : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return event_dict


def select_event():
    """ select_event """

    def select_event_callback(_, input_event, event_data_sel):
        """ select_event_callback """

        event_name = input_event.value
        event_id = event_data_sel[event_name]
        storage['EVENT_ID'] = event_id

        InfoDialog("OK", f"Evénement sélectionné : {event_name}", remove_after=config.REMOVE_AFTER)

        # back to where we started actually joined)
        load_option(None, 'm\'inscrire')

    MY_SUB_PANEL <= html.H3("Sélection d'un événement")

    events_data = common.get_events_data()
    if not events_data:
        if 'EVENT_ID' in storage:
            del storage['EVENT_ID']
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


def event_joiners():
    """ event_joiners """

    MY_SUB_PANEL <= html.H3("Participants à un événement")

    if 'EVENT_ID' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    joiners_table = html.TABLE()

    fields = ['pseudo', 'first_name', 'family_name', 'residence', 'nationality', 'time_zone']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'first_name': 'prénom', 'family_name': 'nom', 'residence': 'résidence', 'nationality': 'nationalité', 'time_zone': 'fuseau horaire'}[field]
        col = html.TD(field_fr)
        thead <= col
    joiners_table <= thead

    code_country_table = {v: k for k, v in config.COUNTRY_CODE_TABLE.items()}

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")

    event_id = storage['EVENT_ID']
    event_dict = get_event_data(event_id)
    joiners = get_registrations(event_id)
    joiners_dict = {j: players_dict[str(j)] for j in joiners}

    count = 0
    for data in sorted(joiners_dict.values(), key=lambda g: g['pseudo'].upper()):

        if 'PSEUDO' in storage and data['pseudo'] == storage['PSEUDO']:
            colour = config.MY_RATING
        else:
            colour = None

        row = html.TR()
        for field in fields:
            value = data[field]

            if field in ['residence', 'nationality']:
                code = value
                country_name = code_country_table[code]
                value = html.IMG(src=f"./national_flags/{code}.png", title=country_name, width="25", height="17")

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }
            row <= col

        joiners_table <= row
        count += 1

    name = event_dict['name']
    description = event_dict['description']

    MY_SUB_PANEL <= html.DIV(f"Evénement {name}", Class='important')
    MY_SUB_PANEL <= html.BR()

    # description
    div_description = html.DIV(Class='information')
    for line in description.split('\n'):
        div_description <= line
        div_description <= html.BR()
    MY_SUB_PANEL <= div_description
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= joiners_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} inscrits")


def register_event():
    """ register_event """

    def register_event_callback(_, register):
        """ register_event_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status not in [200, 201]:
                if 'message' in req_result:
                    alert(f"Erreur à l'inscription à l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'inscription à l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            if register:
                InfoDialog("OK", f"L'inscription a été prise en compte : {messages}", remove_after=config.REMOVE_AFTER)
            else:
                InfoDialog("OK", f"La désinscription a été prise en compte : {messages}", remove_after=config.REMOVE_AFTER)

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/registrations/{event_id}"

        json_dict = {
            'delete': not register,
        }

        # registrating to an event : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started (actually to joiners)
        load_option(None, 'participants à l\'événement')

    MY_SUB_PANEL <= html.H3("Inscription à un événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return
    pseudo = storage['PSEUDO']

    if 'EVENT_ID' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    event_id = storage['EVENT_ID']
    event_dict = get_event_data(event_id)

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiant joueur")
        return

    joiners = get_registrations(event_id)
    player_joined = player_id in joiners

    form = html.FORM()

    if player_joined:
        input_unregister_event = html.INPUT(type="submit", value="se désinscrire de l'événement")
        input_unregister_event.bind("click", lambda e: register_event_callback(e, False))
        form <= input_unregister_event
    else:
        input_register_event = html.INPUT(type="submit", value="s'inscrire à l'événement")
        input_register_event.bind("click", lambda e: register_event_callback(e, True))
        form <= input_register_event

    name = event_dict['name']
    start_date = event_dict['start_date']
    start_hour = event_dict['start_hour']
    end_date = event_dict['end_date']
    location = event_dict['location']
    description = event_dict['description']

    url = f"https://diplomania-gen.fr?event={event_id}"
    MY_SUB_PANEL <= f"Pour inviter un joueur à rejoindre cet événement, lui envoyer le lien : '{url}'"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= html.DIV(f"Evénement {name}", Class='important')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV(f"Date de début : {start_date}", Class='information')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV(f"Heure de début : {start_hour}", Class='information')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV(f"Date de fin : {end_date}", Class='information')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV(f"Lieu : {location}", Class='information')
    MY_SUB_PANEL <= html.BR()

    # description
    div_description = html.DIV(Class='information')
    for line in description.split('\n'):
        div_description <= line
        div_description <= html.BR()
    MY_SUB_PANEL <= div_description
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= form


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
        start_date = input_start_date.value
        start_hour = input_start_hour.value
        end_date = input_end_date.value
        location = input_location.value
        description = input_description.value

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

        if len(location) > MAX_LEN_EVENT_LOCATION:
            alert("Lieu de l'événement trop long")
            MY_SUB_PANEL.clear()
            create_event()
            return

        json_dict = {
            'name': name,
            'start_date': start_date,
            'start_hour': start_hour,
            'end_date': end_date,
            'location': location,
            'description': description,
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

    fieldset = html.FIELDSET()
    legend_start_date = html.LEGEND("date", title="Date de début de l'événement")
    fieldset <= legend_start_date
    input_start_date = html.INPUT(type="date", value="")
    fieldset <= input_start_date
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_start_hour = html.LEGEND("heure", title="Heure de l'événement")
    fieldset <= legend_start_hour
    input_start_hour = html.INPUT(type="time", value="")
    fieldset <= input_start_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_end_date = html.LEGEND("date", title="Date de fin de l'événement")
    fieldset <= legend_end_date
    input_end_date = html.INPUT(type="date", value="")
    fieldset <= input_end_date
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_location = html.LEGEND("lieu", title="Lieu de l'événement")
    fieldset <= legend_location
    input_location = html.INPUT(type="text", value=DEFAULT_EVENT_LOCATION, size=MAX_LEN_EVENT_LOCATION)
    fieldset <= input_location
    form <= fieldset

    form <= html.BR()

    form <= html.BR()
    fieldset = html.FIELDSET()
    legend_description = html.LEGEND("description", title="Cela peut être long. Exemple : 'tournoi par équipes avec négociations'")
    fieldset <= legend_description
    input_description = html.TEXTAREA(type="text", value="", rows=8, cols=80)
    fieldset <= input_description
    form <= fieldset

    form <= html.BR()

    input_create_event = html.INPUT(type="submit", value="créer l'événement")
    input_create_event.bind("click", create_event_callback)
    form <= input_create_event

    MY_SUB_PANEL <= form


def edit_event():
    """ edit_event """

    def edit_event_callback(_):
        """ edit_event_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"L'événement a été mis à jour : {messages}", remove_after=config.REMOVE_AFTER)

        name = input_name.value
        start_date = input_start_date.value
        start_hour = input_start_hour.value
        end_date = input_end_date.value
        location = input_location.value
        description = input_description.value

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

        if len(location) > MAX_LEN_EVENT_LOCATION:
            alert("Lieu de l'événement trop long")
            MY_SUB_PANEL.clear()
            create_event()
            return

        json_dict = {
            'name': name,
            'start_date': start_date,
            'start_hour': start_hour,
            'end_date': end_date,
            'location': location,
            'description': description,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/events/{event_id}"

        # updating an event : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        edit_event()

    MY_SUB_PANEL <= html.H3("Edition d'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    if 'EVENT_ID' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")

    event_id = storage['EVENT_ID']
    event_dict = get_event_data(event_id)

    name = event_dict['name']
    start_date = event_dict['start_date']
    start_hour = event_dict['start_hour']
    end_date = event_dict['end_date']
    location = event_dict['location']
    description = event_dict['description']
    manager_id = event_dict['manager_id']
    manager = players_dict[str(manager_id)]['pseudo']

    form = html.FORM()

    form <= html.DIV("Pas d'espaces ni de tirets dans le nom de l'événement", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom de l'événement (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value=name, size=MAX_LEN_EVENT_NAME)
    fieldset <= input_name
    form <= fieldset

    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_start_date = html.LEGEND("date", title="Date de début de l'événement")
    fieldset <= legend_start_date
    input_start_date = html.INPUT(type="date", value=start_date)
    fieldset <= input_start_date
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_start_hour = html.LEGEND("heure", title="Heure de l'événement")
    fieldset <= legend_start_hour
    input_start_hour = html.INPUT(type="time", value=start_hour)
    fieldset <= input_start_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_end_date = html.LEGEND("date", title="Date de fin de l'événement")
    fieldset <= legend_end_date
    input_end_date = html.INPUT(type="date", value=end_date)
    fieldset <= input_end_date
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_location = html.LEGEND("lieu", title="Lieu de l'événement")
    fieldset <= legend_location
    input_location = html.INPUT(type="text", value=location, size=MAX_LEN_EVENT_LOCATION)
    fieldset <= input_location
    form <= fieldset

    form <= html.BR()
    fieldset = html.FIELDSET()
    legend_description = html.LEGEND("description", title="Cela peut être long. Exemple : 'tournoi par équipes avec négociations'")
    fieldset <= legend_description
    input_description = html.TEXTAREA(type="text", rows=8, cols=80)
    input_description <= description
    fieldset <= input_description
    form <= fieldset

    form <= html.BR()

    input_edit_event = html.INPUT(type="submit", value="modifier l'événement")
    input_edit_event.bind("click", edit_event_callback)
    form <= input_edit_event

    MY_SUB_PANEL <= html.DIV(f"Evénement {name}", Class='important')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV(f"Créateur : {manager}", Class='information')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= form


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
        load_option(None, 'créer un événement')

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

        # back to where we started (actually to select)
        load_option(None, 'sélectionner un événement')

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

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")

    name = event_dict['name']
    description = event_dict['description']
    manager_id = event_dict['manager_id']
    manager = players_dict[str(manager_id)]['pseudo']

    MY_SUB_PANEL <= html.DIV(f"Evénement {name}", Class='important')
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV(f"Créateur : {manager}", Class='information')
    MY_SUB_PANEL <= html.BR()

    # description
    div_description = html.DIV(Class='information')
    for line in description.split('\n'):
        div_description <= line
        div_description <= html.BR()
    MY_SUB_PANEL <= div_description
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
    if item_name == 'participants à l\'événement':
        event_joiners()
    if item_name == 'm\'inscrire':
        register_event()
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
    global ARRIVAL

    ITEM_NAME_SELECTED = OPTIONS[0]

    # this means user wants to join game
    if ARRIVAL:
        ITEM_NAME_SELECTED = 'm\'inscrire'

    ARRIVAL = False
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
