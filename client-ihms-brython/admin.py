""" admin """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time

from browser import document, html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import mydialog
import config
import common
import interface
import login
import mapping
import geometry
import elo


OPTIONS = ['Changer nouvelles', 'Usurper', 'Rectifier les paramètres', 'Rectifier la position', 'Dernières connexions', 'Connexions manquées', 'Récupérations demandées', 'Editer les créateurs', 'Editer les modérateurs', 'Mise à jour du elo', 'Mise à jour de la fiabilité', 'Mise à jour de la régularité', 'Effacement des anciens retard', 'Comptes oisifs', 'Maintenance']

LONG_DURATION_LIMIT_SEC = 1.0

DOWNLOAD_LOG = False


def get_active_data():
    """ get_active_data : returns empty list if problem """

    active_data = []

    def reply_callback(req):
        nonlocal active_data
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return active_data


def get_creators():
    """ get_creators : returns empty list if problem """

    creators_list = []

    def reply_callback(req):
        nonlocal creators_list
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return creators_list


def get_moderators():
    """ get_moderators : returns empty list if problem """

    moderators_list = []

    def reply_callback(req):
        nonlocal moderators_list
        req_result = json.loads(req.text)
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
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return moderators_list


def get_last_logins():
    """ get_last_logins """

    logins_list = []

    def reply_callback(req):
        nonlocal logins_list
        req_result = json.loads(req.text)
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
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return logins_list


def get_last_failures():
    """ get_last_failures """

    failures_list = None

    def reply_callback(req):
        nonlocal failures_list
        req_result = json.loads(req.text)
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
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return failures_list


def get_last_rescues():
    """ get_last_rescues """

    rescues_list = None

    def reply_callback(req):
        nonlocal rescues_list
        req_result = json.loads(req.text)
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
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return rescues_list


def change_news_admin():
    """ change_news_admin """

    def change_news_admin_callback(ev):  # pylint: disable=invalid-name
        """ change_news_admin_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la modification du contenu des nouvelles : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification du contenu des nouvelles : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Les nouvelles ont été changées : {messages}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

    input_change_news_content = html.INPUT(type="submit", value="Mettre à jour")
    input_change_news_content.bind("click", change_news_admin_callback)
    form <= input_change_news_content
    form <= html.BR()

    MY_SUB_PANEL <= form


def usurp():
    """ usurp """

    def usurp_callback(_):
        """ usurp_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
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
            time_stamp_now = time.time()
            storage['LOGIN_TIME'] = str(time_stamp_now)

            common.info_dialog(f"Vous usurpez maintenant : {usurped_user_name}")
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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
    input_usurped = html.SELECT(type="select-one", value="")
    for usurped_pseudo in sorted(possible_usurped, key=lambda pu: pu.upper()):
        option = html.OPTION(usurped_pseudo)
        input_usurped <= option
    fieldset <= input_usurped
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="Usurper")
    input_select_player.bind("click", usurp_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def rectify_parameters():
    """ rectify_parameters """

    # declare the values
    used_for_elo_loaded = None
    fast_loaded = None
    nomessage_loaded = None
    nopress_loaded = None

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
            nonlocal nomessage_loaded
            nonlocal nopress_loaded
            req_result = json.loads(req.text)
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
            nomessage_loaded = req_result['nomessage_game']
            nopress_loaded = req_result['nopress_game']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_parameters_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la modification des paramètres de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la modification des paramètres de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Les paramètres de la partie ont été modifiés : {messages}")

        ev.preventDefault()

        used_for_elo = int(input_used_for_elo.checked)
        fast = int(input_fast.checked)
        nomessage_game = int(input_nomessage.checked)
        nopress_game = int(input_nopress.checked)

        json_dict = {
            'used_for_elo': used_for_elo,
            'fast': fast,
            'nomessage_game': nomessage_game,
            'nopress_game': nopress_game,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/alter_games/{game}"

        # altering game used for elo : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
    input_used_for_elo = html.INPUT(type="checkbox", checked=used_for_elo_loaded)
    fieldset <= input_used_for_elo
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_fast = html.LEGEND("en direct", title="Partie en direct - jouée en temps réel comme sur un plateau")
    fieldset <= legend_fast
    input_fast = html.INPUT(type="checkbox", checked=fast_loaded)
    fieldset <= input_fast
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nomessage = html.LEGEND("pas de message privé", title="Les joueurs ne peuvent pas communiquer (négocier) par message privé avant la fin de la partie")
    fieldset <= legend_nomessage
    input_nomessage = html.INPUT(type="checkbox", checked=nomessage_loaded)
    fieldset <= input_nomessage
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_nopress = html.LEGEND("pas de message public", title="Les joueurs ne peuvent pas communiquer (déclarer) par message public avant la fin de la partie")
    fieldset <= legend_nopress
    input_nopress = html.INPUT(type="checkbox", checked=nopress_loaded)
    fieldset <= input_nopress
    form <= fieldset

    form <= html.BR()

    input_change_used_for_elo_game = html.INPUT(type="submit", value="Changer les paramètres de la partie")
    input_change_used_for_elo_game.bind("click", change_parameters_game_callback)
    form <= input_change_used_for_elo_game

    MY_SUB_PANEL <= form


def rectify_position():
    """rectify_position """

    stored_event = None
    down_click_time = None
    selected_hovered_object = None

    def submit_callback(_):
        """ submit_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission de rectification de position : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission de rectification de position : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez rectifié la position : {messages}")

        # units
        units_list_dict = position_data.save_json()
        units_list_dict_json = json.dumps(units_list_dict)

        # ownerships
        ownerships_list_dict = position_data.save_json2()
        ownerships_list_dict_json = json.dumps(ownerships_list_dict)

        json_dict = {
            'units': units_list_dict_json,
            'ownerships': ownerships_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-positions/{game_id}"

        # submitting position (units ownerships) for rectification : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def callback_canvas_short_click(event):
        """ callback_canvas_short_click """

        # the aim is to give this variable a value
        selected_erase_ownership = None

        # where is the click
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # select unit
        selected_erase_ownership = position_data.closest_ownership(pos)

        # center must be selected
        if selected_erase_ownership is None:
            return

        # remove center
        position_data.remove_ownership(selected_erase_ownership)

        # update map
        callback_render(True)

    def callback_canvas_long_click(event):
        """
        called when there is a click down then a click up separated by more than 'LONG_DURATION_LIMIT_SEC' sec
        or when pressing 'x' in which case a None is passed
        """

        # the aim is to give this variable a value
        selected_erase_unit = None

        # where is the click
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # select unit (cannot be dislodged - issue - maybe later)
        selected_erase_object = position_data.closest_object(pos)

        # must be unit or center
        if isinstance(selected_erase_object, mapping.Unit):
            # remove unit
            selected_erase_unit = selected_erase_object
            position_data.remove_unit(selected_erase_unit)
        elif isinstance(selected_erase_object, mapping.Ownership):
            # remove ownership
            selected_erase_ownership = selected_erase_object
            position_data.remove_ownership(selected_erase_ownership)
        else:
            return

        # tricky
        nonlocal selected_hovered_object
        if selected_hovered_object == selected_erase_unit:
            selected_hovered_object = None

        # update map
        callback_render(True)

    def callback_canvas_mousedown(event):
        """ callback_mousedow : store event"""

        nonlocal stored_event
        nonlocal down_click_time

        down_click_time = time.time()
        stored_event = event

    def callback_canvas_mouseup(_):
        """ callback_mouseup : retrieve event and pass it"""

        nonlocal down_click_time

        if down_click_time is None:
            return

        # get click duration
        up_click_time = time.time()
        click_duration = up_click_time - down_click_time
        down_click_time = None

        # slow : call
        if click_duration > LONG_DURATION_LIMIT_SEC:
            callback_canvas_long_click(stored_event)
            return

        callback_canvas_short_click(stored_event)
        return

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
                if isinstance(selected_hovered_object, mapping.Highliteable):
                    helper <= selected_hovered_object.description()
                else:
                    helper <= "."
            else:
                helper <= "."

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """
        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, False)

    def callback_render(_):
        """ callback_render """

        # since orders are not involved not save/restore context

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        variant_data.render(ctx)

        # put the position
        position_data.render(ctx)

        # put the legends at the end
        variant_data.render_legends(ctx)

        # do not put the orders here

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="Rectifier la position")
        input_submit.bind("click", submit_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit

    # callbacks pour le glisser / deposer

    def mouseover(event):
        """Quand la souris passe sur l'objet déplaçable, changer le curseur."""
        event.target.style.cursor = "pointer"

    def dragstart(event):
        """Fonction appelée quand l'utilisateur commence à déplacer l'objet."""

        # associer une donnée au processus de glissement
        event.dataTransfer.setData("text", event.target.id)
        # permet à l'object d'être déplacé dans l'objet destination
        event.dataTransfer.effectAllowed = "move"

    def dragover(event):
        event.data.dropEffect = 'move'
        event.preventDefault()

    def drop(event):
        """Fonction attachée à la zone de destination.
        Elle définit ce qui se passe quand l'objet est déposé, c'est-à-dire
        quand l'utilisateur relâche la souris alors que l'objet est au-dessus de
        la zone.
        """

        # récupère les données stockées dans drag_start (l'id de l'objet déplacé)
        src_id = event.dataTransfer.getData("text")
        elt = document[src_id]

        # enlever la fonction associée à mouseover
        elt.unbind("mouseover")
        elt.style.cursor = "auto"
        event.preventDefault()

        if src_id in unit_info_table:

            # put unit there
            # get unit dragged
            (type_unit, role) = unit_info_table[src_id]

            # get zone
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
            selected_drop_zone = variant_data.closest_zone(pos)

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
                new_unit = mapping.Army(position_data, role, selected_drop_zone, None)
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                new_unit = mapping.Fleet(position_data, role, selected_drop_zone, None)

            # remove previous occupant if applicable
            if selected_drop_region in position_data.occupant_table:
                previous_unit = position_data.occupant_table[selected_drop_region]
                position_data.remove_unit(previous_unit)

            # add to position
            position_data.add_unit(new_unit)

        if src_id in ownership_info_table:

            # put ownership there
            # get ownership dragged
            (role, ) = ownership_info_table[src_id]

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

        # refresh
        callback_render(True)

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

    game_id = storage['GAME_ID']

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

    # get the position from server
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
                draggable_unit = mapping.Army(position_data, role, None, None)
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                draggable_unit = mapping.Fleet(position_data, role, None, None)

            identifier = f"unit_{num}"
            unit_canvas = html.CANVAS(id=identifier, width=32, height=32, alt="Draguez moi!")
            unit_info_table[identifier] = (type_unit, role)
            num += 1

            unit_canvas.draggable = True
            unit_canvas.bind("mouseover", mouseover)
            unit_canvas.bind("dragstart", dragstart)

            ctx2 = unit_canvas.getContext("2d")
            draggable_unit.render(ctx2)

            col <= unit_canvas
            row <= col

        col = html.TD()

        draggable_ownership = mapping.Ownership(position_data, role, None)

        identifier = f"center_{num}"
        ownership_canvas = html.CANVAS(id=identifier, width=32, height=32, alt="Draguez moi!")
        ownership_info_table[identifier] = (role, )
        num += 1

        ownership_canvas.draggable = True
        ownership_canvas.bind("mouseover", mouseover)
        ownership_canvas.bind("dragstart", dragstart)

        ctx3 = ownership_canvas.getContext("2d")
        draggable_ownership.render(ctx3)

        col <= ownership_canvas
        row <= col

        reserve_table <= row

    display_very_left = html.DIV(id='display_very_left')
    display_very_left.attrs['style'] = 'display: table-cell; width=40px; vertical-align: top; table-layout: fixed;'

    display_very_left <= reserve_table

    display_very_left <= html.BR()

    display_very_left <= html.DIV("Glissez/déposez ces unités ou ces centres sur la carte", Class='instruction')

    map_size = variant_data.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # dragging related events
    canvas.bind('dragover', dragover)
    canvas.bind("drop", drop)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(variant_name_loaded, interface_chosen)
    img.bind('load', lambda _: callback_render(True))

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    helper = html.DIV(".")
    display_left <= helper
    display_left <= canvas

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    legend_select_unit = html.DIV("Clic-long sur une unité pour l'effacer, clic-court sur une possession pour l'effacer", Class='instruction')
    buttons_right <= legend_select_unit

    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_very_left
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    MY_SUB_PANEL <= my_sub_panel2


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
            req_result = json.loads(req.text)
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
            common.info_dialog(f"Le joueur a été promu créateur : {messages}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_creator_callback(ev):  # pylint: disable=invalid-name
        """remove_creator_callback"""

        def reply_callback(req):
            req_result = json.loads(req.text)
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
            common.info_dialog(f"Le joueur a été déchu du rôle de créateur : {messages}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

    input_incomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_incomers, key=lambda pi: pi.upper()):
        option = html.OPTION(play_pseudo)
        input_incomer <= option

    fieldset <= input_incomer
    form <= fieldset

    form <= html.BR()

    input_put_in_game = html.INPUT(type="submit", value="Mettre dans les créateurs")
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

    input_outcomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_outcomers):
        option = html.OPTION(play_pseudo)
        input_outcomer <= option

    fieldset <= input_outcomer
    form <= fieldset

    form <= html.BR()

    input_remove_from_game = html.INPUT(type="submit", value="Retirer des créateurs")
    input_remove_from_game.bind("click", remove_creator_callback)
    form <= input_remove_from_game

    MY_SUB_PANEL <= form


def edit_moderators():
    """ edit_moderators """

    def add_moderator_callback(ev):  # pylint: disable=invalid-name
        """ add_moderator_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
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
            common.info_dialog(f"Le joueur a été promu modérateur : {messages}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def remove_moderator_callback(ev):  # pylint: disable=invalid-name
        """remove_moderator_callback"""

        def reply_callback(req):
            req_result = json.loads(req.text)
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
            common.info_dialog(f"Le joueur a été déchu du rôle de modérateur : {messages}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

    input_incomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_incomers, key=lambda pi: pi.upper()):
        option = html.OPTION(play_pseudo)
        input_incomer <= option

    fieldset <= input_incomer
    form <= fieldset

    form <= html.BR()

    input_put_in_game = html.INPUT(type="submit", value="Mettre dans les modérateurs")
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

    input_outcomer = html.SELECT(type="select-one", value="")
    for play_pseudo in sorted(possible_outcomers):
        option = html.OPTION(play_pseudo)
        input_outcomer <= option

    fieldset <= input_outcomer
    form <= fieldset

    form <= html.BR()

    input_remove_from_game = html.INPUT(type="submit", value="Retirer des modérateurs")
    input_remove_from_game.bind("click", remove_moderator_callback)
    form <= input_remove_from_game

    MY_SUB_PANEL <= form


def update_elo():
    """ update_elo """

    def cancel_update_database_callback(_, dialog):
        """ cancel_update_database_callback """
        dialog.close(None)

    def update_database_callback(_, dialog, elo_raw_list, teaser_text):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la mise à jour du ELO : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise à jour du ELO : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La mise à jour du ELO a été réalisée : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            update_elo()

        dialog.close(None)

        elo_raw_list_json = json.dumps(elo_raw_list)

        json_dict = {
            'elo_list': elo_raw_list_json,
            'teaser': teaser_text
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/elo_rating"

        # update database : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def update_database_confirm(elo_raw_list, teaser_text):
        """ update_database_confirm """

        dialog = mydialog.Dialog("On met à jour la base de données ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, erl=elo_raw_list, tt=teaser_text: update_database_callback(e, d, erl, tt))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_update_database_callback(e, d))

    def extract_elo_data_callback(ev):  # pylint: disable=invalid-name
        """ extract_elo_data_callback """

        def reply_callback(req):

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au calcul du ELO : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au calcul du ELO : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                update_elo()

                return

            games_results_dict = req_result['games_dict']
            elo_information = html.DIV()
            elo_raw_list, teaser_text = elo.process_elo(variant_data, players_dict, games_results_dict, games_dict, elo_information)

            if DOWNLOAD_LOG:
                alert("Télechargement automatique des logs du calcul")

                # exportation of logs
                log_html = elo_information.innerHTML

                # needed too for some reason
                MY_SUB_PANEL <= html.A(id='download_link')

                # perform actual exportation
                text_file_as_blob = window.Blob.new([log_html], {'type': 'text/plain'})
                download_link = document['download_link']
                time_stamp_now = int(time.time())
                download_link.download = f"diplomania_elo_{time_stamp_now}.html"
                download_link.href = window.URL.createObjectURL(text_file_as_blob)
                document['download_link'].click()

            # display result
            MY_SUB_PANEL.clear()
            MY_SUB_PANEL <= elo_information

            # offer update
            update_database_confirm(elo_raw_list, teaser_text)

        ev.preventDefault()

        json_dict = {
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/extract_elo_data"

        # extract_elo_data : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Mettre à jour le ELO")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    games_dict = common.get_games_data()
    if not games_dict:
        return

    variant_name = config.FORCED_VARIANT_NAME

    variant_content = common.game_variant_content_reload(variant_name)
    interface_chosen = interface.get_interface_from_variant(variant_name)
    interface_parameters = common.read_parameters(variant_name, interface_chosen)

    variant_data = mapping.Variant(variant_name, variant_content, interface_parameters)

    form = html.FORM()

    # ---

    input_maintain = html.INPUT(type="submit", value="Extraire et calculer")
    input_maintain.bind("click", extract_elo_data_callback)
    form <= input_maintain

    MY_SUB_PANEL <= form


def update_reliability():
    """ update_reliability """

    def cancel_update_database_callback(_, dialog):
        """ cancel_update_database_callback """
        dialog.close(None)

    def update_database_callback(_, dialog, reliability_list):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la mise à jour de la fiabilité : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise à jour de la fiabilité : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La mise à jour de la fiabilité a été réalisée : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            update_reliability()

        dialog.close(None)

        reliability_list_json = json.dumps(reliability_list)

        json_dict = {
            'reliability_list': reliability_list_json,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/reliability_rating"

        # update database : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def update_database_confirm(reliability_list):
        """ update_database_confirm """

        dialog = mydialog.Dialog("On met à jour la base de données ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, rl=reliability_list: update_database_callback(e, d, rl))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_update_database_callback(e, d))

    def extract_reliability_data_callback(ev):  # pylint: disable=invalid-name
        """ extract_reliability_data_callback """

        def reply_callback(req):

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au calcul de la fiabilité : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au calcul de la fiabilité : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                update_reliability()

                return

            games_results_dict = req_result['games_dict']
            reliability_information = html.DIV()
            reliability_list = elo.process_reliability(players_dict, games_results_dict, reliability_information)

            if DOWNLOAD_LOG:
                alert("Télechargement automatique des logs du calcul")

                # exportation of logs
                log_html = reliability_information.innerHTML

                # needed too for some reason
                MY_SUB_PANEL <= html.A(id='download_link')

                # perform actual exportation
                text_file_as_blob = window.Blob.new([log_html], {'type': 'text/plain'})
                download_link = document['download_link']
                time_stamp_now = int(time.time())
                download_link.download = f"diplomania_reliability_{time_stamp_now}.html"
                download_link.href = window.URL.createObjectURL(text_file_as_blob)
                document['download_link'].click()

            # display result
            MY_SUB_PANEL.clear()
            MY_SUB_PANEL <= reliability_information

            # offer update
            update_database_confirm(reliability_list)

        ev.preventDefault()

        json_dict = {
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/extract_elo_data"

        # extract_elo_data : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Mettre à jour la fiabilité")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    form = html.FORM()

    # ---

    input_maintain = html.INPUT(type="submit", value="Extraire et calculer")
    input_maintain.bind("click", extract_reliability_data_callback)
    form <= input_maintain

    MY_SUB_PANEL <= form


def update_regularity():
    """ update_regularity """

    def cancel_update_database_callback(_, dialog):
        """ cancel_update_database_callback """
        dialog.close(None)

    def update_database_callback(_, dialog, regularity_list):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la mise à jour de la régularité : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la mise à jour de la régularité : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"La mise à jour de la régularité a été réalisée : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            update_regularity()

        dialog.close(None)

        regularity_list_json = json.dumps(regularity_list)

        json_dict = {
            'regularity_list': regularity_list_json,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/regularity_rating"

        # update database : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def update_database_confirm(regularity_list):
        """ update_database_confirm """

        dialog = mydialog.Dialog("On met à jour la base de données ?", ok_cancel=True)
        dialog.ok_button.bind("click", lambda e, d=dialog, rl=regularity_list: update_database_callback(e, d, rl))
        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_update_database_callback(e, d))

    def extract_regularity_data_callback(ev):  # pylint: disable=invalid-name
        """ extract_regularity_data_callback """

        def reply_callback(req):

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au calcul de la régularité : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au calcul de la régularité : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                update_regularity()

                return

            games_results_dict = req_result['games_dict']
            regularity_information = html.DIV()
            regularity_list = elo.process_regularity(players_dict, games_results_dict, regularity_information)

            if DOWNLOAD_LOG:
                alert("Télechargement automatique des logs du calcul")

                # exportation of logs
                log_html = regularity_information.innerHTML

                # needed too for some reason
                MY_SUB_PANEL <= html.A(id='download_link')

                # perform actual exportation
                text_file_as_blob = window.Blob.new([log_html], {'type': 'text/plain'})
                download_link = document['download_link']
                time_stamp_now = int(time.time())
                download_link.download = f"diplomania_regularity_{time_stamp_now}.html"
                download_link.href = window.URL.createObjectURL(text_file_as_blob)
                document['download_link'].click()

            # display result
            MY_SUB_PANEL.clear()
            MY_SUB_PANEL <= regularity_information

            # offer update
            update_database_confirm(regularity_list)

        ev.preventDefault()

        json_dict = {
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/extract_elo_data"

        # extract_elo_data : need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Mettre à jour la régularité")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    form = html.FORM()

    # ---

    input_maintain = html.INPUT(type="submit", value="Extraire et calculer")
    input_maintain.bind("click", extract_regularity_data_callback)
    form <= input_maintain

    MY_SUB_PANEL <= form


def clear_old_delays():
    """ clear_old_delays """

    def clear_old_delays_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'effacement des anciens retards : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Erreur à l'effacement des anciens retards : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                MY_SUB_PANEL.clear()
                clear_old_delays()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            common.info_dialog(f"Vous avez effacé les anciens incidents : {messages}")

            # back to where we started
            MY_SUB_PANEL.clear()
            clear_old_delays()

        ev.preventDefault()

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/clear-old-delays"

        # clear old delays : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Effacer les anciens retards")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    form = html.FORM()

    input_clear_old_delays = html.INPUT(type="submit", value="Effacer les anciens retards")
    input_clear_old_delays.bind("click", clear_old_delays_callback)
    form <= input_clear_old_delays

    MY_SUB_PANEL <= form


def show_idle_data():
    """ show_idle_data """

    def delete_account_callback(ev, player_pseudo):  # pylint: disable=invalid-name
        """ delete_account_callback """

        # first step : usurp to get a token
        # second step : delete account using token

        def reply_callback1(req):

            def reply_callback2(req):
                req_result = json.loads(req.text)
                if req.status != 200:
                    if 'message' in req_result:
                        alert(f"Erreur à la suppression du compte {player_pseudo}: {req_result['message']}")
                    elif 'msg' in req_result:
                        alert(f"Problème à la suppression du compte {player_pseudo} : {req_result['msg']}")
                    else:
                        alert("Réponse du serveur imprévue et non documentée")
                    return

                messages = "<br>".join(req_result['msg'].split('\n'))
                common.info_dialog(f"Le compte {player_pseudo} a été supprimé : {messages}")

                # back to where we started
                MY_SUB_PANEL.clear()
                show_idle_data()

            req_result = json.loads(req.text)
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
            ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': token}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback2, ontimeout=common.noreply_callback)

        ev.preventDefault()

        json_dict = {
            'usurped_user_name': player_pseudo,
        }

        host = config.SERVER_CONFIG['USER']['HOST']
        port = config.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/usurp"

        # usurping : need token
        # note : since we access directly to the user server, we present the token in a slightly different way
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'Authorization': f"Bearer {storage['JWT_TOKEN']}"}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback1, ontimeout=common.noreply_callback)

    def recall_account_callback(ev, player_pseudo):  # pylint: disable=invalid-name
        """ recall_account_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi du rappel: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi du rappel : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            common.info_dialog(f"Message émis vers : {player_pseudo}")

        ev.preventDefault()

        subject = "Message de la part de l'administrateur du site https://diplomania-gen.fr (AFJD)"
        body = ""
        body += f"Bonjour {player_pseudo}"
        body += "\n\n"
        body += "Cher joueur, nous avons noté que tu n’as pas utilisé ton compte depuis longtemps."
        body += "\n"
        body += "Sache que de nombreuses parties (amicales, blitz, en négociation) sont disponibles sur le site https://diplomania-gen.fr/ avec un forum qui t’informera de tous les tournois en cours (en ligne et en face à face)."
        body += "\n"
        body += "C’est peut-être l’occasion de revenir nous voir ?"
        body += "\n"
        body += "Tu peux aussi nous rejoindre sur discord https://discord.gg/mUWes7yEqR. Nous sommes à ton écoute."
        body += "\n"
        body += "On espère te revoir bientôt"
        body += "\n"
        body += "Ludiquement"

        addressed_id = pseudo2id[player_pseudo]

        json_dict = {
            'addressees': str(addressed_id),
            'subject': subject,
            'body': body,
            'type': 'please_play',
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        show_idle_data()

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

    fields = ['player', 'id', 'last_login', 'email', 'recall', 'delete']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'player': 'joueur', 'id': 'id', 'last_login': 'dernier login', 'email': 'courriel', 'recall': 'rappeler', 'delete': 'supprimer'}[field]
        col = html.TD(field_fr)
        thead <= col
    idle_table <= thead

    pseudo2id = {v['pseudo']: int(k) for k, v in players_dict.items()}

    emails_dict = common.get_all_emails()

    time_stamp_now = time.time()

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
                email, _, __ = emails_dict[player]
                email_link = html.A(href=f"mailto:{email}")
                email_link <= email
                value = email_link

            if field == 'recall':
                form = html.FORM()
                input_delete_account = html.INPUT(type="image", src="./images/recall.jpg")
                input_delete_account.bind("click", lambda e, p=player: recall_account_callback(e, p))
                form <= input_delete_account
                value = form

            if field == 'delete':
                form = html.FORM()
                input_delete_account = html.INPUT(type="image", src="./images/delete.png")
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


def maintain():
    """ maintain """

    def maintain_callback(ev):  # pylint: disable=invalid-name
        """ maintain_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
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

            common.info_dialog(f"Maintenance réalisée :{messages}")

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
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    MY_SUB_PANEL <= html.H3("Maintenance")

    if not common.check_admin():
        alert("Pas le bon compte (pas admin)")
        return

    form = html.FORM()

    # ---

    input_maintain = html.INPUT(type="submit", value="Déclencher")
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

ITEM_NAME_SELECTED = OPTIONS[0]

MY_SUB_PANEL = html.DIV(id="admin")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Changer nouvelles':
        change_news_admin()
    if item_name == 'Usurper':
        usurp()
    if item_name == 'Rectifier les paramètres':
        rectify_parameters()
    if item_name == 'Rectifier la position':
        rectify_position()
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
    if item_name == 'Mise à jour du elo':
        update_elo()
    if item_name == 'Mise à jour de la fiabilité':
        update_reliability()
    if item_name == 'Mise à jour de la régularité':
        update_regularity()
    if item_name == 'Effacement des anciens retard':
        clear_old_delays()
    if item_name == 'Comptes oisifs':
        show_idle_data()
    if item_name == 'Maintenance':
        maintain()

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
