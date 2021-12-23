""" admin """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time
import datetime

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import interface
import mapping
import selection
import memoize
import scoring
import index  # circular import


MAX_LEN_EMAIL = 100

OPTIONS = ['toutes les parties', 'résultats tournoi', 'retrouver à partir du courriel', 'récupérer un courriel', 'récupérer un téléphone']


def check_modo(pseudo):
    """ check_modo """

    # TODO improve this with real admin account
    if pseudo != "Palpatine":
        return False

    return True


def get_tournament_players_data(tournament_id):
    """ get_tournament_players_data : returns empty dict if problem """

    tournament_players_dict = dict()

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

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/tournament-allocations/{tournament_id}"

    # getting tournament allocation : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return tournament_players_dict


def get_all_games_roles_submitted_orders():
    """ get_all_games_roles_submitted_orders : returns empty dict on error """

    dict_submitted_data = dict()

    def reply_callback(req):
        nonlocal dict_submitted_data
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des rôles qui ont soumis des ordres pour toutes les parties possibles : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des rôles qui ont soumis des ordres pour toutes les parties possibles : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        dict_submitted_data = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-games-orders-submitted"

    # get roles that submitted orders : need token (but may change)
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_submitted_data


def all_games(state_name):
    """all_games """

    def select_game_callback(_, game_name, game_data_sel):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        InfoDialog("OK", f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page", remove_after=config.REMOVE_AFTER)
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    def again(state_name):
        """ again """
        MY_SUB_PANEL.clear()
        all_games(state_name)

    overall_time_before = time.time()

    # title
    title = html.H3(f"Parties dans l'état: {state_name}")
    MY_SUB_PANEL <= title

    state = config.STATE_CODE_TABLE[state_name]

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # get the players (masters)
    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire des joueurs")
        return

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return
    masters_alloc = allocations_data['game_masters_dict']

    dict_submitted_data = get_all_games_roles_submitted_orders()
    if not dict_submitted_data:
        alert("Erreur chargement des soumissions dans les parties")
        return

    # fill table game -> master
    game_master_dict = dict()
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            game_master_dict[game] = master

    time_stamp_now = time.time()

    games_table = html.TABLE()

    fields = ['jump_here', 'go_away', 'master', 'variant', 'deadline', 'current_advancement', 'all_orders_submitted', 'all_agreed']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'jump_here': 'même onglet', 'go_away': 'nouvel onglet', 'master': 'arbitre', 'variant': 'variante', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'all_orders_submitted': 'ordres', 'all_agreed': 'prêts'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0
    for game_id_str, data in sorted(games_dict.items(), key=lambda g: int(g[0])):

        if data['current_state'] != state:
            continue

        number_games += 1

        game_id = int(game_id_str)

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        if variant_name_loaded in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
            variant_content_loaded = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded]
        else:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                return
            memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded] = variant_content_loaded

        # selected interface (user choice)
        interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

        # parameters

        if (variant_name_loaded, interface_chosen) in memoize.PARAMETERS_READ_MEMOIZE_TABLE:
            parameters_read = memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)]
        else:
            parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)
            memoize.PARAMETERS_READ_MEMOIZE_TABLE[(variant_name_loaded, interface_chosen)] = parameters_read

        # build variant data

        variant_name_loaded_str = str(variant_name_loaded)
        if (variant_name_loaded_str, interface_chosen) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
            variant_data = memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)]
        else:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)] = variant_data

        submitted_data = dict()
        submitted_data['needed'] = dict_submitted_data['dict_needed'][str(game_id)]
        submitted_data['submitted'] = dict_submitted_data['dict_submitted'][str(game_id)]
        submitted_data['agreed'] = dict_submitted_data['dict_agreed'][str(game_id)]

        data['master'] = None
        data['all_orders_submitted'] = None
        data['all_agreed'] = None
        data['jump_here'] = None
        data['go_away'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None

            if field == 'jump_here':
                game_name = data['name']
                form = html.FORM()
                input_jump_game = html.INPUT(type="submit", value=game_name)
                input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                form <= input_jump_game
                value = form

            if field == 'go_away':
                link = html.A(href=f"?game={game_name}", target="_blank")
                link <= game_name
                value = link

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
                deadline_loaded_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded_str

                time_unit = 60 if data['fast'] else 24 * 60 * 60

                # we are after deadline + grace
                if time_stamp_now > deadline_loaded + time_unit * data['grace_duration']:
                    colour = config.PASSED_GRACE_COLOUR
                # we are after deadline
                elif time_stamp_now > deadline_loaded:
                    colour = config.PASSED_DEADLINE_COLOUR
                # deadline is today
                elif time_stamp_now > deadline_loaded - time_unit:
                    colour = config.APPROACHING_DEADLINE_COLOUR

            if field == 'current_advancement':
                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'all_orders_submitted':
                submitted_roles_list = submitted_data['submitted']
                nb_submitted = len(submitted_roles_list)
                needed_roles_list = submitted_data['needed']
                nb_needed = len(needed_roles_list)
                value = f"{nb_submitted}/{nb_needed}"
                if nb_submitted >= nb_needed:
                    # we have all orders : green
                    colour = config.ALL_ORDERS_IN_COLOUR

            if field == 'all_agreed':
                agreed_roles_list = submitted_data['agreed']
                nb_agreed = len(agreed_roles_list)
                submitted_roles_list = submitted_data['submitted']
                nb_submitted = len(submitted_roles_list)
                value = f"{nb_agreed}/{nb_submitted}"
                if nb_agreed >= nb_submitted:
                    # we have all agreements : green
                    colour = config.ALL_AGREEMENTS_IN_COLOUR

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        games_table <= row

    MY_SUB_PANEL <= games_table
    MY_SUB_PANEL <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
    special_info = html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}", Class='note')
    MY_SUB_PANEL <= special_info
    MY_SUB_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed} avec {number_games} partie(s)"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    MY_SUB_PANEL <= html.DIV(stats, Class='load')
    MY_SUB_PANEL <= html.BR()

    for other_state_name in config.STATE_CODE_TABLE:

        if other_state_name != state_name:

            input_change_state = html.INPUT(type="submit", value=other_state_name)
            input_change_state.bind("click", lambda _, s=other_state_name: again(s))

            MY_SUB_PANEL <= input_change_state
            MY_SUB_PANEL <= html.BR()
            MY_SUB_PANEL <= html.BR()


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

    points = dict()

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
        score_table = scoring.scoring(game_scoring, variant_data, ratings)

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

    count = dict()
    for game_id, role_num, _ in tournament_incidents:
        pseudo = gamerole2pseudo[(game_id, role_num)]
        if pseudo not in count:
            count[pseudo] = 1
        else:
            count[pseudo] += 1

    recap_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['rang', 'pseudo', 'score', 'incidents']:
        col = html.TD(field)
        thead <= col
    recap_table <= thead

    rang = 1
    for pseudo, score in sorted(points.items(), key=lambda p: p[1], reverse=True):
        row = html.TR()

        col = html.TD(rang)
        row <= col

        col = html.TD(pseudo)
        row <= col

        col = html.TD(score)
        row <= col

        nb_incidents = count.get(pseudo, 0)
        col = html.TD(nb_incidents)
        row <= col

        recap_table <= row
        rang += 1

    MY_SUB_PANEL <= html.DIV(f"Tournoi {tournament_name}", Class='note')
    MY_SUB_PANEL <= html.BR()

    MY_SUB_PANEL <= recap_table


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

        json_dict = dict()

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/find-player-from-email/{email}"

        # findin pseudo from email : need token
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

        json_dict = dict()

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

        json_dict = dict()

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
    if item_name == 'toutes les parties':
        all_games('en cours')
    if item_name == 'résultats tournoi':
        tournament_result()
    if item_name == 'retrouver à partir du courriel':
        find_from_email_address()
    if item_name == 'récupérer un courriel':
        display_email_address()
    if item_name == 'récupérer un téléphone':
        display_phone_number()

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
        MENU_LEFT <= menu_item


# starts here


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
