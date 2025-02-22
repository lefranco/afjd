""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from json import loads, dumps
from time import time

from browser import html, ajax, alert, document   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import mydialog
import common
import geometry
import mapping

import play  # circular import
import play_low


class AutomatonStateEnum:
    """ AutomatonStateEnum """

    SELECT_ACTIVE_STATE = 1
    SELECT_ORDER_STATE = 2
    SELECT_PASSIVE_UNIT_STATE = 3
    SELECT_DESTINATION_STATE = 4
    SELECT_BUILD_UNIT_TYPE_STATE = 5


class AutomatonStateEnum2:
    """ AutomatonStateEnum2 """

    SELECT_ACTION_STATE = 1
    SELECT_POSITION_STATE = 2
    SELECT_UNIT_STATE = 3


# canvas backup to optimize drawing map when only orders change
BACKUP_CANVAS = None


def save_context(ctx):
    """ save_context """

    global BACKUP_CANVAS

    # create backup canvas
    BACKUP_CANVAS = html.CANVAS(width=ctx.canvas.width, height=ctx.canvas.height)
    bctx = BACKUP_CANVAS.getContext("2d")

    # copy canvas into it
    bctx.drawImage(ctx.canvas, 0, 0)


def restore_context(ctx):
    """ restore_context """

    ctx.drawImage(BACKUP_CANVAS, 0, 0)


def submit_orders():
    """ submit_orders """

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    selected_build_unit_type = None
    selected_build_zone = None
    selected_hovered_object = None
    automaton_state = None
    buttons_right = None
    orders_status = None

    input_now = None
    input_after = None
    input_never = None

    orders_in = None
    definitive_value = None

    vote_value = None

    def add_note_callback(ev):  # pylint: disable=invalid-name
        """ add_note_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de la note dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de la note dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"La note a été enregistrée ! {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            submit_orders()

        ev.preventDefault()

        content = input_note.value

        json_dict = {
            'role_id': play_low.ROLE_ID,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-notes/{play_low.GAME_ID}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        submit_orders()

    def submit_vote_callback(ev):  # pylint: disable=invalid-name
        """ submit_vote_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de vote d'arrêt dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de vote d'arrêt dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Le vote a été enregistré ! {messages}")

            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            submit_orders()

        ev.preventDefault()

        json_dict = {
            'role_id': play_low.ROLE_ID,
            'value': vote_value
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-votes/{play_low.GAME_ID}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        # back to where we started
        play_low.MY_SUB_PANEL.clear()
        submit_orders()

    def update_select(event):
        """ update_select """

        nonlocal vote_value

        if event.target is input_stop:
            vote_value = False
        if event.target is input_continue:
            vote_value = True
        if event.target is input_abstention:
            vote_value = None

    def stack_orders_status(frame):
        """ stack_orders_status """

        nonlocal orders_status

        orders_status = html.DIV(id='orders_status')

        if orders_in is False:
            flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
        elif definitive_value == 1:
            flag = html.IMG(src="./images/agreed.jpg", title="D'accord pour résoudre maintenant")
        elif definitive_value == 2:
            flag = html.IMG(src="./images/agreed_after.jpg", title="D'accord pour résoudre mais à la date limite")
        elif definitive_value == 0:
            flag = html.IMG(src="./images/not_agreed.jpg", title="Pas d'accord pour résoudre")

        orders_status <= flag
        frame <= orders_status

    def cancel_submit_orders_callback(_, dialog):
        dialog.close(None)
        play_low.MY_SUB_PANEL.clear()
        submit_orders()

    def submit_orders_callback(_, warned=False, dialog2=None):
        """ submit_orders_callback """

        nonlocal definitive_value

        def reply_callback(req):

            nonlocal orders_in

            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres : {req_result['message']}")
                elif 'msg' in req_result:
                    # special : we add a little hint
                    report = req_result['msg']
                    if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:
                        report += "\nSi cette erreur est intentionnelle, pensez à utiliser les ordres de com' !"
                    alert(f"Problème à la soumission d'ordres : {report}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            # use a strip to remove trailing "\n"
            messages = "<br>".join(req_result['msg'].strip().split('\n'))

            # to better undestand what is going on, on can use code below :
            #  debug_message = req_result['debug_message'].split('\n')
            #  mydialog.InfoDialog("Information", f"debug_message : {debug_message}", True)

            if messages:
                mydialog.InfoDialog("Information", f"Ordres validés avec le(s) message(s) : {messages}", True)
            else:
                mydialog.InfoDialog("Information", "Ordres validés !")

            # special : send ip address to server
            common.send_ip_address()

            orders_in = True
            buttons_right.removeChild(orders_status)
            stack_orders_status(buttons_right)

            # late
            late = req_result['late']
            if late:
                alert("Vous avez soumis vos ordres en retard !")

            # not really submitted
            unsafe = req_result['unsafe']
            if unsafe:
                alert("Vous n'avez pas mis l'accord, donc vos ordres sont juste enregistrés (pour vous-même) mais vous risquez encore un retard...")

            before_deadline = time() < play_low.GAME_PARAMETERS_LOADED['deadline']

            # forced to wait
            if before_deadline:
                if definitive_value == 1 and play_low.GAME_PARAMETERS_LOADED['force_wait'] == 1:
                    alert("Attention : l'arbitre a forcé l'attente de la date limite et nous sommes avant la date limite, votre accord a très probablement été commuté de 'maintenant' à 'à la date limite' ! Il se peut que l'interface ne montre pas le réel statut de vos ordres. Cliquez sur 'ordonner' si besoin.")
                if definitive_value == 2 and play_low.GAME_PARAMETERS_LOADED['force_wait'] == -1:
                    alert("Attention : l'arbitre a forcé la résoluition à maintenant et nous sommes avant la date limite, votre accord a très probablement été commuté de 'à la date limite' à 'maintenant' ! Il se peut que l'interface ne montre pas le réel statut de vos ordres. Cliquez sur 'ordonner' si besoin.")
            else:
                if definitive_value == 2:
                    alert("Attention : après la date limite, le système commute un accord 'à la date limite' en 'maintenant' ! Il se peut que l'interface ne montre pas le réel statut de vos ordres. Cliquez sur 'ordonner' si besoin.")

            # why no adjudication
            #  missing = req_result['missing']
            # we certainly *could* use it if server filled it in...
            # but we do nothing because :
            # if gunboat : gives information about other players
            # if negociation : gives information about possible stab
            # so server does not fill it

            # adjudication was done
            adjudicated = req_result['adjudicated']
            if adjudicated:

                # seems to be things not updated if back to orders
                alert("La position de la partie a changé !")
                play_low.load_dynamic_stuff()

                play_low.MY_SUB_PANEL.clear()
                play.load_option(None, 'Consulter')

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            role = play_low.VARIANT_DATA.roles[play_low.ROLE_ID]
            nb_builds, _, _, _ = play_low.POSITION_DATA.role_builds(role)
            if nb_builds > 0:
                nb_builds_done = orders_data.number()
                if nb_builds_done < nb_builds:
                    if not warned:
                        dialog = mydialog.Dialog(f"Vous construisez {nb_builds_done} unités alors que vous avez droit à {nb_builds} unités. Vous êtes sûr ?", ok_cancel=True)
                        dialog.ok_button.bind("click", lambda e, w=True, d=dialog: submit_orders_callback(e, w, d))
                        dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_submit_orders_callback(e, d))
                        return

        if dialog2:
            dialog2.close()

        names_dict = play_low.VARIANT_DATA.extract_names()
        names_dict_json = dumps(names_dict)

        inforced_names_dict = play_low.INFORCED_VARIANT_DATA.extract_names()
        inforced_names_dict_json = dumps(inforced_names_dict)

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = dumps(orders_list_dict)

        if input_never.checked:
            definitive_value = 0
        if input_now.checked:
            definitive_value = 1
        if input_after.checked:
            definitive_value = 2

        json_dict = {
            'role_id': play_low.ROLE_ID,
            'orders': orders_list_dict_json,
            'definitive': definitive_value,
            'names': names_dict_json,
            'adjudication_names': inforced_names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-orders/{play_low.GAME_ID}"

        # submitting orders : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # to stop catching keyboard
        document.unbind("keypress")

        # complete orders
        orders_data.rest_hold(play_low.ROLE_ID)

        # update displayed map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag
        play_low.stack_role_flag(buttons_right)

        # button erase for archive games
        if play_low.GAME_PARAMETERS_LOADED['archive']:
            play_low.stack_cancel_last_adjudication_button(buttons_right)

        # button for communication orders
        if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
            play_low.stack_communications_orders_button(buttons_right)

        # button last moves
        play_low.stack_last_moves_button(buttons_right)

        # information retreats/builds
        play_low.stack_possibilities(buttons_right, advancement_season)

        # we are in spring or autumn
        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit

        my_sub_panel2 <= buttons_right
        play_low.MY_SUB_PANEL <= my_sub_panel2
        play_low.MY_SUB_PANEL <= my_sub_panel3

        stack_orders(buttons_right)

        if not orders_data.empty():
            put_erase_all(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        # orders status
        stack_orders_status(buttons_right)

        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        orders_data.erase_orders()

        # update displayed map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag
        play_low.stack_role_flag(buttons_right)

        # button erase for archive games
        if play_low.GAME_PARAMETERS_LOADED['archive']:
            play_low.stack_cancel_last_adjudication_button(buttons_right)

        # button for communication orders
        if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
            play_low.stack_communications_orders_button(buttons_right)

        # button last moves
        play_low.stack_last_moves_button(buttons_right)

        # information retreats/builds
        play_low.stack_possibilities(buttons_right, advancement_season)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum.inventory():
                if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                    input_select = html.INPUT(type="submit", value=play_low.VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)

        # do not put erase all
        if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        # orders status
        stack_orders_status(buttons_right)

        my_sub_panel2 <= buttons_right
        play_low.MY_SUB_PANEL <= my_sub_panel2
        play_low.MY_SUB_PANEL <= my_sub_panel3

    def select_built_unit_type_callback(_, build_unit_type):
        """ select_built_unit_type_callback """

        nonlocal selected_build_unit_type
        nonlocal automaton_state
        nonlocal buttons_right

        if automaton_state is AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE:

            selected_build_unit_type = build_unit_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # button erase for archive games
            if play_low.GAME_PARAMETERS_LOADED['archive']:
                play_low.stack_cancel_last_adjudication_button(buttons_right)

            # button for communication orders
            if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
                play_low.stack_communications_orders_button(buttons_right)

            # button last moves
            play_low.stack_last_moves_button(buttons_right)

            # information retreats/builds
            play_low.stack_possibilities(buttons_right, advancement_season)

            legend_select_active = html.DIV("Sélectionner la zone où construire", Class='instruction')
            buttons_right <= legend_select_active

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            # orders status
            stack_orders_status(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2
            play_low.MY_SUB_PANEL <= my_sub_panel3

            # it is a zone we need now
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        # to stop catching keyboard
        document.unbind("keypress")

        if automaton_state is AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER and nb_builds < 0:
                alert("Bien essayé, mais vous devez détruire !")
                return

            if selected_order_type is mapping.OrderTypeEnum.REMOVE_ORDER and nb_builds > 0:
                alert("Bien essayé, mais vous devez construire !")
                return

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # button erase for archive games
            if play_low.GAME_PARAMETERS_LOADED['archive']:
                play_low.stack_cancel_last_adjudication_button(buttons_right)

            # button for communication orders
            if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
                play_low.stack_communications_orders_button(buttons_right)

            # button last moves
            play_low.stack_last_moves_button(buttons_right)

            # information retreats/builds
            play_low.stack_possibilities(buttons_right, advancement_season)

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de l'attaque", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée offensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée defensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(play_low.POSITION_DATA, order_type, selected_active_unit, None, None, False)
                orders_data.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                play_low.MY_SUB_PANEL <= my_sub_panel2
                play_low.MY_SUB_PANEL <= my_sub_panel3

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.DIV("Sélectionner l'unité convoyée", Class='instruction')
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de la retraite", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.DISBAND_ORDER:

                # insert disband order
                order = mapping.Order(play_low.POSITION_DATA, order_type, selected_active_unit, None, None, False)
                orders_data.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                play_low.MY_SUB_PANEL <= my_sub_panel2
                play_low.MY_SUB_PANEL <= my_sub_panel3

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:

                legend_select_active = html.DIV("Sélectionner le type d'unité à construire", Class='instruction')
                buttons_right <= legend_select_active

                for unit_type in mapping.UnitTypeEnum.inventory():
                    input_select = html.INPUT(type="submit", value=play_low.VARIANT_DATA.unit_name_table[unit_type], Class='btn-inside')
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, u=unit_type: select_built_unit_type_callback(e, u))
                    buttons_right <= html.BR()
                    buttons_right <= input_select

                automaton_state = AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE

            if selected_order_type is mapping.OrderTypeEnum.REMOVE_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_active = html.DIV("Sélectionner l'unité à retirer", Class='instruction')
                buttons_right <= legend_select_active

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            # orders status
            stack_orders_status(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2
        play_low.MY_SUB_PANEL <= my_sub_panel3

    def callback_canvas_click(event):
        """ called when there is a click down then a click up separated by less than 'LONG_DURATION_LIMIT_SEC' sec """

        nonlocal selected_order_type
        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal selected_passive_unit
        nonlocal selected_dest_zone
        nonlocal selected_build_zone
        nonlocal buttons_right

        if event.detail != 1:
            # Otherwise confusion click/double-click
            return

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # this is a shortcut
        if automaton_state is AutomatonStateEnum.SELECT_ORDER_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                selected_order_type = mapping.OrderTypeEnum.ATTACK_ORDER
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_order_type = mapping.OrderTypeEnum.RETREAT_ORDER
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            # passthru

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_active_unit = play_low.POSITION_DATA.closest_unit(pos, False)
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_active_unit = play_low.POSITION_DATA.closest_unit(pos, True)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # button erase for archive games
            if play_low.GAME_PARAMETERS_LOADED['archive']:
                play_low.stack_cancel_last_adjudication_button(buttons_right)

            # button for communication orders
            if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
                play_low.stack_communications_orders_button(buttons_right)

            # button last moves
            play_low.stack_last_moves_button(buttons_right)

            # information retreats/builds
            play_low.stack_possibilities(buttons_right, advancement_season)

            # gm can pass orders on archive games
            if selected_active_unit is None or (play_low.ROLE_ID != 0 and selected_active_unit.role != play_low.VARIANT_DATA.roles[play_low.ROLE_ID]):

                alert("Bien essayé, mais pas d'unité ici ou cette unité ne vous appartient pas ou vous n'avez pas d'ordre à valider.")

                selected_active_unit = None

                # switch back to initial state selecting unit
                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                    legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                    buttons_right <= legend_select_unit

                    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    legend_select_unit = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
                    buttons_right <= legend_select_unit
                    for order_type in mapping.OrderTypeEnum.inventory():
                        if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                            input_select = html.INPUT(type="submit", value=play_low.VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                            buttons_right <= html.BR()
                            input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                            buttons_right <= html.BR()
                            buttons_right <= input_select

                    automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            else:

                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:

                    legend_selected_unit = html.DIV(f"L'unité active sélectionnée est {selected_active_unit}")
                    buttons_right <= legend_selected_unit

                    legend_select_order = html.DIV("Sélectionner l'ordre (ou directement la destination - sous la légende)", Class='instruction')
                    buttons_right <= legend_select_order
                    buttons_right <= html.BR()

                    legend_select_order21 = html.I("Raccourcis clavier :")
                    buttons_right <= legend_select_order21
                    buttons_right <= html.BR()

                    for info in ["(a)ttaquer", "soutenir (o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer"]:
                        legend_select_order22 = html.I(info)
                        buttons_right <= legend_select_order22
                        buttons_right <= html.BR()

                # to catch keyboard
                document.bind("keypress", callback_keypress)

                for order_type in mapping.OrderTypeEnum.inventory():
                    if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                        input_select = html.INPUT(type="submit", value=play_low.VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    order = mapping.Order(play_low.POSITION_DATA, selected_order_type, selected_active_unit, None, None, False)
                    orders_data.insert_order(order)

                    # update map
                    callback_render(False)

                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            # orders status
            stack_orders_status(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2
            play_low.MY_SUB_PANEL <= my_sub_panel3

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                if selected_order_type in [mapping.OrderTypeEnum.ATTACK_ORDER, mapping.OrderTypeEnum.RETREAT_ORDER]:
                    unit_reference_type = mapping.UnitTypeEnum.ARMY_UNIT if isinstance(selected_active_unit, mapping.Army) else mapping.UnitTypeEnum.FLEET_UNIT
                elif selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                    unit_reference_type = mapping.UnitTypeEnum.ARMY_UNIT if isinstance(selected_passive_unit, mapping.Army) else mapping.UnitTypeEnum.FLEET_UNIT
                selected_dest_zone = play_low.VARIANT_DATA.closest_zone(pos, unit_reference_type)

            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                selected_build_zone = play_low.VARIANT_DATA.closest_zone(pos, selected_build_unit_type)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # button erase for archive games
            if play_low.GAME_PARAMETERS_LOADED['archive']:
                play_low.stack_cancel_last_adjudication_button(buttons_right)

            # button for communication orders
            if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
                play_low.stack_communications_orders_button(buttons_right)

            # button last moves
            play_low.stack_last_moves_button(buttons_right)

            # information retreats/builds
            play_low.stack_possibilities(buttons_right, advancement_season)

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone.region == selected_active_unit.zone.region:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(play_low.POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone, False)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(play_low.POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone, False)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone.region == selected_active_unit.zone.region:
                    selected_order_type = mapping.OrderTypeEnum.DISBAND_ORDER
                    selected_dest_zone = None
                order = mapping.Order(play_low.POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone, False)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:
                # create fake unit
                region = selected_build_zone.region
                center = region.center
                if center is None:
                    alert("Bien essayé, mais il n'y a pas de centre à cet endroit !")
                elif region in play_low.POSITION_DATA.occupant_table:
                    alert("Bien essayé, mais il y a déjà une unité à cet endroit !")
                elif center not in play_low.POSITION_DATA.owner_table:
                    alert("Bien essayé, mais ce centre n'appartient à personne !")
                else:
                    # becomes tricky
                    accepted = True
                    deducted_role = play_low.POSITION_DATA.owner_table[center].role
                    if play_low.ROLE_ID == 0:  # game master
                        if not play_low.VARIANT_CONTENT_LOADED['build_everywhere']:
                            expected_role = center.owner_start
                            if not expected_role:
                                alert("Bien essayé mais ce n'est pas un centre de départ !")
                                accepted = False
                            elif expected_role is not deducted_role:
                                alert("Bien essayé mais ce n'est pas une variante dans laquelle on peut construire partout !")
                                accepted = False
                    else:  # player
                        if play_low.ROLE_ID is not deducted_role.identifier:
                            alert("Bien essayé, mais ce centre ne vous appartient pas ")
                            accepted = False
                        elif not play_low.VARIANT_CONTENT_LOADED['build_everywhere']:
                            expected_role = center.owner_start
                            if not expected_role:
                                alert("Bien essayé mais ce n'est pas un centre de départ !")
                                accepted = False
                            elif expected_role is not deducted_role:
                                alert("Bien essayé mais ce n'est pas une variante dans laquelle on peut construire partout !")
                                accepted = False
                    if accepted:  # actual build
                        if selected_build_unit_type is mapping.UnitTypeEnum.ARMY_UNIT:
                            fake_unit = mapping.Army(play_low.POSITION_DATA, deducted_role, selected_build_zone, None, False)
                        if selected_build_unit_type is mapping.UnitTypeEnum.FLEET_UNIT:
                            fake_unit = mapping.Fleet(play_low.POSITION_DATA, deducted_role, selected_build_zone, None, False)
                        # create order
                        order = mapping.Order(play_low.POSITION_DATA, selected_order_type, fake_unit, None, None, False)
                        orders_data.insert_order(order)

            # update map
            callback_render(False)

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                legend_select_unit = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit
                for order_type in mapping.OrderTypeEnum.inventory():
                    if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                        input_select = html.INPUT(type="submit", value=play_low.VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            # orders status
            stack_orders_status(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2
            play_low.MY_SUB_PANEL <= my_sub_panel3

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = play_low.POSITION_DATA.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # button erase for archive games
            if play_low.GAME_PARAMETERS_LOADED['archive']:
                play_low.stack_cancel_last_adjudication_button(buttons_right)

            # button for communication orders
            if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
                play_low.stack_communications_orders_button(buttons_right)

            # button last moves
            play_low.stack_last_moves_button(buttons_right)

            # information retreats/builds
            play_low.stack_possibilities(buttons_right, advancement_season)

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(play_low.POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, None, False)
                orders_data.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                play_low.MY_SUB_PANEL <= my_sub_panel2
                play_low.MY_SUB_PANEL <= my_sub_panel3

                stack_orders(buttons_right)
                if not orders_data.empty():
                    put_erase_all(buttons_right)
                if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                    put_rest_hold(buttons_right)
                if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    buttons_right <= html.BR()
                    put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

                # orders status
                stack_orders_status(buttons_right)

                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination de l'attaque soutenue", Class='instruction')
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination du convoi", Class='instruction')
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
                put_submit(buttons_right)

            # orders status
            stack_orders_status(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2
            play_low.MY_SUB_PANEL <= my_sub_panel3

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_canvas_dblclick(event):
        """
        called when there is a double click
        """

        nonlocal automaton_state
        nonlocal buttons_right

        if event.detail != 2:
            # Otherwise confusion click/double-click
            return

        # the aim is to give this variable a value
        selected_erase_unit = None

        # where is the click
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # moves : select unit : easy case
        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
            selected_erase_unit = play_low.POSITION_DATA.closest_unit(pos, False)

        # retreat : select dislodged unit : easy case
        if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            selected_erase_unit = play_low.POSITION_DATA.closest_unit(pos, True)

        #  builds : tougher case : we take the build units into account
        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            selected_erase_unit = orders_data.closest_unit_or_built_unit(pos)

        # event is None when coming from x pressed, then take 'selected_active_unit' (that can be None)
        if selected_erase_unit is None:
            selected_erase_unit = selected_active_unit

        # unit must be selected
        if selected_erase_unit is None:
            return

        # unit must have an order
        if not orders_data.is_ordered(selected_erase_unit):
            return

        # remove order
        orders_data.remove_order(selected_erase_unit)

        # update map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag
        play_low.stack_role_flag(buttons_right)

        # button erase for archive games
        if play_low.GAME_PARAMETERS_LOADED['archive']:
            play_low.stack_cancel_last_adjudication_button(buttons_right)

        # button for communication orders
        if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
            play_low.stack_communications_orders_button(buttons_right)

        # button last moves
        play_low.stack_last_moves_button(buttons_right)

        # information retreats/builds
        play_low.stack_possibilities(buttons_right, advancement_season)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum.inventory():
                if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                    input_select = html.INPUT(type="submit", value=play_low.VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)
        if not orders_data.empty():
            put_erase_all(buttons_right)
        if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        # orders status
        stack_orders_status(buttons_right)

        my_sub_panel2 <= buttons_right
        play_low.MY_SUB_PANEL <= my_sub_panel2
        play_low.MY_SUB_PANEL <= my_sub_panel3

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = play_low.POSITION_DATA.closest_object(pos)

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

            # redraw all arrows
            if prev_selected_hovered_object is not None or selected_hovered_object is not None:
                orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(prev_selected_hovered_object, mapping.Unit):
                if prev_selected_hovered_object in play_low.POSITION_DATA.dislodging_table:
                    dislodged = play_low.POSITION_DATA.dislodging_table[prev_selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

    def callback_canvas_mouse_enter(event):
        """ callback_canvas_mouse_enter """

        nonlocal selected_hovered_object

        helper.clear()

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = play_low.POSITION_DATA.closest_object(pos)

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

            # redraw all arrows
            orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(selected_hovered_object, mapping.Unit):
                if selected_hovered_object in play_low.POSITION_DATA.dislodging_table:
                    dislodged = play_low.POSITION_DATA.dislodging_table[selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

        helper.clear()
        helper <= "_"

    def callback_keypress(event):
        """ callback_keypress """

        char = chr(event.charCode).lower()

        # order shortcut
        selected_order = mapping.OrderTypeEnum.shortcut(char)
        if selected_order is None:
            return

        select_order_type_callback(event, selected_order)

    def callback_render(refresh):
        """ callback_render """

        if refresh:

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the position and the neutral centers
            play_low.POSITION_DATA.render(ctx)

            # put the legends
            play_low.VARIANT_DATA.render(ctx)

            # save
            save_context(ctx)

        else:

            # restore
            restore_context(ctx)

        # put the orders
        orders_data.render(ctx)

    def stack_orders(buttons_right):
        """ stack_orders """

        buttons_right <= html.P()
        lines = str(orders_data).split('\n')
        orders = html.DIV()
        for line in lines:
            orders <= html.B(line)
            orders <= html.BR()
        buttons_right <= orders

        # capture the units without an order
        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:

            # list units without orders
            unordered_units = [u for u in play_low.POSITION_DATA.units if u.role.identifier == play_low.ROLE_ID and not orders_data.is_ordered(u)]

            # if there are display them
            if unordered_units:
                buttons_right <= html.BR()
                lines = map(str, unordered_units)
                no_orders = html.DIV()
                for line in lines:
                    no_orders <= html.EM(line)
                    no_orders <= html.BR()
                buttons_right <= no_orders

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="Effacer tout", Class='btn-inside')
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_rest_hold(buttons_right):
        """ put_rest_hold """

        input_rest_hold = html.INPUT(type="submit", value="Tout le reste tient", Class='btn-inside')
        input_rest_hold.bind("click", rest_hold_callback)
        buttons_right <= html.BR()
        buttons_right <= input_rest_hold
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        nonlocal input_now
        nonlocal input_after
        nonlocal input_never

        def update_select(event):
            """ update_select """

            nonlocal definitive_value

            if event.target is input_now:
                definitive_value = 1
            if event.target is input_after:
                definitive_value = 2
            if event.target is input_never:
                definitive_value = 0

        label_definitive = html.LABEL(html.B("D'accord pour la résolution ?"))
        buttons_right <= label_definitive
        buttons_right <= html.BR()

        # ---
        option_now_text = "maintenant"
        option_now_em = html.EM(option_now_text)
        if play_low.GAME_PARAMETERS_LOADED['force_wait'] == 1:
            option_now = html.LABEL(option_now_em, disabled="disabled")
        else:
            option_now = html.LABEL(option_now_em)
        label_now = html.LABEL(option_now)
        buttons_right <= label_now

        if play_low.GAME_PARAMETERS_LOADED['force_wait'] == 1:
            input_now = html.INPUT(type="radio", id="now", name="agreed", checked=(definitive_value == 1), disabled=True, Class='btn-inside')
        else:
            input_now = html.INPUT(type="radio", id="now", name="agreed", checked=(definitive_value == 1), Class='btn-inside')

        input_now.bind("click", update_select)
        buttons_right <= input_now
        buttons_right <= html.BR()

        # ---
        option_after_text = "à la date limite (*)"
        option_after_em = html.EM(option_after_text)
        if play_low.GAME_PARAMETERS_LOADED['fast'] or play_low.GAME_PARAMETERS_LOADED['archive'] or play_low.GAME_PARAMETERS_LOADED['force_wait'] == -1:
            label_after = html.LABEL(option_after_em, disabled="disabled")
        else:
            label_after = html.LABEL(option_after_em)
        buttons_right <= label_after

        if play_low.GAME_PARAMETERS_LOADED['fast'] or play_low.GAME_PARAMETERS_LOADED['archive'] or play_low.GAME_PARAMETERS_LOADED['force_wait'] == -1:
            input_after = html.INPUT(type="radio", id="after", name="agreed", checked=(definitive_value == 2), disabled=True, Class='btn-inside')
        else:
            input_after = html.INPUT(type="radio", id="after", name="agreed", checked=(definitive_value == 2), Class='btn-inside')

        input_after.bind("click", update_select)
        buttons_right <= input_after
        buttons_right <= html.BR()

        # ---
        option_never_text = "non"
        # warning for this button if after deadline
        deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']
        time_stamp_now = time()
        if time_stamp_now > deadline_loaded:
            option_never_text += " (ATTENTION : retard !)"

        option_never_em = html.EM(option_never_text)
        option_never = html.EM(option_never_em)
        label_never = html.LABEL(option_never)
        buttons_right <= label_never
        input_never = html.INPUT(type="radio", id="never", name="agreed", checked=(definitive_value == 0), Class='btn-inside')

        input_never.bind("click", update_select)
        buttons_right <= input_never
        buttons_right <= html.BR()

        input_submit = html.INPUT(type="submit", value="Soumettre", Class='btn-inside')
        input_submit.bind("click", submit_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()
        buttons_right <= html.I("(*) Utilisez s'il vous plaît ce choix 'à bon escient', puisqu'il retarde la résolution !", Class='Note')
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        buttons_right <= html.DIV("Pour exporter la position vers le bac à sable, passer par le sous-menu 'consulter'", Class='instruction')
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    # need to be connected
    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        play.load_option(None, 'Consulter')
        return False

    # need to have a role
    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # cannot be archive game unless  game master
    if play_low.GAME_PARAMETERS_LOADED['archive'] and play_low.ROLE_ID != 0:
        alert("Ordonner pour une parties archive est réservé à l'arbitre")
        play.load_option(None, 'Consulter')
        return False

    # cannot be game master unless archive game
    if play_low.ROLE_ID == 0 and not play_low.GAME_PARAMETERS_LOADED['archive']:
        alert("Ordonner pour un arbitre n'est possible que pour les parties archive")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not waiting
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not finished
    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà archivée ou distinguée")
        play.load_option(None, 'Consulter')
        return False

    submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
    if not submitted_data:
        alert("Erreur chargement données de soumission")
        play.load_option(None, 'Consulter')
        return False

    if play_low.ROLE_ID == 0:
        if not submitted_data['needed']:
            alert("Il n'y a pas d'ordre à passer")
            play.load_option(None, 'Consulter')
            return False
    else:
        if play_low.ROLE_ID not in submitted_data['needed']:
            alert("Vous n'avez pas d'ordre à passer.")
            # may still vote or edit notes

    game_over = False

    # check game soloed
    if play_low.GAME_PARAMETERS_LOADED['soloed']:
        alert("La partie est terminée parce qu'un solo a été réalisé !")
        # may still edit notes

    # check game end voted
    if play_low.GAME_PARAMETERS_LOADED['end_voted']:
        alert("La partie est terminée sur un vote de fin unanime !")
        # may still edit notes

    # check game finished (if not soloed nor end voted)
    if play_low.GAME_PARAMETERS_LOADED['finished']:
        alert("La partie est terminée parce qu'arrivée à échéance")
        # may still edit notes

    # load notes
    content_loaded = common.game_note_reload(play_low.GAME_ID)
    if content_loaded is None:
        alert("Erreur chargement note")
        play.load_option(None, 'Consulter')
        return False

    # load vote
    votes = play_low.game_votes_reload(play_low.GAME_ID)
    if votes is None:
        alert("Erreur chargement votes")
        play.load_option(None, 'Consulter')
        return False
    votes = list(votes)

    vote_value = None
    for _, role, vote_val in votes:
        if role == play_low.ROLE_ID:
            vote_value = bool(vote_val)
            break

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    advancement_loaded = play_low.GAME_PARAMETERS_LOADED['current_advancement']
    advancement_season, _ = common.get_short_season(advancement_loaded, play_low.VARIANT_DATA)

    # create canvas
    map_size = play_low.VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return False

    # click and double click
    canvas.bind("click", callback_canvas_click)
    canvas.bind("dblclick", callback_canvas_dblclick)

    # get the orders from server
    orders_loaded = play_low.game_orders_reload(play_low.GAME_ID)
    if not orders_loaded:
        alert("Erreur chargement ordres")
        play.load_option(None, 'Consulter')
        return False

    # digest the orders
    orders_data = mapping.Orders(orders_loaded, play_low.POSITION_DATA, [])
    orders_in = not orders_data.empty()

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseenter", callback_canvas_mouse_enter)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    fog_of_war = play_low.GAME_PARAMETERS_LOADED['fog']
    game_over = play_low.GAME_PARAMETERS_LOADED['soloed'] or play_low.GAME_PARAMETERS_LOADED['end_voted'] or play_low.GAME_PARAMETERS_LOADED['finished']
    game_scoring = play_low.GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = common.make_rating_colours_window(fog_of_war, game_over, play_low.VARIANT_DATA, play_low.POSITION_DATA, play_low.INTERFACE_CHOSEN, game_scoring, play_low.ROLE_ID, play_low.GAME_PLAYERS_DICT, play_low.ID2PSEUDO)

    report_window = common.make_report_window(play_low.REPORT_LOADED)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    helper = html.DIV(Class='helper')
    display_left <= helper

    display_left <= html.BR()
    display_left <= rating_colours_window
    display_left <= html.BR()

    # all reports until last moves
    advancement_selected = play_low.GAME_PARAMETERS_LOADED['current_advancement']

    # exception for start build games
    min_possible_advancement = 4 if play_low.VARIANT_DATA.start_build else 0

    while True:

        # one backwards
        advancement_selected -= 1

        # out of scope : done
        if advancement_selected < min_possible_advancement:
            break

        fog_of_war = play_low.GAME_PARAMETERS_LOADED['fog']
        if fog_of_war:
            transition_loaded = play_low.game_transition_fog_of_war_reload(play_low.GAME_ID, advancement_selected, play_low.ROLE_ID)
        else:
            transition_loaded = play_low.game_transition_reload(play_low.GAME_ID, advancement_selected)
        if not transition_loaded:
            break

        time_stamp = transition_loaded['time_stamp']
        report_loaded = transition_loaded['report_txt']

        fake_report_loaded = {'time_stamp': time_stamp, 'content': report_loaded}
        report_window = common.make_report_window(fake_report_loaded)

        game_status = play_low.get_game_status_histo(play_low.VARIANT_DATA, advancement_selected)
        display_left <= game_status
        display_left <= report_window
        display_left <= html.BR()

        # just displayed last moves : done
        if advancement_selected % 5 in [0, 2]:
            break

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    # role flag
    play_low.stack_role_flag(buttons_right)

    # button erase for archive games
    if play_low.GAME_PARAMETERS_LOADED['archive']:
        play_low.stack_cancel_last_adjudication_button(buttons_right)

    # button for communication orders
    if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
        play_low.stack_communications_orders_button(buttons_right)

    # button last moves
    play_low.stack_last_moves_button(buttons_right)

    if play_low.ROLE_ID in submitted_data['needed'] and not game_over:

        # button for communication orders
        if play_low.GAME_PARAMETERS_LOADED['game_type'] in [1, 3]:  # Blitz
            play_low.stack_communications_orders_button(buttons_right)

        # information retreats/builds
        play_low.stack_possibilities(buttons_right, advancement_season)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        nb_builds = 0
        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:

            # take a note of build / remove
            role = play_low.VARIANT_DATA.roles[play_low.ROLE_ID]
            nb_builds, _, _, _ = play_low.POSITION_DATA.role_builds(role)

            legend_select_order = html.DIV("Sélectionner l'ordre d'ajustement (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum.inventory():
                if mapping.OrderTypeEnum.compatible(order_type, advancement_season):
                    input_select = html.INPUT(type="submit", value=play_low.VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        if play_low.ROLE_ID in submitted_data['agreed_now']:
            definitive_value = 1
        elif play_low.ROLE_ID in submitted_data['agreed_after']:
            definitive_value = 2
        else:
            definitive_value = 0

        stack_orders(buttons_right)
        if not orders_data.empty():
            put_erase_all(buttons_right)
        if not orders_data.all_ordered(play_low.ROLE_ID) and advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
            put_submit(buttons_right)

        # orders status
        stack_orders_status(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    play_low.MY_SUB_PANEL <= my_sub_panel2

    # other stuff
    my_sub_panel3 = html.DIV()

    if not game_over:

        # end vote now
        my_sub_panel3 <= html.H3("Vote de fin de partie")

        # reminder
        reminder = html.DIV("ATTENTION : Pensez à prévenir l'arbitre qu'un vote est en cours (avec la messagerie par exemple)", Class='important')
        special_legend = html.LEGEND(reminder)
        my_sub_panel3 <= special_legend
        my_sub_panel3 <= html.BR()

        label_vote = html.LABEL(html.B("Je vote :"))
        my_sub_panel3 <= label_vote
        my_sub_panel3 <= html.BR()

        # Continuation ===
        option_continue = "pour que la partie s'arrête !"
        label_continue = html.LABEL(html.EM(option_continue))
        my_sub_panel3 <= label_continue
        input_continue = html.INPUT(type="radio", id="stop", name="vote", checked=(vote_value is True), Class='btn-inside')
        input_continue.bind("click", update_select)
        my_sub_panel3 <= input_continue
        my_sub_panel3 <= html.BR()

        # Arret ===
        option_stop = "pour que la partie continue !"
        label_stop = html.LABEL(html.EM(option_stop))
        my_sub_panel3 <= label_stop
        input_stop = html.INPUT(type="radio", id="continue", name="vote", checked=(vote_value is False), Class='btn-inside')
        input_stop.bind("click", update_select)
        my_sub_panel3 <= input_stop
        my_sub_panel3 <= html.BR()

        # Abstention ===
        option_abstention = "non, je m'abstiens ! (équivaut à voter pour continuer)"
        label_abstention = html.LABEL(html.EM(option_abstention))
        my_sub_panel3 <= label_abstention
        input_abstention = html.INPUT(type="radio", id="abstention", name="vote", checked=(vote_value is None), Class='btn-inside')
        input_abstention.bind("click", update_select)
        my_sub_panel3 <= input_abstention
        my_sub_panel3 <= html.BR()

        input_submit = html.INPUT(type="submit", value="Soumettre", Class='btn-inside')
        input_submit.bind("click", submit_vote_callback)
        my_sub_panel3 <= html.BR()
        my_sub_panel3 <= input_submit
        my_sub_panel3 <= html.BR()
        my_sub_panel3 <= html.BR()

        my_sub_panel3 <= html.DIV("Règles du vote d'arrêt de la partie", Class='note')
        rules = html.UL()
        rules <= html.LI("Le vote individuel est confidentiel mais le nombre de votes exprimés est public.")
        rules <= html.LI("Seules les voix des joueurs encore en jeu comptent (ceux qui ont encore un centre et/ou une unité).")
        rules <= html.LI("Les non votants sont considérés en faveur de la continuation de la partie.")
        rules <= html.LI("L'unanimité (pour l'arrêt de la partie) est requise pour que l'arrêt soit voté.")
        rules <= html.LI("La décision est prise en attendant les ordres d'ajustement.")
        rules <= html.LI("Quand un vote est en cours, la partie continue normalement.")
        rules <= html.LI("Les modalités d'un tournoi peuvent interdire l'arrêt de la partie avant une année de jeu spécifique.")

        my_sub_panel3 <= rules

    # notes now

    my_sub_panel3 <= html.H3("Prise de notes")

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_note = html.LEGEND("Prendre des notes", title="Notez ce dont vous avez besoin de vous souvenir au sujet de cette partie")
    fieldset <= legend_note
    form <= fieldset
    input_note = html.TEXTAREA(type="text", rows=6, cols=80)
    input_note <= content_loaded
    fieldset <= input_note
    form <= fieldset

    form <= html.BR()

    input_note_in_game = html.INPUT(type="submit", value="Enregistrer", Class='btn-inside')
    input_note_in_game.bind("click", add_note_callback)
    form <= input_note_in_game
    my_sub_panel3 <= form

    play_low.MY_SUB_PANEL <= my_sub_panel3

    return True


def submit_communication_orders():
    """ submit_communication_orders """

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    selected_hovered_object = None
    automaton_state = None
    buttons_right = None

    def submit_orders_callback(_):
        """ submit_orders_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de communication : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de communication : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            mydialog.InfoDialog("Information", f"Vous avez déposé des ordres de communication (ou aucun): {messages}")
            if not orders_data.empty():
                alert("Vos ordres de communication seront publiés dans le prochain compte-rendu de résolution, pourvu que les unités en question aient reçu l'ordre *réel* de tenir ou de se disperser..")

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = dumps(orders_list_dict)

        json_dict = {
            'role_id': play_low.ROLE_ID,
            'orders': orders_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-communication-orders/{play_low.GAME_ID}"

        # submitting orders : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        orders_data.erase_orders()

        # update displayed map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag
        play_low.stack_role_flag(buttons_right)

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        buttons_right <= html.BR()
        put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        play_low.MY_SUB_PANEL <= my_sub_panel2

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        # to stop catching keyboard
        document.unbind("keypress")

        if automaton_state is AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # explanations
            play_low.stack_explanations_button(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de l'attaque", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée offensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée defensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(play_low.POSITION_DATA, order_type, selected_active_unit, None, None, False)
                orders_data.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                play_low.MY_SUB_PANEL <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = play_low.VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.DIV("Sélectionner l'unité convoyée", Class='instruction')
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_click(event):
        """ called when there is a click down then a click up separated by less than 'LONG_DURATION_LIMIT_SEC' sec """

        nonlocal selected_order_type
        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal selected_passive_unit
        nonlocal selected_dest_zone
        nonlocal buttons_right

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # this is a shortcut
        if automaton_state is AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = mapping.OrderTypeEnum.ATTACK_ORDER
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            # passthru

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:

            selected_active_unit = play_low.POSITION_DATA.closest_unit(pos, None)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # explanations
            play_low.stack_explanations_button(buttons_right)

            # gm can pass orders on archive games
            if selected_active_unit is None or (play_low.ROLE_ID != 0 and selected_active_unit.role != play_low.VARIANT_DATA.roles[play_low.ROLE_ID]):

                alert("Bien essayé, mais pas d'unité ici ou cette unité ne vous appartient pas ou vous n'avez pas d'ordre à valider.")

                selected_active_unit = None

                # switch back to initial state selecting unit
                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            else:

                legend_selected_unit = html.DIV(f"L'unité active sélectionnée est {selected_active_unit}")
                buttons_right <= legend_selected_unit

                legend_select_order = html.DIV("Sélectionner l'ordre (ou directement la destination - sous la légende)", Class='instruction')
                buttons_right <= legend_select_order
                buttons_right <= html.BR()

                legend_select_order21 = html.I("Raccourcis clavier :")
                buttons_right <= legend_select_order21
                buttons_right <= html.BR()

                for info in ["(a)ttaquer", "soutenir (o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer"]:
                    legend_select_order22 = html.I(info)
                    buttons_right <= legend_select_order22
                    buttons_right <= html.BR()

                # to catch keyboard
                document.bind("keypress", callback_keypress)

                for order_type in mapping.OrderTypeEnum.inventory():
                    if mapping.OrderTypeEnum.compatible(order_type, mapping.SeasonEnum.SPRING_SEASON):
                        input_select = html.INPUT(type="submit", value=play_low.VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            if selected_order_type in [mapping.OrderTypeEnum.ATTACK_ORDER, mapping.OrderTypeEnum.RETREAT_ORDER]:
                unit_reference_type = mapping.UnitTypeEnum.ARMY_UNIT if isinstance(selected_active_unit, mapping.Army) else mapping.UnitTypeEnum.FLEET_UNIT
            elif selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                unit_reference_type = mapping.UnitTypeEnum.ARMY_UNIT if isinstance(selected_passive_unit, mapping.Army) else mapping.UnitTypeEnum.FLEET_UNIT
            selected_dest_zone = play_low.VARIANT_DATA.closest_zone(pos, unit_reference_type)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # explanations
            play_low.stack_explanations_button(buttons_right)

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone.region == selected_active_unit.zone.region:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(play_low.POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone, False)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(play_low.POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone, False)
                orders_data.insert_order(order)

            # update map
            callback_render(False)

            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
            buttons_right <= legend_select_unit

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = play_low.POSITION_DATA.closest_unit(pos, None)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            # explanations
            play_low.stack_explanations_button(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(play_low.POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, None, False)
                orders_data.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                play_low.MY_SUB_PANEL <= my_sub_panel2

                stack_orders(buttons_right)
                if not orders_data.empty():
                    put_erase_all(buttons_right)
                buttons_right <= html.BR()
                put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination de l'attaque soutenue", Class='instruction')
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination du convoi", Class='instruction')
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_canvas_dblclick(event):
        """
        called when there is a double click
        """

        nonlocal automaton_state
        nonlocal buttons_right

        # the aim is to give this variable a value
        selected_erase_unit = None

        # first : take from event
        if event:

            # where is the click
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

            # moves : select unit : easy case
            selected_erase_unit = play_low.POSITION_DATA.closest_unit(pos, None)

        # event is None when coming from x pressed, then take 'selected_active_unit' (that can be None)
        if selected_erase_unit is None:
            selected_erase_unit = selected_active_unit

        # unit must be selected
        if selected_erase_unit is None:
            return

        # unit must have an order
        if not orders_data.is_ordered(selected_erase_unit):
            return

        # remove order
        orders_data.remove_order(selected_erase_unit)

        # update map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag
        play_low.stack_role_flag(buttons_right)

        # explanations
        play_low.stack_explanations_button(buttons_right)

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not orders_data.empty():
            put_erase_all(buttons_right)
        buttons_right <= html.BR()
        put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        play_low.MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = play_low.POSITION_DATA.closest_object(pos)

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
            # no

            # redraw all arrows
            if prev_selected_hovered_object is not None or selected_hovered_object is not None:
                orders_data.render(ctx)

    def callback_canvas_mouse_enter(event):
        """ callback_canvas_mouse_enter """

        nonlocal selected_hovered_object

        helper.clear()

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = play_low.POSITION_DATA.closest_object(pos)

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

            # redraw all arrows
            orders_data.render(ctx)

            # redraw dislodged if applicable
            if isinstance(selected_hovered_object, mapping.Unit):
                if selected_hovered_object in play_low.POSITION_DATA.dislodging_table:
                    dislodged = play_low.POSITION_DATA.dislodging_table[selected_hovered_object]
                    if dislodged is not selected_hovered_object:
                        dislodged.highlite(ctx, False)

        helper.clear()
        helper <= "_"

    def callback_keypress(event):
        """ callback_keypress """

        char = chr(event.charCode).lower()

        # order shortcut
        selected_order = mapping.OrderTypeEnum.shortcut(char)
        if selected_order is None:
            return

        select_order_type_callback(event, selected_order)

    def callback_render(refresh):
        """ callback_render """

        if refresh:

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the position and the neutral centers
            play_low.POSITION_DATA.render(ctx)

            # put the legends
            play_low.VARIANT_DATA.render(ctx)

            # save
            save_context(ctx)

        else:

            # restore
            restore_context(ctx)

        # put the orders
        orders_data.render(ctx)

    def stack_orders(buttons_right):
        """ stack_orders """

        buttons_right <= html.P()
        lines = str(orders_data).split('\n')
        communication_orders = html.DIV()
        communication_orders.style = {
            'color': 'magenta',
        }
        for line in lines:
            communication_orders <= html.B(line)
            communication_orders <= html.BR()
        buttons_right <= communication_orders

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="Effacer tout", Class='btn-inside')
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="Enregistrer", Class='btn-inside')
        input_submit.bind("click", submit_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        buttons_right <= html.DIV("ATTENTION ! Ce sont des ordres pour communiquer avec les autres joueurs, pas des ordres pour les unités. Ils seront publiés à la prochaine résolution pourvu que l'unité en question ait reçu l'ordre *réel* de tenir ou de se disperser.", Class='important')

    # need to be connected
    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        play.load_option(None, 'Consulter')
        return False

    # need to have a role
    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # cannot be game master
    if play_low.ROLE_ID == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # cannot be archive game
    if play_low.GAME_PARAMETERS_LOADED['archive']:
        alert("Ce n'est pas possible pour une partie archive")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not waiting
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not finished
    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà archivée ou distinguée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to disallow messages
    if play_low.GAME_PARAMETERS_LOADED['game_type'] not in [1, 3]:  # Blitz
        alert("La partie n'est pas Blitz")
        play.load_option(None, 'Consulter')
        return False

    # phase needs to be moves or retreat
    if play_low.GAME_PARAMETERS_LOADED['current_advancement'] % 5 not in [0, 1, 2, 3]:
        alert("Ce n'est pas une phase de mouvements ou de retraites")
        play.load_option(None, 'Consulter')
        return False

    # need to have orders to submit

    submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
    if not submitted_data:
        alert("Erreur chargement données de soumission")
        play.load_option(None, 'Consulter')
        return False

    if play_low.ROLE_ID not in submitted_data['needed']:
        alert("Vous n'avez pas d'ordre à passer")
        play.load_option(None, 'Consulter')
        return False

    # check game soloed
    if play_low.GAME_PARAMETERS_LOADED['soloed']:
        alert("La partie est terminée parce qu'un solo a été réalisé !")
        play.load_option(None, 'Consulter')
        return False

    # check game end voted
    if play_low.GAME_PARAMETERS_LOADED['end_voted']:
        alert("La partie est terminée sur un vote de fin unanime !")
        play.load_option(None, 'Consulter')
        return False

    # check game finished (if not soloed not end voted)
    if play_low.GAME_PARAMETERS_LOADED['finished']:
        alert("La partie est terminée parce qu'arrivée à échéance")
        play.load_option(None, 'Consulter')
        return False

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # create canvas
    map_size = play_low.VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return False

    # click and double click
    canvas.bind("click", callback_canvas_click)
    canvas.bind("dblclick", callback_canvas_dblclick)

    # get the orders from server
    orders_loaded = play_low.game_orders_reload(play_low.GAME_ID)
    if not orders_loaded:
        alert("Erreur chargement ordres")
        play.load_option(None, 'Consulter')
        return False

    # digest the orders
    orders_data2 = mapping.Orders(orders_loaded, play_low.POSITION_DATA, [])

    # get the communication orders from server
    communication_orders_loaded = play_low.game_communication_orders_reload(play_low.GAME_ID)
    if not communication_orders_loaded:
        alert("Erreur chargement ordres communication")
        play.load_option(None, 'Consulter')
        return False

    # digest the orders
    orders_data = mapping.Orders(communication_orders_loaded, play_low.POSITION_DATA, [])

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseenter", callback_canvas_mouse_enter)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    fog_of_war = play_low.GAME_PARAMETERS_LOADED['fog']
    game_over = play_low.GAME_PARAMETERS_LOADED['soloed'] or play_low.GAME_PARAMETERS_LOADED['end_voted'] or play_low.GAME_PARAMETERS_LOADED['finished']
    game_scoring = play_low.GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = common.make_rating_colours_window(fog_of_war, game_over, play_low.VARIANT_DATA, play_low.POSITION_DATA, play_low.INTERFACE_CHOSEN, game_scoring, play_low.ROLE_ID, play_low.GAME_PLAYERS_DICT, play_low.ID2PSEUDO)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    helper = html.DIV(Class='helper')
    display_left <= helper

    display_left <= html.BR()
    display_left <= rating_colours_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    # role flag
    play_low.stack_role_flag(buttons_right)

    # explanations
    play_low.stack_explanations_button(buttons_right)

    # button for communication orders possibilities
    play_low.stack_communication_possibilities(buttons_right, orders_data2)

    legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic pour effacer)", Class='instruction')
    buttons_right <= legend_select_unit
    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    stack_orders(buttons_right)
    if not orders_data.empty():
        put_erase_all(buttons_right)
    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    play_low.MY_SUB_PANEL <= my_sub_panel2

    return True


def imagine_units():
    """ imagine_units """

    selected_active_unit = None
    automaton_state = None
    buttons_right = None
    imagined_unit = None
    selected_build_unit_type = None

    def imagine_unit_callback(_, delete):
        """ imagine_unit_callback """

        def reply_callback(req):
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur imagine d'unité {delete=}: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème imagine d'unité {delete=} : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            if delete:
                mydialog.InfoDialog("Information", f"Vous avez cessé d'imaginer une unité (vérifiez directement sur la carte) : {messages}")
            else:
                mydialog.InfoDialog("Information", f"Vous avez imaginé une unité (vérifiez directement sur la carte) : {messages}")
            # back to where we started
            play_low.MY_SUB_PANEL.clear()
            # reload position
            play_low.load_dynamic_stuff()
            imagine_units()

        considered_unit = selected_active_unit if delete else imagined_unit

        json_dict = {
            'type_num': 1 if isinstance(considered_unit, mapping.Army) else 2,
            'zone_num': considered_unit.zone.identifier,
            'role_num': considered_unit.role.identifier,
            'delete': delete
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-imagine-unit/{play_low.GAME_ID}/{play_low.ROLE_ID}"

        # showing units : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def reset_callback(_):
        """ reset_callback """

        nonlocal buttons_right
        nonlocal automaton_state

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

        # role flag
        play_low.stack_role_flag(buttons_right)

        for unit_type in mapping.UnitTypeEnum.inventory():
            input_select = html.INPUT(type="submit", value=f"Imaginer une {play_low.VARIANT_DATA.unit_name_table[unit_type]}", Class='btn-inside')
            buttons_right <= html.BR()
            input_select.bind("click", lambda e, u=unit_type: select_built_unit_type_callback(e, u))
            buttons_right <= html.BR()
            buttons_right <= input_select

        input_remove = html.INPUT(type="submit", value="Retirer une unité des imaginées", Class='btn-inside')
        buttons_right <= html.BR()
        input_remove.bind("click", select_remove_unit_callback)
        buttons_right <= html.BR()
        buttons_right <= input_remove

        buttons_right <= html.BR()
        buttons_right <= html.BR()

        legend_select_unit = html.DIV("Cliquez sur l'action à réaliser", Class='instruction')
        buttons_right <= legend_select_unit

        my_sub_panel2 <= buttons_right
        play_low.MY_SUB_PANEL <= my_sub_panel2

        automaton_state = AutomatonStateEnum2.SELECT_ACTION_STATE

    def select_built_unit_type_callback(_, build_unit_type):
        """ select_built_unit_type_callback """

        nonlocal selected_build_unit_type
        nonlocal automaton_state
        nonlocal buttons_right

        if automaton_state is AutomatonStateEnum2.SELECT_ACTION_STATE:

            selected_build_unit_type = build_unit_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            legend_select_active = html.DIV("Sélectionner la zone où mettre cette unité", Class='instruction')
            buttons_right <= legend_select_active

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2

            # it is a zone we need now
            automaton_state = AutomatonStateEnum2.SELECT_POSITION_STATE
            return

    def select_remove_unit_callback(_):
        """ select_remove_unit_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        if automaton_state is AutomatonStateEnum2.SELECT_ACTION_STATE:

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            legend_select_active = html.DIV("Sélectionner l'unité à ne plus imaginer", Class='instruction')
            buttons_right <= legend_select_active

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2

            # it is a zone we need now
            automaton_state = AutomatonStateEnum2.SELECT_UNIT_STATE

    def callback_canvas_click(event):
        """ callback_canvas_click """

        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal buttons_right
        nonlocal imagined_unit

        if automaton_state is AutomatonStateEnum2.SELECT_UNIT_STATE:

            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

            selected_active_unit = play_low.POSITION_DATA.closest_unit(pos, False)

            if not selected_active_unit.imagined:

                alert("Cette unité est réelle !")
                put_reset(buttons_right)

            else:

                # must not be linked to order
                dangling_passives_zones = {o[4] for o in orders_loaded['orders'] if o[4] != 0}

                if selected_active_unit.zone.identifier in dangling_passives_zones:

                    alert("Cette unité est l'objet d'un soutien offensif ou d'un convoi, il faut modifier l'ordre au préalable !")
                    put_reset(buttons_right)

                else:
                    my_sub_panel2.removeChild(buttons_right)
                    buttons_right = html.DIV(id='buttons_right')
                    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

                    # role flag
                    play_low.stack_role_flag(buttons_right)

                    buttons_right <= html.BR()
                    put_submit(buttons_right, True)
                    put_reset(buttons_right)

                    my_sub_panel2 <= buttons_right
                    play_low.MY_SUB_PANEL <= my_sub_panel2

            return

        if automaton_state is AutomatonStateEnum2.SELECT_POSITION_STATE:

            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

            selected_dest_zone = play_low.VARIANT_DATA.closest_zone(pos, selected_build_unit_type)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # role flag
            play_low.stack_role_flag(buttons_right)

            selected_active_unit = None
            if selected_dest_zone.region in play_low.POSITION_DATA.occupant_table:
                alert("Bien essayé, mais il y a déjà une unité ici !")
                legend_imagined_unit = html.DIV("Sélectionner la zone où mettre cette unité")
                buttons_right <= legend_imagined_unit

            # prevent putting armies in sea
            elif selected_dest_zone.region.region_type is mapping.RegionTypeEnum.SEA_REGION and selected_build_unit_type is mapping.UnitTypeEnum.ARMY_UNIT:
                alert("On ne met pas une armée en mer !")
                legend_imagined_unit = html.DIV("Sélectionner la zone où mettre cette unité")
                buttons_right <= legend_imagined_unit

            # prevent putting fleets inland
            elif selected_dest_zone.region.region_type is mapping.RegionTypeEnum.LAND_REGION and selected_build_unit_type is mapping.UnitTypeEnum.FLEET_UNIT:
                alert("On ne met pas une flotte en terre !")
                legend_imagined_unit = html.DIV("Sélectionner la zone où mettre cette unité")
                buttons_right <= legend_imagined_unit

            # prevent putting army on specific coast
            elif selected_dest_zone.coast_type is not None and selected_build_unit_type is mapping.UnitTypeEnum.ARMY_UNIT:
                alert("On ne met pas une armée sur une côte spéciale !")
                legend_imagined_unit = html.DIV("Sélectionner la zone où mettre cette unité")
                buttons_right <= legend_imagined_unit

            # prevent putting fleets on region with specific coasts
            elif selected_dest_zone.coast_type is None and len([z for z in play_low.VARIANT_DATA.zones.values() if z.region == selected_dest_zone.region]) > 1 and selected_build_unit_type is mapping.UnitTypeEnum.FLEET_UNIT:
                alert("On ne met pas une flotte sur une région qui par ailleurs comporte une côte spéciale !")
                legend_imagined_unit = html.DIV("Sélectionner la zone où mettre cette unité")
                buttons_right <= legend_imagined_unit

            else:

                # choose next role in list (arbitrary)
                other_role_id = play_low.ROLE_ID % (len(play_low.VARIANT_DATA.roles) - 1) + 1
                other_role = play_low.VARIANT_DATA.roles[other_role_id]

                if selected_build_unit_type is mapping.UnitTypeEnum.ARMY_UNIT:
                    imagined_unit = mapping.Army(play_low.POSITION_DATA, other_role, selected_dest_zone, None, False)
                if selected_build_unit_type is mapping.UnitTypeEnum.FLEET_UNIT:
                    imagined_unit = mapping.Fleet(play_low.POSITION_DATA, other_role, selected_dest_zone, None, False)

                legend_imagined_unit = html.DIV(f"L'unité imaginée est {imagined_unit}")
                buttons_right <= legend_imagined_unit
                buttons_right <= html.BR()

                legend_imagined_unit2 = html.DIV("Sa nationalité est sans aucune importance", Class='important')
                buttons_right <= legend_imagined_unit2

                buttons_right <= html.BR()
                put_submit(buttons_right, False)
                put_reset(buttons_right)

            my_sub_panel2 <= buttons_right
            play_low.MY_SUB_PANEL <= my_sub_panel2

            return

    def callback_render(refresh):
        """ callback_render """

        if refresh:

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the position and the neutral centers
            play_low.POSITION_DATA.render(ctx)

            # put the legends
            play_low.VARIANT_DATA.render(ctx)

            # save
            save_context(ctx)

        else:

            # restore
            restore_context(ctx)

    def put_reset(buttons_right):
        """ put_reset """

        input_reset = html.INPUT(type="submit", value="Reset", Class='btn-inside')
        input_reset.bind("click", reset_callback)
        buttons_right <= html.BR()
        buttons_right <= input_reset
        buttons_right <= html.BR()
        buttons_right <= html.BR()

    def put_submit(buttons_right, delete):
        """ put_submit """

        if delete:
            input_submit = html.INPUT(type="submit", value="On l'enlève !", Class='btn-inside')
        else:
            input_submit = html.INPUT(type="submit", value="On la met !", Class='btn-inside')
        input_submit.bind("click", lambda e: imagine_unit_callback(e, delete))
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()
        buttons_right <= html.BR()

        buttons_right <= html.DIV("Principe de l'imagination des unités : On imagine une unité sur la carte. Une unité imaginée peut être convoyée et soutenue offensivement (ce dernier point étant le but de l'opération). Si l'unité n'a pas le bon type ou n'existe pas, l'ordre sera annulé à la résolution. Ne pas retirer une unité qui est l'objet d'un soutien ou d'un convoi bien sûr !")

    # need to be connected
    if play_low.PSEUDO is None:
        alert("Il faut se connecter au préalable")
        play.load_option(None, 'Consulter')
        return False

    # need to have a role
    if play_low.ROLE_ID is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # cannot be game master
    if play_low.ROLE_ID == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
        play.load_option(None, 'Consulter')
        return False

    # cannot be archive game
    if play_low.GAME_PARAMETERS_LOADED['archive']:
        alert("Ce n'est pas possible pour une partie archive")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not waiting
    if play_low.GAME_PARAMETERS_LOADED['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        play.load_option(None, 'Consulter')
        return False

    # game needs to be ongoing - not finished
    if play_low.GAME_PARAMETERS_LOADED['current_state'] in [2, 3]:
        alert("La partie est déjà archivée ou distinguée")
        play.load_option(None, 'Consulter')
        return False

    # variant must be foggy
    if not play_low.GAME_PARAMETERS_LOADED['fog']:
        alert("La variante ne restreint pas la visibilité")
        play.load_option(None, 'Consulter')
        return False

    # need to have orders to submit

    submitted_data = play_low.get_roles_submitted_orders(play_low.GAME_ID)
    if not submitted_data:
        alert("Erreur chargement données de soumission")
        play.load_option(None, 'Consulter')
        return False

    if play_low.ROLE_ID not in submitted_data['needed']:
        alert("Vous n'avez pas d'ordre à passer")
        play.load_option(None, 'Consulter')
        return False

    # check game soloed
    if play_low.GAME_PARAMETERS_LOADED['soloed']:
        alert("La partie est terminée parce qu'un solo a été réalisé !")
        play.load_option(None, 'Consulter')
        return False

    # check game end voted
    if play_low.GAME_PARAMETERS_LOADED['end_voted']:
        alert("La partie est terminée sur un vote de fin unanime !")
        play.load_option(None, 'Consulter')
        return False

    # check game finished (if not soloed nor end voted)
    if play_low.GAME_PARAMETERS_LOADED['finished']:
        alert("La partie est terminée parce qu'arrivée à échéance")
        play.load_option(None, 'Consulter')
        return False

    # now we can display

    # header

    # game status
    play_low.MY_SUB_PANEL <= play_low.GAME_STATUS
    play_low.MY_SUB_PANEL <= html.BR()

    # create canvas
    map_size = play_low.VARIANT_DATA.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return False

    # get the orders from server
    orders_loaded = play_low.game_orders_reload(play_low.GAME_ID)
    if not orders_loaded:
        alert("Erreur chargement ordres")
        play.load_option(None, 'Consulter')
        return False

    canvas.bind("mousedown", callback_canvas_click)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(play_low.VARIANT_NAME_LOADED, play_low.INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    fog_of_war = play_low.GAME_PARAMETERS_LOADED['fog']
    game_over = play_low.GAME_PARAMETERS_LOADED['soloed'] or play_low.GAME_PARAMETERS_LOADED['end_voted'] or play_low.GAME_PARAMETERS_LOADED['finished']
    game_scoring = play_low.GAME_PARAMETERS_LOADED['scoring']
    rating_colours_window = common.make_rating_colours_window(fog_of_war, game_over, play_low.VARIANT_DATA, play_low.POSITION_DATA, play_low.INTERFACE_CHOSEN, game_scoring, play_low.ROLE_ID, play_low.GAME_PLAYERS_DICT, play_low.ID2PSEUDO)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas
    display_left <= html.BR()
    display_left <= rating_colours_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    # role flag
    play_low.stack_role_flag(buttons_right)

    for unit_type in mapping.UnitTypeEnum.inventory():
        input_select = html.INPUT(type="submit", value=f"Imaginer une {play_low.VARIANT_DATA.unit_name_table[unit_type]}", Class='btn-inside')
        buttons_right <= html.BR()
        input_select.bind("click", lambda e, u=unit_type: select_built_unit_type_callback(e, u))
        buttons_right <= html.BR()
        buttons_right <= input_select

    input_remove = html.INPUT(type="submit", value="Retirer une unité des imaginées", Class='btn-inside')
    buttons_right <= html.BR()
    input_remove.bind("click", select_remove_unit_callback)
    buttons_right <= html.BR()
    buttons_right <= input_remove

    buttons_right <= html.BR()
    buttons_right <= html.BR()

    legend_select_unit = html.DIV("Cliquez sur l'action à réaliser", Class='instruction')
    buttons_right <= legend_select_unit

    automaton_state = AutomatonStateEnum2.SELECT_ACTION_STATE

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    play_low.MY_SUB_PANEL <= my_sub_panel2

    return True
