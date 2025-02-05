""" sandbox """

# pylint: disable=pointless-statement, expression-not-assigned

from json import loads, dumps
from time import time

from browser import html, alert, document, ajax, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import config
import common
import mapping
import interface
import geometry


ARRIVAL = None

# from home
VARIANT_REQUESTED_NAME = None

# from game
VARIANT_NAME = None

# this will come from variant
INTERFACE_CHOSEN = None
VARIANT_DATA = None
POSITION_DATA = None
ORDERS_DATA = None

MY_PANEL = html.DIV()
MY_SUB_PANEL = html.DIV(id="page")
MY_SUB_PANEL.attrs['style'] = 'display: table-row'
MY_PANEL <= MY_SUB_PANEL


def set_arrival(arrival, variant_requested_name=None):
    """ set_arrival """

    global ARRIVAL
    global VARIANT_REQUESTED_NAME

    ARRIVAL = arrival

    if variant_requested_name:
        VARIANT_REQUESTED_NAME = variant_requested_name


class AutomatonStateEnum:
    """ AutomatonStateEnum """

    SELECT_ACTIVE_STATE = 1
    SELECT_ORDER_STATE = 2
    SELECT_PASSIVE_UNIT_STATE = 3
    SELECT_DESTINATION_STATE = 4


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


def create_empty_position():
    """ create_empty_position """

    global INTERFACE_CHOSEN
    global VARIANT_DATA
    global POSITION_DATA
    global ORDERS_DATA

    # from variant name get variant content
    variant_content_loaded = common.game_variant_content_reload(VARIANT_NAME)
    if not variant_content_loaded:
        return

    # selected interface (user choice)
    INTERFACE_CHOSEN = interface.get_interface_from_variant(VARIANT_NAME)

    # from display chose get display parameters
    parameters_read = common.read_parameters(VARIANT_NAME, INTERFACE_CHOSEN)

    # build variant data
    VARIANT_DATA = mapping.Variant(VARIANT_NAME, variant_content_loaded, parameters_read)

    dict_made_units = {}
    dict_made_ownerships = {}

    # get the position
    position_loaded = {'ownerships': dict_made_ownerships, 'units': dict_made_units, 'forbiddens': {}, 'dislodged_ones': {}}

    # digest the position
    POSITION_DATA = mapping.Position(position_loaded, VARIANT_DATA)

    # no orders
    orders_loaded = {'fake_units': {}, 'orders': {}}

    # digest the orders
    ORDERS_DATA = mapping.Orders(orders_loaded, POSITION_DATA, [])


def import_position(incoming_position):
    """ import position from play/position """

    global VARIANT_NAME
    global POSITION_DATA
    global ORDERS_DATA

    VARIANT_NAME = incoming_position.variant.name

    # make sure we are ready
    create_empty_position()

    # get loaded centers for convenience
    loaded_ownerships = incoming_position.save_json2()
    dict_loaded_ownerships = {}
    for loaded_ownership in loaded_ownerships:
        center_num = loaded_ownership['center_num']
        role_num = loaded_ownership['role']
        dict_loaded_ownerships[center_num] = role_num

    # get loaded units
    loaded_units = incoming_position.save_json()
    dict_loaded_units = {}
    for loaded_unit in loaded_units:
        type_num = loaded_unit['type_unit']
        role_num = loaded_unit['role']
        zone_num = loaded_unit['zone']
        if role_num not in dict_loaded_units:
            dict_loaded_units[role_num] = []
        dict_loaded_units[role_num].append([type_num, zone_num])

    # get the position
    position_loaded = {'ownerships': dict_loaded_ownerships, 'units': dict_loaded_units, 'forbiddens': {}, 'dislodged_ones': {}}

    # copy position
    POSITION_DATA = mapping.Position(position_loaded, VARIANT_DATA)

    # no orders
    orders_loaded = {'fake_units': {}, 'orders': {}}

    # digest the orders
    ORDERS_DATA = mapping.Orders(orders_loaded, POSITION_DATA, [])


def sandbox():
    """ sandbox """

    global VARIANT_NAME
    global ARRIVAL

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    selected_hovered_object = None
    automaton_state = None
    buttons_right = None
    report_window = None

    moved_item_id = None

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # to stop catching keyboard
        document.unbind("keypress")

        # complete orders
        ORDERS_DATA.rest_hold(0)

        # update displayed map
        callback_render(False)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not POSITION_DATA.empty():
            put_download(buttons_right)
        if not POSITION_DATA.empty():
            put_erase_all(buttons_right)
        if not ORDERS_DATA.empty():
            put_erase_orders(buttons_right)
        # do not put rest hold
        if not ORDERS_DATA.empty():
            put_submit(buttons_right)
        buttons_right <= html.BR()

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        ORDERS_DATA.erase_orders()

        # erase centers
        POSITION_DATA.erase_centers()

        # erase units
        POSITION_DATA.erase_units()

        # update displayed map
        callback_render(True)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        # do not put erase all
        # do not put erase orders
        # do not put submit
        # do not put download
        buttons_right <= html.BR()

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def erase_orders_callback(_):
        """ erase_orders_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        ORDERS_DATA.erase_orders()

        # update displayed map
        callback_render(True)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not POSITION_DATA.empty():
            put_erase_all(buttons_right)
        # do not put erase orders
        # do not put submit
        # do not put download
        buttons_right <= html.BR()

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def submit_callback(_):
        """ submit_callback """

        def reply_callback(req):
            nonlocal report_window
            req_result = loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission de situation et ordres de simulation : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission de situation et ordres de simulation : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = req_result['msg']
            alert(f"Vous avez soumis les ordres et la situation pour une simulation : {messages}")

            if 'result' in req_result:

                # remove previous
                display_left.removeChild(report_window)

                # put new
                time_stamp_now = time()
                report_txt = req_result['result']
                fake_report_loaded = {'time_stamp': time_stamp_now, 'content': report_txt}
                report_window = common.make_report_window(fake_report_loaded)
                display_left <= report_window

        names_dict = VARIANT_DATA.extract_names()
        names_dict_json = dumps(names_dict)

        orders_list_dict = ORDERS_DATA.save_json()
        orders_list_dict_json = dumps(orders_list_dict)

        # units
        units_list_dict = POSITION_DATA.save_json()
        units_list_dict_json = dumps(units_list_dict)

        # orders
        orders_list_dict = ORDERS_DATA.save_json()
        orders_list_dict_json = dumps(orders_list_dict)

        json_dict = {
            'variant_name': VARIANT_NAME,
            'names': names_dict_json,
            'units': units_list_dict_json,
            'orders': orders_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/simulation"

        # submitting position and orders for simulation : do not need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def download_map_callback(_):
        """ download_callback """

        # make a random like label
        time_stamp_now = time()
        label = int(time_stamp_now) % 1000

        # needed too for some reason
        MY_SUB_PANEL <= html.A(id='download_link')

        # perform actual exportation
        download_link = document['download_link']
        download_link.download = f"diplomania_map_{label}.png"
        download_link.href = canvas.toDataURL('image/png')
        document['download_link'].click()

    def download_situation_callback(_):
        """ download_situation_callback """

        # make a random like label
        time_stamp_now = time()
        label = int(time_stamp_now) % 1000

        # needed too for some reason
        MY_SUB_PANEL <= html.A(id='download_link')

        # perform actual exportation

        # perform actual exportation
        text_file_as_blob = window.Blob.new(["coucou"], {'type': 'text/plain'})
        download_link = document['download_link']
        download_link.download = f"diplomania_position_{label}.json"
        download_link.href = window.URL.createObjectURL(text_file_as_blob)
        document['download_link'].click()

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

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de l'attaque", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée offensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée defensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(POSITION_DATA, order_type, selected_active_unit, None, None, False)
                ORDERS_DATA.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = VARIANT_DATA.order_name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.DIV("Sélectionner l'unité convoyée", Class='instruction')
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            stack_orders(buttons_right)
            if not POSITION_DATA.empty():
                put_download(buttons_right)
            if not POSITION_DATA.empty():
                put_erase_all(buttons_right)
            if not ORDERS_DATA.empty():
                put_erase_orders(buttons_right)
            if not ORDERS_DATA.all_ordered(0):
                put_rest_hold(buttons_right)
            if not ORDERS_DATA.empty():
                put_submit(buttons_right)
            buttons_right <= html.BR()

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_click(event):
        """ called when there is a click down then a click up separated by less than 'LONG_DURATION_LIMIT_SEC' sec """

        nonlocal selected_order_type
        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal selected_passive_unit
        nonlocal selected_dest_zone
        nonlocal buttons_right

        if event.detail != 1:
            # Otherwise confusion click/double-click
            return

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:
            if moved_item_id:
                callback_drop_item(event)
                return

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

                for info in ["(a)ttaquer", "soutenir (o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer"]:
                    legend_select_order22 = html.I(info)
                    buttons_right <= legend_select_order22
                    buttons_right <= html.BR()

                # to catch keyboard
                document.bind("keypress", callback_keypress)

                for order_type in mapping.OrderTypeEnum.inventory():
                    if mapping.OrderTypeEnum.compatible(order_type, mapping.SeasonEnum.AUTUMN_SEASON):
                        input_select = html.INPUT(type="submit", value=VARIANT_DATA.order_name_table[order_type], Class='btn-inside')
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

            stack_orders(buttons_right)
            if not POSITION_DATA.empty():
                put_download(buttons_right)
            if not POSITION_DATA.empty():
                put_erase_all(buttons_right)
            if not ORDERS_DATA.empty():
                put_erase_orders(buttons_right)
            if not ORDERS_DATA.all_ordered(0):
                put_rest_hold(buttons_right)
            if not ORDERS_DATA.empty():
                put_submit(buttons_right)
            buttons_right <= html.BR()

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            # can be None if no retreating unit on board
            if selected_active_unit is not None:
                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                unit_reference_type = mapping.UnitTypeEnum.ARMY_UNIT if isinstance(selected_active_unit, mapping.Army) else mapping.UnitTypeEnum.FLEET_UNIT
            elif selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                unit_reference_type = mapping.UnitTypeEnum.ARMY_UNIT if isinstance(selected_passive_unit, mapping.Army) else mapping.UnitTypeEnum.FLEET_UNIT

            selected_dest_zone = VARIANT_DATA.closest_zone(pos, unit_reference_type)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone.region == selected_active_unit.zone.region:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, None, selected_dest_zone, False)
                ORDERS_DATA.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone, False)
                ORDERS_DATA.insert_order(order)

            # update map
            callback_render(False)

            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
            buttons_right <= legend_select_unit

            stack_orders(buttons_right)
            if not POSITION_DATA.empty():
                put_download(buttons_right)
            if not POSITION_DATA.empty():
                put_erase_all(buttons_right)
            if not ORDERS_DATA.empty():
                put_erase_orders(buttons_right)
            if not ORDERS_DATA.all_ordered(0):
                put_rest_hold(buttons_right)
            if not ORDERS_DATA.empty():
                put_submit(buttons_right)
            buttons_right <= html.BR()

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = POSITION_DATA.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(POSITION_DATA, selected_order_type, selected_active_unit, selected_passive_unit, None, False)
                ORDERS_DATA.insert_order(order)

                # update map
                callback_render(False)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                MY_SUB_PANEL <= my_sub_panel2

                stack_orders(buttons_right)
                if not POSITION_DATA.empty():
                    put_download(buttons_right)
                if not POSITION_DATA.empty():
                    put_erase_all(buttons_right)
                if not ORDERS_DATA.empty():
                    put_erase_orders(buttons_right)
                if not ORDERS_DATA.all_ordered(0):
                    put_rest_hold(buttons_right)
                if not ORDERS_DATA.empty():
                    put_submit(buttons_right)
                buttons_right <= html.BR()

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
            if not POSITION_DATA.empty():
                put_download(buttons_right)
            if not POSITION_DATA.empty():
                put_erase_all(buttons_right)
            if not ORDERS_DATA.empty():
                put_erase_orders(buttons_right)
            if not ORDERS_DATA.all_ordered(0):
                put_rest_hold(buttons_right)
            if not ORDERS_DATA.empty():
                put_submit(buttons_right)
            buttons_right <= html.BR()

            my_sub_panel2 <= buttons_right
            MY_SUB_PANEL <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_canvas_dblclick(event):
        """
        called when there is a double click
        """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_hovered_object

        if event.detail != 2:
            # Otherwise confusion click/double-click
            return

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

        # really nothing to do
        if selected_erase_unit is None:
            return

        # if unit does not have an order... remove unit
        if ORDERS_DATA.is_ordered(selected_erase_unit):

            # remove order
            ORDERS_DATA.remove_order(selected_erase_unit)

        else:

            # remove unit
            POSITION_DATA.remove_unit(selected_erase_unit)

            # tricky
            if selected_hovered_object == selected_erase_unit:
                selected_hovered_object = None

        # update map
        callback_render(True)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not POSITION_DATA.empty():
            put_download(buttons_right)
        if not POSITION_DATA.empty():
            put_erase_all(buttons_right)
        if not ORDERS_DATA.empty():
            put_erase_orders(buttons_right)
        if not ORDERS_DATA.all_ordered(0):
            put_rest_hold(buttons_right)
        if not ORDERS_DATA.empty():
            put_submit(buttons_right)
        buttons_right <= html.BR()

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        nonlocal selected_hovered_object

        prev_selected_hovered_object = selected_hovered_object

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

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
                ORDERS_DATA.render(ctx)

    def callback_canvas_mouse_enter(event):
        """ callback_canvas_mouse_enter """

        nonlocal selected_hovered_object

        helper.clear()

        # find where is mouse
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_hovered_object = POSITION_DATA.closest_object(pos)

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
            ORDERS_DATA.render(ctx)

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
            POSITION_DATA.render(ctx)

            # put the legends
            VARIANT_DATA.render(ctx)

            # save
            save_context(ctx)

        else:

            # restore
            restore_context(ctx)

        # put the orders
        ORDERS_DATA.render(ctx)

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

        input_erase_all = html.INPUT(type="submit", value="Effacer tout", Class='btn-inside')
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_erase_orders(buttons_right):
        """ put_erase_orders """

        input_erase_orders = html.INPUT(type="submit", value="Effacer les ordres", Class='btn-inside')
        input_erase_orders.bind("click", erase_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_orders
        buttons_right <= html.BR()

    def put_rest_hold(buttons_right):
        """ put_rest_hold """

        input_rest_hold = html.INPUT(type="submit", value="Tout le reste tient", Class='btn-inside')
        input_rest_hold.bind("click", rest_hold_callback)
        buttons_right <= html.BR()
        buttons_right <= input_rest_hold
        buttons_right <= html.BR()

    def put_download(buttons_right):
        """ put_download """

        input_export_png = html.INPUT(type="submit", value="Télécharger la carte au format PNG", Class='btn-inside')
        input_export_png.bind("click", download_map_callback)
        buttons_right <= html.BR()
        buttons_right <= input_export_png
        buttons_right <= html.BR()
        input_export_json = html.INPUT(type="submit", value="Télécharger la position format JSON", Class='btn-inside')
        input_export_json.bind("click", download_situation_callback)
        buttons_right <= html.BR()
        buttons_right <= input_export_json
        buttons_right <= html.BR()

    def callback_take_item(event):
        """  take an item (unit or center)  """

        nonlocal moved_item_id

        # Need to be in this state
        if automaton_state != AutomatonStateEnum.SELECT_ACTIVE_STATE:
            return

        # take unit or center
        moved_item_id = event.target.id

    def callback_drop_item(event):
        """  drop an item (unit or center)  """

        nonlocal automaton_state
        nonlocal buttons_right

        nonlocal moved_item_id

        # Need to be in this state
        if automaton_state != AutomatonStateEnum.SELECT_ACTIVE_STATE:
            return

        if moved_item_id in unit_info_table:
            assert moved_item_id is not None
            (type_unit, role) = unit_info_table[moved_item_id]

        # get zone
        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        selected_drop_zone = VARIANT_DATA.closest_zone(pos, type_unit)

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
            # we are not on a specific coast
            if len([z for z in VARIANT_DATA.zones.values() if z.region == selected_drop_region]) > 1:
                # prevent putting fleet on non specific coasts if exists
                if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                    type_unit = mapping.UnitTypeEnum.ARMY_UNIT

        # create unit
        if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
            new_unit = mapping.Army(POSITION_DATA, role, selected_drop_zone, None, False)
        if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
            new_unit = mapping.Fleet(POSITION_DATA, role, selected_drop_zone, None, False)

        # remove previous occupant if applicable
        if selected_drop_region in POSITION_DATA.occupant_table:
            previous_unit = POSITION_DATA.occupant_table[selected_drop_region]
            POSITION_DATA.remove_unit(previous_unit)

            # and the order too
            if ORDERS_DATA.is_ordered(previous_unit):
                ORDERS_DATA.remove_order(previous_unit)

        # add to position
        POSITION_DATA.add_unit(new_unit)

        # Forget about this moved unit
        moved_item_id = None

        # refresh
        # unit added so refresh all
        callback_render(True)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit

        stack_orders(buttons_right)
        if not POSITION_DATA.empty():
            put_download(buttons_right)
        if not POSITION_DATA.empty():
            put_erase_all(buttons_right)
        if not ORDERS_DATA.empty():
            put_erase_orders(buttons_right)
        if not ORDERS_DATA.all_ordered(0):
            put_rest_hold(buttons_right)
        if not ORDERS_DATA.empty():
            put_submit(buttons_right)
        buttons_right <= html.BR()

        my_sub_panel2 <= buttons_right
        MY_SUB_PANEL <= my_sub_panel2

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="Soumettre", Class='btn-inside')
        input_submit.bind("click", submit_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()

    # starts here

    # make sure we have a variant name

    # coming fom a game page
    if ARRIVAL == "play":

        VARIANT_NAME = storage['GAME_VARIANT']
        ARRIVAL = None

    # coming fom a variant page
    elif ARRIVAL == "variant":

        VARIANT_NAME = VARIANT_REQUESTED_NAME
        ARRIVAL = None

    # just arriving
    else:

        if 'GAME_VARIANT' in storage:
            VARIANT_NAME = storage['GAME_VARIANT']
        else:
            VARIANT_NAME = config.FORCED_VARIANT_NAME

        create_empty_position()

    # finds data about the dragged unit
    unit_info_table = {}

    reserve_table = html.TABLE()

    num = 1
    for role in sorted(VARIANT_DATA.roles.values(), key=lambda v: VARIANT_DATA.role_name_table[v]):

        # ignore GM
        if role.identifier == 0:
            continue

        row = html.TR()

        # country name
        col = html.TD()
        col <= html.B(VARIANT_DATA.role_name_table[role])
        row <= col

        for type_unit in mapping.UnitTypeEnum.inventory():

            col = html.TD()

            if type_unit is mapping.UnitTypeEnum.ARMY_UNIT:
                pickable_unit = mapping.Army(POSITION_DATA, role, None, None, False)
            if type_unit is mapping.UnitTypeEnum.FLEET_UNIT:
                pickable_unit = mapping.Fleet(POSITION_DATA, role, None, None, False)

            identifier = f"unit_{num}"
            unit_canvas = html.CANVAS(id=identifier, width=32, height=32, alt="Cliquez-moi dessus !")
            unit_info_table[identifier] = (type_unit, role)
            num += 1

            unit_canvas.bind("click", callback_take_item)

            ctx2 = unit_canvas.getContext("2d")
            pickable_unit.render(ctx2)

            col <= unit_canvas
            row <= col

        reserve_table <= row

    time_stamp_now = time()
    fake_report_loaded = {'time_stamp': time_stamp_now, 'content': ""}
    report_window = common.make_report_window(fake_report_loaded)

    display_very_left = html.DIV(id='display_very_left')
    display_very_left.attrs['style'] = 'display: table-cell; width=40px; vertical-align: top; table-layout: fixed;'

    display_very_left <= reserve_table

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Cliquez sur une de ces unités, *puis* sur la carte", Class='instruction')
    display_very_left <= html.BR()

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Pour avoir la situation d'une partie, aller dans la partie puis cliquer 'exporter vers le bac à sable'", Class='instruction')
    display_very_left <= html.BR()

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Pour tester une autre variante, sélectionnez une partie de la variante en question au préalable", Class='important')
    display_very_left <= html.BR()

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Le but du bac à sable est uniquement de lever les ambigüités sur la résolution des mouvements, il n'y a donc pas de continuité sur les phases suivantes...", Class='note')
    display_very_left <= html.BR()

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Vous pouvez exporter cette position pour vous en servir à titre d'illustration", Class='note')
    display_very_left <= html.BR()

    map_size = VARIANT_DATA.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # click and double click
    canvas.bind("click", callback_canvas_click)
    canvas.bind("dblclick", callback_canvas_dblclick)

    # hovering effect
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseenter", callback_canvas_mouse_enter)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(VARIANT_NAME, INTERFACE_CHOSEN)
    img.bind('load', lambda _: callback_render(True))

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    helper = html.DIV(Class='helper')
    display_left <= helper

    # need to be one there
    display_left <= html.BR()
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (double-clic sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
    buttons_right <= legend_select_unit
    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    stack_orders(buttons_right)
    if not POSITION_DATA.empty():
        put_download(buttons_right)
    if not POSITION_DATA.empty():
        put_erase_all(buttons_right)
    if not ORDERS_DATA.empty():
        put_erase_orders(buttons_right)
    if not ORDERS_DATA.all_ordered(0):
        put_rest_hold(buttons_right)
    if not ORDERS_DATA.empty():
        put_submit(buttons_right)
    buttons_right <= html.BR()

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_very_left
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    MY_SUB_PANEL <= html.H2(f"Le bac à sable (variante {VARIANT_NAME})")
    MY_SUB_PANEL <= my_sub_panel2


PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global PANEL_MIDDLE
    PANEL_MIDDLE = panel_middle

    MY_SUB_PANEL.clear()
    sandbox()
    panel_middle <= MY_SUB_PANEL
