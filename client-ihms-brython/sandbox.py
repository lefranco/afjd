""" master """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import enum
import time

from browser import document, html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error

import config
import common
import tools
import geometry
import mapping
import oracle
import index  # circular import

LONG_DURATION_LIMIT_SEC = 1.0

VARIANT_NAME = "standard"

my_panel = html.DIV(id="sandbox")
my_panel.attrs['style'] = 'display: table'

# TODO : remove this sub_panel
my_sub_panel = html.DIV(id="sub")
my_panel <= my_sub_panel

initial_orders = {'fake_units': dict(), 'orders': dict(), }


@enum.unique
class AutomatonStateEnum(enum.Enum):
    """ AutomatonStateEnum """

    IDLE_STATE = enum.auto()
    SELECT_ACTIVE_STATE = enum.auto()
    SELECT_ORDER_STATE = enum.auto()
    SELECT_PASSIVE_UNIT_STATE = enum.auto()
    SELECT_DESTINATION_STATE = enum.auto()


# this will not change
variant_name_loaded = VARIANT_NAME  # pylint: disable=invalid-name

# this will
display_chosen = None  # pylint: disable=invalid-name
variant_data = None  # pylint: disable=invalid-name
position_data = None  # pylint: disable=invalid-name
orders_data = None  # pylint: disable=invalid-name


def create_initial_position():
    """ create_initial_position """

    global display_chosen  # pylint: disable=invalid-name
    global variant_data  # pylint: disable=invalid-name
    global position_data  # pylint: disable=invalid-name
    global orders_data  # pylint: disable=invalid-name

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # selected display (user choice)
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    # get the position
    position_loaded = {'ownerships': dict(), 'units': dict(), 'forbiddens': dict(), 'dislodged_ones': dict()}

    # digest the position
    position_data = mapping.Position(position_loaded, variant_data)

    # get the orders from server
    orders_loaded = initial_orders

    # digest the orders
    orders_data = mapping.Orders(orders_loaded, position_data)


def import_position(new_position_data):
    """ import position from play/position """

    global position_data  # pylint: disable=invalid-name
    global orders_data  # pylint: disable=invalid-name

    # make sure we are ready
    if not position_data:
        create_initial_position()

    # get loaded units
    loaded_units = new_position_data.save_json()
    dict_loaded_units = dict()
    for loaded_unit in loaded_units:
        type_num = loaded_unit['type_unit']
        role_num = loaded_unit['role']
        zone_num = loaded_unit['zone']
        if role_num not in dict_loaded_units:
            dict_loaded_units[role_num] = list()
        dict_loaded_units[role_num].append([type_num, zone_num])

    # get loaded centers for convenience
    loaded_ownerships = new_position_data.save_json2()
    dict_loaded_ownerships = dict()
    for loaded_ownership in loaded_ownerships:
        center_num = loaded_ownership['center_num']
        role_num = loaded_ownership['role']
        dict_loaded_ownerships[center_num] = role_num

    # get the position
    position_imported = {'ownerships': dict_loaded_ownerships, 'units': dict_loaded_units, 'forbiddens': dict(), 'dislodged_ones': dict()}

    # copy position
    position_data = mapping.Position(position_imported, variant_data)

    # get the orders from server
    orders_loaded = initial_orders

    # digest the orders
    orders_data = mapping.Orders(orders_loaded, position_data)


def sandbox():
    """ sandbox """

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    automaton_state = None

    stored_event = None
    down_click_time = None

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # complete orders
        orders_data.rest_hold(None)

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)

        if not orders_data.empty():
            put_erase_all(buttons_right)
        # do not put all rest hold
        if not orders_data.empty():
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        orders_data.erase_orders()

        # erase units
        position_data.erase_units()

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
        if not orders_data.empty():
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

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
                report_loaded = req_result['result']
                report_window = common.make_report_window(report_loaded)
                display_left <= report_window

        variant_name = variant_name_loaded

        names_dict = variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        # units
        units_list_dict = position_data.save_json()
        units_list_dict_json = json.dumps(units_list_dict)

        # orders
        orders_list_dict = orders_data.save_json()
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

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.DIV("Sélectionner la destination de l'attaque", Class='instruction')
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée offensivement (cliquer sous la légende)", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.DIV("Sélectionner l'unité supportée defensivement", Class='instruction')
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(position_data, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.DIV(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.DIV("Sélectionner l'unité convoyée", Class='instruction')
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            stack_orders(buttons_right)
            if not position_data.empty():
                put_erase_all(buttons_right)
            put_rest_hold(buttons_right)
            if not orders_data.empty():
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

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

            selected_active_unit = position_data.closest_unit(pos, False)

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

                for info in ["(a)ttaquer", "soutenir(o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer", "(x)supprimer l'ordre/l'unité"]:
                    legend_select_order22 = html.I(info)
                    buttons_right <= legend_select_order22
                    buttons_right <= html.BR()

                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(mapping.SeasonEnum.AUTUMN_SEASON):
                        input_select = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

            stack_orders(buttons_right)
            if not position_data.empty():
                put_erase_all(buttons_right)
            put_rest_hold(buttons_right)
            if not orders_data.empty():
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            # can be None if no retreating unit on board
            if selected_active_unit is not None:
                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            selected_dest_zone = variant_data.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone)
                orders_data.insert_order(order)

            # update map
            callback_render(None)

            legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
            buttons_right <= legend_select_unit

            stack_orders(buttons_right)
            if not position_data.empty():
                put_erase_all(buttons_right)
            put_rest_hold(buttons_right)
            if not orders_data.empty():
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = position_data.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, selected_passive_unit, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                stack_orders(buttons_right)
                if not position_data.empty():
                    put_erase_all(buttons_right)
                put_rest_hold(buttons_right)
                if not orders_data.empty():
                    put_submit(buttons_right)

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
            if not position_data.empty():
                put_erase_all(buttons_right)
            put_rest_hold(buttons_right)
            if not orders_data.empty():
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_canvas_long_click(event):
        """
        called when there is a click down then a click up separated by more than 'LONG_DURATION_LIMIT_SEC' sec
        or when pressing 'x' in which case a None is passed
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
            selected_erase_unit = position_data.closest_unit(pos, False)

        # event is None when coming from x pressed, then take 'selected_active_unit' (that can be None)
        if selected_erase_unit is None:
            selected_erase_unit = selected_active_unit

        # unit must be selected
        if selected_erase_unit is None:
            return

        # if unit does not have an order... remove unit
        if not orders_data.is_ordered(selected_erase_unit):

            # remove unit
            position_data.remove_unit(selected_erase_unit)

        else:

            # remove order
            orders_data.remove_order(selected_erase_unit)

        # update map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not position_data.empty():
            put_erase_all(buttons_right)
        put_rest_hold(buttons_right)
        if not orders_data.empty():
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

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

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        variant_data.render(ctx)

        # put the position
        position_data.render(ctx)

        # put the orders
        orders_data.render(ctx)

        # put the legends at the end
        variant_data.render_legends(ctx)

    def stack_orders(buttons_right):
        """ stack_orders """

        buttons_right <= html.P()
        lines = str(orders_data).split('\n')
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

            # and the order too
            if orders_data.is_ordered(previous_unit):
                orders_data.remove_order(previous_unit)

        # add to position
        position_data.add_unit(new_unit)

        # refresh
        callback_render(ctx)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        legend_select_unit = html.DIV("Cliquez sur l'unité à ordonner (clic-long sur un ordre/unité sans ordre pour l'effacer)", Class='instruction')
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not position_data.empty():
            put_erase_all(buttons_right)
        put_rest_hold(buttons_right)
        if not orders_data.empty():
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

    def callback_export_oracle(_):
        """ callback_export_oracle """

        # action on importing game
        oracle.import_position(position_data)

        # action of going to sandbox page
        index.load_option(None, 'oracle')

    # starts here

    # make sure we are ready
    if not position_data:
        create_initial_position()

    # finds data about the dragged unit
    unit_info_table = dict()

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

        reserve_table <= row

    report_window = common.make_report_window("")

    display_very_left = html.DIV(id='display_very_left')
    display_very_left.attrs['style'] = 'display: table-cell; width=40px; vertical-align: top; table-layout: fixed;'

    display_very_left <= reserve_table

    display_very_left <= html.BR()
    display_very_left <= html.DIV("Glissez/déposez ces unités sur la carte", Class='instruction')
    display_very_left <= html.BR()

    input_export_sandbox = html.INPUT(type="submit", value="exporter vers l'oracle")
    input_export_sandbox.bind("click", callback_export_oracle)
    display_very_left <= input_export_sandbox

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

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(variant_name_loaded, display_chosen)
    img.bind('load', callback_render)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

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
    if not position_data.empty():
        put_erase_all(buttons_right)
    put_rest_hold(buttons_right)
    if not orders_data.empty():
        put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_very_left
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= html.H2("Le bac à sable : \"what if ?\"")
    my_sub_panel <= my_sub_panel2


def render(panel_middle):
    """ render """

    my_sub_panel.clear()
    panel_middle <= my_panel
    sandbox()
