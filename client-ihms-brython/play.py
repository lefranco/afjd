""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import enum

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import geometry
import mapping

DIPLOMACY_SEASON_CYCLE = [1, 2, 1, 2, 3]

OPTIONS = ['game status', 'game position', 'submit orders', 'negotiate', 'game master', 'all game parameters', 'players in game']

my_panel = html.DIV(id="play")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel


@enum.unique
class AutomatonStateEnum(enum.Enum):
    """ AutomatonStateEnum """

    SELECT_ACTIVE_STATE = enum.auto()
    SELECT_ORDER_STATE = enum.auto()
    SELECT_PASSIVE_UNIT_STATE = enum.auto()
    SELECT_DESTINATION_STATE = enum.auto()
    SELECT_BUILD_UNIT_TYPE_STATE = enum.auto()


def get_role_allocated_to_player(game_id, player_id):
    """ get_role the player has in the game """

    role_id = None

    def reply_callback(req):
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting role allocated to player: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting role allocated to player: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return
        req_result = json.loads(req.text)
        nonlocal role_id
        # TODO : consider if ap player has more than one role
        role_id = req_result[str(player_id)] if str(player_id) in req_result else None

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-allocations/{game_id}"

    # get players allocated to game : do not need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return role_id


def make_report_window(report_loaded):
    """ make_report_window """

    lines = report_loaded.split('\n')
    split_size = (len(lines) + 3) // 3
    report_table = html.TABLE()
    report_table.style = {
        "border": "solid",
    }
    report_row = html.TR()
    report_row.style = {
        "border": "solid",
    }
    report_table <= report_row
    for chunk_num in range(3):
        report_col = html.TD()
        report_col.style = {
            "border": "solid",
        }
        chunk_content = lines[chunk_num * split_size: (chunk_num + 1) * split_size]
        for line in chunk_content:
            report_col <= line
            report_col <= html.BR()
        report_row <= report_col
    return report_table


def get_display_from_variant(variant):
    """ get_display_from_variant """

    # TODO : make it possible to choose which display users wants (descartes/hasbro)
    # At least test it
    assert variant == 'standard'
    return "stabbeur"


def get_season(advancement, variant) -> None:
    """ store season """

    len_season_cycle = len(DIPLOMACY_SEASON_CYCLE)
    advancement_season_num = advancement % len_season_cycle + 1
    advancement_season = mapping.SeasonEnum.from_code(advancement_season_num)
    advancement_year = (advancement // len_season_cycle) + 1 + variant.year_zero
    return advancement_season, advancement_year


def show_status():
    """ show_status """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # select display (should be a user choice)
    display_chosen = get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters

    parameters_file_name = f"./variants/{variant_name_loaded}/{display_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file:
        parameters_read = json.load(read_file)

    # build variant data
    variant_data = mapping.Variant(variant_content_loaded, parameters_read)

    game_parameters_loaded = common.game_parameters_reload(game)
    if not game_parameters_loaded:
        return

    # just to prevent a erroneous pylint warning
    game_parameters_loaded = dict(game_parameters_loaded)

    game_params_table = html.TABLE()
    game_params_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }
    for key in ['name', 'description', 'variant', 'current_state', 'current_advancement', 'deadline']:
        row = html.TR()
        row.style = {
            "border": "solid",
        }

        col1 = html.TD(key)
        col1.style = {
            "border": "solid",
        }
        row <= col1

        if key == 'name':
            value = game_parameters_loaded[key]

        if key == 'description':
            value = game_parameters_loaded[key]

        if key == 'variant':
            value = game_parameters_loaded[key]

        if key == 'current_state':
            state_loaded = game_parameters_loaded[key]
            for possible_state in config.STATE_CODE_TABLE:
                if config.STATE_CODE_TABLE[possible_state] == state_loaded:
                    state_readable = possible_state
                    break
            value = state_readable

        if key == 'current_advancement':
            advancement_loaded = game_parameters_loaded[key]
            advancement_season, advancement_year = get_season(advancement_loaded, variant_data)
            advancement_season_readable = variant_data.name_table[advancement_season]
            value = f"Season : {advancement_season_readable} {advancement_year}"

        if key == 'deadline':
            deadline_loaded = game_parameters_loaded[key]
            datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
            deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
            deadline_loaded_hour = f"{datetime_deadline_loaded.hour}:{datetime_deadline_loaded.minute}"
            deadline_readable = f"{deadline_loaded_day} {deadline_loaded_hour}"
            value = f"Deadline : {deadline_readable} GMT time"

        col2 = html.TD(value)
        col2.style = {
            "border": "solid",
        }
        row <= col2

        game_params_table <= row

    my_sub_panel <= game_params_table


def show_position():
    """ show_position """

    variant_name_loaded = None
    variant_content_loaded = None
    variant_data = None
    position_loaded = None
    position_data = None

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the legends
        variant_data.render(ctx)

        # put the position
        position_data.render(ctx)

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # select display (should be a user choice)
    display_chosen = get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters

    parameters_file_name = f"./variants/{variant_name_loaded}/{display_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file:
        parameters_read = json.load(read_file)

    # build variant data
    variant_data = mapping.Variant(variant_content_loaded, parameters_read)

    # get the position from server
    position_loaded = common.game_position_reload(game)
    if not position_loaded:
        return

    # digest the position
    position_data = mapping.Position(position_loaded, variant_data)

    # now we can display

    map_size = variant_data.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Please use a more recent navigator")
        return

    # put background (this will call the callback that display the whole map)
    img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/map.png")
    img.bind('load', callback_render)

    my_sub_panel <= canvas

    report_loaded = common.game_report_reload(game)
    if report_loaded is None:
        return

    report_window = make_report_window(report_loaded)
    my_sub_panel <= report_window


def submit_orders():
    """ submit_orders """

    variant_name_loaded = None
    variant_content_loaded = None
    variant_data = None
    position_loaded = None
    position_data = None

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    selected_build_unit_type = None
    selected_build_zone = None
    automaton_state = None

    def submit_orders_callback(_):
        """ submit_orders_callback """

        #  print("submit_orders_callback")

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error submitting orders: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem submitting orders: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Orders submitted : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        names_dict = variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': pseudo,
            'orders': orders_list_dict_json,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-orders/{game_id}"

        # submitting orders : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def select_built_unit_type_callback(_, build_unit_type):
        """ select_built_unit_type_callback """

        #  print("select_built_unit_type_callback")

        nonlocal selected_build_unit_type
        nonlocal automaton_state
        nonlocal buttons_right

        if automaton_state == AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE:

            selected_build_unit_type = build_unit_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            legend_select_active = html.LEGEND("Select zone where to build")
            buttons_right <= legend_select_active

            stack_orders(buttons_right)
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            # it is a zone we need now
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        #  print("select_order_type_callback")

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"Selected order is {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Select destination of attack")
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"Selected order is {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.LEGEND("Select offensively suported unit")
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"Selected order is {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.LEGEND("Select defensively supported unit")
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(position_data, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Click on unit to order (double-click to erase)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"Selected order is {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.LEGEND("Select convoyed unit")
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"Selected order is {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Select destination of retreat")
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.DISBAND_ORDER:

                # insert disband order
                order = mapping.Order(position_data, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Click on unit to order (double-click to erase)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:

                legend_select_active = html.LEGEND("Select unit type to build")
                buttons_right <= legend_select_active

                for unit_type in mapping.UnitTypeEnum:
                    input_debug = html.INPUT(type="submit", value=variant_data.name_table[unit_type])
                    input_debug.bind("click", lambda e, u=unit_type: select_built_unit_type_callback(e, u))
                    buttons_right <= html.BR()
                    buttons_right <= input_debug

                automaton_state = AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE

            if selected_order_type is mapping.OrderTypeEnum.REMOVE_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"Selected order is {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_active = html.LEGEND("Select unit to remove")
                buttons_right <= legend_select_active

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            stack_orders(buttons_right)
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

    def callback_click(event):
        """ callback_click """

        #  print("callback_click")

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal selected_passive_unit
        nonlocal selected_dest_zone
        nonlocal selected_build_zone
        nonlocal buttons_right

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_active_unit = position_data.closest_unit(pos, False)
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_active_unit = position_data.closest_unit(pos, True)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:

                legend_selected_unit = html.LEGEND(f"Selected active unit is {selected_active_unit}")
                buttons_right <= legend_selected_unit

            legend_select_order = html.LEGEND("Select order")
            buttons_right <= legend_select_order

            for order_type in mapping.OrderTypeEnum:
                if order_type.compatible(advancement_season):
                    input_debug = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                    input_debug.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_debug

            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

            stack_orders(buttons_right)
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE
            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_dest_zone = variant_data.closest_zone(pos)
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                selected_build_zone = variant_data.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:
                # create fake unit
                region = selected_build_zone.region
                center = region.center
                if center is not None:
                    deducted_role = center.owner_start
                    if deducted_role is not None:
                        if selected_build_unit_type is mapping.UnitTypeEnum.ARMY_UNIT:
                            fake_unit = mapping.Army(position_data, deducted_role, selected_build_zone, None)
                        if selected_build_unit_type is mapping.UnitTypeEnum.FLEET_UNIT:
                            fake_unit = mapping.Fleet(position_data, deducted_role, selected_build_zone, None)
                        # create order
                        order = mapping.Order(position_data, selected_order_type, fake_unit, None, None)
                        orders_data.insert_order(order)
                    else:
                        alert("No one can build on that center")
                else:
                    alert("No center there")

            # update map
            callback_render(None)

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                legend_select_unit = html.LEGEND("Click on unit to order (double-click to erase)")
                buttons_right <= legend_select_unit
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                legend_select_unit = html.LEGEND("Select order")
                buttons_right <= legend_select_unit
                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(advancement_season):
                        input_debug = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                        input_debug.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_debug

            stack_orders(buttons_right)
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = position_data.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, selected_passive_unit, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Click on unit to order (double-click to erase)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                stack_orders(buttons_right)
                put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.LEGEND(f"Selected offensively supported unit is {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.LEGEND(f"Selected convoyed unit is {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.LEGEND("Select destination of supported attack")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.LEGEND("Select destination of convoy")
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_dblclick(event):
        """ callback_dblclick """

        #  print("callback_dblclick")

        nonlocal automaton_state

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        nonlocal buttons_right

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
            selected_erase_unit = position_data.closest_unit(pos, False)
        if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            selected_erase_unit = position_data.closest_unit(pos, True)

        # remove order
        orders_data.remove_order(selected_erase_unit)

        # update map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.LEGEND("Click on unit to order (double-click to erase)")
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.LEGEND("Select order")
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum:
                if order_type.compatible(advancement_season):
                    input_debug = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                    input_debug.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_debug
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)
        put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the legends
        variant_data.render(ctx)

        # put the position
        position_data.render(ctx)

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

    def put_submit(buttons_right):
        """ put_submit """

        if not orders_data.empty():
            input_submit = html.INPUT(type="submit", value="submit these orders")
            input_submit.bind("click", submit_orders_callback)
            buttons_right <= html.BR()
            buttons_right <= input_submit

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    # from game name get game id

    game_id = common.get_game_id(game)
    if game_id is None:
        return

    # from pseudo get player id

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        return

    # from game id and player id get role_id of player

    role_id = get_role_allocated_to_player(game_id, player_id)
    if role_id is None:
        alert("You do not appear to play or master this game")
        return

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # select display (should be a user choice)
    display_chosen = get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters

    parameters_file_name = f"./variants/{variant_name_loaded}/{display_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file:
        parameters_read = json.load(read_file)

    # build variant data
    variant_data = mapping.Variant(variant_content_loaded, parameters_read)

    game_parameters_loaded = common.game_parameters_reload(game)
    if not game_parameters_loaded:
        return

    # just to prevent a erroneous pylint warning
    game_parameters_loaded = dict(game_parameters_loaded)

    advancement_loaded = game_parameters_loaded['current_advancement']
    advancement_season, _ = get_season(advancement_loaded, variant_data)

    # get the position from server
    position_loaded = common.game_position_reload(game)
    if not position_loaded:
        return

    # digest the position
    position_data = mapping.Position(position_loaded, variant_data)

    # now we can display

    map_size = variant_data.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    canvas.bind("click", callback_click)
    canvas.bind("dblclick", callback_dblclick)

    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Please use a more recent navigator")
        return

    # get the orders from server
    orders_loaded = common.game_orders_reload(game)
    if not orders_loaded:
        return

    # digest the orders
    orders_data = mapping.Orders(orders_loaded, position_data)

    # put background (this will call the callback that display the whole map)
    img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/map.png")
    img.bind('load', callback_render)

    report_loaded = common.game_report_reload(game)
    if report_loaded is None:
        return

    report_window = make_report_window(report_loaded)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; vertical-align: top;'

    display_left <= canvas
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        legend_select_unit = html.LEGEND("Click on unit to order (double-click to erase)")
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        legend_select_order = html.LEGEND("Select order")
        buttons_right <= legend_select_order
        for order_type in mapping.OrderTypeEnum:
            if order_type.compatible(advancement_season):
                input_debug = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                input_debug.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                buttons_right <= html.BR()
                buttons_right <= input_debug
        automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

    stack_orders(buttons_right)
    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= my_sub_panel2


def negotiate():
    """ negotiate """

    dummy = html.P("Sorry, negotiate is not implemented here yet...")
    my_sub_panel <= dummy


def game_master():
    """ game_master """

    def adjudicate_callback(_):
        """ adjudicate_callback """

        #  print("adjudicate_callback")

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error adjudicating: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem adjudicating: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Adjudication performed submitted : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        names_dict = variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'pseudo': pseudo,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-adjudications/{game_id}"

        # asking adjudication : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    # from game name get game id

    game_id = common.get_game_id(game)
    if game_id is None:
        return

    # from pseudo get player id

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        return

    # from game id and player id get role_id of player

    role_id = get_role_allocated_to_player(game_id, player_id)
    if role_id != 0:
        alert("You do not appear master this game")
        return

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # select display (should be a user choice)
    display_chosen = get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters

    parameters_file_name = f"./variants/{variant_name_loaded}/{display_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file:
        parameters_read = json.load(read_file)

    # build variant data
    variant_data = mapping.Variant(variant_content_loaded, parameters_read)

    input_adjudicate = html.INPUT(type="submit", value="adjudicate now!")
    input_adjudicate.bind("click", adjudicate_callback)
    my_sub_panel <= input_adjudicate


def show_game_parameters():
    """ show_game_parameters """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    game_parameters_loaded = common.game_parameters_reload(game)
    if not game_parameters_loaded:
        return

    game_params_table = html.TABLE()
    game_params_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }
    for key, value in game_parameters_loaded.items():
        row = html.TR()
        row.style = {
            "border": "solid",
        }

        col1 = html.TD(key)
        col1.style = {
            "border": "solid",
        }
        row <= col1

        if key in ['description', 'variant', 'deadline', 'current_state', 'current_advancement']:
            continue

        col2 = html.TD(value)
        col2.style = {
            "border": "solid",
        }
        row <= col2

        game_params_table <= row

    my_sub_panel <= game_params_table


def get_game_players_data(game_id):
    """ get_game_players_data """

    game_players_dict = None

    def reply_callback(req):
        nonlocal game_players_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting game/game players list: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting game/game players list: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        req_result = json.loads(req.text)
        game_players_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-allocations/{game_id}"

    # getting game allocation : do not need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return game_players_dict


def show_players_in_game():
    """ show_game_players_data """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # select display (should be a user choice)
    display_chosen = get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters

    parameters_file_name = f"./variants/{variant_name_loaded}/{display_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file:
        parameters_read = json.load(read_file)

    # build variant data
    variant_data = mapping.Variant(variant_content_loaded, parameters_read)

    # game id now
    game_id = common.get_game_id(game)
    if game_id is None:
        return

    # get the players of the game
    game_players_dict = get_game_players_data(game_id)

    if not game_players_dict:
        return

    # get the players (all players)
    players_dict = common.get_players()

    if not players_dict:
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    game_players_table = html.TABLE()
    game_players_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    # TODO : make it possible to sort etc...
    fields = ['player', 'role', 'flag']

    # header
    thead = html.THEAD()
    for field in fields:
        col = html.TD(field)
        col.style = {
            "border": "solid",
            "font-weight": "bold",
        }
        thead <= col
    game_players_table <= thead

    for player_id_str, role_id in game_players_dict.items():
        row = html.TR()
        row.style = {
            "border": "solid",
        }

        # player
        player_id = int(player_id_str)
        pseudo = id2pseudo[player_id]
        col = html.TD(pseudo)
        col.style = {
            "border": "solid",
        }
        row <= col

        # role name
        if role_id == -1:
            role_name = "NOT ALLOCATED"
        else:
            role = variant_data.roles[role_id]
            role_name = variant_data.name_table[role]

        col = html.TD(role_name)
        col.style = {
            "border": "solid",
        }
        row <= col

        # role flag
        if role_id == -1:
            role_icon_img = None
        elif role_id == 0:
            role_icon_img = None
        else:
            role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg")

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        col.style = {
            "border": "solid",
        }
        row <= col

        game_players_table <= row

    my_sub_panel <= game_players_table


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'game status':
        show_status()
    if item_name == 'game position':
        show_position()
    if item_name == 'submit orders':
        submit_orders()
    if item_name == 'negotiate':
        negotiate()
    if item_name == 'game master':
        game_master()
    if item_name == 'all game parameters':
        show_game_parameters()
    if item_name == 'players in game':
        show_players_in_game()

    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not)
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


def render(panel_middle):
    """ render """

    load_option(None, item_name_selected)
    panel_middle <= my_panel
