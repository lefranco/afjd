""" admin """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time
import datetime

from browser import document, html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import interface
import login
import mapping
import geometry


OPTIONS = ['changer nouvelles', 'usurper', 'rectifier la position', 'envoyer un courriel', 'dernières connexions', 'connexions manquées', 'tous les courriels', 'éditer les modérateurs']

LONG_DURATION_LIMIT_SEC = 1.0

ADMIN_PSEUDO = 'Palpatine'


def check_admin(pseudo):
    """ check_admin """

    # TODO improve this with real admin account
    if pseudo != ADMIN_PSEUDO:
        return False

    return True


def get_last_logins():
    """ get_last_logins """

    logins_list = None

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


def change_news():
    """ change_news """

    def change_news_callback(_):
        """ change_news_callback """

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
            InfoDialog("OK", f"Les nouvelles ont été changées : {messages}", remove_after=config.REMOVE_AFTER)

        news_content = input_news_content.value
        if not news_content:
            alert("Contenu nouvelles manquant")
            return

        json_dict = {
            'pseudo': pseudo,
            'content': news_content,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/news"

        # changing news : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        change_news()

    MY_SUB_PANEL <= html.H3("Editer les nouvelles")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        alert("Pas le bon compte (pas admin)")
        return

    news_content_loaded = common.get_news_content()
    if news_content_loaded is None:
        return

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_news_content = html.LEGEND("nouvelles", title="Saisir le nouveau contenu de nouvelles")
    fieldset <= legend_news_content
    input_news_content = html.TEXTAREA(type="text", rows=20, cols=100)
    input_news_content <= news_content_loaded
    fieldset <= input_news_content
    form <= fieldset

    form <= html.BR()

    input_change_news_content = html.INPUT(type="submit", value="mettre à jour")
    input_change_news_content.bind("click", change_news_callback)
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
            time_stamp = time.time()
            storage['LOGIN_TIME'] = str(time_stamp)

            InfoDialog("OK", f"Vous usurpez maintenant : {usurped_user_name}", remove_after=config.REMOVE_AFTER)
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

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
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

    input_select_player = html.INPUT(type="submit", value="usurper")
    input_select_player.bind("click", usurp_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def rectify():
    """rectify """

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
            InfoDialog("OK", f"Vous avez rectifié la position : {messages}", remove_after=config.REMOVE_AFTER)

        # units
        units_list_dict = position_data.save_json()
        units_list_dict_json = json.dumps(units_list_dict)

        # ownerships
        ownerships_list_dict = position_data.save_json2()
        ownerships_list_dict_json = json.dumps(ownerships_list_dict)

        json_dict = {
            'pseudo': pseudo,
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
        callback_render(None)

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
        selected_erase_unit = position_data.closest_unit(pos, None)

        # unit must be selected
        if selected_erase_unit is None:
            return

        # remove unit
        position_data.remove_unit(selected_erase_unit)

        # tricky
        nonlocal selected_hovered_object
        if selected_hovered_object == selected_erase_unit:
            selected_hovered_object = None

        # update map
        callback_render(None)

    def callback_canvas_mousedown(event):
        """ callback_mousedow : store event"""

        nonlocal down_click_time
        nonlocal stored_event

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

            # put back previous
            if prev_selected_hovered_object is not None:
                prev_selected_hovered_object.highlite(ctx, False)

            # hightlite object where mouse is
            if selected_hovered_object is not None:
                selected_hovered_object.highlite(ctx, True)

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """
        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, False)

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        variant_data.render(ctx)

        # put the position
        position_data.render(ctx)

        # put the legends at the end
        variant_data.render_legends(ctx)

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="rectifier la position")
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
        callback_render(ctx)

    # starts here

    MY_SUB_PANEL <= html.H3("Rectifier la position")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
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
        col <= html.B(variant_data.name_table[role])
        row <= col

        for type_unit in mapping.UnitTypeEnum:

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

            ctx = unit_canvas.getContext("2d")
            draggable_unit.render(ctx)

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

        ctx = ownership_canvas.getContext("2d")
        draggable_ownership.render(ctx)

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
    img.bind('load', callback_render)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

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


def sendmail():
    """ sendmail """

    def sendmail_callback(_):
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

            InfoDialog("OK", f"Message émis vers : {addressed_user_name}", remove_after=config.REMOVE_AFTER)

        addressed_user_name = input_addressed.value
        if not addressed_user_name:
            alert("User name destinataire manquant")
            return

        subject = "Message de la part de l'administrateur du site https://diplomania-gen.fr (AFJD)"

        if not input_message.value:
            alert("Contenu du message vide")
            return

        body = input_message.value

        addressed_id = players_dict[addressed_user_name]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': pseudo,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        MY_SUB_PANEL.clear()
        sendmail()

    MY_SUB_PANEL <= html.H3("Envoyer un courriel")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        alert("Pas le bon compte (pas admin)")
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
    input_message = html.TEXTAREA(type="text", rows=5, cols=80)
    fieldset <= input_message
    form <= fieldset

    form <= html.BR()

    input_select_player = html.INPUT(type="submit", value="envoyer le courriel")
    input_select_player.bind("click", sendmail_callback)
    form <= input_select_player

    MY_SUB_PANEL <= form


def last_logins():
    """ logins """

    MY_SUB_PANEL <= html.H3("Liste des dernières connexions")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        alert("Pas le bon compte (pas admin)")
        return

    logins_list = get_last_logins()

    logins_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'date']:
        col = html.TD(field)
        thead <= col
    logins_table <= thead

    for pseudo, date in sorted(logins_list, key=lambda l: l[1], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        date_now_gmt = datetime.datetime.fromtimestamp(date, datetime.timezone.utc)
        date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
        col = html.TD(date_now_gmt_str)
        row <= col

        logins_table <= row

    MY_SUB_PANEL <= logins_table


def last_failures():
    """ failures """

    MY_SUB_PANEL <= html.H3("Liste des connexions manquées")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        alert("Pas le bon compte (pas admin)")
        return

    failures_list = get_last_failures()

    failures_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['pseudo', 'date']:
        col = html.TD(field)
        thead <= col
    failures_table <= thead

    for pseudo, date in sorted(failures_list, key=lambda l: l[1], reverse=True):
        row = html.TR()

        col = html.TD(pseudo)
        row <= col

        date_now_gmt = datetime.datetime.fromtimestamp(date, datetime.timezone.utc)
        date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")
        col = html.TD(date_now_gmt_str)
        row <= col

        failures_table <= row

    MY_SUB_PANEL <= failures_table


def all_emails():
    """ all_emails """

    MY_SUB_PANEL <= html.H3("Liste joueurs avec leurs courriels")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        alert("Pas le bon compte (pas admin)")
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


def edit_moderators():
    """ edit_moderators """

    def add_moderator_callback(_):
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
            InfoDialog("OK", f"Le joueur a été mis dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_moderators()

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

    def remove_moderator_callback(_):
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
            InfoDialog("OK", f"Le joueur a été retiré de la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            MY_SUB_PANEL.clear()
            edit_moderators()

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

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_admin(pseudo):
        alert("Pas le bon compte (pas admin)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    moderators_list = common.get_moderators()

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

    input_put_in_game = html.INPUT(type="submit", value="mettre dans les modérateur")
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

    input_remove_from_game = html.INPUT(type="submit", value="retirer des modérateurs")
    input_remove_from_game.bind("click", remove_moderator_callback)
    form <= input_remove_from_game

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
    if item_name == 'changer nouvelles':
        change_news()
    if item_name == 'usurper':
        usurp()
    if item_name == 'rectifier la position':
        rectify()
    if item_name == 'envoyer un courriel':
        sendmail()
    if item_name == 'dernières connexions':
        last_logins()
    if item_name == 'connexions manquées':
        last_failures()
    if item_name == 'tous les courriels':
        all_emails()
    if item_name == 'éditer les modérateurs':
        edit_moderators()

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
