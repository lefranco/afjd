""" players """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps

from browser import html, alert, ajax, document, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import mydialog
import config
import mydatetime
import index  # circular import

OPTIONS = {
    'Sélectionner un événement': "Sélectionner un événement sur le site",
    'Inscription à l\'événement': "S'inscrire et/ou consulter la liste des inscrits à l'événement sélectionné",
    'Créer un événement': "Créer un événement sur le site",
    'Editer l\'événement': "Editer l'événement sélectionné",
    'Gérer les participations': "Gérer les participations de l'événement sélectionné",
    'Supprimer l\'événement': "Supprimer l'événement sélectionné"
}


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
        req_result = loads(req.text)
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

    # get registrations : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return registrations_list


def get_event_data(event_id):
    """ get_event_data : returns empty dict if problem """

    event_dict = {}

    def reply_callback(req):
        nonlocal event_dict
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return event_dict


def select_event():
    """ select_event """

    def select_event_callback(ev, input_event):  # pylint: disable=invalid-name
        """ select_event_callback """

        ev.preventDefault()

        event_name = input_event.value
        storage['EVENT'] = event_name

        # back to where we started
        MY_SUB_PANEL.clear()
        select_event()

    MY_SUB_PANEL <= html.H3("Sélection d'un événement")

    events_data = common.get_events_data()

    # delete obsolete event
    if 'EVENT' in storage:
        event_name_selected = storage['EVENT']
        if event_name_selected not in [g['name'] for g in events_data.values()]:
            del storage['EVENT']
            alert("Votre événement sélectionné n'existe plus")

    # exit if no event
    if not events_data:
        alert("Pas d'événement de prévu pour le moment")
        return

    select_table = html.TABLE()

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_event = html.LEGEND("nom", title="Sélection de l'événement")
    fieldset <= legend_event
    input_event = html.SELECT(type="select-one", value="", Class='btn-inside')
    event_list = sorted([g['name'] for g in events_data.values()], key=lambda n: n.upper())
    for event_name in event_list:
        option = html.OPTION(event_name)
        if 'EVENT' in storage:
            if storage['EVENT'] == event_name:
                option.selected = True
        input_event <= option
    fieldset <= input_event
    form <= fieldset

    form <= html.BR()

    input_select_event = html.INPUT(type="submit", value="Sélectionner cet événement", Class='btn-inside')
    input_select_event.bind("click", lambda e, ie=input_event: select_event_callback(e, ie))
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


def registrations():
    """ registrations """

    def download_players_callback(ev):  # pylint: disable=invalid-name

        ev.preventDefault()

        # needed too for some reason
        MY_SUB_PANEL <= html.A(id='download_link')

        # perform actual exportation
        text_file_as_blob = window.Blob.new(['\n'.join(pseudo_players_list)], {'type': 'text/plain'})
        download_link = document['download_link']
        download_link.download = f"players_event_{event_name}.txt"
        download_link.href = window.URL.createObjectURL(text_file_as_blob)
        document['download_link'].click()

    def create_account_callback(ev):  # pylint: disable=invalid-name
        """ create_account_callback """

        ev.preventDefault()

        # go to create account page
        index.load_option(None, 'Mon compte')

    def store_comment_callback(ev):  # pylint: disable=invalid-name
        """ store_information_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status not in [200, 201]:
                if 'message' in req_result:
                    alert(f"Erreur au commentaire de l'inscription : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème commentaire de l'inscription à l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le commentaire d'inscription a été prise en compte : {messages}")

        ev.preventDefault()

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/registrations/{event_id}"

        json_dict = {
            'delete': False,
            'comment': input_comment.value,
        }

        # commenting registration to an event : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        registrations()

    def sendmess_callback(ev):  # pylint: disable=invalid-name
        """ sendmess_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de message dans les messages privés : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de message dans les messages privés : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le message privé a été envoyé ! {messages}")

        ev.preventDefault()

        if 'PSEUDO' not in storage:
            alert("Il faut être identifié")
            # back to where we started
            MY_SUB_PANEL.clear()
            registrations()
            return

        if not input_message.value:
            alert("Contenu du message vide")
            # back to where we started
            MY_SUB_PANEL.clear()
            registrations()
            return

        ev.preventDefault()

        content = '\n\n'.join([f"[Evénement {event_name}]", input_message.value])

        json_dict = {
            'dest_user_id': manager_id,
            'content': content
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/private-messages"

        # sending private message : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        registrations()

    def register_event_callback(ev, register):  # pylint: disable=invalid-name
        """ register_event_callback """

        def reply_callback(req):
            req_result = loads(req.text)
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
                mydialog.InfoDialog("Information", f"L'inscription a été prise en compte : {messages}")
            else:
                mydialog.InfoDialog("Information", f"La désinscription a été prise en compte : {messages}")

        ev.preventDefault()

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/registrations/{event_id}"

        json_dict = {
            'delete': not register,
            'comment': '',
        }

        # registrating to an event : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        registrations()

    player_id = None
    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']
        player_id = common.get_player_id(pseudo)
        # player_id None does not matter

    if 'EVENT' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    event_name = storage['EVENT']
    events_dict = common.get_events_data()
    eventname2id = {v['name']: int(k) for k, v in events_dict.items()}
    event_id = eventname2id[event_name]
    event_dict = get_event_data(event_id)

    joiners = get_registrations(event_id)
    dict_status = {j[0]: (j[2], j[3]) for j in joiners}
    player_joined = False
    player_status = 0
    player_comment = ""
    if player_id is not None:
        player_joined = player_id in dict_status
        if player_joined:
            player_status, player_comment = dict_status[player_id]

    joiners_table = html.TABLE()

    fields = ['rank', 'date', 'pseudo', 'first_name', 'family_name', 'residence', 'nationality', 'time_zone', 'comment', 'status']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'rank': 'rang', 'date': 'date', 'pseudo': 'pseudo', 'first_name': 'prénom', 'family_name': 'nom', 'residence': 'résidence', 'nationality': 'nationalité', 'time_zone': 'fuseau horaire', 'comment': 'commentaire', 'status': 'statut'}[field]
        col = html.TD(field_fr)
        thead <= col
    joiners_table <= thead

    code_country_table = {v: k for k, v in config.COUNTRY_CODE_TABLE.items()}

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")

    joiners_dict = {}
    for joiner in joiners:
        joiner_data = players_dict[str(joiner[0])].copy()
        joiner_data.update({'date': joiner[1], 'status': joiner[2], 'comment': joiner[3]})
        joiners_dict[joiner[0]] = joiner_data

    pseudo_players_list = []

    # sorting is done by server
    for num, data in enumerate(joiners_dict.values()):

        data['rank'] = None

        colour = None
        if 'PSEUDO' in storage:
            if data['pseudo'] == pseudo:
                colour = config.MY_RATING

        row = html.TR()
        for field in fields:
            value = data[field]

            if field == 'pseudo':
                pseudo_players_list.append(value)

            if field == 'rank':
                value = num + 1

            if field == 'date':
                date_reg_gmt = mydatetime.fromtimestamp(value)
                date_reg_gmt_str = mydatetime.strftime(*date_reg_gmt)
                value = date_reg_gmt_str

            if field in ['residence', 'nationality']:
                code = value
                country_name = code_country_table[code]
                value = html.IMG(src=f"./national_flags/{code}.png", title=country_name, width="25", height="17")

            if field == 'status':
                value = {-1: "Refusé", 0: "En attente", 1: "Accepté"}[value]

            if field == 'comment':
                value = "<br>".join(value.split('\n'))

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }
            row <= col

        joiners_table <= row

    if 'PSEUDO' in storage:
        if player_joined:
            assert player_id is not None
            if player_status < 0:
                player_status_str = "Votre inscription est refusée"
            elif player_status > 0:
                player_status_str = "Votre inscription est acceptée"
            else:
                player_status_str = "Votre inscription est en attente"
        else:
            player_status_str = "Vous n'êtes pas inscrit"

        register_form = html.FORM()
        if player_joined:
            input_unregister_event = html.INPUT(type="submit", value="Sans moi !", Class='btn-inside')
            input_unregister_event.bind("click", lambda e: register_event_callback(e, False))
            register_form <= input_unregister_event
        else:
            input_register_event = html.INPUT(type="submit", value="Mettez moi dedans !", Class='btn-inside')
            input_register_event.bind("click", lambda e: register_event_callback(e, True))
            register_form <= input_register_event
    else:
        player_status_str = "Vous n'êtes pas identifié"

    detail_form = html.FORM()

    fieldset = html.FIELDSET()
    legend_message = html.LEGEND("Votre commentaire", title="Mettez un commentaire (rondes jouées typiquement)")
    fieldset <= legend_message
    input_comment = html.TEXTAREA(type="text", rows=8, cols=80)
    input_comment <= player_comment
    fieldset <= input_comment
    detail_form <= fieldset

    input_store_comment = html.INPUT(type="submit", value="Enregistrer", Class='btn-inside')
    input_store_comment.bind("click", store_comment_callback)
    detail_form <= input_store_comment

    contact_form = html.FORM()

    fieldset = html.FIELDSET()
    legend_message = html.LEGEND("Votre message", title="Qu'avez vous à lui dire ?")
    fieldset <= legend_message
    input_message = html.TEXTAREA(type="text", rows=8, cols=80)
    fieldset <= input_message
    contact_form <= fieldset

    contact_form <= html.DIV("Votre message lui parviendra par messagerie privée.")
    contact_form <= html.BR()

    input_send_message = html.INPUT(type="submit", value="Envoyer le message privé", Class='btn-inside')
    input_send_message.bind("click", sendmess_callback)
    contact_form <= input_send_message

    name = event_dict['name']
    start_date = event_dict['start_date']
    start_hour = event_dict['start_hour']
    end_date = event_dict['end_date']
    location = event_dict['location']
    external = event_dict['external']
    description = event_dict['description']

    manager_id = event_dict['manager_id']
    manager = players_dict[str(manager_id)]['pseudo']

    event_information = html.DIV(Class='event_element')
    event_information <= html.B("Créateur")
    event_information <= f" : {manager}"
    event_information <= html.BR()

    event_information <= html.B("Date de début")
    event_information <= f" : {start_date}"
    event_information <= html.BR()

    event_information <= html.B("Heure de début")
    event_information <= f" : {start_hour}"
    event_information <= html.BR()

    event_information <= html.B("Date de fin")
    event_information <= f" : {end_date}"
    event_information <= html.BR()

    event_information <= html.B("Lieu")
    event_information <= f" : {location}"
    event_information <= html.BR()

    event_information <= html.B("Externe")
    event_information <= f" : {'Oui' if external else 'Non'}"
    event_information <= html.BR()

    event_information <= html.B("Description complète")
    event_information <= " :"
    event_information <= html.BR()
    for line in description.split('\n'):
        if line.startswith("http"):
            anchor = html.A(href=line, target="_blank")
            anchor <= line
            event_information <= anchor
        else:
            event_information <= line
        event_information <= html.BR()

    # button for creating account
    account_button = None
    if 'PSEUDO' not in storage:
        # shortcut to create account
        account_button = html.BUTTON("Je n'ai pas de compte, je veux le créer !", Class='btn-inside')
        account_button.bind("click", create_account_callback)

    MY_SUB_PANEL <= html.H3(f"Inscription à l'événement {name}")

    MY_SUB_PANEL <= html.H4("Toutes les informations")

    MY_SUB_PANEL <= event_information
    MY_SUB_PANEL <= html.BR()

    # provide the link
    if not external:
        url = f"https://diplomania-gen.fr?event={name}"
        MY_SUB_PANEL <= f"Pour inviter un joueur à s'inscrire à cet événement, lui envoyer le lien : '{url}'"

    MY_SUB_PANEL <= html.H4("Votre inscription")

    # put button to register/un register
    if external:
        MY_SUB_PANEL <= html.EM("Attention : l'inscription est externe, c'est à dire qu'elle n'est pas gérée sur le site.")
    else:
        # tell the guy his situation
        MY_SUB_PANEL <= html.DIV(player_status_str, Class='important')
        MY_SUB_PANEL <= html.BR()

        if 'PSEUDO' in storage:
            MY_SUB_PANEL <= register_form
        else:
            MY_SUB_PANEL <= account_button

    # provide more data about registration
    if 'PSEUDO' in storage:
        if player_joined:
            MY_SUB_PANEL <= html.H4("Commentez votre inscription")
            MY_SUB_PANEL <= detail_form

    # provide mean to contact organizer

    # put button to register/un register
    if 'PSEUDO' in storage:
        MY_SUB_PANEL <= html.H4("Contacter l'organisateur")
        MY_SUB_PANEL <= contact_form

    # provide people already in
    if not external:
        MY_SUB_PANEL <= html.H4("Ils/elles vous attendent :")
        MY_SUB_PANEL <= joiners_table
        MY_SUB_PANEL <= html.BR()
        input_export_players = html.INPUT(type="submit", value="Télécharger la liste des inscrits", Class='btn-inside')
        input_export_players.bind("click", download_players_callback)
        MY_SUB_PANEL <= input_export_players


def create_event(json_dict):
    """ create_event """

    # load previous values if applicable
    name = json_dict['name'] if json_dict and 'name' in json_dict else None
    start_date = json_dict['start_date'] if json_dict and 'start_date' in json_dict else None
    start_hour = json_dict['start_hour'] if json_dict and 'start_hour' in json_dict else None
    end_date = json_dict['end_date'] if json_dict and 'end_date' in json_dict else None
    location = json_dict['location'] if json_dict and 'location' in json_dict else None
    external = json_dict['external'] if json_dict and 'external' in json_dict else None
    description = json_dict['description'] if json_dict and 'description' in json_dict else None
    summary = json_dict['summary'] if json_dict and 'summary' in json_dict else None

    def create_event_callback(ev):  # pylint: disable=invalid-name
        """ create_event_callback """

        nonlocal name
        nonlocal start_date
        nonlocal start_hour
        nonlocal end_date
        nonlocal location
        nonlocal external
        nonlocal description
        nonlocal summary

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la création de l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la création de l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"L'événement a été créé : {messages}")

        ev.preventDefault()

        # get values from user input

        name = input_name.value
        start_date = input_start_date.value
        start_hour = input_start_hour.value
        end_date = input_end_date.value
        location = input_location.value
        external = int(input_external.checked)
        description = input_description.value
        summary = input_summary.value

        # make data structure
        json_dict = {
            'name': name,
            'start_date': start_date,
            'start_hour': start_hour,
            'end_date': end_date,
            'location': location,
            'external': external,
            'description': description,
            'summary': summary,
        }

        # start checking data

        if not name:
            alert("Nom d'événement manquant")
            MY_SUB_PANEL.clear()
            create_event(json_dict)
            return

        if len(name) > MAX_LEN_EVENT_NAME:
            alert("Nom d'événement trop long")
            MY_SUB_PANEL.clear()
            create_event(json_dict)
            return

        if len(location) > MAX_LEN_EVENT_LOCATION:
            alert("Lieu de l'événement trop long")
            MY_SUB_PANEL.clear()
            create_event(json_dict)
            return

        # send to server

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/events"

        # creating an event : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        create_event(json_dict)

    MY_SUB_PANEL <= html.H3("Création d'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    form = html.FORM()

    form <= html.DIV("Pas de tirets dans le nom de l'événement", Class='note')
    form <= html.DIV("Pour les liens, les mettre en début de ligne (http...)", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom de l'événement (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value=name if name is not None else "", size=MAX_LEN_EVENT_NAME, Class='btn-inside')
    fieldset <= input_name
    form <= fieldset

    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_start_date = html.LEGEND("date de début", title="Date de début de l'événement")
    fieldset <= legend_start_date
    input_start_date = html.INPUT(type="date", value=start_date if start_date is not None else "", Class='btn-inside')
    fieldset <= input_start_date
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_start_hour = html.LEGEND("heure de début", title="Heure de l'événement")
    fieldset <= legend_start_hour
    input_start_hour = html.INPUT(type="time", value=start_hour if start_hour is not None else "", step=1, Class='btn-inside')
    fieldset <= input_start_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_end_date = html.LEGEND("date de fin", title="Date de fin de l'événement")
    fieldset <= legend_end_date
    input_end_date = html.INPUT(type="date", value=end_date if end_date is not None else "", Class='btn-inside')
    fieldset <= input_end_date
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_location = html.LEGEND("lieu", title="Lieu de l'événement")
    fieldset <= legend_location
    input_location = html.INPUT(type="text", value=location if location is not None else DEFAULT_EVENT_LOCATION, size=MAX_LEN_EVENT_LOCATION, Class='btn-inside')
    fieldset <= input_location
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_external = html.LEGEND("externe", title="L'événement est-il externe au site")
    fieldset <= legend_external
    input_external = html.INPUT(type="checkbox", checked=False, Class='btn-inside')
    fieldset <= input_external
    form <= fieldset

    form <= html.BR()

    form <= html.BR()
    fieldset = html.FIELDSET()
    legend_description = html.LEGEND("description complète", title="Description complète de l'événement pour les inscrits")
    fieldset <= legend_description
    input_description = html.TEXTAREA(type="text", rows=16, cols=80)
    input_description <= description if description is not None else ""
    fieldset <= input_description
    form <= fieldset

    form <= html.BR()
    fieldset = html.FIELDSET()
    legend_summary = html.LEGEND("résumé", title="Description courte de l'événement pour la page d'accueil (pas plus de trois lignes)")
    fieldset <= legend_summary
    input_summary = html.TEXTAREA(type="text", rows=5, cols=80)
    input_summary <= summary if summary is not None else ""
    fieldset <= input_summary
    form <= fieldset

    form <= html.BR()

    input_create_event = html.INPUT(type="submit", value="Créer l'événement", Class='btn-inside')
    input_create_event.bind("click", create_event_callback)
    form <= input_create_event

    MY_SUB_PANEL <= form


def edit_event():
    """ edit_event """

    def edit_event_callback(ev):  # pylint: disable=invalid-name
        """ edit_event_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"L'événement a été mis à jour : {messages}")

        ev.preventDefault()

        name = input_name.value
        start_date = input_start_date.value
        start_hour = input_start_hour.value
        end_date = input_end_date.value
        location = input_location.value
        description = input_description.value
        summary = input_summary.value

        # make data structure
        json_dict = {
            'name': name,
            'start_date': start_date,
            'start_hour': start_hour,
            'end_date': end_date,
            'location': location,
            'description': description,
            'summary': summary,
        }

        # start checking data

        if not name:
            alert("Nom d'événement manquant")
            MY_SUB_PANEL.clear()
            edit_event()
            return

        if len(name) > MAX_LEN_EVENT_NAME:
            alert("Nom d'événement trop long")
            MY_SUB_PANEL.clear()
            edit_event()
            return

        if len(location) > MAX_LEN_EVENT_LOCATION:
            alert("Lieu de l'événement trop long")
            MY_SUB_PANEL.clear()
            edit_event()
            return

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/events/{event_id}"

        # updating an event : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        edit_event()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return
    pseudo = storage['PSEUDO']
    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiant joueur")
        return

    if 'EVENT' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    # title
    event_name = storage['EVENT']
    title = html.H3(f"Edition de l'événement {event_name}")
    MY_SUB_PANEL <= title

    events_dict = common.get_events_data()
    eventname2id = {v['name']: int(k) for k, v in events_dict.items()}
    event_id = eventname2id[event_name]
    event_dict = get_event_data(event_id)

    start_date = event_dict['start_date']
    start_hour = event_dict['start_hour']
    end_date = event_dict['end_date']
    location = event_dict['location']
    description = event_dict['description']
    summary = event_dict['summary']

    form = html.FORM()

    form <= html.DIV("Pas de tirets dans le nom de l'événement", Class='note')
    form <= html.DIV("Pour les liens, les mettre en début de ligne (http...)", Class='note')
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom de l'événement (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value=event_name, size=MAX_LEN_EVENT_NAME, Class='btn-inside')
    fieldset <= input_name
    form <= fieldset

    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_start_date = html.LEGEND("date de début", title="Date de début de l'événement")
    fieldset <= legend_start_date
    input_start_date = html.INPUT(type="date", value=start_date, Class='btn-inside')
    fieldset <= input_start_date
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_start_hour = html.LEGEND("heure de début", title="Heure de l'événement")
    fieldset <= legend_start_hour
    input_start_hour = html.INPUT(type="time", value=start_hour, step=1, Class='btn-inside')
    fieldset <= input_start_hour
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_end_date = html.LEGEND("date de fin", title="Date de fin de l'événement")
    fieldset <= legend_end_date
    input_end_date = html.INPUT(type="date", value=end_date, Class='btn-inside')
    fieldset <= input_end_date
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_location = html.LEGEND("lieu", title="Lieu de l'événement")
    fieldset <= legend_location
    input_location = html.INPUT(type="text", value=location, size=MAX_LEN_EVENT_LOCATION, Class='btn-inside')
    fieldset <= input_location
    form <= fieldset

    form <= html.BR()
    fieldset = html.FIELDSET()
    legend_description = html.LEGEND("description complète", title="Description complète de l'événement pour les inscrits")
    fieldset <= legend_description
    input_description = html.TEXTAREA(type="text", rows=16, cols=80)
    input_description <= description
    fieldset <= input_description
    form <= fieldset

    form <= html.BR()
    fieldset = html.FIELDSET()
    legend_summary = html.LEGEND("résumé", title="Description courte de l'événement pour la page d'accueil (pas plus de trois lignes)")
    fieldset <= legend_summary
    input_summary = html.TEXTAREA(type="text", rows=5, cols=80)
    input_summary <= summary
    fieldset <= input_summary
    form <= fieldset

    form <= html.BR()

    input_edit_event = html.INPUT(type="submit", value="Modifier l'événement", Class='btn-inside')
    input_edit_event.bind("click", edit_event_callback)
    form <= input_edit_event

    MY_SUB_PANEL <= form


def handle_joiners():
    """ handle_joiners """

    def registration_action_callback(ev, player_id, value):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de l'inscription {player_id} {value}: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de l'inscription {player_id} {value}: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"L'inscription a été modifiée : {messages}")

        ev.preventDefault()

        json_dict = {
            'player_id': player_id,
            'value': value
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/registrations/{event_id}"

        # changing event registration : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        handle_joiners()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return
    pseudo = storage['PSEUDO']
    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiant joueur")
        return

    if 'EVENT' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    joiners_table = html.TABLE()

    fields = ['rank', 'date', 'pseudo', 'first_name', 'family_name', 'residence', 'nationality', 'time_zone', 'status', 'action']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'rank': 'rang', 'date': 'date', 'pseudo': 'pseudo', 'first_name': 'prénom', 'family_name': 'nom', 'residence': 'résidence', 'nationality': 'nationalité', 'time_zone': 'fuseau horaire', 'status': 'statut', 'action': 'action'}[field]
        col = html.TD(field_fr)
        thead <= col
    joiners_table <= thead

    code_country_table = {v: k for k, v in config.COUNTRY_CODE_TABLE.items()}

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")

    # title
    event_name = storage['EVENT']
    title = html.H3(f"Gérer les participations de l'événement {event_name}")
    MY_SUB_PANEL <= title

    events_dict = common.get_events_data()
    eventname2id = {v['name']: int(k) for k, v in events_dict.items()}
    event_id = eventname2id[event_name]

    joiners = get_registrations(event_id)
    joiners_dict = {}
    for joiner in joiners:
        joiner_data = players_dict[str(joiner[0])].copy()
        joiner_data.update({'date': joiner[1], 'status': joiner[2]})
        joiners_dict[joiner[0]] = joiner_data

    # sorting is done by server
    for num, (player_id, data) in enumerate(joiners_dict.items()):

        data['rank'] = None
        data['action'] = None

        if 'PSEUDO' in storage and data['pseudo'] == storage['PSEUDO']:
            colour = config.MY_RATING
        else:
            colour = None

        row = html.TR()
        for field in fields:
            value = data[field]

            if field == 'rank':
                value = num + 1

            if field == 'date':
                date_reg_gmt = mydatetime.fromtimestamp(value)
                date_reg_gmt_str = mydatetime.strftime(*date_reg_gmt)
                value = date_reg_gmt_str

            if field in ['residence', 'nationality']:
                code = value
                country_name = code_country_table[code]
                value = html.IMG(src=f"./national_flags/{code}.png", title=country_name, width="25", height="17")

            if field == 'status':
                value = {-1: "Refusé", 0: "En attente", 1: "Accepté"}[value]

            if field == 'action':
                value = html.TABLE()
                row2 = html.TR()
                if data['status'] != -1:
                    form = html.FORM()
                    input_event_reject = html.INPUT(type="image", src="./images/event_reject.jpg", title="Pour rejeter cette inscription", Class='btn-inside')
                    input_event_reject.bind("click", lambda e, pi=player_id: registration_action_callback(e, pi, -1))
                    form <= input_event_reject
                    col2 = html.TD()
                    col2 <= form
                    row2 <= col2
                if data['status'] != 0:
                    form = html.FORM()
                    input_event_wait = html.INPUT(type="image", src="./images/event_wait.jpg", title="Pour réinitialiser cette inscription", Class='btn-inside')
                    input_event_wait.bind("click", lambda e, pi=player_id: registration_action_callback(e, pi, 0))
                    form <= input_event_wait
                    col2 = html.TD()
                    col2 <= form
                    row2 <= col2
                if data['status'] != 1:
                    form = html.FORM()
                    input_event_accept = html.INPUT(type="image", src="./images/event_accept.jpg", title="Pour accepter cette inscription", Class='btn-inside')
                    input_event_accept.bind("click", lambda e, pi=player_id: registration_action_callback(e, pi, 1))
                    form <= input_event_accept
                    col2 = html.TD()
                    col2 <= form
                    row2 <= col2
                value <= row2

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }
            row <= col

        joiners_table <= row

    MY_SUB_PANEL <= joiners_table


def delete_event():
    """ delete_event """

    def cancel_delete_event_callback(_, dialog):
        """ cancel_delete_event_callback """
        dialog.close(None)

    def delete_event_callback(_, dialog):

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la suppression de l'événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la suppression de l'événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"L'événement a été supprimé : {messages}")

            del storage['EVENT']

        # back to where we started (actually to select)
        load_option(None, 'Sélectionner un événement')

        dialog.close(None)

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/events/{event_id}"

        # deleting event : need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def delete_event_callback_confirm(ev):  # pylint: disable=invalid-name
        """ delete_event_callback_confirm """

        ev.preventDefault()

        dialog = mydialog.Dialog("On supprime vraiment l'événement ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog: delete_event_callback(e, d))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_delete_event_callback(e, d))

        # back to where we started (actually to select)
        load_option(None, 'Sélectionner un événement')

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return
    pseudo = storage['PSEUDO']
    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiant joueur")
        return

    if 'EVENT' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    # title
    event_name = storage['EVENT']
    title = html.H3(f"Suppression de l'événement {event_name}")
    MY_SUB_PANEL <= title

    events_dict = common.get_events_data()
    eventname2id = {v['name']: int(k) for k, v in events_dict.items()}
    event_id = eventname2id[event_name]

    form = html.FORM()

    input_delete_event = html.INPUT(type="submit", value="Supprimer l'événement", Class='btn-inside')
    input_delete_event.bind("click", delete_event_callback_confirm)
    form <= input_delete_event

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")

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

ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

MY_SUB_PANEL = html.DIV(id="page")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Sélectionner un événement':
        select_event()
    if item_name == 'Inscription à l\'événement':
        registrations()
    if item_name == 'Créer un événement':
        create_event(None)
    if item_name == 'Editer l\'événement':
        edit_event()
    if item_name == 'Gérer les participations':
        handle_joiners()
    if item_name == 'Supprimer l\'événement':
        delete_event()

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


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    global ARRIVAL

    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    # this means user wants to join game
    if ARRIVAL:
        ITEM_NAME_SELECTED = 'Inscription à l\'événement'
        ARRIVAL = False

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
