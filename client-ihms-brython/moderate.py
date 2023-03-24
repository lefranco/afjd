""" moderate """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import interface
import mapping
import memoize
import scoring
import mydatetime


MAX_LEN_EMAIL = 100

OPTIONS = ['Changer nouvelles', 'Préparer un publipostage', 'Codes de vérification', 'Envoyer un courriel', 'Récupérer un courriel et téléphone', 'Résultats tournoi', 'Destituer arbitre', 'Changer responsable événement', 'Toutes les parties d\'un joueur', 'Les dernières soumissions d\'ordres', 'Vérification des adresses IP', 'Vérification des courriels', 'Courriels non confirmés']


def check_modo(pseudo):
    """ check_modo """

    priviledged = common.PRIVILEDGED
    if not priviledged:
        return False
    moderators_list = priviledged['moderators']
    if pseudo not in moderators_list:
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


def get_this_player_games_playing_in(player_id):
    """ get_this_player_games_playing_in """

    player_games_dict = None

    def reply_callback(req):
        nonlocal player_games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récuperation de la liste des parties du joueur : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récuperation de la liste des parties du joueur : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        player_games_dict = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/player-allocations2/{player_id}"

    # getting player games playing in list : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict(player_games_dict)


def change_news_modo():
    """ change_news_modo """

    def change_news_modo_callback(ev):  # pylint: disable=invalid-name
        """ change_news_modo_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du contenu des nouvelles (modo) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du contenu des nouvelles (modo) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Les nouvelles (modo) ont été changées : {messages}")

        ev.preventDefault()

        news_content = input_news_content.value
        if not news_content:
            alert("Contenu nouvelles manquant")
            return

        json_dict = {
            'topic': 'modo',
            'content': news_content
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/news"

        # changing news : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_news_modo()

    MY_SUB_PANEL <= html.H3("Editer les nouvelles")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    news_content_table_loaded = common.get_news_content()
    if not news_content_table_loaded:
        return

    news_content_loaded = news_content_table_loaded['modo']

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_news_content = html.LEGEND("nouvelles", title="Saisir le nouveau contenu de nouvelles (modo)")
    fieldset <= legend_news_content
    input_news_content = html.TEXTAREA(type="text", rows=20, cols=100)
    input_news_content <= news_content_loaded
    fieldset <= input_news_content
    form <= fieldset

    form <= html.BR()

    input_change_news_content = html.INPUT(type="submit", value="Mettre à jour")
    input_change_news_content.bind("click", change_news_modo_callback)
    form <= input_change_news_content
    form <= html.BR()

    MY_SUB_PANEL <= form


def prepare_mailing():
    """ prepare_mailing """

    def patch_account_callback(ev, player_pseudo):  # pylint: disable=invalid-name
        """ patch_account_callback """

        def reply_callback(req):

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au patch {player_pseudo} : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au patch {player_pseudo} : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            # back to where we started
            MY_SUB_PANEL.clear()
            prepare_mailing()

        ev.preventDefault()

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/remove-newsletter/{player_pseudo}"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Préparation d'un publipostage")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    emails_dict = common.get_all_emails()

    emails_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'courriel', 'confirmé', 'newsletter', 'ne veut plus recevoir']:
        col = html.TD(field)
        thead <= col
    emails_table <= thead

    for pseudo, (email, confirmed, newsletter) in sorted(emails_dict.items(), key=lambda t: t[1][0].upper()):

        if not newsletter:
            continue

        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        if confirmed:
            email_formatted = html.B(email)
        else:
            email_formatted = html.EM(email)

        col = html.TD(email_formatted)
        row <= col

        col = html.TD("Oui" if confirmed else "Non")
        row <= col

        col = html.TD("Oui" if newsletter else "Non")
        row <= col

        form = html.FORM()
        input_patch_account = html.INPUT(type="image", src="./images/refuses.png")
        input_patch_account.bind("click", lambda e, p=pseudo: patch_account_callback(e, p))
        form <= input_patch_account

        col = html.TD(form)
        row <= col

        emails_table <= row

    emails_table2 = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'courriel', 'confirmé', 'newsletter']:
        col = html.TD(field)
        thead <= col
    emails_table2 <= thead

    for pseudo, (email, confirmed, newsletter) in sorted(emails_dict.items(), key=lambda t: t[1][0].upper()):

        if newsletter:
            continue

        row = html.TR()

        col = html.TD(pseudo)
        col.style = {
            'background-color': 'Red'
        }
        row <= col

        if confirmed:
            email_formatted = html.B(email)
        else:
            email_formatted = html.EM(email)

        col = html.TD(email_formatted)
        col.style = {
            'background-color': 'Red'
        }
        row <= col

        col = html.TD("Oui" if confirmed else "Non")
        col.style = {
            'background-color': 'Red'
        }
        row <= col

        col = html.TD("Oui" if newsletter else "Non")
        col.style = {
            'background-color': 'Red'
        }
        row <= col

        emails_table2 <= row

    MY_SUB_PANEL <= html.H4("Publipostage")
    MY_SUB_PANEL <= emails_table
    MY_SUB_PANEL <= html.H4("Information (ATTENTION : ne pas envoyer la lettre d'information)")
    MY_SUB_PANEL <= emails_table2
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV("Les courriels en gras sont confimés, les courriels en italique ne le sont pas.", Class='note')


def show_verif_codes():
    """ show_verif_codes """

    MY_SUB_PANEL <= html.H3("Les codes de vérification pour le forum")

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

    players_table = html.TABLE()

    fields = ['pseudo', 'code']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'code': 'code'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    for pseudo in sorted(players_dict, key=lambda p: p.upper()):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        code = common.verification_code(pseudo)
        col = html.TD(code)
        row <= col

        players_table <= row

    MY_SUB_PANEL <= players_table


def sendmail():
    """ sendmail """

    def sendmail_callback(ev):  # pylint: disable=invalid-name
        """ sendmail_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            common.info_dialog(f"Message émis vers : {addressed_user_name}")

        ev.preventDefault()

        addressed_user_name = input_addressed.value
        if not addressed_user_name:
            alert("User name destinataire manquant")
            return

        subject = "Message de la part d'un modérateur du site https://diplomania-gen.fr (AFJD)"

        if not input_message.value:
            alert("Contenu du message vide")
            # back to where we started
            MY_SUB_PANEL.clear()
            sendmail()
            return

        body = input_message.value

        addressed_id = players_dict[addressed_user_name]
        addressees = [addressed_id]

        json_dict = {
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'type': 'forced',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        sendmail()

    MY_SUB_PANEL <= html.H3("Envoi de courriel individuel")

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

    # all players can be usurped
    possible_addressed = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_addressee = html.LEGEND("Destinataire", title="Sélectionner le joueur à contacter par courriel")
    fieldset <= legend_addressee
    input_addressed = html.SELECT(type="select-one", value="")
    for addressee_pseudo in sorted(possible_addressed, key=lambda pu: pu.upper()):
        option = html.OPTION(addressee_pseudo)
        input_addressed <= option
    fieldset <= input_addressed
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_message = html.LEGEND("Votre message", title="Qu'avez vous à lui dire ?")
    fieldset <= legend_message
    input_message = html.TEXTAREA(type="text", rows=8, cols=80)
    fieldset <= input_message
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Envoyer le courriel")
    input_select_player.bind("click", sendmail_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def display_personal_info():
    """ display_personal_info """

    def display_personal_info_callback(ev):  # pylint: disable=invalid-name
        """ display_personal_info_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des informations personnelles : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des informations personnelles : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            email = req_result['email']
            telephone = req_result['telephone']
            alert(f"Son courriel est '{email}' et son téléphone est '{telephone}'")

        ev.preventDefault()

        contact_user_name = input_contact.value
        if not contact_user_name:
            alert("User name manquant")
            return

        json_dict = {}

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player-information/{contact_user_name}"

        # getting email: need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        display_personal_info()

    MY_SUB_PANEL <= html.H3("Afficher les informations personnelles d'un compte")

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
    legend_contact = html.LEGEND("Contact", title="Sélectionner le joueur dont on veut les informations personnelles")
    fieldset <= legend_contact
    input_contact = html.SELECT(type="select-one", value="")
    for contact_pseudo in sorted(possible_contacts, key=lambda pu: pu.upper()):
        option = html.OPTION(contact_pseudo)
        input_contact <= option
    fieldset <= input_contact
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Récupérer ses informations personnelles")
    input_select_player.bind("click", display_personal_info_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def tournament_result():
    """ tournament_result """

    MY_SUB_PANEL <= html.H3("Résultats intermédiaires du tournoi")

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

    tournament_dict = common.get_tournament_data(game)
    if not tournament_dict:
        alert("Pas de tournoi pour cette partie ou problème au chargement liste des parties du tournoi")
        return

    tournament_name = tournament_dict['name']
    tournament_id = tournament_dict['identifier']
    games_in = tournament_dict['games']

    MY_SUB_PANEL <= f"Tournoi concerné : {tournament_name}"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

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

        rolename2num = {variant_data.role_name_table[r]: n for n, r in variant_data.roles.items()}

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
        pseudo = gamerole2pseudo[(game_id, role_num)]
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

    MY_SUB_PANEL <= html.DIV(f"Tournoi {tournament_name}", Class='note')

    MY_SUB_PANEL <= html.H4("Classement")
    MY_SUB_PANEL <= recap_table

    MY_SUB_PANEL <= html.H4("Retards")
    MY_SUB_PANEL <= incident_table

    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées", Class='note')

    MY_SUB_PANEL <= html.H4("Désordres Civils")
    MY_SUB_PANEL <= incident_table2


def revoke_master():
    """ revoke_master """

    def revoke_master_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la destitution de l'arbitre : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Erreur à la destitution de l'arbitre : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                revoke_master()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez destitué l'arbitre : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            revoke_master()

        ev.preventDefault()

        json_dict = {
            'pseudo': pseudo,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/revoke/{game_id}"

        # revoking master : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Destituer l'arbitre")

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

    if 'GAME_VARIANT' not in storage:
        alert("ERREUR : variante introuvable")
        return

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    game_name = storage['GAME']
    MY_SUB_PANEL <= f"Partie concernée : {game_name}"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    game_id = storage['GAME_ID']

    form = html.FORM()

    input_revoke_master = html.INPUT(type="submit", value="Destituer l'arbitre de la partie sélectionnée")
    input_revoke_master.bind("click", revoke_master_callback)
    form <= input_revoke_master

    MY_SUB_PANEL <= form


def change_manager():
    """ change_manager """

    def promote_managers_callback(ev):  # pylint: disable=invalid-name
        """ promote_managers_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la promotion responsable événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la promotion responsable événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            common.info_dialog(f"Il a été promu responsable: {manager}")

        ev.preventDefault()

        manager = input_manager.value
        manager_id = players_dict[manager]

        json_dict = {
            'manager_id': manager_id,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/events_manager/{event_id}"

        # updating an event : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_manager()

    MY_SUB_PANEL <= html.H3("Changer le responsable de l'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    if 'EVENT' not in storage:
        alert("Il faut sélectionner un événement au préalable")
        return

    event_name = storage['EVENT']
    events_dict = common.get_events_data()

    # delete obsolete event
    if event_name not in [g['name'] for g in events_dict.values()]:
        del storage['EVENT']
        alert("Votre événement sélectionné n'existe plus")
        return

    eventname2id = {v['name']: int(k) for k, v in events_dict.items()}
    event_id = eventname2id[event_name]

    MY_SUB_PANEL <= f"Evénement concerné : {event_name}"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    players_dict = common.get_players()
    if not players_dict:
        return

    # all players can be usurped
    possible_managers = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_manager = html.LEGEND("Destinataire", title="Sélectionner le nouveau responsable")
    fieldset <= legend_manager
    input_manager = html.SELECT(type="select-one", value="")
    for manager_pseudo in sorted(possible_managers, key=lambda pu: pu.upper()):
        option = html.OPTION(manager_pseudo)
        input_manager <= option
    fieldset <= input_manager
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Promouvoir responsable")
    input_select_player.bind("click", promote_managers_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def show_player_games(pseudo_player, game_list):
    """ show_player_games """

    def display_all_games_callback(ev):  # pylint: disable=invalid-name
        """ display_personal_info_callback """

        ev.preventDefault()

        selected_pseudo_player = input_player.value

        player_id = players_dict[selected_pseudo_player]

        player_games = get_this_player_games_playing_in(player_id)
        if player_games is None:
            alert("Erreur chargement liste parties jouées par le joueur")
            return

        game_list = [int(k) for k, v in player_games.items() if v >= 1]

        # back to where we started
        MY_SUB_PANEL.clear()
        show_player_games(selected_pseudo_player, game_list)

    MY_SUB_PANEL <= html.H3("Toutes les parties d'un compte")

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

    # all players can be investigated
    possible_players = set(players_dict.keys())

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_player = html.LEGEND("Joueur", title="Sélectionner le joueur dont on veut la liste des parties")
    fieldset <= legend_player
    input_player = html.SELECT(type="select-one", value="")
    for player_pseudo in sorted(possible_players, key=lambda pu: pu.upper()):
        option = html.OPTION(player_pseudo)
        input_player <= option
    fieldset <= input_player
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Récupérer la liste de ses parties")
    input_select_player.bind("click", display_all_games_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form

    if pseudo_player:
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()

        MY_SUB_PANEL <= f"Parties de {pseudo_player} (avec un role joueur et non arbitre)"
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()

    if game_list:
        time_stamp_now = time.time()

        games_table = html.TABLE()

        # the display order
        fields = ['current_state', 'name', 'deadline', 'variant', 'used_for_elo', 'nopress_game', 'nomessage_game']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'current_state': 'état', 'name': 'nom', 'deadline': 'date limite', 'variant': 'variante', 'used_for_elo': 'elo', 'nopress_game': 'publics(*)', 'nomessage_game': 'privés(*)'}[field]
            col = html.TD(field_fr)
            thead <= col
        games_table <= thead

        for game_id_str, data in sorted(games_dict.items(), key=lambda t: int(t[0]), reverse=True):

            game_id = int(game_id_str)
            if game_id not in game_list:
                continue

            row = html.TR()
            for field in fields:

                value = data[field]
                colour = None
                game_name = data['name']

                if field == 'current_state':
                    if value == 1:
                        colour = 'Orange'
                    state_loaded = value
                    for possible_state_code, possible_state_desc in config.STATE_CODE_TABLE.items():
                        if possible_state_desc == state_loaded:
                            state_loaded = possible_state_code
                            break
                    value = state_loaded

                if field == 'name':
                    value = game_name

                if field == 'deadline':
                    deadline_loaded = value
                    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                    datetime_deadline_loaded_str = mydatetime.strftime2(*datetime_deadline_loaded)
                    value = datetime_deadline_loaded_str

                    if data['fast']:
                        if time_stamp_now > deadline_loaded:
                            colour = config.PASSED_DEADLINE_COLOUR
                    else:
                        # we are after everything !
                        if time_stamp_now > deadline_loaded + 60 * 60 * 24 * config.CRITICAL_DELAY_DAY:
                            colour = config.CRITICAL_COLOUR
                        # we are after deadline + grace
                        elif time_stamp_now > deadline_loaded + 60 * 60 * data['grace_duration']:
                            colour = config.PASSED_GRACE_COLOUR
                        # we are after deadline + slight
                        elif time_stamp_now > deadline_loaded + config.SLIGHT_DELAY_SEC:
                            colour = config.PASSED_DEADLINE_COLOUR
                        # we are slightly after deadline
                        elif time_stamp_now > deadline_loaded:
                            colour = config.SLIGHTLY_PASSED_DEADLINE_COLOUR
                        # deadline is today
                        elif time_stamp_now > deadline_loaded - config.APPROACH_DELAY_SEC:
                            colour = config.APPROACHING_DEADLINE_COLOUR

                if field == 'used_for_elo':
                    value = "Oui" if value else "Non"

                if field == 'nopress_game':
                    value1 = value
                    value2 = data['nopress_current']
                    if value2 == value1:
                        value = "Non" if value1 else "Oui"
                    else:
                        value1 = "Non" if value1 else "Oui"
                        value2 = "Non" if value2 else "Oui"
                        value = f"{value1} ({value2})"

                if field == 'nomessage_game':
                    value1 = value
                    value2 = data['nomessage_current']
                    if value2 == value1:
                        value = "Non" if value1 else "Oui"
                    else:
                        value1 = "Non" if value1 else "Oui"
                        value2 = "Non" if value2 else "Oui"
                        value = f"{value1} ({value2})"

                col = html.TD(value)
                if colour is not None:
                    col.style = {
                        'background-color': colour
                    }

                row <= col
            games_table <= row

        MY_SUB_PANEL <= games_table
        MY_SUB_PANEL <= html.BR()


def show_last_submissions():
    """ show_last_submissions """

    MY_SUB_PANEL <= html.H3("Les dernières soumissions d'ordres")

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

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    ip_submission_table = common.get_ip_submission_table()
    if not ip_submission_table:
        return

    submission_table = ip_submission_table['submissions_list']

    players_table = html.TABLE()

    fields = ['date', 'pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'date': 'date', 'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    for data in sorted(submission_table, key=lambda c: c[0], reverse=True):

        row = html.TR()
        for field in fields:

            if field == 'date':
                time_stamp = data[0]
                submit_time = mydatetime.fromtimestamp(time_stamp)
                submit_time_str = mydatetime.strftime(*submit_time)
                value = submit_time_str

            if field == 'pseudo':
                value = num2pseudo[data[1]]

            col = html.TD(value)

            row <= col

        players_table <= row

    MY_SUB_PANEL <= players_table


def show_ip_addresses():
    """ show_ip_addresses """

    MY_SUB_PANEL <= html.H3("Vérification des doublons sur les adresses IP à la soumission d'ordres")

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

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    ip_submission_table = common.get_ip_submission_table()
    if not ip_submission_table:
        return

    ip_table = ip_submission_table['addresses_list']

    players_table = html.TABLE()

    fields = ['ip_value', 'pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'ip_value': 'adresse IP', 'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    # duplicated ones
    sorted_ips = sorted([i[0] for i in ip_table])
    duplicated_ips = {sorted_ips[i] for i in range(len(sorted_ips)) if (i < len(sorted_ips) - 1 and sorted_ips[i] == sorted_ips[i + 1]) or (i > 0 and sorted_ips[i] == sorted_ips[i - 1])}

    # same as admin ones (or orangecar)
    admin_ips = {i[0] for i in ip_table if num2pseudo[i[1]] in [common.ADMIN_PSEUDO, common.ALTERNATE_ADMIN_PSEUDO]}

    for data in sorted(ip_table, key=lambda c: (c[0], num2pseudo[c[1]].upper())):

        row = html.TR()
        for field in fields:

            if field == 'pseudo':
                value = num2pseudo[data[1]]

            if field == 'ip_value':
                value = data[0]

                if value in admin_ips:
                    colour = 'blue'
                elif value in duplicated_ips:
                    colour = 'red'
                else:
                    colour = None

            col = html.TD(value)

            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        players_table <= row

    MY_SUB_PANEL <= players_table


def show_all_emails():
    """ show_all_emails """

    MY_SUB_PANEL <= html.H3("Vérification des doublons des courriels")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    emails_dict = common.get_all_emails()
    if not emails_dict:
        return

    emails_table = html.TABLE()

    fields = ['email', 'pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'email': 'courriel', 'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    emails_table <= thead

    # duplicated ones
    sorted_emails = sorted([e[0] for e in emails_dict.values()])
    duplicated_emails = {sorted_emails[i] for i in range(len(sorted_emails)) if (i < len(sorted_emails) - 1 and sorted_emails[i] == sorted_emails[i + 1]) or (i > 0 and sorted_emails[i] == sorted_emails[i - 1])}

    for pseudo, (email, _, _) in sorted(emails_dict.items(), key=lambda t: t[1][0].upper()):

        row = html.TR()
        for field in fields:

            colour = None

            if field == 'email':
                value = email

                if value in duplicated_emails:
                    colour = 'red'

            if field == 'pseudo':
                value = pseudo

            col = html.TD(value)

            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        emails_table <= row

    MY_SUB_PANEL <= emails_table


def show_non_confirmed_data():
    """ show_non_confirmed_data """

    MY_SUB_PANEL <= html.H3("Les inscrits non confirmés")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_modo(pseudo):
        alert("Pas le bon compte (pas modo)")
        return

    emails_dict = common.get_all_emails()
    if not emails_dict:
        return

    players_table = html.TABLE()

    fields = ['pseudo', 'email']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'email': 'courriel'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    count = 0
    for pseudo, (email, confirmed, _) in sorted(emails_dict.items(), key=lambda t: t[0].upper()):

        if confirmed:
            continue

        row = html.TR()
        for field in fields:

            if field == 'pseudo':
                value = pseudo

            if field == 'email':
                value = email

            col = html.TD(value)
            row <= col

            count += 1

        players_table <= row

    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} comptes non confirmés")


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

MY_SUB_PANEL = html.DIV(id="moderate")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Changer nouvelles':
        change_news_modo()
    if item_name == 'Préparer un publipostage':
        prepare_mailing()
    if item_name == 'Codes de vérification':
        show_verif_codes()
    if item_name == 'Envoyer un courriel':
        sendmail()
    if item_name == 'Récupérer un courriel et téléphone':
        display_personal_info()
    if item_name == 'Résultats tournoi':
        tournament_result()
    if item_name == 'Destituer arbitre':
        revoke_master()
    if item_name == 'Changer responsable événement':
        change_manager()
    if item_name == 'Toutes les parties d\'un joueur':
        show_player_games(None, [])
    if item_name == 'Les dernières soumissions d\'ordres':
        show_last_submissions()
    if item_name == 'Vérification des adresses IP':
        show_ip_addresses()
    if item_name == 'Vérification des courriels':
        show_all_emails()
    if item_name == 'Courriels non confirmés':
        show_non_confirmed_data()

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
