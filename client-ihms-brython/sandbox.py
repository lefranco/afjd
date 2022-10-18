""" master """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import enum
import time

from browser import document, html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error

import config
import common
import interface
import geometry
import mapping

LONG_DURATION_LIMIT_SEC = 1.0

VARIANT_NAME = "standard"

MY_PANEL = html.DIV(id="sandbox")
MY_PANEL.attrs['style'] = 'display: table-row'


@enum.unique
class AutomatonStateEnum(enum.Enum):
    """ AutomatonStateEnum """

    SELECT_ACTIVE_STATE = enum.auto()
    SELECT_ORDER_STATE = enum.auto()
    SELECT_PASSIVE_UNIT_STATE = enum.auto()
    SELECT_DESTINATION_STATE = enum.auto()


# this will not change
VARIANT_NAME_LOADED = VARIANT_NAME

# this will
INTERFACE_CHOSEN = None
VARIANT_DATA = None
POSITION_DATA = None
ORDERS_DATA = None


def create_initial_position():
    """ create_initial_position """

    global INTERFACE_CHOSEN
    global VARIANT_DATA
    global POSITION_DATA
    global ORDERS_DATA

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(VARIANT_NAME_LOADED)
    if not variant_content_loaded:
        return

    # selected interface (user choice)
    INTERFACE_CHOSEN = interface.get_interface_from_variant(VARIANT_NAME_LOADED)

    # from display chose get display parameters
    parameters_read = common.read_parameters(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)

    # build variant data
    VARIANT_DATA = mapping.Variant(VARIANT_NAME_LOADED, variant_content_loaded, parameters_read)

    # get the position
    position_loaded = {'ownerships': {}, 'units': {}, 'forbiddens': {}, 'dislodged_ones': {}}

    # digest the position
    POSITION_DATA = mapping.Position(position_loaded, VARIANT_DATA)

    # get the orders from server (actually no)
    orders_loaded = {'fake_units': {}, 'orders': {}}

    # digest the orders
    ORDERS_DATA = mapping.Orders(orders_loaded, POSITION_DATA)


def import_position(new_position_data):
    """ import position from play/position """

    global POSITION_DATA
    global ORDERS_DATA

    # make sure we are ready
    if not POSITION_DATA:
        create_initial_position()

    # get loaded units
    loaded_units = new_position_data.save_json()
    dict_loaded_units = {}
    for loaded_unit in loaded_units:
        type_num = loaded_unit['type_unit']
        role_num = loaded_unit['role']
        zone_num = loaded_unit['zone']
        if role_num not in dict_loaded_units:
            dict_loaded_units[role_num] = []
        dict_loaded_units[role_num].append([type_num, zone_num])

    # get loaded centers for convenience
    loaded_ownerships = new_position_data.save_json2()
    dict_loaded_ownerships = {}
    for loaded_ownership in loaded_ownerships:
        center_num = loaded_ownership['center_num']
        role_num = loaded_ownership['role']
        dict_loaded_ownerships[center_num] = role_num

    # get the position
    position_imported = {'ownerships': dict_loaded_ownerships, 'units': dict_loaded_units, 'forbiddens': {}, 'dislodged_ones': {}}

    # copy position
    POSITION_DATA = mapping.Position(position_imported, VARIANT_DATA)

    # get the orders from server (actually no)
    orders_loaded = {'fake_units': {}, 'orders': {}}

    # digest the orders
    ORDERS_DATA = mapping.Orders(orders_loaded, POSITION_DATA)


def sandbox():
    """ sandbox """

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    automaton_state = None

    stored_event = None
    down_click_time = None
    selected_hovered_object = None

    def show_zone_callback(_, zone_area):
        mapping.show_zone(ctx, zone_area)

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # complete orders
        ORDERS_DATA.rest_hold(None)

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)

        if not ORDERS_DATA.empty():
            put_erase_all(buttons_right)
        # do not put all rest hold
        if not ORDERS_DATA.empty():
            put_submit(buttons_right)
        if not POSITION_DATA.empty():
            put_download(buttons_right)
        buttons_right <= html.BR()
        put_checkers(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_PANEL <= my_sub_panel2

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        ORDERS_DATA.erase_orders()

        # erase units
        POSITION_DATA.erase_units()

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)

        # do not put erase all
        if not ORDERS_DATA.empty():
            put_submit(buttons_right)
        if not POSITION_DATA.empty():
            put_download(buttons_right)
        buttons_right <= html.BR()
        put_checkers(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_PANEL <= my_sub_panel2

    def submit_callback(_):
        """ submit_callback """

        def reply_callback(req):
            nonlocal report_window
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission de situaion et ordres de simulation : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission de situaion et ordres de simulation : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez soumis les ordres et la situation pour une simulation : {messages}", remove_after=config.REMOVE_AFTER)

            if 'result' in req_result:

                # remove previous
                display_left.removeChild(report_window)

                # put new
                time_stamp = time.time()
                report_txt = req_result['result']
                fake_report_loaded = {'time_stamp': time_stamp, 'content': report_txt}
                report_window = common.make_report_window(fake_report_loaded)
                display_left <= report_window

        variant_name = VARIANT_NAME_LOADED

        names_dict = VARIANT_DATA.extract_names()
        names_dict_json = json.dumps(names_dict)

        orders_list_dict = ORDERS_DATA.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        # units
        units_list_dict = POSITION_DATA.save_json()
        units_list_dict_json = json.dumps(units_list_dict)

        # orders
        orders_list_dict = ORDERS_DATA.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        json_dict = {
            'variant_name': variant_name,
            'names': names_dict_json,
            'units': units_list_dict_json,
            'orders': orders_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/simulation"

        # submitting position and orders for simulation : do not need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def download_callback(_):
        """ download_callback """

        # make a rendom like label
        time_stamp = time.time()
        label = int(time_stamp) % 1000

        # needed too for some reason
        MY_PANEL <= html.A(id='download_link')

        # perform actual exportation
        download_link = document['download_link']
        download_link.download = f"diplomania_map_{label}.png"
        download_link.href = canvas.toDataURL('image/png')
        document['download_link'].click()

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        if automaton_state is AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de l'attaque", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée offensivement (cliquer sous la légende)", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée defensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(POSITION_DATA, order_type, selected_active_unit, None, None)
                ORDERS_DATA.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_PANEL <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = VARIANT_DATA.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.DIV("Sélectionner l'unité convoyée", Class='instruction')
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            stack_orders(buttons_right)
            if not POSITION_DATA.empty():
                put_erase_all(buttons_right)
            put_rest_hold(buttons_right)
            if not ORDERS_DATA.empty():
                put_submit(buttons_right)
            if not POSITION_DATA.empty():
                put_download(buttons_right)
            buttons_right <= html.BR()
            put_checkers(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_PANEL <= my_sub_panel2

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

            selected_active_unit = POSITION_DATA.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # can be None if no retreating unit on board
            if selected_active_unit is not None:

                legend_selected_unit = html.DIV(f"L'unité active sélectionnée est {selected_active_unit}")
                buttons_right <= legend_selected_unit

                legend_select_order = html.DIV("Sélectionner l'ordre (ou directement la destination - sous la légende)", Class='instruction')
                buttons_right <= legend_select_order
                buttons_right <= html.BR()

                legend_select_order21 = html.I("Raccourcis clavier :")
                buttons_right <= legend_select_order21
                buttons_right <= html.BR()

                for info in ["(a)ttaquer", "soutenir (o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer", "(x)supprimer l'ordre/l'unité"]:
                    legend_select_order22 = html.I(info)
                    buttons_right <= legend_select_order22
                    buttons_right <= html.BR()

                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(mapping.SeasonEnum.AUTUMN_SEASON):
                        input_select = html.INPUT(type="submit", value=VARIANT_DATA.name_table[order_type])
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

            stack_orders(buttons_right)
            if not POSITION_DATA.empty():
                put_erase_all(buttons_right)
            put_rest_hold(buttons_right)
            if not ORDERS_DATA.empty():
                put_submit(buttons_right)
            if not POSITION_DATA.empty():
                put_download(buttons_right)
            buttons_right <= html.BR()
            put_checkers(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_PANEL <= my_sub_panel2

            # can be None if no retreating unit on board
            if selected_active_unit is not None:
                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            selected_dest_zone = VARIANT_DATA.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone)
                ORDERS_DATA.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone)
                ORDERS_DATA.insert_order(order)

            # update map
            callback_render(None)

            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
            buttons_right <= legend_select_unit

            stack_orders(buttons_right)
            if not POSITION_DATA.empty():
                put_erase_all(buttons_right)
            put_rest_hold(buttons_right)
            if not ORDERS_DATA.empty():
                put_submit(buttons_right)
            if not POSITION_DATA.empty():
                put_download(buttons_right)
            buttons_right <= html.BR()
            put_checkers(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = POSITION_DATA.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, None)
                ORDERS_DATA.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_PANEL <= my_sub_panel2

                stack_orders(buttons_right)
                if not POSITION_DATA.empty():
                    put_erase_all(buttons_right)
                put_rest_hold(buttons_right)
                if not ORDERS_DATA.empty():
                    put_submit(buttons_right)
                if not POSITION_DATA.empty():
                    put_download(buttons_right)
                buttons_right <= html.BR()
                put_checkers(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.DIV(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination de l'attaque soutenue (cliquer sous la légende)", Class='instruction')
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.DIV("Sélectionner la destination du convoi (cliquer sous la légende)", Class='instruction')
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not POSITION_DATA.empty():
                put_erase_all(buttons_right)
            put_rest_hold(buttons_right)
            if not ORDERS_DATA.empty():
                put_submit(buttons_right)
            if not POSITION_DATA.empty():
                put_download(buttons_right)
            buttons_right <= html.BR()
            put_checkers(buttons_right)

            my_sub_panel2 <= buttons_right
            MY_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_canvas_long_click(event):
        """
        called when there is a click down then a click up separated by more than 'LONG_DURATION_LIMIT_SEC' sec
        or when pressing 'x' in which case a None is passed
        """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_hovered_object

        # the aim is to give this variable a value
        selected_erase_unit = None

        # first : take from event
        if event:

            # where is the click
            pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

            # moves : select unit : easy case
            selected_erase_unit = POSITION_DATA.closest_unit(pos, False)

        # event is None when coming from x pressed, then take 'selected_active_unit' (that can be None)
        if selected_erase_unit is None:
            selected_erase_unit = selected_active_unit

        # unit must be selected
        if selected_erase_unit is None:
            return

        # if unit does not have an order... remove unit
        if not ORDERS_DATA.is_ordered(selected_erase_unit):

            # remove unit
            POSITION_DATA.remove_unit(selected_erase_unit)

            # tricky
            if selected_hovered_object == selected_erase_unit:
                selected_hovered_object = None

        else:

            # remove order
            ORDERS_DATA.remove_order(selected_erase_unit)

        # update map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not POSITION_DATA.empty():
            put_erase_all(buttons_right)
        put_rest_hold(buttons_right)
        if not ORDERS_DATA.empty():
            put_submit(buttons_right)
        if not POSITION_DATA.empty():
            put_download(buttons_right)
        buttons_right <= html.BR()
        put_checkers(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_PANEL <= my_sub_panel2

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

        # normal : call
        callback_canvas_click(stored_event)

    def callback_keypress(event):
        """ callback_keypress """

        char = chr(event.charCode).lower()

        # order removal : special
        if char == 'x':
            # pass to double click
            callback_canvas_long_click(None)
            return

        # order shortcut
        selected_order = mapping.OrderTypeEnum.shortcut(char)
        if selected_order is None:
            return

        select_order_type_callback(event, selected_order)

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

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

            # redraw all arrows
            if prev_selected_hovered_object is not None or selected_hovered_object is not None:
                ORDERS_DATA.render(ctx)

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """

        if selected_hovered_object is not None:
            selected_hovered_object.highlite(ctx, False)
            # redraw all arrows
            ORDERS_DATA.render(ctx)

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        VARIANT_DATA.render(ctx)

        # put the position
        POSITION_DATA.render(ctx)

        # put the orders
        ORDERS_DATA.render(ctx)

        # put the legends at the end
        VARIANT_DATA.render_legends(ctx)

    def stack_orders(buttons_right):
        """ stack_orders """

        buttons_right <= html.P()
        lines = str(ORDERS_DATA).split('\n')
        orders = html.DIV()
        for line in lines:
            orders <= html.B(line)
            orders <= html.BR()
        buttons_right <= orders

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="effacer tout")
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_rest_hold(buttons_right):
        """ put_rest_hold """

        input_rest_hold = html.INPUT(type="submit", value="tout le reste tient")
        input_rest_hold.bind("click", rest_hold_callback)
        buttons_right <= html.BR()
        buttons_right <= input_rest_hold
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="soumettre au simulateur")
        input_submit.bind("click", submit_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()

    def put_download(buttons_right):
        """ put_export """

        input_export = html.INPUT(type="submit", value="télécharger cette position")
        input_export.bind("click", download_callback)
        buttons_right <= html.BR()
        buttons_right <= input_export
        buttons_right <= html.BR()

    def put_checkers(buttons_right):
        """ put_checkers """

        buttons_right <= "Vérifier zone :"
        buttons_right <= html.BR()

        # to check positions
        for zone in sorted(VARIANT_DATA.zones.values(), key=lambda z: VARIANT_DATA.name_table[z]):
            zone_area = VARIANT_DATA.path_table[zone]
            zone_name = VARIANT_DATA.name_table[zone]

            input_submit = html.INPUT(type="submit", value=zone_name)
            input_submit.bind("click", lambda e, za=zone_area: show_zone_callback(e, za))
            buttons_right <= input_submit

        buttons_right <= html.BR()

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

        nonlocal automaton_state
        nonlocal buttons_right

        # récupère les données stockées dans drag_start (l'id de l'objet déplacé)
        src_id = event.dataTransfer.getData("text")
        elt = document[src_id]

        # enlever la fonction associée à mouseover
        elt.unbind("mouseover")
        elt.style.cursor = "auto"
        event.preventDefault()

        # put unit there
        # get unit dragged
        (type_unit, role) = unit_info_table[src_id]
        # get zone
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_drop_zone = VARIANT_DATA.closest_zone(pos)

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
            if len([z for z in VARIANT_DATA.zones.values() if z.region == selected_drop_region]) > 1:
                # prevent putting fleet on non specific coasts if exists
                if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                    type_unit = mapping.UnitTypeEnum.ARMY_UNIT

        # create unit
        if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
            new_unit = mapping.Army(POSITION_DATA, role, selected_drop_zone, None)
        if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
            new_unit = mapping.Fleet(POSITION_DATA, role, selected_drop_zone, None)

        # remove previous occupant if applicable
        if selected_drop_region in POSITION_DATA.occupant_table:
            previous_unit = POSITION_DATA.occupant_table[selected_drop_region]
            POSITION_DATA.remove_unit(previous_unit)

            # and the order too
            if ORDERS_DATA.is_ordered(previous_unit):
                ORDERS_DATA.remove_order(previous_unit)

        # add to position
        POSITION_DATA.add_unit(new_unit)

        # refresh
        callback_render(ctx)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not POSITION_DATA.empty():
            put_erase_all(buttons_right)
        put_rest_hold(buttons_right)
        if not ORDERS_DATA.empty():
            put_submit(buttons_right)
        if not POSITION_DATA.empty():
            put_download(buttons_right)
        buttons_right <= html.BR()
        put_checkers(buttons_right)

        my_sub_panel2 <= buttons_right
        MY_PANEL <= my_sub_panel2

    # starts here

    # make sure we are ready
    if not POSITION_DATA:
        create_initial_position()

    # finds data about the dragged unit
    unit_info_table = {}

    reserve_table = html.TABLE()

    num = 1
    for role in VARIANT_DATA.roles.values():

        # ignore GM
        if role.identifier == 0:
            continue

        row = html.TR()

        # country name
        col = html.TD()
        col <= html.B(VARIANT_DATA.name_table[role])
        row <= col

        for type_unit in mapping.UnitTypeEnum:

            col = html.TD()

            if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
                draggable_unit = mapping.Army(POSITION_DATA, role, None, None)
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                draggable_unit = mapping.Fleet(POSITION_DATA, role, None, None)

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

        reserve_table <= row

    time_stamp = time.time()
    fake_report_loaded = {'time_stamp': time_stamp, 'content': ""}
    report_window = common.make_report_window(fake_report_loaded)

    display_very_left = html.DIV(id='display_very_left')
    display_very_left.attrs['style'] = 'display: table-cell; width=40px; vertical-align: top; table-layout: fixed;'

    display_very_left <= reserve_table

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Glissez/déposez ces unités sur la carte", Class='instruction')
    display_very_left <= html.BR()

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Pour une situation initiale (ou approchant), aller dans une partie puis cliquer 'exporter vers le bac à sable'", Class='note')
    display_very_left <= html.BR()

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Vous pouvez exporter (bouton 'télécharger cette position') cette carte au format PNG pour vous en servir à titre d'illustration (dans un quizz par exemple)", Class='important')
    display_very_left <= html.BR()

    map_size = VARIANT_DATA.map_size

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

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME_LOADED, INTERFACE_CHOSEN)
    img.bind('load', callback_render)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    helper = html.DIV(".")
    display_left <= helper
    display_left <= canvas

    # need to be one there
    display_left <= html.BR()
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
    buttons_right <= legend_select_unit
    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    stack_orders(buttons_right)
    if not POSITION_DATA.empty():
        put_erase_all(buttons_right)
    put_rest_hold(buttons_right)
    if not ORDERS_DATA.empty():
        put_submit(buttons_right)
    if not POSITION_DATA.empty():
        put_download(buttons_right)
    buttons_right <= html.BR()
    put_checkers(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_very_left
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    MY_PANEL <= html.H2("Le bac à sable : \"what if ?\"")
    MY_PANEL <= my_sub_panel2


def render(panel_middle):
    """ render """

    MY_PANEL.clear()
    panel_middle <= MY_PANEL
    sandbox()
