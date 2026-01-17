""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps

from browser import html, ajax, alert, window, document   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mydatetime
import config
import common
import sandbox
import geometry
import mapping
import mydialog

import index  # circular import

import play  # circular import
import play_low


NON_DIVULGUE = "Non divulgué"


def display_special_information_callback(_):
    """ display_special_information_callback """

    alert("Après un stab - réussi ou pas ou tout autre raison - la victime vous insulte ? Voici la conduite à tenir :\n\n 1) Contacter l'arbitre de la partie par la messagerie de la partie\n\n 2) Contacter un modérateur - la liste des modérateurs est dans Classement/Groupe Modérateur et la messagerie personnelle s'accède par Accueil/Messagerie personnelle\n\n 3) Contacter un administrateur par Accueil/Déclarer un incident.\n\n Ne passer à l'étape suivante qu'en cas d'échec de l'étape précédente bien sûr !\n\nDans tous les cas, notez bien et transmettez le numéro ('id') du message ou de la déclaration incriminée pour référence !")


def date_last_visit_update(game_id, role_id, visit_type):
    """ date_last_visit_update """

    def reply_callback(req):
        req_result = loads(req.text)
        if req.status != 201:
            if 'message' in req_result:
                alert(f"Erreur à la mise à jour de la dernière visite de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la mise à jour de la dernière visite de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")

    json_dict = {
        'role_id': role_id,
    }

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-visits/{game_id}/{visit_type}"

    # putting visit in a game : need token
    ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)


def join_game():
    """ join_game_action : the third way of joining a game (by a link) """

    def cancel_join_callback(_, dialog):
        alert("Sage décision !")
        dialog.close(None)

    def confirm_join_callback(_, dialog):
        def reply_callback(req):

            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'inscription à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'inscription à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            alert("Félicitations, vous avez bien rejoint la partie !")
            alert("Si elle n'est pas en cours, un courriel vous préviendra de son démarrage mais revenez régulièrement sur le site surveiller pour ne pas le manquer...")

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Vous avez rejoint la partie  : {messages}")

            # This needs to be updated
            play_low.ROLE_ID, play_low.IN_GAME = common.get_role_allocated_to_player_in_game(play_low.GAME_ID)

            # and we need te refresh
            play_low.MY_SUB_PANEL.clear()
            show_position()

        dialog.close(None)
        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # adding allocation : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        return

    pseudo = play_low.PSEUDO

    if play_low.GAME_ID is None:
        alert("Problème avec la partie")
        return

    game_id = play_low.GAME_ID

    alert("Vous vous apprêtez à rejoindre une partie. Pouvons-nous compter sur votre engagement jusqu'à la fin ? Une popup va s'afficher vous demandant confirmation...")
    dialog = mydialog.MyDialog("Vous êtes sûr de jouer ?", ok_cancel=True)
    dialog.ok_button.bind("click", lambda e, d=dialog: confirm_join_callback(e, d))
    dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_join_callback(e, d))


def non_playing_information():
    """ non_playing_information """

    # need to be connected
    if play_low.PSEUDO is None:
        return None

    # is game anonymous
    if not (play_low.ROLE_ID == 0 or not play_low.GAME_PARAMETERS_LOADED['anonymous']):
        return None

    dangling_players = [p for p, d in play_low.GAME_PLAYERS_DICT.items() if d == - 1]
    if not dangling_players:
        return None

    info = "Les pseudos suivants sont alloués à la partie sans rôle : "
    for dangling_player_id_str in dangling_players:
        dangling_player_id = int(dangling_player_id_str)
        dangling_player = play_low.ID2PSEUDO[dangling_player_id]
        info += f"{dangling_player} "

    return html.EM(info)


def show_position(advancement=None):
    """ show_position """

    position_data = None
    fake_report_loaded = None
    orders_data_txt = ""
    selected_hovered_object = None

    canvas = None
    helper = None
    ctx = None

    pseudo = None
    game_id = None
    role_id = None
    in_game = False

    def join_game_callback(ev):  # pylint: disable=invalid-name

        ev.preventDefault()
        play.set_arrival('rejoindre')
        play.render(play_low.PANEL_MIDDLE)

    def quit_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la désinscription de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Erreur à la désinscription de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                play_low.MY_SUB_PANEL.clear()
                show_position()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Vous avez quitté la partie : {messages}")

            # go to game
            play_low.PANEL_MIDDLE.clear()
            play.render(play_low.PANEL_MIDDLE)

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'delete': 1
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # should be a delete but body in delete requests is more or less forbidden
        # quitting a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def take_mastering_game_callback(ev):  # pylint: disable=invalid-name

        def reply_callback(req):

            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la prise de l'arbitrage de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la prise de l'arbitrage de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")

                # failed but refresh
                play_low.MY_SUB_PANEL.clear()
                show_position()

                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Vous avez pris l'arbitrage de la partie : {messages}")

            # go to game
            play_low.PANEL_MIDDLE.clear()
            play.render(play_low.PANEL_MIDDLE)

        ev.preventDefault()

        json_dict = {
            'game_id': game_id,
            'role_id': 0,
            'player_pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # taking game mastering : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = position_data.closest_object(pos)

        if selected_hovered_object != prev_selected_hovered_object:

            helper.clear()

            # unhightlite previous
            if prev_selected_hovered_object is not None:
                prev_selected_hovered_object.highlite(ctx, False)

            # hightlite object where mouse is
            if selected_hovered_object is not None:
                selected_hovered_object.highlite(ctx, True)
                helper <= selected_hovered_object.description()
            else:
                helper <= "_"

            # redraw dislodged if applicable
            if isinstance(prev_selected_hovered_object, mapping.Unit):
                if prev_selected_hovered_object in position_data.dislodging_table:
                    dislodged = position_data.dislodging_table[prev_selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

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

            # redraw dislodged if applicable
            if isinstance(selected_hovered_object, mapping.Unit):
                if selected_hovered_object in position_data.dislodging_table:
                    dislodged = position_data.dislodging_table[selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

        helper.clear()
        helper <= "_"

    def callback_refresh(_):
        """ callback_refresh """

        game_parameters_loaded = common.game_parameters_reload(play_low.GAME)
        if not game_parameters_loaded:
            alert("Erreur chargement paramètres")
            return

        if game_parameters_loaded['current_advancement'] == play_low.GAME_PARAMETERS_LOADED['current_advancement']:
            # no change it seeems
            mydialog.info_go("Rien de nouveau sous le soleil !")
            return

        alert("La position de la partie a changé !")
        play_low.load_dynamic_stuff()

        play_low.MY_SUB_PANEL.clear()
        play.load_option(None, 'Consulter')

    def callback_text_orders(_):
        """ callback_text_orders """

        if orders_data_txt:
            alert(orders_data_txt)

    def callback_export_sandbox(_):
        """ callback_export_sandbox """

        # action on importing game
        sandbox.set_arrival("play")

        # action on importing game
        sandbox.import_position(play_low.POSITION_DATA)

        # action of going to sandbox page
        index.load_option(None, 'Bac à sable')

    def callback_download_game_json(_):
        """ callback_download_game_json """

        json_return_dict = None

        def reply_callback(req):
            nonlocal json_return_dict
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de l'export json de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de l'export json de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return
            json_return_dict = req_result['content']
            json_text = dumps(json_return_dict, indent=4, ensure_ascii=False)

            # needed too for some reason
            play_low.MY_SUB_PANEL <= html.A(id='download_link')

            # perform actual exportation
            text_file_as_blob = window.Blob.new([json_text], {'type': 'text/plain'})
            download_link = document['download_link']
            download_link.download = f"diplomania_{play_low.GAME}_{play_low.GAME_ID}_json.txt"
            download_link.href = window.URL.createObjectURL(text_file_as_blob)
            document['download_link'].click()

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-export/{play_low.GAME_ID}"

        # getting game json export : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return True

    def transition_display_callback(_, advancement_selected):

        nonlocal position_data
        nonlocal fake_report_loaded
        nonlocal orders_data_txt

        nonlocal canvas
        nonlocal helper
        nonlocal ctx

        def copy_url_consult_callback(_):
            """ copy_url_consult_callback """
            input_copy_url_consult.select()
            # ev.setSelectionRange(0, 99999) # For mobile devices
            window.navigator.clipboard.writeText(input_copy_url_consult.value)
            alert(f"Lien '{input_copy_url_consult.value}' copié dans le presse papier...")

        def copy_url_consult2_callback(_):
            """ copy_url_consult2_callback """
            input_copy_url_consult.select()
            # ev.setSelectionRange(0, 99999) # For mobile devices
            window.navigator.clipboard.writeText(input_copy_url_consult2.value)
            alert(f"Lien '{input_copy_url_consult2.value}' copié dans le presse papier...")

        def copy_url_join_callback(_):
            """ copy_url_join_callback """
            input_copy_url_join.select()
            # ev.setSelectionRange(0, 99999) # For mobile devices
            window.navigator.clipboard.writeText(input_copy_url_join.value)
            alert(f"Lien '{input_copy_url_join.value}' copié dans le presse papier...")

        def copy_url_extract_callback(_):
            """ copy_url_extract_callback """
            input_copy_url_extract.select()
            # ev.setSelectionRange(0, 99999) # For mobile devices
            window.navigator.clipboard.writeText(input_copy_url_extract.value)
            alert(f"Lien '{input_copy_url_extract.value}' copié dans le presse papier...")

        def callback_render(_):
            """ callback_render """

            # since orders are part of the data not save/restore context

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the position and the neutral centers
            position_data.render(ctx)

            # put the legends
            play_low.VARIANT_DATA.render(ctx)

            # put the orders (if history)
            if orders_data:
                orders_data.render(ctx)

        # current position is default
        orders_loaded = None
        fake_report_loaded = play_low.REPORT_LOADED
        position_data = play_low.POSITION_DATA
        orders_data = None

        # exception for start build games
        min_possible_advancement = 4 if play_low.VARIANT_DATA.start_build else 0

        if advancement_selected != last_advancement:

            fog_of_war = play_low.GAME_PARAMETERS_LOADED['fog']
            if fog_of_war:
                transition_loaded = play_low.game_transition_fog_of_war_reload(play_low.GAME_ID, advancement_selected, play_low.ROLE_ID)
            else:
                transition_loaded = play_low.game_transition_reload(play_low.GAME_ID, advancement_selected)

            if transition_loaded:

                # retrieve stuff from history
                time_stamp = transition_loaded['time_stamp']
                report_loaded = transition_loaded['report_txt']
                fake_report_loaded = {'time_stamp': time_stamp, 'content': report_loaded}

                # digest the position
                position_loaded = transition_loaded['situation']
                position_data = mapping.Position(position_loaded, play_low.VARIANT_DATA)

                # digest the orders
                orders_loaded = transition_loaded['orders']
                communication_orders_loaded = transition_loaded['communication_orders']
                orders_data = mapping.Orders(orders_loaded, position_data, communication_orders_loaded)

                # make a text version (for fog mainly)
                orders_data_txt = orders_data.text_version()

            else:

                # to force current map to be displayed
                advancement_selected = last_advancement

                # erase
                orders_data_txt = ""

        else:

            # erase
            orders_data_txt = ""

        # now we can display
        play_low.MY_SUB_PANEL.clear()
        #  play_low.MY_SUB_PANEL.attrs['style'] = 'display:table-row'

        # title
        play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
        play_low.MY_SUB_PANEL <= html.BR()

        # create left side
        display_left = html.DIV(id='display_left')
        display_left.attrs['style'] = 'display: table-cell; width:500px; vertical-align: top; table-layout: fixed;'

        # put it in
        play_low.MY_SUB_PANEL <= display_left

        # put stuff in left side

        if advancement_selected != last_advancement:
            # display only if from history
            game_status = play_low.get_game_status_histo(play_low.VARIANT_DATA, advancement_selected)
            display_left <= game_status
            display_left <= html.BR()

        # create canvas
        map_size = play_low.VARIANT_DATA.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        ctx = canvas.getContext("2d")
        if ctx is None:
            alert("Il faudrait utiliser un navigateur plus récent !")
            return

        # hovering effect
        canvas.bind("mousemove", callback_canvas_mouse_move)
        canvas.bind("mouseenter", callback_canvas_mouse_enter)
        canvas.bind("mouseleave", callback_canvas_mouse_leave)

        # put background (this will call the callback that display the whole map)
        img = common.read_map(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN)
        img.bind('load', lambda _: callback_render(True))

        display_left <= canvas

        helper = html.DIV(Class='helper')
        display_left <= helper

        display_left <= html.BR()

        fog_of_war = play_low.GAME_PARAMETERS_LOADED['fog']
        game_over = play_low.GAME_PARAMETERS_LOADED['soloed'] or play_low.GAME_PARAMETERS_LOADED['end_voted'] or play_low.GAME_PARAMETERS_LOADED['finished']
        game_scoring = play_low.GAME_PARAMETERS_LOADED['scoring']
        rating_colours_window = common.make_rating_colours_window(fog_of_war, game_over, play_low.VARIANT_DATA, position_data, play_low.INTERFACE_CHOSEN, game_scoring, play_low.ROLE_ID, play_low.GAME_PLAYERS_DICT, play_low.ID2PSEUDO)

        display_left <= rating_colours_window
        display_left <= html.BR()

        report_non_playing = non_playing_information()
        if report_non_playing is not None:
            display_left <= report_non_playing
            display_left <= html.BR()
            display_left <= html.BR()

        report_window = common.make_report_window(fake_report_loaded)
        display_left <= report_window

        # create right part
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # put it in
        play_low.MY_SUB_PANEL <= buttons_right

        # put stuff in right side

        # role flag if applicable
        if play_low.ROLE_ID is not None:
            play_low.stack_role_flag(buttons_right)

        buttons_right <= html.H3("Position")

        input_refresh = html.INPUT(type="submit", value="Recharger la partie", Class='btn-inside')
        input_refresh.bind("click", callback_refresh)
        buttons_right <= input_refresh
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        # button last moves
        play_low.stack_last_moves_button(buttons_right, play_low.MY_SUB_PANEL, None, None, False)

        buttons_right <= html.H3("Historique")

        if advancement_selected != min_possible_advancement:
            input_first = html.BUTTON("||<<", Class='btn-inside')
            input_first.bind("click", lambda e, a=min_possible_advancement: transition_display_callback(e, a))
        else:
            input_first = html.BUTTON("||<<", disabled=True, Class='btn-inside')
            input_first.style = {'pointer-events': 'none'}
        buttons_right <= input_first
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        if advancement_selected > min_possible_advancement:
            input_previous = html.BUTTON("<", Class='btn-inside')
            input_previous.bind("click", lambda e, a=advancement_selected - 1: transition_display_callback(e, a))
        else:
            input_previous = html.BUTTON("<", disabled=True, Class='btn-inside')
            input_previous.style = {'pointer-events': 'none'}
        buttons_right <= input_previous
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        if advancement_selected < last_advancement:
            input_next = html.BUTTON(">", Class='btn-inside')
        else:
            input_next = html.BUTTON(">", disabled=True, Class='btn-inside')
            input_next.style = {'pointer-events': 'none'}
        input_next.bind("click", lambda e, a=advancement_selected + 1: transition_display_callback(e, a))
        buttons_right <= input_next
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        if advancement_selected != last_advancement:
            input_last = html.BUTTON(">>||", Class='btn-inside')
        else:
            input_last = html.BUTTON(">>||", disabled=True, Class='btn-inside')
            input_last.style = {'pointer-events': 'none'}
        input_last.bind("click", lambda e, a=last_advancement: transition_display_callback(e, a))
        buttons_right <= input_last
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        for adv_sample in range(4, last_advancement, 5):

            adv_sample_season, adv_sample_year = common.get_short_season(adv_sample, play_low.VARIANT_DATA)
            adv_sample_season_readable = play_low.VARIANT_DATA.season_name_table[adv_sample_season]

            input_last = html.INPUT(type="submit", value=f"{adv_sample_season_readable} {adv_sample_year}", Class='btn-inside')
            input_last.bind("click", lambda e, a=adv_sample: transition_display_callback(e, a))
            buttons_right <= input_last
            if adv_sample + 5 < last_advancement:
                buttons_right <= html.BR()
                buttons_right <= html.BR()

        buttons_right <= html.H3("Appariement")

        if pseudo is None:

            player_status_str = "Vous n'êtes pas identifié"
            buttons_right <= html.DIV(player_status_str, Class='important')

        else:

            if role_id is None:

                # join game
                if not in_game:
                    form = html.FORM()
                    input_join_game = html.INPUT(type="submit", value="Je rejoins la partie", Class='btn-inside')
                    input_join_game.bind("click", join_game_callback)
                    form <= input_join_game
                    buttons_right <= form
                    buttons_right <= html.BR()

                # quit game
                if in_game:
                    form = html.FORM()
                    input_quit_game = html.INPUT(type="submit", value="Je quitte la partie !", Class='btn-inside')
                    input_quit_game.bind("click", quit_game_callback)
                    form <= input_quit_game
                    buttons_right <= form
                    buttons_right <= html.BR()

                # take mastering
                if not play_low.GAME_MASTER:
                    form = html.FORM()
                    input_join_game = html.INPUT(type="submit", value="Je prends l'arbitrage !", Class='btn-inside')
                    input_join_game.bind("click", take_mastering_game_callback)
                    form <= input_join_game
                    buttons_right <= form
                    buttons_right <= html.BR()

        buttons_right <= html.H3("Divers")

        if orders_data_txt:
            input_show_orders_text = html.INPUT(type="submit", value="Visualiser les ordres en texte", Class='btn-inside')
            input_show_orders_text.bind("click", callback_text_orders)
            buttons_right <= input_show_orders_text
            buttons_right <= html.BR()
            buttons_right <= html.BR()

        input_export_sandbox = html.INPUT(type="submit", value="Exporter la partie vers le bac à sable", Class='btn-inside')
        input_export_sandbox.bind("click", callback_export_sandbox)
        buttons_right <= input_export_sandbox
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        url = f"{config.SITE_ADDRESS}?game={play_low.GAME}"
        input_copy_url_consult = html.INPUT(type="text", value=url)
        button_copy_url_consult = html.BUTTON("Copier le lien pour inviter un joueur à consulter la partie.", Class='btn-inside')
        button_copy_url_consult.bind("click", copy_url_consult_callback)
        buttons_right <= button_copy_url_consult
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        url = f"{config.SITE_ADDRESS}?game={play_low.GAME}&advancement={advancement_selected}"
        input_copy_url_consult2 = html.INPUT(type="text", value=url)
        button_copy_url_consult2 = html.BUTTON("Copier le lien pour inviter un joueur à consulter la partie sur la saison affichée.", Class='btn-inside')
        button_copy_url_consult2.bind("click", copy_url_consult2_callback)
        buttons_right <= button_copy_url_consult2
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        url = f"{config.SITE_ADDRESS}?game={play_low.GAME}&arrival=rejoindre"
        input_copy_url_join = html.INPUT(type="text", value=url)
        button_copy_url_join = html.BUTTON("Copier le lien pour inviter un joueur à rejoindre la partie.", Class='btn-inside')
        button_copy_url_join.bind("click", copy_url_join_callback)
        buttons_right <= button_copy_url_join
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-export/{play_low.GAME_ID}"
        input_copy_url_extract = html.INPUT(type="text", value=url)
        button_copy_url_extract = html.BUTTON("Copier le lien pour une extraction automatique depuis le back-end.", Class='btn-inside')
        button_copy_url_extract.bind("click", copy_url_extract_callback)
        buttons_right <= button_copy_url_extract
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        if play_low.VARIANT_DATA.name.startswith('standard'):
            input_download_game_json = html.INPUT(type="submit", value="Télécharger la partie au format JSON", Class='btn-inside')
            input_download_game_json.bind("click", callback_download_game_json)
            buttons_right <= input_download_game_json
            buttons_right <= html.BR()
            buttons_right <= html.BR()

    game_id = play_low.GAME_ID
    role_id = play_low.ROLE_ID
    in_game = play_low.IN_GAME
    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']

    last_advancement = play_low.GAME_PARAMETERS_LOADED['current_advancement']

    # initiates callback
    if advancement is not None:
        transition_display_callback(None, advancement)
    else:
        transition_display_callback(None, last_advancement)

    return True


def show_informations():
    """ show_informations """

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    play_low.MY_SUB_PANEL <= html.H3("Informations")
    play_low.MY_SUB_PANEL <= html.H4("Paramètres")

    # conversion
    game_type_conv = {v: k for k, v in config.GAME_TYPES_CODE_TABLE.items()}
    force_wait_conv = {-1: 'Maintenant', 0: 'Pas de forçage', 1: 'A la date limite'}
    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

    game_params_table = html.TABLE()

    # table header
    thead = html.THEAD()
    for field_name in "Nom du paramètre", "Type", "Valeur pour la partie", "Explication":
        col = html.TD(field_name)
        thead <= col
    game_params_table <= thead

    for key, value in play_low.GAME_PARAMETERS_LOADED.items():

        if key in ['name', 'description', 'variant', 'deadline', 'current_state', 'current_advancement', 'soloed', 'end_voted', 'finished']:
            continue

        row = html.TR()

        parameter_name, parameter_type, parameter_explanation = {
            'fog':                            ("brouillard",                                     "oui ou non", "Si oui, la visibilité des unités est restreinte, Les joueurs ne voient que les unités voisines de leurs centres et leurs unités"),  # noqa: E241
            'exposition':                     ("exposition",                                     "oui ou non", "Si oui, la partie n'est pas jouée, elle est juste consultable, L'arbitre peut passer des ordres, les dates limites ne sont pas gérées, le système autorise les résolutions sans tenir compte des soumissions des joueurs, le système ne réalise pas l'attribution des roles au démarrage de la partie, pas de courriel de notification aux joueurs"),  # noqa: E241
            'used_for_elo':                   ("utilisée pour le calcul du élo",                 "oui ou non", "Si oui, Le résultat de la partie est pris en compte dans le calcul du élo des joueurs du site"),  # noqa: E241
            'anonymous':                      ("anonyme",                                        "oui ou non", "Si oui, Seul l'arbitre peut savoir qui joue et les joueurs ne savent pas qui a passé les ordres - effacé à la fin de la partie"),  # noqa: E241
            'nomessage_current':              ("blocage de la messagerie",                       "oui ou non", "Si oui le système empêche l'utilisation de la messagerie - cette valeur est modifiable pendant la partie et effacée en fin de partie"),  # noqa: E241
            'nopress_current':                ("blocage de la presse",                           "oui ou non", "Si oui le système empêche l'utilisation de la presse - cette valeur est modifiable pendant la partie et effacée en fin de partie"),  # noqa: E241
            'fast':                           ("en direct",                                      "oui ou non", "Si oui, La partie est jouée en temps réel comme sur un plateau, Les paramètres de calcul des dates limites sont en minutes et non en heures, pas de courriel de notification aux joueurs"),  # noqa: E241
            'manual':                         ("attribution manuelle des rôles",                 "oui ou non", "L'arbitre doit attribuer lui-même les roles, Le système ne réalise pas l'attribution des roles au démarrage de la partie"),  # noqa: E241
            'end_vote_allowed':               ("autorisation de votes de fin",                   "oui ou non", "Si oui, les joueurs peuvent voter l'arrêt prématuré de la partie"),  # noqa: E241
            'scoring':                        ("scorage",                                        "choix sur liste", "Le système de scorage appliqué - Se reporter à Accueil/Technique/Documents pour le détail des scorages implémentés. Note : Le calcul est réalisé dans l'interface"),  # noqa: E241
            'deadline_hour':                  ("heure de la date limite",                        "entier entre 0 et 23", "Heure à laquelle le système placera la date limite dans la journée si la synchronisation est souhaitée"),  # noqa: E241
            'deadline_sync':                  ("synchronisation de la date limite",              "oui ou non", "Si oui, Le système synchronise la date limite à une heure précise dans la journée"),  # noqa: E241
            'grace_duration':                 ("durée de la grâce",                              "entier en heures", "Passé un retard d'autant d'heure la date limite change de couleur, si les DC sont autorisés des ordres par défaut sont alors entrés..."),  # noqa: E241
            'speed_moves':                    ("vitesse pour les mouvements",                    "entier en heures", "Le système ajoute autant d'heures avant une résolution de mouvement pour une date limite"),  # noqa: E241
            'speed_retreats':                 ("vitesse pour les retraites",                     "entier en heures", "Le système ajoute autant d'heures avant une résolution de retraites pour une date limite"),  # noqa: E241
            'speed_adjustments':              ("vitesse pour les ajustements",                   "entier en heures", "Le système ajoute autant d'heures avant une résolution d'ajustements pour une date limite"),  # noqa: E241
            'cd_possible_moves':              ("désordre civil possible pour les mouvements",    "oui ou non", "Si oui, L'arbitre est en mesure d'imposer un désordre civil pour une phase de mouvements"),  # noqa: E241
            'cd_possible_retreats':           ("désordre civil possible pour les retraites",     "oui ou non", "Si oui, L'arbitre est en mesure d'imposer un désordre civil pour une phase de retraites"),  # noqa: E241
            'cd_possible_builds':             ("désordre civil possible pour les constructions", "oui ou non", "Si oui, L'arbitre est en mesure d'imposer un désordre civil pour une phase d'ajustements"),  # noqa: E241
            'play_weekend':                   ("jeu le week-end",                                "oui ou non", "Si oui, on joue le week-end et Le système pourra placer une date limite pendant le week-end"),  # noqa: E241
            'access_restriction_reliability': ("",          "entier", "Un minimum de fiabilité est exigé pour rejoindre la partie"),  # noqa: E241
            'access_restriction_regularity':  ("",          "entier", "Un minimum de régularité est exigé pour rejoindre la partie"),  # noqa: E241
            'access_restriction_performance': ("",          "entier", "Un minimum de performance est exigé pour rejoindre la partie"),  # noqa: E241
            'nb_max_cycles_to_play':          ("nombre maximum de cycles (années) à jouer",      "entier", "Durée de la partie : Le système déclare la partie terminée si autant de cycles ont été joués"),  # noqa: E241
            'game_type':                      ("type de la partie",                              "choix sur liste", "Type de la partie : Négo : pas de restriction, tout est possible ! Blitz : pas de communication, tout est fermé ! NégoPublique : presse (déclarations publiques) uniquement... BlitzOuverte : comme Blitz avec ouverture de la presse pour organiser la partie sans faire action de jeu."),  # noqa: E241
            'force_wait':                     ("forçage d'attente ou maintenant",                "maintenant, pas de forçage, à la date limite", "L'arbitre peut forcer la résolution à maintenant ou à la date limite (ou ne rien forcer)"),  # noqa: E241

        }[key]

        # some parameters are not used
        if not parameter_name:
            continue

        col = html.TD(html.B(parameter_name))
        row <= col

        col = html.TD(parameter_type)
        row <= col

        if key == 'game_type':
            parameter_value = game_type_conv[value]
        elif key == 'force_wait':
            parameter_value = force_wait_conv[value]
        elif value is False:
            parameter_value = "Non"
        elif value is True:
            parameter_value = "Oui"
        else:
            parameter_value = value

        col = html.TD(html.B(parameter_value), Class='important')
        row <= col

        col = html.TD(parameter_explanation)
        row <= col

        game_params_table <= row

    play_low.MY_SUB_PANEL <= game_params_table

    # incidents2
    play_low.MY_SUB_PANEL <= html.H4("Désordres civils")

    # get the actual incidents of the game
    game_incidents2 = play_low.game_incidents2_reload(play_low.GAME_ID)
    # there can be no incidents (if no incident of failed to load)

    game_incidents2_table = html.TABLE()

    fields = ['flag', 'role', 'season', 'date']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'rôle', 'season': 'saison', 'date': 'date'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_incidents2_table <= thead

    for role_id, advancement, time_stamp in sorted(game_incidents2, key=lambda i: i[2], reverse=True):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        col = html.TD(role_name)
        row <= col

        # season
        nb_max_cycles_to_play = play_low.GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
        game_season = common.get_full_season(advancement, play_low.VARIANT_DATA, nb_max_cycles_to_play, False)
        col = html.TD(game_season)
        row <= col

        # date
        datetime_incident = mydatetime.fromtimestamp(time_stamp)
        datetime_incident_str = mydatetime.strftime(*datetime_incident, year_first=True)
        col = html.TD(datetime_incident_str)
        row <= col

        game_incidents2_table <= row

    play_low.MY_SUB_PANEL <= game_incidents2_table

    if game_incidents2:
        play_low.MY_SUB_PANEL <= html.BR()
        play_low.MY_SUB_PANEL <= html.DIV("Un désordre civil signifie que l'arbitre (ou l'automate de résolution) a forcé des ordres pour le joueur", Class='note')

    # quitters
    play_low.MY_SUB_PANEL <= html.H4("Abandons")

    # get the actual dropouts of the game
    game_dropouts = common.game_dropouts_reload(play_low.GAME_ID)
    # there can be no dropouts (if no incident of failed to load)

    game_dropouts_table = html.TABLE()

    fields = ['flag', 'role', 'pseudo', 'date']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'rôle', 'pseudo': 'pseudo', 'date': 'date'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_dropouts_table <= thead

    for role_id, player_id, time_stamp in sorted(game_dropouts, key=lambda d: d[2], reverse=True):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        col = html.TD(role_name)
        row <= col

        # pseudo
        col = html.TD()

        if player_id in play_low.ID2PSEUDO:
            pseudo_quitter = play_low.ID2PSEUDO[player_id]
            player_id_current = None
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id_current = int(player_id_str)
            if player_id == player_id_current:
                col <= pseudo_quitter
            else:
                col <= html.I(html.SMALL(pseudo_quitter))

        row <= col

        # date
        datetime_incident = mydatetime.fromtimestamp(time_stamp)
        datetime_incident_str = mydatetime.strftime(*datetime_incident, year_first=True)
        col = html.TD(datetime_incident_str)
        row <= col

        game_dropouts_table <= row

    play_low.MY_SUB_PANEL <= game_dropouts_table
    play_low.MY_SUB_PANEL <= html.BR()

    # incidents
    play_low.MY_SUB_PANEL <= html.H4("Retards")

    # get the actual incidents of the game
    if play_low.ROLE_ID == 0:
        # game master  gets a better picture
        game_incidents = play_low.game_master_incidents_reload(play_low.GAME_ID)
    else:
        # others have None for player_id if anonymous
        game_incidents = play_low.game_incidents_reload(play_low.GAME_ID)
    # there can be no incidents (if no incident of failed to load)

    game_incidents_table = html.TABLE()

    fields = ['flag', 'role', 'pseudo', 'season', 'duration', 'date']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'rôle', 'pseudo': 'pseudo', 'season': 'saison', 'duration': 'durée', 'date': 'date'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_incidents_table <= thead

    for role_id, advancement, player_id, duration, time_stamp in sorted(game_incidents, key=lambda i: i[4], reverse=True):

        row = html.TR()

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        col = html.TD(role_name)
        row <= col

        # pseudo
        col = html.TD()
        if player_id in play_low.ID2PSEUDO:
            pseudo_quitter = play_low.ID2PSEUDO[player_id]
            player_id_current = None
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id_current = int(player_id_str)
            if player_id == player_id_current:
                col <= pseudo_quitter
            else:
                col <= html.I(html.SMALL(pseudo_quitter))
        row <= col

        # season
        nb_max_cycles_to_play = play_low.GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']
        game_season = common.get_full_season(advancement, play_low.VARIANT_DATA, nb_max_cycles_to_play, False)
        col = html.TD(game_season)
        row <= col

        # duration
        col = html.TD(f"{duration}")
        row <= col

        # date
        datetime_incident = mydatetime.fromtimestamp(time_stamp)
        datetime_incident_str = mydatetime.strftime(*datetime_incident, year_first=True)
        col = html.TD(datetime_incident_str)
        row <= col

        game_incidents_table <= row

    play_low.MY_SUB_PANEL <= game_incidents_table
    play_low.MY_SUB_PANEL <= html.BR()

    count = {}

    for role_id, advancement, player_id, duration, _ in game_incidents:
        if player_id not in play_low.ID2PSEUDO:
            continue
        pseudo_quitter = play_low.ID2PSEUDO[player_id]
        player_id_current = None
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id_current = int(player_id_str)
        if player_id != player_id_current:
            continue
        if role_id not in count:
            count[role_id] = []
        count[role_id].append(duration)

    recap_table = html.TABLE()

    # header
    thead = html.THEAD()
    for field in ['rang', 'role', 'pseudo', 'retards', 'nombre', 'cumul', 'ratio']:
        col = html.TD(field)
        thead <= col
    recap_table <= thead

    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

    rank = 1
    for role_id in sorted(count.keys(), key=lambda r: (len(count[r]), max(count[r])), reverse=True):
        row = html.TR()

        # rank
        col = html.TD(rank)
        row <= col

        # role flag
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]
        role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id, role_name)
        col = html.TD(role_icon_img)
        row <= col

        # pseudo
        col = html.TD()
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_quitter = play_low.ID2PSEUDO[player_id]
            col <= pseudo_quitter
        row <= col

        # incidents
        incidents_list = count.get(role_id, [])
        col = html.TD(" ".join([f"{i}" for i in incidents_list]))
        row <= col

        # incidents number
        incidents_number = len(count.get(role_id, []))
        col = html.TD(f"{incidents_number}")
        row <= col

        # incidents total
        incidents_total = sum(count.get(role_id, []))
        col = html.TD(f"{incidents_total}")
        row <= col

        # ratio
        nb_played = (play_low.GAME_PARAMETERS_LOADED['current_advancement'] / 5) * 3
        # avoid division by zero
        if nb_played == 0:
            nb_played = 1
        ratio = int((incidents_number / nb_played) * 100)
        col = html.TD(f"{ratio} %")
        row <= col

        recap_table <= row
        rank += 1

    play_low.MY_SUB_PANEL <= recap_table
    play_low.MY_SUB_PANEL <= html.BR()

    if game_incidents:

        play_low.MY_SUB_PANEL <= html.DIV("Un retard signifie que le joueur (ou l'arbitre) a réalisé la transition 'pas d'accord pour le résolution' -> 'd'accord pour résoudre' après la date limite", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

        play_low.MY_SUB_PANEL <= html.DIV("Les retards des joueurs qui depuis ont été remplacés n'apparaissent pas", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

        play_low.MY_SUB_PANEL <= html.DIV("Les retards sont en heures entamées", Class='note')
        play_low.MY_SUB_PANEL <= html.BR()

    return True


# the idea is not to lose the content of a message if not destinee were specified
CONTENT_BACKUP = None

SLICE_SIZE = 10


def negotiate(default_dest_set, def_focus_role_id):
    """ negotiate """

    focus_role_id = None

    def focus_callback(ev, role_id):  # pylint: disable=invalid-name
        """ focus_callback """
        nonlocal focus_role_id
        ev.preventDefault()
        if role_id == focus_role_id:
            focus_role_id = None
        else:
            focus_role_id = role_id
        play_low.MY_SUB_PANEL.clear()
        negotiate({}, focus_role_id)

    def answer_callback(ev, dest_set):  # pylint: disable=invalid-name
        """ answer_callback """
        ev.preventDefault()
        play_low.MY_SUB_PANEL.clear()
        negotiate(dest_set, focus_role_id)

    def add_message_callback(ev):  # pylint: disable=invalid-name
        """ add_message_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de message dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de message dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"Le message a été envoyé ! {messages}")

            # back to where we started
            global CONTENT_BACKUP
            CONTENT_BACKUP = None
            play_low.MY_SUB_PANEL.clear()
            negotiate({}, focus_role_id)

        ev.preventDefault()

        dest_role_ids = ' '.join([str(role_num) for (role_num, button) in selected.items() if button.checked])

        content = input_message.value

        # keep a backup
        global CONTENT_BACKUP
        CONTENT_BACKUP = content

        if not content:
            alert("Pas de contenu pour ce message !")
            play_low.MY_SUB_PANEL.clear()
            negotiate({}, focus_role_id)
            return

        if not dest_role_ids:
            alert("Pas de destinataire pour ce message !")
            play_low.MY_SUB_PANEL.clear()
            negotiate({}, focus_role_id)
            return

        role_id = play_low.ROLE_ID
        role = play_low.VARIANT_DATA.roles[role_id]
        role_name = play_low.VARIANT_DATA.role_name_table[role]

        json_dict = {
            'role_id': play_low.ROLE_ID,
            'dest_role_ids': dest_role_ids,
            'role_name': role_name,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{play_low.GAME_ID}"

        # adding a message in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def messages_reload(game_id):
        """ messages_reload """

        messages = []

        def reply_callback(req):
            nonlocal messages
            req_result = loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des messages dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des messages dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = req_result['messages_list']

        json_dict = {}

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{game_id}"

        # extracting messages from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return messages

    def select_dest_callback(col):

        # invert
        col_selected[col] = not col_selected[col]

        # display
        if col_selected[col]:
            col.style.background = config.DEST_SELECTED
        else:
            col.style.background = original_color

    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(play_low.GAME_ID, config.MESSAGES_TYPE)

    # copy
    focus_role_id = def_focus_role_id

    # put time stamp of last visit of declarations as now
    date_last_visit_update(play_low.GAME_ID, play_low.ROLE_ID, config.MESSAGES_TYPE)

    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre message", title="Qu'avez vous à lui/leur dire ?")
    fieldset <= legend_declaration
    input_message = html.TEXTAREA(type="text", rows=8, cols=80)
    if CONTENT_BACKUP is not None:
        input_message <= CONTENT_BACKUP
    fieldset <= input_message
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_destinees = html.LEGEND("Destinataire(s)", title="Et à qui ?")
    fieldset <= legend_destinees

    table = html.TABLE()
    col_selected = {}
    selected = {}
    original_color = None

    # we make sure game master goes first in sorting
    roles_left = sorted(range(play_low.VARIANT_CONTENT_LOADED['roles']['number'] + 1), key=lambda r: (int(r != 0), play_low.VARIANT_DATA.role_name_table[play_low.VARIANT_DATA.roles[r]]))

    position_data = play_low.POSITION_DATA
    colours = position_data.role_colours()

    while roles_left:

        roles_todo = roles_left[:SLICE_SIZE]
        roles_left = roles_left[SLICE_SIZE:]

        row = html.TR()

        for role_id_dest in roles_todo:

            # dest only if allowed
            if play_low.GAME_PARAMETERS_LOADED['nomessage_current']:
                if play_low.ROLE_ID != 0:
                    # not game master
                    if role_id_dest != 0:
                        # only to game master
                        continue

            role_dest = play_low.VARIANT_DATA.roles[role_id_dest]
            role_name = play_low.VARIANT_DATA.role_name_table[role_dest]
            role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id_dest, role_name)

            # to restrict
            action = "Filtrer" if role_id_dest != focus_role_id else "Pas Filtrer"
            button_focus = html.BUTTON(action, Class='btn-inside')
            button_focus.bind("click", lambda e, r=role_id_dest: focus_callback(e, r))

            # necessary to link flag with button
            label_dest = html.LABEL(role_icon_img, for_=str(role_id_dest))

            # little square : so convenient for unusual variants
            canvas2 = html.CANVAS(id="rect", width=15, height=15, alt=role_name)
            ctx2 = canvas2.getContext("2d")
            colour = colours[role_name]
            outline_colour = colour.outline_colour()
            ctx2.strokeStyle = outline_colour.str_value()
            ctx2.lineWidth = 2
            ctx2.beginPath()
            ctx2.rect(0, 0, 14, 14)
            ctx2.stroke()
            ctx2.closePath()  # no fill
            ctx2.fillStyle = colour.str_value()
            ctx2.fillRect(1, 1, 13, 13)

            # player
            pseudo_there = ""
            if role_id_dest == 0:
                if play_low.GAME_MASTER:
                    pseudo_there = play_low.GAME_MASTER
            elif role_id_dest in role2pseudo:
                player_id_str = role2pseudo[role_id_dest]
                player_id = int(player_id_str)
                pseudo_there = play_low.ID2PSEUDO[player_id]

            # the alternative
            input_dest = html.INPUT(type="checkbox", id=str(role_id_dest), checked=role_id_dest in default_dest_set, Class='btn-inside')

            # create col
            col = html.TD()

            # not selected by default
            col_selected[col] = False

            # if there is ony game master as dest we select it automatically
            if play_low.GAME_PARAMETERS_LOADED['nomessage_current']:
                if play_low.ROLE_ID != 0:
                    # not game master
                    if role_id_dest == 0:
                        # only to master
                        input_dest.checked = True
                        input_dest.disabled = True

            # width
            col.style = {
                'width': '70px'
            }

            if original_color is None:
                original_color = col.style.background

            # if forced or inherited
            if input_dest.checked:
                select_dest_callback(col)

            # will emphasize if selected (to see it better)
            input_dest.bind("click", lambda e, c=col: select_dest_callback(c))

            # now put stuff
            col <= html.CENTER(button_focus)
            col <= html.BR()
            col <= html.CENTER(label_dest)
            col <= html.CENTER(html.B(role_name))
            col <= html.CENTER(canvas2)
            if pseudo_there:
                col <= html.CENTER(pseudo_there)
            col <= html.CENTER(input_dest)

            row <= col

            selected[role_id_dest] = input_dest

        table <= row

    fieldset <= table
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Envoyer ce message", Class='btn-inside')
    input_declare_in_game.bind("click", add_message_callback)
    form <= input_declare_in_game

    # now we display messages

    messages = messages_reload(play_low.GAME_ID)
    # there can be no message (if no message of failed to load)

    # insert new field 'type'
    messages = [(common.MessageTypeEnum.TEXT, 0, i, f, t, d, c) for (i, f, t, d, c) in messages]

    # get the transition table
    game_transitions = common.game_transitions_reload(play_low.GAME_ID)

    # add fake messages (game transitions)
    fake_messages = [(common.MessageTypeEnum.SEASON, int(k), -1, -1, v, [], common.readable_season(int(k), play_low.VARIANT_DATA)) for k, v in game_transitions.items()]
    messages.extend(fake_messages)

    # get the replacements table
    game_replacements = common.game_replacements_reload(play_low.GAME_ID)

    # add fake messages (game replacements)
    fake_messages = [(common.MessageTypeEnum.REPLACEMENT, 0, -1, r, d, [], f"Le joueur ou arbitre avec le pseudo '{play_low.ID2PSEUDO.get(p, NON_DIVULGUE)}' et avec ce rôle {'a été mis dans' if e else 'a été retiré de'} la partie...") for r, p, d, e in game_replacements]
    messages.extend(fake_messages)

    # sort with all that was added
    messages.sort(key=lambda m: (float(m[4]), float(m[1])), reverse=True)

    messages_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Destinataire(s)', 'Contenu', 'Répondre']:
        col = html.TD(html.B(title))
        thead <= col
    messages_table <= thead

    for type_, _, id_, from_role_id_msg, time_stamp, dest_role_id_msgs, content in messages:

        class_ = ''

        if type_ is common.MessageTypeEnum.TEXT:
            # if focusing ignore other messages
            if focus_role_id is not None:
                if focus_role_id not in [from_role_id_msg] + dest_role_id_msgs:
                    continue
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

        col = html.TD(Class=class_)

        if from_role_id_msg != -1:

            role = play_low.VARIANT_DATA.roles[from_role_id_msg]
            role_name = play_low.VARIANT_DATA.role_name_table[role]
            role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, from_role_id_msg, role_name)
            col <= role_icon_img

            # player
            pseudo_there = ""
            if from_role_id_msg == 0:
                if play_low.GAME_MASTER:
                    pseudo_there = play_low.GAME_MASTER
            elif from_role_id_msg in role2pseudo:
                player_id_str = role2pseudo[from_role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = play_low.ID2PSEUDO[player_id]

            if pseudo_there:
                col <= html.BR()
                if focus_role_id is not None and from_role_id_msg == focus_role_id:
                    pseudo_there = html.B(pseudo_there)
                col <= pseudo_there

        row <= col

        col = html.TD(Class=class_)

        for dest_role_id_msg in dest_role_id_msgs:

            role = play_low.VARIANT_DATA.roles[dest_role_id_msg]
            role_name = play_low.VARIANT_DATA.role_name_table[role]
            role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, dest_role_id_msg, role_name)

            # player
            pseudo_there = ""
            if dest_role_id_msg == 0:
                if play_low.GAME_MASTER:
                    pseudo_there = play_low.GAME_MASTER
            elif dest_role_id_msg in role2pseudo:
                player_id_str = role2pseudo[dest_role_id_msg]
                player_id = int(player_id_str)
                pseudo_there = play_low.ID2PSEUDO[player_id]

            col <= role_icon_img
            if pseudo_there:
                col <= html.BR()
                if focus_role_id is not None and dest_role_id_msg == focus_role_id:
                    pseudo_there = html.B(pseudo_there)
                col <= pseudo_there

            # separator
            col <= html.BR()

        row <= col

        col = html.TD(Class=class_)

        for line in content.split('\n'):
            # new so put in bold
            if from_role_id_msg != play_low.ROLE_ID and time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        col = html.TD()
        if play_low.ROLE_ID in dest_role_id_msgs:
            button = html.BUTTON("Répondre", Class='btn-inside')
            new_dest_role_id_msgs = set(dest_role_id_msgs)
            new_dest_role_id_msgs.add(from_role_id_msg)
            new_dest_role_id_msgs.remove(play_low.ROLE_ID)
            button.bind("click", lambda e, d=new_dest_role_id_msgs: answer_callback(e, d))
            col <= button
        row <= col

        messages_table <= row

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # role flag
    play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    # see my orders
    play_low.stack_position_and_my_orders(play_low.MY_SUB_PANEL, play_low.MY_SUB_PANEL, messages_table)

    # see last moves
    play_low.stack_last_moves_button(play_low.MY_SUB_PANEL, play_low.MY_SUB_PANEL, messages_table, None, False)

    # form
    play_low.MY_SUB_PANEL <= form
    play_low.MY_SUB_PANEL <= html.BR()
    play_low.MY_SUB_PANEL <= html.BR()

    # messages already
    play_low.MY_SUB_PANEL <= messages_table
    play_low.MY_SUB_PANEL <= html.BR()
    play_low.MY_SUB_PANEL <= html.BR()

    button = html.BUTTON("Un message avec un contenu inaproprié ?", Class='btn-inside')
    button.bind("click", display_special_information_callback)
    play_low.MY_SUB_PANEL <= button
    play_low.MY_SUB_PANEL <= html.BR()
    play_low.MY_SUB_PANEL <= html.BR()

    information = html.DIV(Class='note')
    information <= "Le pseudo affiché est celui du joueur en cours, pas forcément celui de l'auteur réel du message"
    play_low.MY_SUB_PANEL <= information

    return True


def declare():
    """ declare """

    def add_declaration_callback(ev):  # pylint: disable=invalid-name
        """ add_declaration_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de presse dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de presse dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.info_go(f"La presse a été publiée ! {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            declare()

        ev.preventDefault()

        anonymous = input_anonymous.checked
        announce = False

        content = input_declaration.value

        if not content:
            alert("Pas de contenu pour cette presse !")
            play_low.MY_SUB_PANEL.clear()
            declare()
            return

        role_id = play_low.ROLE_ID
        if anonymous:
            role_name = ""
        else:
            role = play_low.VARIANT_DATA.roles[role_id]
            role_name = play_low.VARIANT_DATA.role_name_table[role]

        json_dict = {
            'role_id': role_id,
            'anonymous': anonymous,
            'announce': announce,
            'role_name': role_name,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{play_low.GAME_ID}"

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
                    alert(f"Erreur à la récupération des presses dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des presses dans la partie : {req_result['msg']}")
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

    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(play_low.GAME_ID, config.DECLARATIONS_TYPE)

    # put time stamp of last visit of declarations as now
    date_last_visit_update(play_low.GAME_ID, play_low.ROLE_ID, config.DECLARATIONS_TYPE)

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre presse", title="Qu'avez vous à déclarer à tout le monde ?")
    fieldset <= legend_declaration
    input_declaration = html.TEXTAREA(type="text", rows=8, cols=80)
    fieldset <= input_declaration
    form <= fieldset

    fieldset = html.FIELDSET()
    label_anonymous = html.LABEL("En restant anonyme ? (pas anonyme auprès de l'arbitre cependant)")
    fieldset <= label_anonymous
    input_anonymous = html.INPUT(type="checkbox", Class='btn-inside')
    fieldset <= input_anonymous
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="Publier cette presse", Class='btn-inside')
    input_declare_in_game.bind("click", add_declaration_callback)
    form <= input_declare_in_game

    # now we display declarations

    declarations = declarations_reload(play_low.GAME_ID)
    # there can be no message (if no declaration of failed to load)

    # insert new field 'type'
    declarations = [(common.MessageTypeEnum.TEXT, 0, i, ann, ano, r, t, c) for (i, ann, ano, r, t, c) in declarations]

    # get the transition table
    game_transitions = common.game_transitions_reload(play_low.GAME_ID)

    # add fake declarations (game transitions) and sort
    fake_declarations = [(common.MessageTypeEnum.SEASON, int(k), -1, False, False, -1, v, common.readable_season(int(k), play_low.VARIANT_DATA)) for k, v in game_transitions.items()]
    declarations.extend(fake_declarations)

    # get the replacements table
    game_replacements = common.game_replacements_reload(play_low.GAME_ID)

    # add fake messages (game replacements)
    fake_declarations = [(common.MessageTypeEnum.REPLACEMENT, 0, -1, False, False, r, d, f"Le joueur ou arbitre avec le pseudo '{play_low.ID2PSEUDO.get(p, NON_DIVULGUE)}' et avec ce rôle {'a été mis dans' if e else 'a été retiré de'} la partie...") for r, p, d, e in game_replacements]
    declarations.extend(fake_declarations)

    # sort with all that was added
    declarations.sort(key=lambda d: (float(d[6]), float(int(d[2] != -1)), float(d[1])), reverse=True)

    declarations_table = html.TABLE()

    thead = html.THEAD()
    for title in ['id', 'Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    declarations_table <= thead

    role2pseudo = {v: k for k, v in play_low.GAME_PLAYERS_DICT.items()}

    for type_, _, id_, announce, anonymous, role_id_msg, time_stamp, content in declarations:

        class_ = ''

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
        if announce:
            player_id = role_id_msg
            if player_id in play_low.ID2PSEUDO:
                pseudo_there = play_low.ID2PSEUDO[player_id]
        else:
            if role_id_msg != -1:

                role = play_low.VARIANT_DATA.roles[role_id_msg]
                role_name = play_low.VARIANT_DATA.role_name_table[role]
                role_icon_img = common.display_flag(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN, role_id_msg, role_name)

                # player
                if role_id_msg == 0:
                    if play_low.GAME_MASTER:
                        pseudo_there = play_low.GAME_MASTER
                elif role_id_msg in role2pseudo:
                    player_id_str = role2pseudo[role_id_msg]
                    player_id = int(player_id_str)
                    pseudo_there = play_low.ID2PSEUDO[player_id]

        col = html.TD(Class=class_)

        col <= role_icon_img
        if pseudo_there:
            col <= html.BR()
            col <= pseudo_there

        row <= col

        col = html.TD(Class=class_)

        for line in content.split('\n'):
            # new so put in bold
            if role_id_msg != play_low.ROLE_ID and time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        declarations_table <= row

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # role flag
    play_low.stack_role_flag(play_low.MY_SUB_PANEL)

    # see my orders
    play_low.stack_position_and_my_orders(play_low.MY_SUB_PANEL, play_low.MY_SUB_PANEL, declarations_table)

    # see last moves
    play_low.stack_last_moves_button(play_low.MY_SUB_PANEL, play_low.MY_SUB_PANEL, declarations_table, None, False)

    # form only if allowed
    if play_low.GAME_PARAMETERS_LOADED['nopress_current'] and play_low.ROLE_ID != 0:
        play_low.MY_SUB_PANEL <= html.P("Cette partie est sans presse des joueurs")
    else:
        # form
        play_low.MY_SUB_PANEL <= form
        play_low.MY_SUB_PANEL <= html.BR()
        play_low.MY_SUB_PANEL <= html.BR()

    # declarations already
    play_low.MY_SUB_PANEL <= declarations_table
    play_low.MY_SUB_PANEL <= html.BR()
    play_low.MY_SUB_PANEL <= html.BR()

    button = html.BUTTON("Une presse avec un contenu inaproprié ?", Class='btn-inside')
    button.bind("click", display_special_information_callback)
    play_low.MY_SUB_PANEL <= button
    play_low.MY_SUB_PANEL <= html.BR()
    play_low.MY_SUB_PANEL <= html.BR()

    information = html.DIV(Class='note')
    information <= "Le pseudo affiché est celui du joueur en cours, pas forcément celui de l'auteur réel du message"
    play_low.MY_SUB_PANEL <= information

    return True
