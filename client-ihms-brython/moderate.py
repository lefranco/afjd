""" admin """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import interface
import mapping
import memoize
import scoring


MAX_LEN_EMAIL = 100

OPTIONS = ['retrouver à partir du courriel', 'tous les courriels', 'récupérer un courriel', 'récupérer un téléphone', 'résultats tournoi']


def check_modo(pseudo):
    """ check_modo """

    moderator_list = common.get_moderators()
    if pseudo not in moderator_list:
        return False

    return True


def get_tournament_players_data(tournament_id):
    """ get_tournament_players_data : returns empty dict if problem """

    tournament_players_dict = {}

    def reply_callback(req):
        nonlocal tournament_players_dict
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return tournament_players_dict


def get_all_emails():
    """ get_all_emails returns empty dict if error """

    emails_dict = {}

    def reply_callback(req):
        nonlocal emails_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des courriels : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des courriels : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        emails_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players-emails"

    # changing news : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return emails_dict


def find_from_email_address():
    """ find_from_email_address """

    def find_from_email_addresss_callback(_):
        """ find_from_email_addresss_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération du pseudo à partir du courriel : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération du pseudo à partir du courriel : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            pseudo_found = req_result['pseudo']
            alert(f"Son pseudo est '{pseudo_found}'")

        email = input_email.value
        if not email:
            alert("Courriel à retrouver manquant")
            return

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/find-player-from-email/{email}"

        # finding pseudo from email : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        find_from_email_address()

    MY_SUB_PANEL <= html.H3("Retrouver un compte par courriel")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_email = html.LEGEND("courriel", title="Le courriel de la personne à identifier")
    fieldset <= legend_email
    input_email = html.INPUT(type="email", value="", size=MAX_LEN_EMAIL)
    fieldset <= input_email
    form <= fieldset

    form <= html.BR()

    input_find_email = html.INPUT(type="submit", value="retrouver le compte")
    input_find_email.bind("click", find_from_email_addresss_callback)
    form <= input_find_email

    MY_SUB_PANEL <= form


def all_emails():
    """ all_emails """

    MY_SUB_PANEL <= html.H3("Liste joueurs avec leurs courriels")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    emails_dict = get_all_emails()

    emails_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'email']:
        col = html.TD(field)
        thead <= col
    emails_table <= thead

    for pseudo, email in emails_dict.items():
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        col = html.TD(email)
        row <= col

        emails_table <= row

    MY_SUB_PANEL <= emails_table


def display_email_address():
    """ display_email_address """

    def display_email_address_callback(_):
        """ display_email_address_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération du courriel : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération du courriel : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            email = req_result['email']
            alert(f"Son courriel est '{email}'")

        contact_user_name = input_contact.value
        if not contact_user_name:
            alert("User name à contacter manquant")
            return

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-email/{contact_user_name}"

        # getting email: need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        display_email_address()

    MY_SUB_PANEL <= html.H3("Afficher un courriel")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    # all players can be contacted
    possible_contacts = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_contact = html.LEGEND("Contact", title="Sélectionner le joueur à contacter par courriel")
    fieldset <= legend_contact
    input_contact = html.SELECT(type="select-one", value="")
    for contact_pseudo in sorted(possible_contacts, key=lambda pu: pu.upper()):
        option = html.OPTION(contact_pseudo)
        input_contact <= option
    fieldset <= input_contact
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="récupérer son courriel")
    input_select_player.bind("click", display_email_address_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def display_phone_number():
    """ get_phone_number """

    def display_phone_number_callback(_):
        """ get_phone_number_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de numéro de téléphone : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de numéro de téléphone : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            telephone = req_result['telephone']
            if telephone:
                alert(f"Son numéro est '{telephone}'")
            else:
                alert("Pas de numéro entré !")

        contact_user_name = input_contact.value
        if not contact_user_name:
            alert("User name à contacter manquant")
            return

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-telephone/{contact_user_name}"

        # getting private phone number : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        display_phone_number()

    MY_SUB_PANEL <= html.H3("Afficher un numéro de téléphone")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    # all players can be contacted
    possible_contacts = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_contact = html.LEGEND("Contact", title="Sélectionner le joueur à contacter par téléphone")
    fieldset <= legend_contact
    input_contact = html.SELECT(type="select-one", value="")
    for contact_pseudo in sorted(possible_contacts, key=lambda pu: pu.upper()):
        option = html.OPTION(contact_pseudo)
        input_contact <= option
    fieldset <= input_contact
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="récupérer son numéro de téléphone")
    input_select_player.bind("click", display_phone_number_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def tournament_result():
    """ tournament_result """

    MY_SUB_PANEL <= html.H3("Résultat intermédiaire du tournoi")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    tournament_dict = common.tournament_data(game)
    if not tournament_dict:
        alert("Pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    tournament_name = tournament_dict['name']
    tournament_id = tournament_dict['identifier']
    games_in = tournament_dict['games']

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement info joueurs")
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    tournament_players_dict = get_tournament_players_data(tournament_id)
    if not tournament_players_dict:
        alert("Erreur chargement allocation tournois")
        return

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
        solo_threshold = variant_data.number_centers() // 2
        score_table = scoring.scoring(game_scoring, solo_threshold, ratings)

        rolename2num = {variant_data.name_table[r]: n for n, r in variant_data.roles.items()}

        for role_name, score in score_table.items():
            role_num = rolename2num[role_name]
            if (game_id, role_num) in gamerole2pseudo:
                pseudo = gamerole2pseudo[(game_id, role_num)]
            else:
                pseudo = "&lt;pas alloué&gt;"
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
        pseudo = gamerole2pseudo[(game_id, role_num)]
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
    for pseudo, score in sorted(points.items(), key=lambda p: p[1], reverse=True):
        row = html.TR()

        col = html.TD(rank)
        row <= col

        col = html.TD(pseudo)
        row <= col

        col = html.TD(f"{score:.2f}")
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

    MY_SUB_PANEL <= html.DIV(f"Tournoi {tournament_name}", Class='note')

    MY_SUB_PANEL <= html.H4("Classement")
    MY_SUB_PANEL <= recap_table
    MY_SUB_PANEL <= html.H4("Retards")
    MY_SUB_PANEL <= incident_table

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées (sauf pour les parties en direct - en minutes)", Class='note')


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

MY_SUB_PANEL = html.DIV(id="admin")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scrollTo(0, 0)

    if item_name == 'retrouver à partir du courriel':
        find_from_email_address()
    if item_name == 'tous les courriels':
        all_emails()
    if item_name == 'récupérer un courriel':
        display_email_address()
    if item_name == 'récupérer un téléphone':
        display_phone_number()
    if item_name == 'résultats tournoi':
        tournament_result()

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
