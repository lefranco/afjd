""" moderate """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from time import time

from browser import html, ajax, alert, document, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import interface
import mapping
import memoize
import mydatetime
import play
import mydialog


MAX_LEN_EMAIL = 100

OPTIONS = {
    # communication
    'Changer nouvelles': "Changer nouvelles du site pour le modérateur",
    'Effacer le chat': "Effacer le contenu des discussions en ligne (chat) en cours",
    'Préparer un publipostage': "Préparer un publipostage vers tous les utilisateurs du site",
    'Annoncer dans toutes les parties': "Annoncer dans toutes les parties en cours du site",
    'Annoncer dans la partie': "Annoncer dans la partie séléctionnée",
    'Récupérer un courriel et téléphone': "Récupérer un courriel et téléphone d'un utilisateur du site",
    # surveillance
    'Tous les ordres manquants': "Tous les ordres manquants sur les parties en cours",
    'Pires récidivistes retard et abandon': "Pires récidivistes retard et abandon sur les parties en cours",
    'Toutes les parties d\'un joueur': "Toutes les parties d\'un joueur du site",
    'Tous les joueurs de la partie': "Toutes les joueurs d'une partie du site",
    'Dernières soumissions d\'ordres': "Dernières soumissions d\'ordres sur les parties du site",
    'Vérification adresses IP': "Détecter les doubons d'adresses IP des utilisateurs du site",
    'Vérification courriels': "Détecter les doubons de courriels des utilisateurs du site",
    'Codes de vérification': "Codes de vérification pour le forum",
    # management
    'Destituer arbitre partie': "Destituer l'arbitre de la partie sélectionnée",
    'Changer responsable tournoi': "Changer le responsable tournoi de la partie sélectionnée",
    'Changer responsable événement': "Changer le responsable de l'événement séléctionné"
}


def show_game_selected():
    """  show_game_selected """

    log_message = html.DIV()
    if 'GAME' in storage:
        log_message <= "La partie sélectionnée est "
        log_message <= html.B(storage['GAME'])
    else:
        log_message <= "Pas de partie sélectionnée..."

    show_game_selected_panel = html.DIV(id="show_game_selected")
    show_game_selected_panel.attrs['style'] = 'text-align: left'
    show_game_selected_panel <= log_message

    if 'show_game_selected' in document:
        del document['show_game_selected']

    document <= show_game_selected_panel


def get_all_games_roles_missing_orders():
    """ get_all_games_roles_missing_orders : returns empty dict if problem """

    dict_missing_orders_data = {}

    def reply_callback(req):
        nonlocal dict_missing_orders_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des rôles dont il manque les ordres pour toutes les parties en cours : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des rôles dont il manque les ordres pour toutes les parties en cours : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        dict_missing_orders_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/all-games-missing-orders"

    # get roles that submitted orders : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_missing_orders_data


def get_current_worst_annoyers():
    """ get_current_worst_annoyers : returns empty dict if problem """

    dict_current_worst_annoyers_data = {}

    def reply_callback(req):
        nonlocal dict_current_worst_annoyers_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des pires recidivistes du retard : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des pires recidivistes du retard : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        dict_current_worst_annoyers_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/current-worst-annoyers"

    # get roles that submitted orders : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict_current_worst_annoyers_data


def get_this_player_games_playing_in(player_id):
    """ get_this_player_games_playing_in """

    player_games_dict = None

    def reply_callback(req):
        nonlocal player_games_dict
        req_result = loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict(player_games_dict)


def change_news_modo():
    """ change_news_modo """

    def change_news_modo_callback(ev):  # pylint: disable=invalid-name
        """ change_news_modo_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du contenu des nouvelles (modo) : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du contenu des nouvelles (modo) : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Les nouvelles (modérateur) ont été changées : {messages}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_news_modo()

    MY_SUB_PANEL <= html.H3("Editer les nouvelles")

    if not common.check_modo():
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

    input_change_news_content = html.INPUT(type="submit", value="Mettre à jour", Class='btn-inside')
    input_change_news_content.bind("click", change_news_modo_callback)
    form <= input_change_news_content
    form <= html.BR()

    MY_SUB_PANEL <= form


def erase_chat_content():
    """ erase_chat_content """

    def erase_chat_callback(ev):  # pylint: disable=invalid-name
        """ erase_chat_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'effacement des chats : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'effacement des chats : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le contenu des disussions a été effacé ! {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            erase_chat_content()

        ev.preventDefault()

        json_dict = {}

        host = config.SERVER_CONFIG['EMAIL']['HOST']
        port = config.SERVER_CONFIG['EMAIL']['PORT']
        url = f"{host}:{port}/chat-messages"

        # getting email: need token
        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        erase_chat_content()

    MY_SUB_PANEL <= html.H3("Effacer le contenu des discussions en ligne (chat)")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    button = html.BUTTON("Raser la bête",  Class='btn-inside')
    button.bind("click", erase_chat_callback)

    MY_SUB_PANEL <= button


def prepare_mailing():
    """ prepare_mailing """

    def download_emails_callback(ev):  # pylint: disable=invalid-name

        ev.preventDefault()

        # needed too for some reason
        MY_SUB_PANEL <= html.A(id='download_link')

        # perform actual exportation
        text_file_as_blob = window.Blob.new(['\n'.join(emails_list)], {'type': 'text/plain'})
        download_link = document['download_link']
        download_link.download = "emails_for_mailing.txt"
        download_link.href = window.URL.createObjectURL(text_file_as_blob)
        document['download_link'].click()

    def patch_account_refuses_callback(ev, player_pseudo):  # pylint: disable=invalid-name
        """ patch_account_refuses_callback """

        def reply_callback(req):

            req_result = loads(req.text)
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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def patch_account_confirmed_callback(ev, player_pseudo):  # pylint: disable=invalid-name
        """ patch_account_confirmed_callback """

        def reply_callback(req):

            req_result = loads(req.text)
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
        url = f"{host}:{port}/confirm-email/{player_pseudo}"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def patch_account_unconfirmed_callback(ev, player_pseudo):  # pylint: disable=invalid-name
        """ patch_account_unconfirmed_callback """

        def reply_callback(req):

            req_result = loads(req.text)
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
        url = f"{host}:{port}/unconfirm-email/{player_pseudo}"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Préparation d'un publipostage")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    emails_dict = common.get_all_emails()

    emails_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'nom', 'prénom', 'courriel', 'confirmation', 'action', 'publipostage', 'action']:
        col = html.TD(field)
        thead <= col
    emails_table <= thead

    emails_list = []

    for pseudo, (email, family_name, first_name, confirmed, newsletter) in sorted(emails_dict.items(), key=lambda t: t[1][0].upper()):

        if not newsletter:
            continue

        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        col = html.TD(family_name)
        row <= col

        col = html.TD(first_name)
        row <= col

        emails_list.append(email)

        col = html.TD(email)
        if not confirmed:
            col.style = {
                'background-color': 'red'
            }
        row <= col

        col = html.TD()
        if confirmed:
            col <= "Confirmé"
        else:
            col <= "Non confirmé"
        row <= col

        col = html.TD()
        if confirmed:
            input_patch_account_not_confirmed = html.BUTTON("Enlever la confirmation", Class='btn-inside')
            input_patch_account_not_confirmed.bind("click", lambda e, p=pseudo: patch_account_unconfirmed_callback(e, p))
            col <= input_patch_account_not_confirmed
        else:
            input_patch_account_confirmed = html.BUTTON("Confirmer", Class='btn-inside')
            input_patch_account_confirmed.bind("click", lambda e, p=pseudo: patch_account_confirmed_callback(e, p))
            col <= input_patch_account_confirmed
        row <= col

        col = html.TD()
        col <= "Accepte"
        row <= col

        col = html.TD()
        input_patch_account_refuses = html.BUTTON("Faire refuser", Class='btn-inside')
        input_patch_account_refuses.bind("click", lambda e, p=pseudo: patch_account_refuses_callback(e, p))
        col <= input_patch_account_refuses
        row <= col

        emails_table <= row

    emails_table2 = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'nom', 'prénom', 'courriel', 'confirmation', 'action', 'publipostage']:
        col = html.TD(field)
        thead <= col
    emails_table2 <= thead

    for pseudo, (email, family_name, first_name, confirmed, newsletter) in sorted(emails_dict.items(), key=lambda t: t[1][0].upper()):

        if newsletter:
            continue

        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        col = html.TD(family_name)
        row <= col

        col = html.TD(first_name)
        row <= col

        col = html.TD(email)
        if not confirmed:
            col.style = {
                'background-color': 'red'
            }
        row <= col

        col = html.TD()
        if confirmed:
            col <= "Confirmé"
        else:
            col <= "Non confirmé"
        row <= col

        col = html.TD()
        if confirmed:
            input_patch_account_not_confirmed = html.BUTTON("Enlever la confirmation", Class='btn-inside')
            input_patch_account_not_confirmed.bind("click", lambda e, p=pseudo: patch_account_unconfirmed_callback(e, p))
            col <= input_patch_account_not_confirmed
        else:
            input_patch_account_confirmed = html.BUTTON("Confirmer", Class='btn-inside')
            input_patch_account_confirmed.bind("click", lambda e, p=pseudo: patch_account_confirmed_callback(e, p))
            col <= input_patch_account_confirmed
        row <= col

        col = html.TD()
        col <= "Refuse"
        row <= col

        emails_table2 <= row

    MY_SUB_PANEL <= html.H4("Ceux qui sont d'accord pour recevoir la newletter")
    MY_SUB_PANEL <= emails_table

    MY_SUB_PANEL <= html.BR()
    input_export_emails = html.INPUT(type="submit", value="Télécharger la liste des courriels", Class='btn-inside')
    input_export_emails.bind("click", download_emails_callback)
    MY_SUB_PANEL <= input_export_emails

    MY_SUB_PANEL <= html.H4("Ceux qui ne le sont pas (pour information)")
    MY_SUB_PANEL <= emails_table2


def general_announce():
    """ general_announce """

    def add_declaration_callback(ev):  # pylint: disable=invalid-name
        """ add_declaration_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout annonce générale dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout annonce générale dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"L'annonce dans toutes les parties a été faite ! {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            general_announce()

        ev.preventDefault()

        content = input_declaration.value

        if not content:
            alert("Pas de contenu pour cette déclaration !")
            MY_SUB_PANEL.clear()
            game_announce()
            return

        json_dict = {
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/announce-games"

        # adding a declaration in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Annoncer dans toutes la partie en cours")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    announce = ""

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre déclaration", title="Qu'avez vous à déclarer dans toutes les parties en cours ?")
    fieldset <= legend_declaration
    input_declaration = html.TEXTAREA(type="text", rows=8, cols=80)
    input_declaration <= announce
    fieldset <= input_declaration
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Déclarer dans toutes les parties en cours", Class='btn-inside')
    input_declare_in_game.bind("click", add_declaration_callback)
    form <= input_declare_in_game

    MY_SUB_PANEL <= form


def game_announce():
    """ game_announce """

    def add_declaration_callback(ev):  # pylint: disable=invalid-name
        """ add_declaration_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de déclaration (annonce) dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de déclaration (annonce) dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"L'annonce dans la partie a été faite ! {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            game_announce()

        ev.preventDefault()

        anonymous = False
        announce = True

        content = input_declaration.value

        if not content:
            alert("Pas de contenu pour cette déclaration !")
            MY_SUB_PANEL.clear()
            game_announce()
            return

        # to avoid typing all over again
        storage['ANNOUNCE'] = content

        role_id = 0
        role_name = ""

        json_dict = {
            'role_id': role_id,
            'anonymous': anonymous,
            'announce': announce,
            'role_name': role_name,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{game_id}"

        # adding a declaration in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def declarations_reload(game_id):
        """ declarations_reload """

        declarations = []

        def reply_callback(req):
            nonlocal declarations
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de déclarations dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de déclarations dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            declarations = req_result['declarations_list']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{game_id}"

        # extracting declarations from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return declarations

    MY_SUB_PANEL <= html.H3("Annoncer dans la partie")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game_name = storage['GAME']
    MY_SUB_PANEL <= f"Partie concernée : {game_name}"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    game_id = storage['GAME_ID']

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement info joueurs")
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    game_master_id = common.get_game_master(game_id)
    if game_master_id is not None:
        game_master = id2pseudo[game_master_id]

    game_players_dict = common.get_game_players_data(game_id)
    if not game_players_dict:
        alert("Erreur chargement joueurs de la partie")
        return

    variant_name_loaded = storage['GAME_VARIANT']

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # selected interface (user choice)
    interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

    # from interface chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    announce = ""
    if 'ANNOUNCE' in storage:
        announce = storage['ANNOUNCE']

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre déclaration", title="Qu'avez vous à déclarer dans la partie ?")
    fieldset <= legend_declaration
    input_declaration = html.TEXTAREA(type="text", rows=8, cols=80)
    input_declaration <= announce
    fieldset <= input_declaration
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Annoncer dans la partie", Class='btn-inside')
    input_declare_in_game.bind("click", add_declaration_callback)
    form <= input_declare_in_game

    MY_SUB_PANEL <= form

    # now we display declarations

    declarations = declarations_reload(game_id)
    # there can be no message (if no declaration of failed to load)

    # insert new field 'type'
    declarations = [(common.MessageTypeEnum.TEXT, 0, i, ann, ano, r, t, c) for (i, ann, ano, r, t, c) in declarations]

    # get the transition table
    game_transitions = common.game_transitions_reload(game_id)

    # add fake declarations (game transitions) and sort
    fake_declarations = [(common.MessageTypeEnum.SEASON, int(k), -1, False, False, -1, v, common.readable_season(int(k), variant_data)) for k, v in game_transitions.items()]
    declarations.extend(fake_declarations)

    # get the dropouts table
    game_replacements = common.game_replacements_reload(game_id)

    # add fake messages (game replacements)
    fake_declarations = [(common.MessageTypeEnum.REPLACEMENT, 0, -1, False, False, r, d, f"Le joueur ou arbitre avec le pseudo '{id2pseudo[p]}' et avec ce rôle {'a été mis dans' if e else 'a été retiré de'} la partie...") for r, p, d, e in game_replacements]
    declarations.extend(fake_declarations)

    # sort with all that was added
    declarations.sort(key=lambda d: (float(d[6]), float(int(d[2] != -1)), float(d[1])), reverse=True)

    declarations_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    declarations_table <= thead

    role2pseudo = {v: k for k, v in game_players_dict.items()}

    for type_, _, id_, announce, anonymous, role_id_msg, time_stamp, content in declarations:

        if type_ is common.MessageTypeEnum.TEXT:
            if announce:
                class_ = 'text_announce'
            elif anonymous:
                class_ = 'text_anonymous'
            else:
                class_ = 'text'
        elif type_ is common.MessageTypeEnum.SEASON:
            class_ = 'season'
        elif type_ is common.MessageTypeEnum.REPLACEMENT:
            class_ = 'replacement'

        row = html.TR()

        id_txt = str(id_) if id_ != -1 else ""
        col = html.TD(id_txt, Class=class_)
        row <= col

        date_desc_gmt = mydatetime.fromtimestamp(time_stamp)
        date_desc_gmt_str = mydatetime.strftime(*date_desc_gmt)

        col = html.TD(f"{date_desc_gmt_str}", Class=class_)
        row <= col

        role_icon_img = ""
        pseudo_there = ""
        if role_id_msg != -1:

            if announce:

                player_id = role_id_msg
                pseudo_there = id2pseudo[player_id]

            else:

                role = variant_data.roles[role_id_msg]
                role_name = variant_data.role_name_table[role]
                role_icon_img = common.display_flag(variant_name_loaded, interface_chosen, role_id_msg, role_name)

                # player
                if role_id_msg == 0:
                    if game_master:
                        pseudo_there = game_master
                elif role_id_msg in role2pseudo:
                    player_id_str = role2pseudo[role_id_msg]
                    player_id = int(player_id_str)
                    pseudo_there = id2pseudo[player_id]

        col = html.TD(Class=class_)

        col <= role_icon_img
        if pseudo_there:
            col <= html.BR()
            col <= pseudo_there

        row <= col

        col = html.TD(Class=class_)

        for line in content.split('\n'):
            col <= line
            col <= html.BR()

        row <= col

        declarations_table <= row

    # now we can display

    # header very simplified
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    # declarations already
    MY_SUB_PANEL <= declarations_table
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    information = html.DIV(Class='note')
    information <= "Le pseudo affiché est celui du joueur en cours, pas forcément celui de l'auteur réel du message"
    MY_SUB_PANEL <= information


def display_personal_info():
    """ display_personal_info """

    def display_personal_info_callback(ev):  # pylint: disable=invalid-name
        """ display_personal_info_callback """

        def reply_callback(req):
            req_result = loads(req.text)
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
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        display_personal_info()

    MY_SUB_PANEL <= html.H3("Afficher les informations personnelles d'un compte")

    if not common.check_modo():
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
    input_contact = html.SELECT(type="select-one", value="", Class='btn-inside')
    for contact_pseudo in sorted(possible_contacts, key=lambda pu: pu.upper()):
        option = html.OPTION(contact_pseudo)
        input_contact <= option
    fieldset <= input_contact
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Récupérer ses informations personnelles", Class='btn-inside')
    input_select_player.bind("click", display_personal_info_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def all_missing_orders():
    """ all_missing_orders """

    def select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        show_game_selected()

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    MY_SUB_PANEL <= html.H3("Tous les ordres manquants")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    state = 1

    games_dict = common.get_games_data(state)
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    players_dict = common.get_players_data()
    if not players_dict:
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data(state)
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']

    # gather game to master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            if str(game_id) in games_dict:
                game = games_dict[str(game_id)]['name']
                game_master_dict[game] = master

    players_dict2 = common.get_players()
    if not players_dict2:
        return

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict2.items()}

    dict_missing_orders_data = get_all_games_roles_missing_orders()
    if not dict_missing_orders_data:
        alert("Erreur chargement des ordres manquants dans les parties")
        return

    delays_table = html.TABLE()

    # the display order
    fields = ['name', 'go_game', 'late', 'deadline', 'current_advancement', 'variant', 'used_for_elo', 'master']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'go_game': 'aller dans la partie', 'late': 'en retard', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'variant': 'variante', 'used_for_elo': 'elo', 'master': 'arbitre'}[field]
        col = html.TD(field_fr)
        thead <= col
    delays_table <= thead

    time_stamp_now = time()

    gameover_table = {int(game_id_str): data['soloed'] or data['finished'] for game_id_str, data in games_dict.items()}

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    # force sort according to deadline (latest games first of course)
    for game_id_str, data in sorted(games_dict.items(), key=lambda t: t[1]['deadline']):

        data['go_game'] = None
        data['late'] = None
        data['master'] = None

        # must be ongoing game
        if data['current_state'] != 1:
            continue

        game_id = int(game_id_str)

        # must not be game over
        if gameover_table[game_id]:
            continue

        # must be late
        deadline_loaded = data['deadline']
        if time_stamp_now <= deadline_loaded:
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

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None
            game_name = data['name']

            if field == 'name':
                value = game_name

            if field == 'go_game':
                if storage['GAME_ACCESS_MODE'] == 'button':
                    form = html.FORM()
                    input_jump_game = html.INPUT(type="image", src="./images/play.png", title="Pour aller dans la partie", Class='btn-inside')
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                    form <= input_jump_game
                    value = form
                else:
                    img = html.IMG(src="./images/play.png", title="Pour aller dans la partie")
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= img
                    value = link

            if field == 'late':
                value = html.DIV()
                for role_id_str, player_id in dict_missing_orders_data[game_id_str].items():
                    role_id = int(role_id_str)
                    role = variant_data.roles[role_id]
                    role_name = variant_data.role_name_table[role]
                    role_icon_img = common.display_flag(variant_name_loaded, interface_chosen, role_id, role_name)
                    value <= role_icon_img
                    value <= " "
                    value <= num2pseudo[player_id]
                    value <= html.BR()

            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                datetime_deadline_loaded_str = mydatetime.strftime(*datetime_deadline_loaded, year_first=True)
                value = datetime_deadline_loaded_str

                if data['fast']:
                    factor = 60
                else:
                    factor = 60 * 60

                # game over
                if gameover_table[game_id]:
                    # should not happen here
                    if data['soloed']:
                        colour = config.SOLOED_COLOUR
                        value = "(solo)"
                    elif data['finished']:
                        colour = config.FINISHED_COLOUR
                        value = "(terminée)"

                elif int(data['current_state']) == 1:

                    # we are after everything !
                    if time_stamp_now > deadline_loaded + factor * 24 * config.CRITICAL_DELAY_DAY:
                        colour = config.CRITICAL_COLOUR
                    # we are after deadline + grace
                    elif time_stamp_now > deadline_loaded + factor * data['grace_duration']:
                        colour = config.PASSED_GRACE_COLOUR
                    # we are after deadline + slight
                    elif time_stamp_now > deadline_loaded + config.SLIGHT_DELAY_SEC:
                        colour = config.PASSED_DEADLINE_COLOUR
                    # we are slightly after deadline
                    elif time_stamp_now > deadline_loaded:
                        colour = config.SLIGHTLY_PASSED_DEADLINE_COLOUR
                    # deadline is today
                    elif time_stamp_now > deadline_loaded - config.APPROACH_DELAY_SEC:
                        # should not happen here
                        colour = config.APPROACHING_DEADLINE_COLOUR

            if field == 'current_advancement':
                advancement_loaded = value
                nb_max_cycles_to_play = data['nb_max_cycles_to_play']
                value = common.get_full_season(advancement_loaded, variant_data, nb_max_cycles_to_play, False)

            if field == 'used_for_elo':
                value = "Oui" if value else "Non"

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        delays_table <= row

    MY_SUB_PANEL <= delays_table


def current_worst_annoyers():
    """ current_worst_annoyers """

    MY_SUB_PANEL <= html.H3("Les pires récidivistes du retard ou de l'abandon dans les parties en cours")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    games_dict = common.get_games_data(1)
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    players_dict = common.get_players_data()
    if not players_dict:
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']

    # gather game to master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            if str(game_id) in games_dict:
                game = games_dict[str(game_id)]['name']
                game_master_dict[game] = master

    players_dict2 = common.get_players()
    if not players_dict2:
        return

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict2.items()}

    dict_worst_annoyers_data = get_current_worst_annoyers()
    if not dict_worst_annoyers_data:
        alert("Erreur chargement des pires recidivistes du retard et de l'abandon dans les parties en cours")
        return

    # reshape data
    annoyers_dict = {}
    for game_name, game_data in dict_worst_annoyers_data['games_dict'].items():

        for player_id_str, num_delays in game_data['delays_number'].items():

            if player_id_str not in annoyers_dict:
                annoyers_dict[player_id_str] = {}
                annoyers_dict[player_id_str]['delays'] = 0
                annoyers_dict[player_id_str]['dropouts'] = 0
            annoyers_dict[player_id_str]['delays'] += num_delays

            if 'games' not in annoyers_dict[player_id_str]:
                annoyers_dict[player_id_str]['games'] = set()
            annoyers_dict[player_id_str]['games'].add(game_name)

        for player_id_str, num_dropouts in game_data['dropouts_number'].items():

            if player_id_str not in annoyers_dict:
                annoyers_dict[player_id_str] = {}
                annoyers_dict[player_id_str]['delays'] = 0
                annoyers_dict[player_id_str]['dropouts'] = 0
            annoyers_dict[player_id_str]['dropouts'] += num_dropouts

            if 'games' not in annoyers_dict[player_id_str]:
                annoyers_dict[player_id_str]['games'] = set()
            annoyers_dict[player_id_str]['games'].add(game_name)

    annoyers_table = html.TABLE()

    # the display order
    fields = ['pseudo', 'dropouts', 'delays', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'dropouts': 'abandons', 'delays': 'retards', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    annoyers_table <= thead

    # force sort according to deadline (latest games first of course)
    for player_id_str, data in sorted(annoyers_dict.items(), key=lambda p: (p[1]['dropouts'], p[1]['delays']), reverse=True):

        if int(player_id_str) in num2pseudo:
            pseudo = num2pseudo[int(player_id_str)]
        else:
            pseudo = "???"
        data['pseudo'] = pseudo

        row = html.TR()
        for field in fields:

            value = data[field]

            if field == 'games':
                value = ' '.join([str(n) for n in sorted(value)])

            col = html.TD(value)

            row <= col

        annoyers_table <= row

    MY_SUB_PANEL <= annoyers_table


def show_player_games(pseudo_player, game_list):
    """ show_player_games """

    def select_game_callback(ev, game_name, game_data_sel):  # pylint: disable=invalid-name
        """ select_game_callback """

        ev.preventDefault()

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        show_game_selected()

        # action of going to game page
        PANEL_MIDDLE.clear()
        play.render(PANEL_MIDDLE)

    def display_all_games_callback(ev):  # pylint: disable=invalid-name
        """ display_personal_info_callback """

        ev.preventDefault()

        selected_pseudo_player = input_player.value

        player_id = players_dict2[selected_pseudo_player]

        player_games = get_this_player_games_playing_in(player_id)
        if player_games is None:
            alert("Erreur chargement liste parties jouées par le joueur")
            return

        game_list = [int(k) for k, v in player_games.items() if v >= 1]

        # back to where we started
        MY_SUB_PANEL.clear()
        show_player_games(selected_pseudo_player, game_list)

    MY_SUB_PANEL <= html.H3("Toutes les parties d'un joueur")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    games_dict = common.get_games_data()
    if games_dict is None:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)

    players_dict = common.get_players_data()
    if not players_dict:
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']

    # gather game to master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            if str(game_id) in games_dict:
                game = games_dict[str(game_id)]['name']
                game_master_dict[game] = master

    players_dict2 = common.get_players()
    if not players_dict2:
        return

    # all players can be investigated
    possible_players = set(players_dict2.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_player = html.LEGEND("Joueur", title="Sélectionner le joueur dont on veut la liste des parties")
    fieldset <= legend_player
    input_player = html.SELECT(type="select-one", value="", Class='btn-inside')
    for player_pseudo in sorted(possible_players, key=lambda pu: pu.upper()):
        option = html.OPTION(player_pseudo)
        input_player <= option
    fieldset <= input_player
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Récupérer la liste de ses parties", Class='btn-inside')
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

        gameover_table = {int(game_id_str): data['soloed'] or data['finished'] for game_id_str, data in games_dict.items()}

        # conversion
        game_type_conv = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}

        time_stamp_now = time()

        games_table = html.TABLE()

        # the display order
        fields = ['current_state', 'name', 'go_game', 'deadline', 'variant', 'used_for_elo', 'nopress_current', 'nomessage_current', 'game_type', 'master']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'current_state': 'état', 'name': 'nom', 'go_game': 'aller dans la partie', 'deadline': 'date limite', 'variant': 'variante', 'used_for_elo': 'elo', 'nopress_current': 'déclarations', 'nomessage_current': 'négociations', 'game_type': 'type de partie', 'master': 'arbitre'}[field]
            col = html.TD(field_fr)
            thead <= col
        games_table <= thead

        # create a table to pass information about selected game
        game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

        for game_id_str, data in sorted(games_dict.items(), key=lambda t: int(t[0]), reverse=True):

            data['go_game'] = None
            data['master'] = None

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

                if field == 'go_game':
                    if storage['GAME_ACCESS_MODE'] == 'button':
                        form = html.FORM()
                        input_jump_game = html.INPUT(type="image", src="./images/play.png", title="Pour aller dans la partie", Class='btn-inside')
                        input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                        form <= input_jump_game
                        value = form
                    else:
                        img = html.IMG(src="./images/play.png", title="Pour aller dans la partie")
                        link = html.A(href=f"?game={game_name}", target="_blank")
                        link <= img
                        value = link

                if field == 'deadline':
                    deadline_loaded = value
                    datetime_deadline_loaded = mydatetime.fromtimestamp(deadline_loaded)
                    datetime_deadline_loaded_str = mydatetime.strftime(*datetime_deadline_loaded, year_first=True)
                    value = datetime_deadline_loaded_str

                    if data['fast']:
                        factor = 60
                    else:
                        factor = 60 * 60

                    # game over
                    if gameover_table[game_id]:
                        if data['soloed']:
                            colour = config.SOLOED_COLOUR
                            value = "(solo)"
                        elif data['finished']:
                            colour = config.FINISHED_COLOUR
                            value = "(terminée)"

                    elif int(data['current_state']) == 1:

                        # we are after everything !
                        if time_stamp_now > deadline_loaded + factor * 24 * config.CRITICAL_DELAY_DAY:
                            colour = config.CRITICAL_COLOUR
                        # we are after deadline + grace
                        elif time_stamp_now > deadline_loaded + factor * data['grace_duration']:
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

                if field == 'nopress_current':
                    value = "Non" if data['nopress_current'] else "Oui"

                if field == 'nomessage_current':
                    value = "Non" if data['nomessage_current'] else "Oui"

                if field == 'game_type':
                    value = game_type_conv[value]

                if field == 'master':
                    game_name = data['name']
                    # some games do not have a game master
                    master_name = game_master_dict.get(game_name, '')
                    value = master_name

                col = html.TD(value)
                if colour is not None:
                    col.style = {
                        'background-color': colour
                    }

                row <= col
            games_table <= row

        MY_SUB_PANEL <= games_table
        MY_SUB_PANEL <= html.BR()


def show_players_game():
    """ show_player_games """

    MY_SUB_PANEL <= html.H3("Les joueurs de cette partie")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game_name = storage['GAME']
    MY_SUB_PANEL <= f"Partie concernée : {game_name}"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    game_id = storage['GAME_ID']

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement info joueurs")
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    game_players_dict = common.get_game_players_data(game_id)
    if not game_players_dict:
        alert("Erreur chargement joueurs de la partie")
        return

    role2pseudo = {v: k for k, v in game_players_dict.items()}

    variant_name_loaded = storage['GAME_VARIANT']

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # selected interface (user choice)
    interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

    # from interface chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    game_admin_table = html.TABLE()

    for role_id, role in variant_data.roles.items():

        # discard game master
        if role_id == 0:
            continue

        row = html.TR()

        role_name = variant_data.role_name_table[role]

        # flag
        col = html.TD()
        role_icon_img = common.display_flag(variant_name_loaded, interface_chosen, role_id, role_name)
        col <= role_icon_img
        row <= col

        # role name
        col = html.TD()
        col <= role_name
        row <= col

        # player
        col = html.TD()
        pseudo_there = ""
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        col <= pseudo_there
        row <= col

        game_admin_table <= row

    MY_SUB_PANEL <= game_admin_table


def show_last_submissions():
    """ show_last_submissions """

    MY_SUB_PANEL <= html.H3("Les dernières soumissions d'ordres")

    if not common.check_modo():
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

    if not common.check_modo():
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

    for data in sorted(ip_table, key=lambda c: (c[0], num2pseudo[c[1]].upper())):

        row = html.TR()
        for field in fields:

            if field == 'pseudo':
                value = num2pseudo[data[1]]

            if field == 'ip_value':
                value = data[0]

                if value in duplicated_ips:
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

    if not common.check_modo():
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

    for pseudo, (email, _, _, _, _) in sorted(emails_dict.items(), key=lambda t: t[1][0].upper()):

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


def show_verif_codes():
    """ show_verif_codes """

    MY_SUB_PANEL <= html.H3("Les codes de vérification pour le forum")

    if not common.check_modo():
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


def revoke_master():
    """ revoke_master """

    def revoke_master_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
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
            mydialog.InfoDialog("Information", f"Vous avez destitué l'arbitre : {messages}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Destituer l'arbitre")

    if not common.check_modo():
        alert("Pas le bon compte (pas modo)")
        return

    pseudo = storage['PSEUDO']

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

    input_revoke_master = html.INPUT(type="submit", value="Destituer l'arbitre de la partie sélectionnée", Class='btn-inside')
    input_revoke_master.bind("click", revoke_master_callback)
    form <= input_revoke_master

    MY_SUB_PANEL <= form


def change_director():
    """ change_director """

    def promote_directors_callback(ev):  # pylint: disable=invalid-name
        """ promote_directors_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la promotion responsable tournoi : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la promotion responsable tournoi : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            mydialog.InfoDialog("Information", f"Il a été promu responsable du tournoi: {director}")

        ev.preventDefault()

        director = input_director.value
        director_id = players_dict[director]

        json_dict = {
            'director_id': director_id,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/tournaments_manager/{tournament_id}"

        # updating a tournament : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_director()

    MY_SUB_PANEL <= html.H3("Changer le responsable du tournoi")

    if not common.check_modo():
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

    MY_SUB_PANEL <= f"Tournoi concerné : {tournament_name}"
    MY_SUB_PANEL <= html.BR()
    MY_SUB_PANEL <= html.BR()

    players_dict = common.get_players()
    if not players_dict:
        return

    # all players can be selected
    possible_directors = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_director = html.LEGEND("Responsable", title="Sélectionner le nouveau responsable")
    fieldset <= legend_director
    input_director = html.SELECT(type="select-one", value="", Class='btn-inside')
    for director_pseudo in sorted(possible_directors, key=lambda pu: pu.upper()):
        option = html.OPTION(director_pseudo)
        input_director <= option
    fieldset <= input_director
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Promouvoir responsable", Class='btn-inside')
    input_select_player.bind("click", promote_directors_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def change_manager():
    """ change_manager """

    def promote_managers_callback(ev):  # pylint: disable=invalid-name
        """ promote_managers_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la promotion responsable événement : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la promotion responsable événement : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            mydialog.InfoDialog("Information", f"Il a été promu responsable de l'événement: {manager}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_manager()

    MY_SUB_PANEL <= html.H3("Changer le responsable de l'événement")

    if not common.check_modo():
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

    # all players can be selected
    possible_managers = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_manager = html.LEGEND("Responsable", title="Sélectionner le nouveau responsable")
    fieldset <= legend_manager
    input_manager = html.SELECT(type="select-one", value="", Class='btn-inside')
    for manager_pseudo in sorted(possible_managers, key=lambda pu: pu.upper()):
        option = html.OPTION(manager_pseudo)
        input_manager <= option
    fieldset <= input_manager
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Promouvoir responsable", Class='btn-inside')
    input_select_player.bind("click", promote_managers_callback)
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

ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

MY_SUB_PANEL = html.DIV(id="moderate")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    # communication
    if item_name == 'Changer nouvelles':
        change_news_modo()
    if item_name == 'Effacer le chat':
        erase_chat_content()
    if item_name == 'Préparer un publipostage':
        prepare_mailing()
    if item_name == 'Annoncer dans toutes les parties':
        general_announce()
    if item_name == 'Annoncer dans la partie':
        game_announce()
    if item_name == 'Récupérer un courriel et téléphone':
        display_personal_info()
    # surveillance
    if item_name == 'Tous les ordres manquants':
        all_missing_orders()
    if item_name == 'Pires récidivistes retard et abandon':
        current_worst_annoyers()
    if item_name == 'Toutes les parties d\'un joueur':
        show_player_games(None, [])
    if item_name == 'Tous les joueurs de la partie':
        show_players_game()
    if item_name == 'Dernières soumissions d\'ordres':
        show_last_submissions()
    if item_name == 'Vérification adresses IP':
        show_ip_addresses()
    if item_name == 'Vérification courriels':
        show_all_emails()
    if item_name == 'Codes de vérification':
        show_verif_codes()
    # management
    if item_name == 'Destituer arbitre partie':
        revoke_master()
    if item_name == 'Changer responsable tournoi':
        change_director()
    if item_name == 'Changer responsable événement':
        change_manager()

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
