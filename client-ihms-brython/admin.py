""" admin """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from time import time
from base64 import standard_b64encode

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common
import interface
import login
import mapping
import geometry
import mydialog
import allgames

import index

OPTIONS = {
    'Changer nouvelles': "Changer nouvelles du site pour l'administrateur",
    'Changer image': "Changer l'image du site",
    'Usurper': "Usurper le compte d'un untilisateur",
    'Rectifier les paramètres': "Rectifier les paramètres de la partie sélectionnée",
    'Rectifier la position': "Rectifier la position de la partie sélectionnée",
    'Rectifier l\'état': "Rectifier l\'état de la partie sélectionnée",
    'Rectifier le nom': "Rectifier le nom de la partie sélectionnée",
    'Logs des soumissions d\'ordres': "Les soumissions d'ordres sur le site",
    'Dernières connexions': "Les connexions réussies sur le site",
    'Connexions manquées': "Les connexions manquées sur le site",
    'Récupérations demandées': "Les récupérations demandées sur le site",
    'Editer les créateurs': "Editer les comptes créateurs du site",
    'Editer les modérateurs': "Editer les comptes modérateurs du site",
    'Comptes oisifs': "Lister les comptes oisifs pour les avertir ou les supprimer",
    'Logs du scheduler': "Consulter les logs du scheduleur",
    'Maintenance': "Opération de maintenance à définir"
}

DOWNLOAD_LOG = False

# max size in bytes of image (before b64)
# let 's say one 0.5 Mo
MAX_SIZE_IMAGE = 500000

MAX_LEN_GAME_NAME = 50


def get_active_data():
    """ get_active_data : returns empty list if problem """

    active_data = []

    def reply_callback(req):
        nonlocal active_data
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur au chargement des actifs : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème au chargement des actifs : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        active_data = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/active_players"

    # getting active data : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return active_data


def get_creators():
    """ get_creators : returns empty list if problem """

    creators_list = []

    def reply_callback(req):
        nonlocal creators_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des créateurs : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des créateurs : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        creators_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/creators"

    # getting moderators list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return creators_list


def get_moderators():
    """ get_moderators : returns empty list if problem """

    moderators_list = []

    def reply_callback(req):
        nonlocal moderators_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des modérateurs : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des modérateurs : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        moderators_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/moderators"

    # getting moderators list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return moderators_list


def get_last_logins():
    """ get_last_logins """

    logins_list = []

    def reply_callback(req):
        nonlocal logins_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des connexions : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des connexions : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        logins_list = req_result['login_list']

    json_dict = {}

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/logins_list"

    # logins list : need token
    # note : since we access directly to the user server, we present the token in a slightly different way
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return logins_list


def get_last_failures():
    """ get_last_failures """

    failures_list = None

    def reply_callback(req):
        nonlocal failures_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des connexions manquées : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des connexions manquées : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        failures_list = req_result['failure_list']

    json_dict = {}

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/failures_list"

    # failures_list list : need token
    # note : since we access directly to the user server, we present the token in a slightly different way
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return failures_list


def get_last_rescues():
    """ get_last_rescues """

    rescues_list = None

    def reply_callback(req):
        nonlocal rescues_list
        req_result = loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération des demandes de récupération : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération des demandes de récupération : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        rescues_list = req_result['rescue_list']

    json_dict = {}

    host = config.SERVER_CONFIG['USER']['HOST']
    port = config.SERVER_CONFIG['USER']['PORT']
    url = f"{host}:{port}/rescues_list"

    # failures_list list : need token
    # note : since we access directly to the user server, we present the token in a slightly different way
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return rescues_list


def change_news_admin():
    """ change_news_admin """

    def change_news_admin_callback(ev):  # pylint: disable=invalid-name
        """ change_news_admin_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du contenu des nouvelles : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du contenu des nouvelles : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Les nouvelles (administrateur) ont été changées : {messages}")

        ev.preventDefault()

        news_content = input_news_content.value
        if not news_content:
            alert("Contenu nouvelles manquant")
            return

        json_dict = {
            'topic': 'admin',
            'content': news_content
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/news"

        # changing news : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_news_admin()

    MY_SUB_PANEL <= html.H3("Editer les nouvelles")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    news_content_table_loaded = common.get_news_content()
    if not news_content_table_loaded:
        return

    news_content_loaded = news_content_table_loaded['admin']

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_news_content = html.LEGEND("nouvelles", title="Saisir le nouveau contenu de nouvelles (admin)")
    fieldset <= legend_news_content
    input_news_content = html.TEXTAREA(type="text", rows=20, cols=100)
    input_news_content <= news_content_loaded
    fieldset <= input_news_content
    form <= fieldset

    form <= html.BR()

    input_change_news_content = html.INPUT(type="submit", value="Mettre à jour", Class='btn-inside')
    input_change_news_content.bind("click", change_news_admin_callback)
    form <= input_change_news_content
    form <= html.BR()

    MY_SUB_PANEL <= form


INPUT_FILE = None


def change_site_image():
    """ change_site_image """

    def put_site_picture_callback(ev):  # pylint: disable=invalid-name
        """ put_site_picture_callback """

        def onload_callback(_):
            """ onload_callback """

            def reply_callback(req):
                req_result = loads(req.text)
                if req.status != 201:
                    if 'message' in req_result:
                        alert(f"Erreur à la modification de l'image du site : {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à la modification de l'image du site  : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    return

                messages = "<br>".join(req_result['msg'].split('\n'))
                mydialog.InfoDialog("Information", f"L'image du site a été changée : {messages}")

                index.SITE_IMAGE_DICT['image'] = image_str
                index.SITE_IMAGE_DICT['legend'] = legend_content

                # back to where we started
                MY_SUB_PANEL.clear()
                change_site_image()

            # get the image content
            image_bytes = bytes(window.Array["from"](window.Uint8Array.new(reader.result)))

            if len(image_bytes) > MAX_SIZE_IMAGE:
                alert(f"Ce fichier est trop gros : la limite est {MAX_SIZE_IMAGE} octets")
                return

            # b64 encode to pass it on server
            try:
                image_str = standard_b64encode(image_bytes).decode()
            except:  # noqa: E722 pylint: disable=bare-except
                alert("Problème à l'encodage pour le web... ")
                return

            legend_content = input_legend_content.value
            if not legend_content:
                alert("Contenu légende manquant")
                return

            json_dict = {
                'legend': legend_content,
                'image': image_str
            }

            host = config.SERVER_CONFIG['PLAYER']['HOST']
            port = config.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/site_image"

            # changing site image : need token
            ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        ev.preventDefault()

        if not INPUT_FILE.files:

            alert("Pas de fichier")

            # back to where we started
            MY_SUB_PANEL.clear()
            change_site_image()
            return

        # Create a new DOM FileReader instance
        reader = window.FileReader.new()
        # Extract the file
        file_name = INPUT_FILE.files[0]
        # Read the file content as text
        reader.bind("load", onload_callback)
        reader.readAsArrayBuffer(file_name)

    MY_SUB_PANEL <= html.H3("Changer l'image du site")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("Ficher JPG uniquement ! (et rester inférieur en taille à 100 pixels en largeur)")
    fieldset <= legend_name
    form <= fieldset

    # need to make this global to keep it (only way it seems)
    global INPUT_FILE
    if INPUT_FILE is None:
        INPUT_FILE = html.INPUT(type="file", accept='.jpg', Class='btn-inside')
    form <= INPUT_FILE
    form <= html.BR()

    form <= html.BR()

    legend_content_loaded = index.SITE_IMAGE_DICT['legend']

    fieldset = html.FIELDSET()
    legend_legend_content = html.LEGEND("nouvelles", title="Saisir la légende")
    fieldset <= legend_legend_content
    input_legend_content = html.TEXTAREA(type="text", rows=5, cols=100)
    input_legend_content <= legend_content_loaded
    fieldset <= input_legend_content
    form <= fieldset

    input_put_picture = html.INPUT(type="submit", value="Mettre cette image avec cette légende", Class='btn-inside')
    input_put_picture.bind("click", put_site_picture_callback)
    form <= input_put_picture

    MY_SUB_PANEL <= form


def usurp():
    """ usurp """

    def usurp_callback(_):
        """ usurp_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'usurpation : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'usurpation : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            storage['PSEUDO'] = usurped_user_name
            storage['JWT_TOKEN'] = req_result['AccessToken']
            time_stamp_now = time()
            storage['LOGIN_TIME'] = str(time_stamp_now)

            mydialog.InfoDialog("Information", f"Vous usurpez maintenant : {usurped_user_name}")
            login.show_login()

        usurped_user_name = input_usurped.value
        if not usurped_user_name:
            alert("User name usurpé manquant")
            return

        json_dict = {
            'usurped_user_name': usurped_user_name,
        }

        host = config.SERVER_CONFIG['USER']['HOST']
        port = config.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/usurp"

        # usurping : need token
        # note : since we access directly to the user server, we present the token in a slightly different way
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Usurper un inscrit")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    # all players can be usurped
    possible_usurped = set(players_dict.keys())

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_usurped = html.LEGEND("Usurpé", title="Sélectionner le joueur à usurper")
    fieldset <= legend_usurped
    input_usurped = html.SELECT(type="select-one", value="", Class='btn-inside')
    for usurped_pseudo in sorted(possible_usurped, key=lambda pu: pu.upper()):
        option = html.OPTION(usurped_pseudo)
        input_usurped <= option
    fieldset <= input_usurped
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Usurper", Class='btn-inside')
    input_select_player.bind("click", usurp_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def rectify_parameters():
    """ rectify_parameters """

    # declare the values
    used_for_elo_loaded = None
    fast_loaded = None
    archive_loaded = None
    game_type_loaded = None
    finished_loaded = None
    end_voted_loaded = None
    nb_max_cycles_to_play_loaded = None

    def change_parameters_reload():
        """ change_parameters_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
            nonlocal used_for_elo_loaded
            nonlocal fast_loaded
            nonlocal archive_loaded
            nonlocal game_type_loaded
            nonlocal finished_loaded
            nonlocal end_voted_loaded
            nonlocal nb_max_cycles_to_play_loaded
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des paramètres de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des paramètres de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            used_for_elo_loaded = req_result['used_for_elo']
            fast_loaded = req_result['fast']
            archive_loaded = req_result['archive']
            game_type_loaded = req_result['game_type']
            finished_loaded = req_result['finished']
            end_voted_loaded = req_result['end_voted']
            nb_max_cycles_to_play_loaded = req_result['nb_max_cycles_to_play']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_parameters_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification des paramètres de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification des paramètres de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Les paramètres de la partie ont été modifiés : {messages}")

        ev.preventDefault()

        used_for_elo = int(input_used_for_elo.checked)
        fast = int(input_fast.checked)
        archive = int(input_archive.checked)
        game_type = input_game_type.value
        game_type_code = config.GAME_TYPES_CODE_TABLE[game_type]
        finished = int(input_finished.checked)
        end_voted = int(input_end_voted.checked)
        nb_max_cycles_to_play = int(input_nb_max_cycles_to_play.value)

        json_dict = {
            'used_for_elo': used_for_elo,
            'fast': fast,
            'archive': archive,
            'game_type': game_type_code,
            'finished': finished,
            'end_voted': end_voted,
            'nb_max_cycles_to_play': nb_max_cycles_to_play
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/alter_games/{game}"

        # altering game used for elo : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_parameters()

    MY_SUB_PANEL <= html.H3("Rectifier des paramètres de la partie")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    status = change_parameters_reload()
    if not status:
        return

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_used_for_elo = html.LEGEND("utilisée pour le élo", title="Partie sérieuse - les résultats de la partie comptent pour le calcul du élo sur le site")
    fieldset <= legend_used_for_elo
    input_used_for_elo = html.INPUT(type="checkbox", checked=used_for_elo_loaded, Class='btn-inside')
    fieldset <= input_used_for_elo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_fast = html.LEGEND("en direct", title="Partie en direct - jouée en temps réel comme sur un plateau")
    fieldset <= legend_fast
    input_fast = html.INPUT(type="checkbox", checked=fast_loaded, Class='btn-inside')
    fieldset <= input_fast
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_archive = html.LEGEND("archive", title="Partie archive - la partie n'est pas jouée - l'arbitre passe tous les ordres et tout le monde pourra en regarder le déroulement")
    fieldset <= legend_archive
    input_archive = html.INPUT(type="checkbox", checked=archive_loaded, Class='btn-inside')
    fieldset <= input_archive
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_variant = html.LEGEND("type de partie", title="Type de partie pour la communication en jeu")
    fieldset <= legend_variant
    input_game_type = html.SELECT(type="select-one", value="", Class='btn-inside')

    for game_type_name in config.GAME_TYPES_CODE_TABLE:
        option = html.OPTION(game_type_name)
        if config.GAME_TYPES_CODE_TABLE[game_type_name] == game_type_loaded:
            option.selected = True
        input_game_type <= option

    fieldset <= input_game_type
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nb_max_cycles_to_play = html.LEGEND("maximum de cycles (années)", title="Combien d'années à jouer au plus ?")
    fieldset <= legend_nb_max_cycles_to_play
    input_nb_max_cycles_to_play = html.INPUT(type="number", value=nb_max_cycles_to_play_loaded, Class='btn-inside')
    fieldset <= input_nb_max_cycles_to_play
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_finished = html.LEGEND("terminée", title="Partie finie dernière saison jouée")
    fieldset <= legend_finished
    input_finished = html.INPUT(type="checkbox", checked=finished_loaded, Class='btn-inside')
    fieldset <= input_finished
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_end_voted = html.LEGEND("fin votée", title="La fin de la partie a été votée")
    fieldset <= legend_end_voted
    input_end_voted = html.INPUT(type="checkbox", checked=end_voted_loaded, Class='btn-inside')
    fieldset <= input_end_voted
    form <= fieldset

    form <= html.BR()

    input_change_parameters_game = html.INPUT(type="submit", value="Changer les paramètres de la partie", Class='btn-inside')
    input_change_parameters_game.bind("click", change_parameters_game_callback)
    form <= input_change_parameters_game

    MY_SUB_PANEL <= form


def rectify_position():
    """rectify_position """

    selected_hovered_object = None
    moved_item_id = None

    def submit_callback(_):
        """ submit_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission de rectification de position : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission de rectification de position : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Vous avez rectifié la position : {messages}")

        # units
        units_list_dict = position_data.save_json()
        units_list_dict_json = dumps(units_list_dict)

        # ownerships
        ownerships_list_dict = position_data.save_json2()
        ownerships_list_dict_json = dumps(ownerships_list_dict)

        json_dict = {
            'units': units_list_dict_json,
            'ownerships': ownerships_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-positions/{game_id}"

        # submitting position (units ownerships) for rectification : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def callback_canvas_click(event):
        """ callback_canvas_click """

        if event.detail != 1:
            # Otherwise confusion click/double-click
            return

        if moved_item_id:
            callback_drop_item(event)

    def callback_canvas_dblclick(event):
        """
        called when there is a double click
        """

        if event.detail != 2:
            # Otherwise confusion click/double-click
            return

        # where is the click
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # select unit
        selected_erase_object = position_data.closest_object(pos)

        # something must be selected
        if selected_erase_object is None:
            return

        # must be unit or ownership
        if isinstance(selected_erase_object, mapping.Unit):
            # remove unit
            selected_erase_ownership = None
            selected_erase_unit = selected_erase_object
            position_data.remove_unit(selected_erase_unit)
        elif isinstance(selected_erase_object, mapping.Ownership):
            # remove ownership
            selected_erase_ownership = selected_erase_object
            position_data.remove_ownership(selected_erase_ownership)
            selected_erase_unit = None
        else:
            return

        # tricky
        nonlocal selected_hovered_object
        if selected_hovered_object == selected_erase_unit:
            selected_hovered_object = None
        if selected_hovered_object == selected_erase_ownership:
            selected_hovered_object = None

        # update map
        callback_render(True)

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = position_data.closest_object(pos)

        if selected_hovered_object != prev_selected_hovered_object:

            helper.clear()

            # put back previous
            if prev_selected_hovered_object is not None:
                prev_selected_hovered_object.highlite(ctx, False)

            # hightlite object where mouse is
            if selected_hovered_object is not None:
                selected_hovered_object.highlite(ctx, True)
                helper <= selected_hovered_object.description()
            else:
                helper <= "_"

            # redraw dislodged if applicable
            # no

            # redraw all arrows
            # no

    def callback_canvas_mouse_enter(event):
        """ callback_canvas_mouse_enter """

        nonlocal selected_hovered_object

        helper.clear()

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = position_data.closest_object(pos)

        # hightlite object where mouse is
        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, True)
            helper <= selected_hovered_object.description()
        else:
            helper <= "_"

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """

        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, False)

        helper.clear()
        helper <= "_"

    def callback_render(_):
        """ callback_render """

        # since orders are not involved not save/restore context

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the position and neutral centers
        position_data.render(ctx)

        # put the legends
        variant_data.render(ctx)

        # do not put the orders here

    def callback_take_item(event):
        """  take an item (unit or center)  """

        nonlocal moved_item_id

        # take unit or center
        moved_item_id = event.target.id

    def callback_drop_item(event):
        """  drop an item (unit or center)  """

        nonlocal moved_item_id

        if moved_item_id in unit_info_table:

            assert moved_item_id is not None
            (type_unit, role) = unit_info_table[moved_item_id]

            # get zone
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
            selected_drop_zone = variant_data.closest_zone(pos, type_unit)

            # get region
            selected_drop_region = selected_drop_zone.region

            # prevent putting armies in sea
            if type_unit is mapping.UnitTypeEnum.ARMY_UNIT and selected_drop_zone.region.region_type is mapping.RegionTypeEnum.SEA_REGION:
                type_unit = mapping.UnitTypeEnum.FLEET_UNIT

            # prevent putting fleets inland
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT and selected_drop_zone.region.region_type is mapping.RegionTypeEnum.LAND_REGION:
                type_unit = mapping.UnitTypeEnum.ARMY_UNIT

            if selected_drop_zone.coast_type is not None:
                # prevent putting army on specific coasts
                if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
                    type_unit = mapping.UnitTypeEnum.FLEET_UNIT
            else:
                # we are not on a specific cosat
                if len([z for z in variant_data.zones.values() if z.region == selected_drop_region]) > 1:
                    # prevent putting fleet on non specific coasts if exists
                    if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                        type_unit = mapping.UnitTypeEnum.ARMY_UNIT

            # create unit
            if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
                new_unit = mapping.Army(position_data, role, selected_drop_zone, None, False)
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                new_unit = mapping.Fleet(position_data, role, selected_drop_zone, None, False)

            # remove previous occupant if applicable
            if selected_drop_region in position_data.occupant_table:
                previous_unit = position_data.occupant_table[selected_drop_region]
                position_data.remove_unit(previous_unit)

            # add to position
            position_data.add_unit(new_unit)

            # Forget about this moved unit
            moved_item_id = None

        if moved_item_id in ownership_info_table:

            assert moved_item_id is not None
            (role, ) = ownership_info_table[moved_item_id]

            # get center
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
            selected_drop_center = variant_data.closest_center(pos)

            # create ownership
            new_ownership = mapping.Ownership(position_data, role, selected_drop_center)

            # remove previous ownership if applicable
            if selected_drop_center in position_data.owner_table:
                previous_ownership = position_data.owner_table[selected_drop_center]
                position_data.remove_ownership(previous_ownership)

            # add to position
            position_data.add_ownership(new_ownership)

            # Forget about this moved center
            moved_item_id = None

        # refresh
        callback_render(True)

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="Rectifier la position", Class='btn-inside')
        input_submit.bind("click", submit_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit

    # starts here

    MY_SUB_PANEL <= html.H3("Rectifier la position")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    if 'GAME_VARIANT' not in storage:
        alert("ERREUR : variante introuvable")
        return

    variant_name_loaded = storage['GAME_VARIANT']

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    alert("Attention :\n 1) Ne pas rectifier une position en dehors des phases de mouvements !\n 2) Ne pas supprimer une unité qui a déjà reçu un ordre !\n (DANGER !!!)")

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

    game_name = storage['GAME']

    parameters_loaded = common.game_parameters_reload(game_name)
    if not parameters_loaded:
        alert("Impossible de récupérer les paramètres de la partie modèle")
        return

    game_id = storage['GAME_ID']

    # get the position from server
    fog_of_war = parameters_loaded['fog']
    if fog_of_war:
        position_loaded = common.game_position_fog_of_war_reload(game_id, 0)
    else:
        position_loaded = common.game_position_reload(game_id)
    if not position_loaded:
        return

    # digest the position
    position_data = mapping.Position(position_loaded, variant_data)

    # finds data about the dragged unit
    unit_info_table = {}

    # finds data about the dragged ownership
    ownership_info_table = {}

    reserve_table = html.TABLE()

    num = 1
    for role in variant_data.roles.values():

        # ignore GM
        if role.identifier == 0:
            continue

        row = html.TR()

        # country name
        col = html.TD()
        col <= html.B(variant_data.role_name_table[role])
        row <= col

        for type_unit in mapping.UnitTypeEnum.inventory():

            col = html.TD()

            if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
                pickable_unit = mapping.Army(position_data, role, None, None, False)
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                pickable_unit = mapping.Fleet(position_data, role, None, None, False)

            identifier = f"unit_{num}"
            unit_canvas = html.CANVAS(id=identifier, width=32, height=32, alt="Cliquez-moi dessus !")
            unit_info_table[identifier] = (type_unit, role)
            num += 1

            unit_canvas.bind("click", callback_take_item)

            ctx2 = unit_canvas.getContext("2d")
            pickable_unit.render(ctx2)

            col <= unit_canvas
            row <= col

        col = html.TD()

        pickable_ownership = mapping.Ownership(position_data, role, None)

        identifier = f"center_{num}"
        ownership_canvas = html.CANVAS(id=identifier, width=32, height=32, alt="Cliquez-moi dessus !")
        ownership_info_table[identifier] = (role, )
        num += 1

        ownership_canvas.bind("click", callback_take_item)

        ctx3 = ownership_canvas.getContext("2d")
        pickable_ownership.render(ctx3)

        col <= ownership_canvas
        row <= col

        reserve_table <= row

    display_very_left = html.DIV(id='display_very_left')
    display_very_left.attrs['style'] = 'display: table-cell; width=40px; vertical-align: top; table-layout: fixed;'

    display_very_left <= reserve_table

    display_very_left <= html.BR()

    display_very_left <= html.DIV("Cliquez sur une de ces unités ou sur un de ces centres, *puis* sur la carte", Class='instruction')

    map_size = variant_data.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # click only
    canvas.bind("click", callback_canvas_click)
    canvas.bind("dblclick", callback_canvas_dblclick)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseenter", callback_canvas_mouse_enter)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(variant_name_loaded, interface_chosen)
    img.bind('load', lambda _: callback_render(True))

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    helper = html.DIV(Class='helper')
    display_left <= helper

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    legend_select_unit = html.DIV("Double-Clic sur une unité ou une possession pour l'effacer", Class='instruction')
    buttons_right <= legend_select_unit

    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_very_left
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    MY_SUB_PANEL <= my_sub_panel2


def rectify_current_state():
    """ rectify_current_state """

    # declare the values
    current_state_loaded = None

    def change_current_state_reload():
        """ change_current_state_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
            nonlocal current_state_loaded
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de l'état de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de l'état de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            current_state_loaded = req_result['current_state']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_current_state_callback(ev, current_state_selected):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification de l'état de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification de l'état de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"L'état de la partie a été modifiés : {messages}")

        ev.preventDefault()

        json_dict = {
            'current_state': current_state_selected,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/alter_games/{game}"

        # altering game  : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_current_state()

    MY_SUB_PANEL <= html.H3("Rectifier l'état de la partie")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    status = change_current_state_reload()
    if not status:
        return

    # list the states we have
    state_list = config.STATE_CODE_TABLE.values()

    rev_state_code_table = {v: k for k, v in config.STATE_CODE_TABLE.items()}

    for current_state in state_list:

        if current_state == current_state_loaded:
            continue

        current_state_str = rev_state_code_table[current_state]
        input_change_current_state = html.INPUT(type="submit", value=f"Mettre dans l'état {current_state_str}", Class='btn-inside')
        input_change_current_state.bind("click", lambda e, cs=current_state: change_current_state_callback(e, cs))
        MY_SUB_PANEL <= input_change_current_state
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()


def rectify_name():
    """ rectify_name """

    # declare the values
    name_loaded = None

    def change_name_reload():
        """ change_name_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problème (pas de réponse de la part du serveur)")
            status = False

        def reply_callback(req):
            nonlocal status
            nonlocal name_loaded
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération du nom de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération du nom de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                status = False
                return

            name_loaded = req_result['name']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_name_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du nom de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du nom de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le nom de la partie a été modifié : {messages}")

            # Important otherwise we are lost ;-)
            storage['GAME'] = name_selected
            allgames.show_game_selected()

        ev.preventDefault()

        name_selected = input_name.value

        json_dict = {
            'name': name_selected,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/alter_games/{game}"

        # altering game  : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        rectify_name()

    MY_SUB_PANEL <= html.H3("Rectifier le nom de la partie")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    status = change_name_reload()
    if not status:
        return

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("nom", title="Nom de la partie (faites court et simple)")
    fieldset <= legend_name
    input_name = html.INPUT(type="text", value=name_loaded, size=MAX_LEN_GAME_NAME, Class='btn-inside')
    fieldset <= input_name
    form <= fieldset

    input_rename_game = html.INPUT(type="submit", value="Renommer la partie", Class='btn-inside')
    input_rename_game.bind("click", change_name_callback)
    form <= input_rename_game

    MY_SUB_PANEL <= form


LINES_SUBMISSION_LOGS = 1000


def show_submissions_logs():
    """ show_submissions_logs """

    def get_logs():  # pylint: disable=invalid-name
        """ get_logs_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des logs de soumission : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des logs de soumission: {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                return

            req_result2 = req_result.copy()
            req_result2.reverse()
            for log in req_result2:
                MY_SUB_PANEL <= log
                MY_SUB_PANEL <= html.BR()

        json_dict = {
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/access-submission-logs/{LINES_SUBMISSION_LOGS}"

        # get logs : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Logs soumissions")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    get_logs()


def last_logins():
    """ logins """

    MY_SUB_PANEL <= html.H3("Liste des dernières connexions")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    logins_list = get_last_logins()

    logins_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'adresse IP', 'date']:
        col = html.TD(field)
        thead <= col
    logins_table <= thead

    for pseudo, ip_address, time_stamp in sorted(logins_list, key=lambda ll: ll[2], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        if ip_address is None:
            ip_address = '-'
        col = html.TD(ip_address)
        row <= col

        date_now_gmt = mydatetime.fromtimestamp(time_stamp)
        date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
        col = html.TD(date_now_gmt_str)
        row <= col

        logins_table <= row

    MY_SUB_PANEL <= logins_table


def last_failures():
    """ failures """

    MY_SUB_PANEL <= html.H3("Connexions manquées")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    failures_list = get_last_failures()

    # to get the sum
    failures_recap = {}

    # chronologically

    failures_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'adresse IP', 'date']:
        col = html.TD(field)
        thead <= col
    failures_table <= thead

    for pseudo, ip_address, time_stamp in sorted(failures_list, key=lambda f: f[2], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        if ip_address is None:
            ip_address = '-'
        col = html.TD(ip_address)
        row <= col

        date_now_gmt = mydatetime.fromtimestamp(time_stamp)
        date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
        col = html.TD(date_now_gmt_str)
        row <= col

        failures_table <= row

        # to get the sum
        if pseudo not in failures_recap:
            failures_recap[pseudo] = 0
        failures_recap[pseudo] += 1

    # per player

    failures_summary = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'number']:
        col = html.TD(field)
        thead <= col
    failures_summary <= thead

    for pseudo, number in sorted(failures_recap.items(), key=lambda ll: ll[1], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        col = html.TD(number)
        row <= col

        failures_summary <= row

    # Now display

    MY_SUB_PANEL <= html.H4("Chronologiquement")
    MY_SUB_PANEL <= failures_table

    MY_SUB_PANEL <= html.H4("Par inscrit")
    MY_SUB_PANEL <= failures_summary


def last_rescues():
    """ rescues """

    MY_SUB_PANEL <= html.H3("Récupérations demandées")
    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    rescues_list = get_last_rescues()

    # to get the sum
    rescues_recap = {}

    # chronologically

    rescues_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'adresse IP', 'date']:
        col = html.TD(field)
        thead <= col
    rescues_table <= thead

    for pseudo, ip_address, time_stamp in sorted(rescues_list, key=lambda f: f[2], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        if ip_address is None:
            ip_address = '-'
        col = html.TD(ip_address)
        row <= col

        date_now_gmt = mydatetime.fromtimestamp(time_stamp)
        date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
        col = html.TD(date_now_gmt_str)
        row <= col

        rescues_table <= row

        # to get the sum
        if pseudo not in rescues_recap:
            rescues_recap[pseudo] = 0
        rescues_recap[pseudo] += 1

    # per player

    rescues_summary = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'number']:
        col = html.TD(field)
        thead <= col
    rescues_summary <= thead

    for pseudo, number in sorted(rescues_recap.items(), key=lambda ll: ll[1], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        col = html.TD(number)
        row <= col

        rescues_summary <= row

    # Now display

    MY_SUB_PANEL <= html.H4("Chronologiquement")
    MY_SUB_PANEL <= rescues_table

    MY_SUB_PANEL <= html.H4("Par inscrit")
    MY_SUB_PANEL <= rescues_summary


def edit_creators():
    """ edit_creators """

    def add_creator_callback(ev):  # pylint: disable=invalid-name
        """ add_creator_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la mise d'un créateur : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise d'un créateur : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                edit_creators()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur a été promu créateur : {messages}")
            alert("Recharger la page pour une prise en compte dans le navigateur en cours d'utilisation")

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_creators()

        ev.preventDefault()

        player_pseudo = input_incomer.value

        json_dict = {
            'player_pseudo': player_pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/creators"

        # putting a moderator : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_creator_callback(ev):  # pylint: disable=invalid-name
        """remove_creator_callback"""

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au retrait d'un créateur : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au retrait d'un créateur : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                edit_creators()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur a été déchu du rôle de créateur : {messages}")
            alert("Recharger la page pour une prise en compte dans le navigateur en cours d'utilisation")

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_creators()

        ev.preventDefault()

        player_pseudo = input_outcomer.value

        json_dict = {
            'player_pseudo': player_pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/creators"

        # removing a moderator : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Editer les modérateurs")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    creators_list = get_creators()

    form = html.FORM()

    # ---

    fieldset = html.FIELDSET()
    legend_incomer = html.LEGEND("Entrant", title="Sélectionner le joueur à promouvoir")
    fieldset <= legend_incomer

    # all players can come in
    possible_incomers = set(players_dict.keys())

    # not those already in
    possible_incomers -= set(creators_list)

    input_incomer = html.SELECT(type="select-one", value="", Class='btn-inside')
    for play_pseudo in sorted(possible_incomers, key=lambda pi: pi.upper()):
        option = html.OPTION(play_pseudo)
        input_incomer <= option

    fieldset <= input_incomer
    form <= fieldset

    form <= html.BR()

    input_put_in_game = html.INPUT(type="submit", value="Mettre dans les créateurs", Class='btn-inside')
    input_put_in_game.bind("click", add_creator_callback)
    form <= input_put_in_game

    form <= html.BR()
    form <= html.BR()

    # ---

    fieldset = html.FIELDSET()
    fieldset <= html.LEGEND("Sont créateurs : ")
    fieldset <= html.DIV(" ".join(sorted(list(set(creators_list)), key=lambda p: p.upper())), Class='note')
    form <= fieldset

    # ---
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_outcomer = html.LEGEND("Sortant", title="Sélectionner le joueur à destituer")
    fieldset <= legend_outcomer

    # players can come out are the ones not assigned
    possible_outcomers = creators_list

    input_outcomer = html.SELECT(type="select-one", value="", Class='btn-inside')
    for play_pseudo in sorted(possible_outcomers):
        option = html.OPTION(play_pseudo)
        input_outcomer <= option

    fieldset <= input_outcomer
    form <= fieldset

    form <= html.BR()

    input_remove_from_game = html.INPUT(type="submit", value="Retirer des créateurs", Class='btn-inside')
    input_remove_from_game.bind("click", remove_creator_callback)
    form <= input_remove_from_game

    MY_SUB_PANEL <= form


def edit_moderators():
    """ edit_moderators """

    def add_moderator_callback(ev):  # pylint: disable=invalid-name
        """ add_moderator_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la mise d'un modérateur : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise d'un modérateur : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                edit_moderators()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur a été promu modérateur : {messages}")
            alert("Recharger la page pour une prise en compte dans le navigateur en cours d'utilisation")

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_moderators()

        ev.preventDefault()

        player_pseudo = input_incomer.value

        json_dict = {
            'player_pseudo': player_pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"

        # putting a moderator : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_moderator_callback(ev):  # pylint: disable=invalid-name
        """remove_moderator_callback"""

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au retrait d'un modérateur : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au retrait d'un modérateur : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                edit_moderators()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le joueur a été déchu du rôle de modérateur : {messages}")
            alert("Recharger la page pour une prise en compte dans le navigateur en cours d'utilisation")

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_moderators()

        ev.preventDefault()

        player_pseudo = input_outcomer.value

        json_dict = {
            'player_pseudo': player_pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/moderators"

        # removing a moderator : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Editer les modérateurs")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    moderators_list = get_moderators()

    form = html.FORM()

    # ---

    fieldset = html.FIELDSET()
    legend_incomer = html.LEGEND("Entrant", title="Sélectionner le joueur à promouvoir")
    fieldset <= legend_incomer

    # all players can come in
    possible_incomers = set(players_dict.keys())

    # not those already in
    possible_incomers -= set(moderators_list)

    input_incomer = html.SELECT(type="select-one", value="", Class='btn-inside')
    for play_pseudo in sorted(possible_incomers, key=lambda pi: pi.upper()):
        option = html.OPTION(play_pseudo)
        input_incomer <= option

    fieldset <= input_incomer
    form <= fieldset

    form <= html.BR()

    input_put_in_game = html.INPUT(type="submit", value="Mettre dans les modérateurs", Class='btn-inside')
    input_put_in_game.bind("click", add_moderator_callback)
    form <= input_put_in_game

    form <= html.BR()
    form <= html.BR()

    # ---

    fieldset = html.FIELDSET()
    fieldset <= html.LEGEND("Sont modérateurs : ")
    fieldset <= html.DIV(" ".join(sorted(list(set(moderators_list)), key=lambda p: p.upper())), Class='note')
    form <= fieldset

    # ---
    form <= html.BR()

    fieldset = html.FIELDSET()
    legend_outcomer = html.LEGEND("Sortant", title="Sélectionner le joueur à destituer")
    fieldset <= legend_outcomer

    # players can come out are the ones not assigned
    possible_outcomers = moderators_list

    input_outcomer = html.SELECT(type="select-one", value="", Class='btn-inside')
    for play_pseudo in sorted(possible_outcomers):
        option = html.OPTION(play_pseudo)
        input_outcomer <= option

    fieldset <= input_outcomer
    form <= fieldset

    form <= html.BR()

    input_remove_from_game = html.INPUT(type="submit", value="Retirer des modérateurs", Class='btn-inside')
    input_remove_from_game.bind("click", remove_moderator_callback)
    form <= input_remove_from_game

    MY_SUB_PANEL <= form


def show_idle_data():
    """ show_idle_data """

    def delete_account_callback(ev, player_pseudo):  # pylint: disable=invalid-name
        """ delete_account_callback """

        # first step : usurp to get a token
        # second step : delete account using token

        def reply_callback1(req):

            def reply_callback2(req):
                req_result = loads(req.text)
                if req.status != 200:
                    if 'message' in req_result:
                        alert(f"Erreur à la suppression du compte {player_pseudo}: {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à la suppression du compte {player_pseudo} : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    return

                messages = "<br>".join(req_result['msg'].split('\n'))
                mydialog.InfoDialog("Information", f"Le compte {player_pseudo} a été supprimé : {messages}")

                # back to where we started
                MY_SUB_PANEL.clear()
                show_idle_data()

            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'usurpation {player_pseudo} : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'usurpation {player_pseudo} : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            token = req_result['AccessToken']

            json_dict = {}

            host = config.SERVER_CONFIG['PLAYER']['HOST']
            port = config.SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/players/{player_pseudo}"

            # deleting account : need token (of player or of admin)
            ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': token}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback2, ontimeout=common.noreply_callback)

        ev.preventDefault()

        json_dict = {
            'usurped_user_name': player_pseudo,
        }

        host = config.SERVER_CONFIG['USER']['HOST']
        port = config.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/usurp"

        # usurping : need token
        # note : since we access directly to the user server, we present the token in a slightly different way
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback1, ontimeout=common.noreply_callback)

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    complete_set = {pd['pseudo'] for pd in players_dict.values()}

    # get the link (allocations) of players
    active_data = get_active_data()
    if not active_data:
        alert("Erreur chargement actifs")
        return

    active_set = {players_dict[str(i)]['pseudo'] for i in active_data}

    # ignore admin
    priviledged = common.PRIVILEDGED
    admin_pseudo = priviledged['admin']
    active_set.add(admin_pseudo)

    # ignore moderators
    moderators_list = get_moderators()
    active_set.update(moderators_list)

    # ignore creators
    creators_list = get_creators()
    active_set.update(creators_list)

    idle_set = complete_set - active_set

    logins_list = get_last_logins()
    if not logins_list:
        alert("Erreur chargement logins joueurs")
        return
    last_login_time = {ll[0]: ll[2] for ll in logins_list}

    idle_table = html.TABLE()

    fields = ['player', 'id', 'last_login', 'email', 'delete']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'player': 'joueur', 'id': 'id', 'last_login': 'dernier login', 'email': 'courriel', 'delete': 'supprimer'}[field]
        col = html.TD(field_fr)
        thead <= col
    idle_table <= thead

    pseudo2id = {v['pseudo']: int(k) for k, v in players_dict.items()}

    emails_dict = common.get_all_emails()

    time_stamp_now = time()

    count = 0
    for player in sorted(idle_set, key=lambda p: int(last_login_time[p]) if p in last_login_time else 0, reverse=False):
        row = html.TR()

        for field in fields:

            colour = None

            if field == 'player':
                value = player

            if field == 'id':
                value = pseudo2id[player]

            if field == 'last_login':
                value = ''
                if player in last_login_time:
                    time_stamp = last_login_time[player]
                    day_idle = int(time_stamp_now - time_stamp) // (24 * 3600)
                    if day_idle > config.IDLE_DAY_TIMEOUT:
                        colour = 'red'
                    date_now_gmt = mydatetime.fromtimestamp(time_stamp)
                    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
                    value = f"{date_now_gmt_str}"

            if field == 'email':
                email, _, __, ___, ____ = emails_dict[player]
                email_link = html.A(href=f"mailto:{email}")
                email_link <= email
                value = email_link

            if field == 'delete':
                form = html.FORM()
                input_delete_account = html.INPUT(type="image", src="./images/delete.png", title="Pour supprimer le compte", Class='btn-inside')
                input_delete_account.bind("click", lambda e, p=player: delete_account_callback(e, p))
                form <= input_delete_account
                value = form

            col = html.TD(value)

            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        idle_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les oisifs")
    MY_SUB_PANEL <= idle_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} oisifs")


LINES_SCHEDULER_LOGS = 600


def show_scheduler_logs():
    """ show_scheduler_logs """

    def get_logs():  # pylint: disable=invalid-name
        """ get_logs_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des logs du scheduleur : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des logs du scheduleur : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                return

            req_result2 = req_result.copy()
            req_result2.reverse()
            for log in req_result2:
                MY_SUB_PANEL <= log
                MY_SUB_PANEL <= html.BR()

        json_dict = {
        }

        host = config.SERVER_CONFIG['SCHEDULER']['HOST']
        port = config.SERVER_CONFIG['SCHEDULER']['PORT']
        url = f"{host}:{port}/access-logs/{LINES_SCHEDULER_LOGS}"

        # get logs : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Logs scheduler")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    get_logs()


def maintain():
    """ maintain """

    def maintain_callback(ev):  # pylint: disable=invalid-name
        """ maintain_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la maintenance : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la maintenance : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                maintain()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            print(messages)

            mydialog.InfoDialog("Information", f"Maintenance réalisée :{messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            maintain()

        ev.preventDefault()

        json_dict = {
        }

#        host = config.SERVER_CONFIG['PLAYER']['HOST']
#        port = config.SERVER_CONFIG['PLAYER']['PORT']

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']

        url = f"{host}:{port}/maintain"

        # maintain : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Maintenance")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    form = html.FORM()

    # ---

    input_maintain = html.INPUT(type="submit", value="Déclencher", Class='btn-inside')
    input_maintain.bind("click", maintain_callback)
    form <= input_maintain

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

MY_SUB_PANEL = html.DIV(id="admin")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Changer nouvelles':
        change_news_admin()
    if item_name == 'Changer image':
        change_site_image()
    if item_name == 'Usurper':
        usurp()
    if item_name == 'Rectifier les paramètres':
        rectify_parameters()
    if item_name == 'Rectifier la position':
        rectify_position()
    if item_name == 'Rectifier l\'état':
        rectify_current_state()
    if item_name == 'Rectifier le nom':
        rectify_name()
    if item_name == 'Logs des soumissions d\'ordres':
        show_submissions_logs()
    if item_name == 'Dernières connexions':
        last_logins()
    if item_name == 'Connexions manquées':
        last_failures()
    if item_name == 'Récupérations demandées':
        last_rescues()
    if item_name == 'Editer les modérateurs':
        edit_moderators()
    if item_name == 'Editer les créateurs':
        edit_creators()
    if item_name == 'Comptes oisifs':
        show_idle_data()
    if item_name == 'Logs du scheduler':
        show_scheduler_logs()
    if item_name == 'Maintenance':
        maintain()

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


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
