""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import enum

from browser import document, html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import geometry
import mapping
import login


OPTIONS = ['position', 'ordonner', 'négocier', 'déclarer', 'voter', 'arbitrer', 'paramètres', 'joueurs', 'historique']

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

    IDLE_STATE = enum.auto()
    SELECT_ACTIVE_STATE = enum.auto()
    SELECT_ORDER_STATE = enum.auto()
    SELECT_PASSIVE_UNIT_STATE = enum.auto()
    SELECT_DESTINATION_STATE = enum.auto()
    SELECT_BUILD_UNIT_TYPE_STATE = enum.auto()


def make_rating_colours_window(ratings, colours):
    """ make_rating_window """

    rating_table = html.TABLE()
    rating_table.style = {
        "border": "solid",
    }
    rating_row = html.TR()
    rating_row.style = {
        "border": "solid",
    }
    rating_table <= rating_row
    for role_name, ncenters in ratings.items():
        rating_col = html.TD()
        rating_col.style = {
            "border": "solid",
        }

        canvas = html.CANVAS(id="rect", width=15, height=15, alt=role_name)
        ctx = canvas.getContext("2d")

        colour = colours[role_name]

        outline_colour = colour.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.rect(0, 0, 14, 14)
        ctx.stroke()
        ctx.closePath()  # no fill

        ctx.fillStyle = colour.str_value()
        ctx.fillRect(1, 1, 13, 13)

        rating_col <= canvas
        rating_col <= f"{role_name} {ncenters}"
        rating_row <= rating_col

    return rating_table


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
            if line.find("(échec)") != -1 or line.find("(coupé)") != -1 or line.find("(délogée)") != -1 or line.find("(détruite)") != -1 or line.find("(invalide)") != -1:
                report_col <= html.B(html.CODE(line, style={'color': 'red'}))
            elif line.find(":") != -1:
                report_col <= html.B(html.CODE(line, style={'color': 'blue'}))
            else:
                report_col <= html.B(html.CODE(line, style={'color': 'black'}))
            report_col <= html.BR()
        report_row <= report_col
    return report_table


def get_game_status(variant_data, game_parameters_loaded, full):
    """ get_game__status """

    game_name = game_parameters_loaded['name']
    game_description = game_parameters_loaded['description']
    game_variant = game_parameters_loaded['variant']

    state_loaded = game_parameters_loaded['current_state']
    for possible_state in config.STATE_CODE_TABLE:
        if config.STATE_CODE_TABLE[possible_state] == state_loaded:
            game_state_readable = possible_state
            break

    advancement_loaded = game_parameters_loaded['current_advancement']
    advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
    advancement_season_readable = variant_data.name_table[advancement_season]
    game_season = f"{advancement_season_readable} {advancement_year}"

    deadline_loaded = game_parameters_loaded['deadline']
    datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
    deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
    deadline_loaded_hour = f"{datetime_deadline_loaded.hour}:{datetime_deadline_loaded.minute}"
    game_deadline = f"{deadline_loaded_day} {deadline_loaded_hour}"

    game_status_table = html.TABLE()
    game_status_table.style = {
        "border": "solid",
    }

    row = html.TR()
    row.style = {
        "border": "solid",
    }

    col = html.TD(f"Partie {game_name} ({game_variant})")
    col.style = {
        "border": "solid",
    }
    row <= col
    if full:
        col = html.TD(f"Etat {game_state_readable}")
        col.style = {
            "border": "solid",
        }
        row <= col
    col = html.TD(f"Saison {game_season}")
    col.style = {
        "border": "solid",
    }
    row <= col
    col = html.TD(f"DL {game_deadline} GMT")
    col.style = {
        "border": "solid",
    }
    row <= col
    game_status_table <= row

    if full:
        row = html.TR()
        row.style = {
            "border": "solid",
        }

        col = html.TD(game_description, colspan="4")
        col.style = {
            "border": "solid",
        }
        row <= col
        game_status_table <= row

    return game_status_table


def get_game_status_histo(variant_data, game_parameters_loaded, advancement_selected):
    """ get_game_status_histo """

    advancement_selected_season, advancement_selected_year = common.get_season(advancement_selected, variant_data)
    advancement_selected_season_readable = variant_data.name_table[advancement_selected_season]

    game_name = game_parameters_loaded['name']
    game_variant = game_parameters_loaded['variant']
    game_season = f"{advancement_selected_season_readable} {advancement_selected_year}"

    game_status_table = html.TABLE()
    game_status_table.style = {
        "border": "solid",
    }

    row = html.TR()
    row.style = {
        "border": "solid",
    }

    col = html.TD(f"Partie {game_name} ({game_variant})")
    col.style = {
        "border": "solid",
    }
    row <= col
    col = html.TD(f"Saison {game_season}")
    col.style = {
        "border": "solid",
    }
    row <= col

    game_status_table <= row
    return game_status_table


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
        alert("Il faut choisir la partie au préalable")
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
    display_chosen = common.get_display_from_variant(variant_name_loaded)

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

    game_parameters_loaded = common.game_parameters_reload(game)
    if not game_parameters_loaded:
        return

    # just to prevent a erroneous pylint warning
    game_parameters_loaded = dict(game_parameters_loaded)

    game_status = get_game_status(variant_data, game_parameters_loaded, True)
    my_sub_panel <= game_status

    # digest the position
    position_data = mapping.Position(position_loaded, variant_data)

    # now we can display

    map_size = variant_data.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # put background (this will call the callback that display the whole map)
    img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/map.png")
    img.bind('load', callback_render)

    my_sub_panel <= canvas

    ratings = position_data.role_ratings()
    colours = position_data.role_colours()
    rating_colours_window = make_rating_colours_window(ratings, colours)

    report_loaded = common.game_report_reload(game)
    if report_loaded is None:
        return

    report_window = make_report_window(report_loaded)

    my_sub_panel <= rating_colours_window
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

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # just a check
        assert advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]

        # complete orders
        orders_data.rest_hold(role_id if role_id != 0 else None)

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

        stack_role_flag(buttons_right)

        # we are in spring or autumn
        legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
        buttons_right <= legend_select_unit

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

        stack_orders(buttons_right)

        if not orders_data.empty():
            put_erase_all(buttons_right)
        # do not put all hold
        if not orders_data.empty():
            put_submit(buttons_right)

        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    def erase_all_callback(_):
        """ erase_all_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # erase orders
        orders_data.erase_orders()

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

        stack_role_flag(buttons_right)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            if position_data.has_dislodged():
                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
                buttons_right <= legend_select_unit
                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
            else:
                automaton_state = AutomatonStateEnum.IDLE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.LEGEND("Sélectionner l'ordre d'adjustement")
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum:
                if order_type.compatible(advancement_season):
                    input_select = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)

        # do not put erase all
        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty():
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

    def submit_orders_callback(_):
        """ submit_orders_callback """

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
            InfoDialog("OK", f"Vous avez soumis les ordres : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

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

        nonlocal selected_build_unit_type
        nonlocal automaton_state
        nonlocal buttons_right

        if automaton_state == AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE:

            selected_build_unit_type = build_unit_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            stack_role_flag(buttons_right)

            legend_select_active = html.LEGEND("Sélectionner la zone où construire")
            buttons_right <= legend_select_active

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty():
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            # it is a zone we need now
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Sélectionner la destination de l'attaque")
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.LEGEND("Sélectionner l'unité supportée offensivement")
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.LEGEND("Sélectionner l'unité supportée defensivement")
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(position_data, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.LEGEND("Sélectionner l'unité convoyée")
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Sélectionner la destination de la retraite")
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.DISBAND_ORDER:

                # insert disband order
                order = mapping.Order(position_data, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:

                legend_select_active = html.LEGEND("Sélectionner le type d'unité à construire")
                buttons_right <= legend_select_active

                for unit_type in mapping.UnitTypeEnum:
                    input_select = html.INPUT(type="submit", value=variant_data.name_table[unit_type])
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, u=unit_type: select_built_unit_type_callback(e, u))
                    buttons_right <= html.BR()
                    buttons_right <= input_select

                automaton_state = AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE

            if selected_order_type is mapping.OrderTypeEnum.REMOVE_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_active = html.LEGEND("Sélectionner l'unité à retirer")
                buttons_right <= legend_select_active

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty():
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

    def callback_click(event):
        """ callback_click """

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        nonlocal selected_order_type
        nonlocal automaton_state
        nonlocal selected_active_unit
        nonlocal selected_passive_unit
        nonlocal selected_dest_zone
        nonlocal selected_build_zone
        nonlocal buttons_right

        # this is a shortcut
        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                selected_order_type = mapping.OrderTypeEnum.ATTACK_ORDER
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_order_type = mapping.OrderTypeEnum.RETREAT_ORDER
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            # passthru

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_active_unit = position_data.closest_unit(pos, False)
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_active_unit = position_data.closest_unit(pos, True)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            stack_role_flag(buttons_right)

            # can be None if no retreating unit on board
            if selected_active_unit is not None:

                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:

                    legend_selected_unit = html.LEGEND(f"L'unité active sélectionnée est {selected_active_unit}")
                    buttons_right <= legend_selected_unit

                legend_select_order = html.LEGEND("Sélectionner l'ordre (ou directement la destination)")
                buttons_right <= legend_select_order
                legend_select_order2 = html.I("Raccourcis clavier :(a)ttaquer/soutenir(o)ffensivement/soutenir (d)éfensivement/(t)enir/(c)onvoyer/(x)supprimer l'ordre")
                buttons_right <= legend_select_order2

                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(advancement_season):
                        input_select = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    order = mapping.Order(position_data, selected_order_type, selected_active_unit, None, None)
                    orders_data.insert_order(order)

                    # update map
                    callback_render(None)

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
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

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_dest_zone = variant_data.closest_zone(pos)
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                selected_build_zone = variant_data.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

            stack_role_flag(buttons_right)

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
            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.DISBAND_ORDER
                    selected_dest_zone = None
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
                        alert("On ne peut pas construire sur ce centre")
                else:
                    alert("Pas de centre à cet endroit")

            # update map
            callback_render(None)

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
                buttons_right <= legend_select_unit
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                legend_select_unit = html.LEGEND("Sélectionner l'ordre d'adjustement")
                buttons_right <= legend_select_unit
                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(advancement_season):
                        input_select = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty():
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

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, selected_passive_unit, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                stack_orders(buttons_right)
                if not orders_data.empty():
                    put_erase_all(buttons_right)
                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                    put_rest_hold(buttons_right)
                if not orders_data.empty():
                    put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.LEGEND(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.LEGEND(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.LEGEND("Sélectionner la destination de l'attaque soutenue")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.LEGEND("Sélectionner la destination du convoi")
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty():
                put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            return

    def callback_dblclick(event, selected_erase_unit):
        """ callback_dblclick """

        nonlocal automaton_state

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        nonlocal buttons_right

        # easy cases
        if selected_erase_unit is None:

            # moves : select unit
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_erase_unit = position_data.closest_unit(pos, False)

            # retreat : select dislodged unit
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_erase_unit = position_data.closest_unit(pos, True)

            # tough case : builds
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:

                # first look for a build to cancel
                selected_erase_unit = orders_data.closest_unit(pos)

                # if failed, look for a removal to cancel
                if selected_erase_unit is None:

                    selected_erase_unit = position_data.closest_unit(pos, False)

                    # does this unit has a removal order ?
                    if not orders_data.is_ordered(selected_erase_unit):
                        selected_erase_unit = None

        # remove order
        if selected_erase_unit is not None:
            orders_data.remove_order(selected_erase_unit)

        # update map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

        stack_role_flag(buttons_right)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.LEGEND("Sélectionner l'ordre d'adjustement")
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum:
                if order_type.compatible(advancement_season):
                    input_select = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                    buttons_right <= html.BR()
                    buttons_right <= input_select
            automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

        stack_orders(buttons_right)
        if not orders_data.empty():
            put_erase_all(buttons_right)
        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            put_rest_hold(buttons_right)
        if not orders_data.empty():
            put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

    def callback_keypress(event):
        """ callback_keypress """

        char = chr(event.charCode).lower()

        # order removal
        if char == 'x':

            # check there is a selected unit
            if selected_active_unit is None:
                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    alert("Impossible d'annuler une constrution de cette manière")
                return

            if not orders_data.is_ordered(selected_active_unit):
                return

            # pass to double click
            callback_dblclick(event, selected_active_unit)
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

        # put the legends
        variant_data.render(ctx)

        # put the position
        position_data.render(ctx)

        # put the orders
        orders_data.render(ctx)

    def stack_role_flag(buttons_right):
        """ stack_role_flag """
        # role flag
        role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg")
        buttons_right <= role_icon_img

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

        input_submit = html.INPUT(type="submit", value="soumettre ces ordres")
        input_submit.bind("click", submit_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
        return

    pseudo = storage['PSEUDO']

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # from game name get game id

    game_id = common.get_game_id(game)
    if game_id is None:
        return

    # from pseudo get player id

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        return

    # from game id and player id get role_id of player

    role_id = common.get_role_allocated_to_player(game_id, player_id)
    if role_id is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
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
    display_chosen = common.get_display_from_variant(variant_name_loaded)

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

    # game needs to be ongoing
    if game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarée")
        return
    if game_parameters_loaded['current_state'] == 2:
        alert("La partie est déjà terminée")
        return

    game_status = get_game_status(variant_data, game_parameters_loaded, False)
    my_sub_panel <= game_status

    advancement_loaded = game_parameters_loaded['current_advancement']
    advancement_season, _ = common.get_season(advancement_loaded, variant_data)

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
    canvas.bind("dblclick", lambda e: callback_dblclick(e, None))

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
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

    ratings = position_data.role_ratings()
    colours = position_data.role_colours()
    rating_colours_window = make_rating_colours_window(ratings, colours)

    report_loaded = common.game_report_reload(game)
    if report_loaded is None:
        return

    report_window = make_report_window(report_loaded)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; vertical-align: top;'

    display_left <= canvas
    display_left <= rating_colours_window
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

    stack_role_flag(buttons_right)

    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
        legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        if position_data.has_dislodged():
            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (double-clic pour effacer)")
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
        else:
            automaton_state = AutomatonStateEnum.IDLE_STATE

    if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        legend_select_order = html.LEGEND("Sélectionner l'ordre d'adjustement")
        buttons_right <= legend_select_order
        for order_type in mapping.OrderTypeEnum:
            if order_type.compatible(advancement_season):
                input_select = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                buttons_right <= html.BR()
                input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                buttons_right <= html.BR()
                buttons_right <= input_select
        automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

    stack_orders(buttons_right)
    if not orders_data.empty():
        put_erase_all(buttons_right)
    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
        put_rest_hold(buttons_right)
    if not orders_data.empty():
        put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= my_sub_panel2


def negotiate():
    """ negotiate """

    # because we do not want the token stale in the middle of the process
    login.check_token()

    dummy = html.P("Sorry, negotiate is not implemented yet...")
    my_sub_panel <= dummy


def declare():
    """ negotiate """

    def add_declaration_callback(_):
        """ add_declaration_callback """

        def reply_callback(req):
            """ reply_callback """

            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error adding declaration in game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem adding declaration in game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            InfoDialog("OK", "La déclaration a été faite !", remove_after=config.REMOVE_AFTER)

            # back to where we started
            declare()

        content = input_declaration.value

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'role_id': role_id,
            'pseudo': pseudo,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{game_id}"

        # adding a declaration in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def declarations_reload(game_id):
        """ reload_declarations """

        declarations = None

        def reply_callback(req):
            """ reply_callback """

            nonlocal declarations

            req_result = json.loads(req.text)

            declarations = req_result['declarations_list']

            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error extracting declarations from game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem extracting declarations in game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

        json_dict = {
            'role_id': role_id,
            'pseudo': pseudo,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{game_id}"

        # extracting declarations from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return declarations

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
        return

    pseudo = storage['PSEUDO']

    # because we do not want the token stale in the middle of the process
    login.check_token()

    game_id = common.get_game_id(game)
    if game_id is None:
        return

    # from pseudo get player id

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        return

    # from game id and player id get role_id of player

    role_id = common.get_role_allocated_to_player(game_id, player_id)
    if role_id is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        return

    form = html.FORM()

    legend_declaration = html.LEGEND("Votre déclaration", title="Qu'avez vous à déclarer ?")
    form <= legend_declaration
    form <= html.BR()

    input_declaration = html.TEXTAREA(type="text", rows=5, cols=80)
    form <= input_declaration
    form <= html.BR()

    form <= html.BR()
    input_declare_in_game = html.INPUT(type="submit", value="déclarer dans la partie")
    input_declare_in_game.bind("click", add_declaration_callback)
    form <= input_declare_in_game

    declarations = declarations_reload(game_id)
    if declarations is None:
        return

    # to avoid warning
    declarations = list(declarations)

    declarations_table = html.TABLE()
    declarations_table.style = {
        "border": "solid",
    }

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # select display (should be a user choice)
    display_chosen = common.get_display_from_variant(variant_name_loaded)

    for time_stamp, role_id_msg, content in declarations:

        row = html.TR()
        row.style = {
            "border": "solid",
        }

        date_desc = datetime.datetime.fromtimestamp(time_stamp)
        col = html.TD(f"{date_desc}")
        col.style = {
            "border": "solid",
        }
        row <= col

        role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id_msg}.jpg")
        col = html.TD(role_icon_img)
        col.style = {
            "border": "solid",
        }
        row <= col

        col = html.TD()
        col.style = {
            "border": "solid",
        }

        for line in content.split('\n'):
            col <= line
            col <= html.BR()

        row <= col

        declarations_table <= row

    my_sub_panel.clear()

    # role
    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg")
    my_sub_panel <= role_icon_img

    # form
    my_sub_panel <= form
    form <= html.BR()
    form <= html.BR()

    # declarations already
    my_sub_panel <= declarations_table


def vote():
    """ vote """

    # because we do not want the token stale in the middle of the process
    login.check_token()

    dummy = html.P("Sorry, votes is not implemented yet...")
    my_sub_panel <= dummy


def game_master():
    """ game_master """

    def civil_disorder_callback(_, __):
        """ civil_disorder_callback """

        alert("Désolé: la mise en désordre civil n'est pas implémentée - vous pouvez passer les ordres à la place du joueur en tant qu'arbitre en attendant...")

    def unallocate_role_callback(_, pseudo_removed, role_id):
        """ unallocate_role_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error allocating role to game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem allocating role to game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            InfoDialog("OK", f"Le joueur s'est vu retirer le rôle dans la partie: {req_result['msg']}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            my_sub_panel.clear()
            game_master()

        json_dict = {
            'game_id': game_id,
            'role_id': role_id,
            'player_pseudo': pseudo_removed,
            'delete': 1,
            'pseudo': pseudo,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def allocate_role_callback(_, input_for_role, role_id):
        """ allocate_role_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error allocating role to game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem allocating role to game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            InfoDialog("OK", f"Le joueur s'est vu attribuer le rôle dans la partie: {req_result['msg']}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            my_sub_panel.clear()
            game_master()

        player_pseudo = input_for_role.value

        json_dict = {
            'game_id': game_id,
            'role_id': role_id,
            'player_pseudo': player_pseudo,
            'delete': 0,
            'pseudo': pseudo,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/role-allocations"

        # put role : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def get_list_pseudo_allocatable_game(id2pseudo):
        """ get_list_pseudo_allocatable_game """

        pseudo_list = None

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error getting list pseudo allocatable game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem getting list pseudo allocatable game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return None
            req_result = json.loads(req.text)
            nonlocal pseudo_list
            pseudo_list = [id2pseudo[int(k)] for k, v in req_result.items() if v == -1]
            return pseudo_list

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{game_id}"

        # get roles that are allocated to game : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return pseudo_list

    def adjudicate_callback(_):
        """ adjudicate_callback """

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

            InfoDialog("OK", f"La résolution a été réalisée : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            my_sub_panel.clear()
            game_master()

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
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
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

    role_id = common.get_role_allocated_to_player(game_id, player_id)
    if role_id != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
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
    display_chosen = common.get_display_from_variant(variant_name_loaded)

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

    # game needs to be ongoing
    if game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarée")
        return
    if game_parameters_loaded['current_state'] == 2:
        alert("La partie est déjà terminée")
        return

    game_status = get_game_status(variant_data, game_parameters_loaded, False)
    my_sub_panel <= game_status

    my_sub_panel <= html.BR()

    # get the players of the game
    game_players_dict = get_game_players_data(game_id)

    if not game_players_dict:
        return

    # get the players (all players)
    players_dict = common.get_players()

    if not players_dict:
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    game_admin_table = html.TABLE()
    game_admin_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    role2pseudo = {v: k for k, v in game_players_dict.items()}

    submitted_data = common.get_roles_submitted_orders(game_id)
    if submitted_data is None:
        return

    # just to avoid a warning
    submitted_data = dict(submitted_data)

    # who can I put in this role
    possible_given_role = get_list_pseudo_allocatable_game(id2pseudo)

    for role_id in variant_data.roles:

        # discard game master
        if role_id == 0:
            continue

        row = html.TR()
        row.style = {
            "border": "solid",
        }

        role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg")
        col = html.TD(role_icon_img)
        col.style = {
            "border": "solid",
        }
        row <= col

        # player
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        else:
            pseudo_there = None
        col = html.TD(pseudo_there if pseudo_there else "")
        col.style = {
            "border": "solid",
        }
        row <= col

        submitted_roles_list = submitted_data['submitted']
        needed_roles_list = submitted_data['needed']
        if role_id in submitted_roles_list:
            flag = html.IMG(src="./data/orders_are_in.gif")
        elif role_id in needed_roles_list:
            flag = html.IMG(src="./data/orders_are_not_in.gif")
        else:
            flag = ""
        col = html.TD(flag)
        col.style = {
            "border": "solid",
        }
        row <= col

        input_civil_disorder = html.INPUT(type="submit", value="mettre en désordre civil")
        input_civil_disorder.bind("click", lambda e, r=role_id: civil_disorder_callback(e, r))
        col = html.TD(input_civil_disorder)
        col.style = {
            "border": "solid",
        }
        row <= col

        if pseudo_there is not None:
            input_unallocate_role = html.INPUT(type="submit", value="retirer le rôle")
            input_unallocate_role.bind("click", lambda e, p=pseudo_there, r=role_id: unallocate_role_callback(e, p, r))
        else:
            input_unallocate_role = None
        col = html.TD(input_unallocate_role if input_unallocate_role else "")
        col.style = {
            "border": "solid",
        }
        row <= col

        if pseudo_there is None:

            form = html.FORM()

            input_for_role = html.SELECT(type="select-one", value="", display='inline')
            for play_role_pseudo in sorted(possible_given_role):
                option = html.OPTION(play_role_pseudo)
                input_for_role <= option

            form <= input_for_role
            form <= " "

            input_put_in_role = html.INPUT(type="submit", value="attribuer le rôle", display='inline')
            input_put_in_role.bind("click", lambda e, i=input_for_role, r=role_id: allocate_role_callback(e, i, r))

            form <= input_put_in_role

        else:

            form = None

        col = html.TD(form if form else "")
        col.style = {
            "border": "solid",
        }
        row <= col

        game_admin_table <= row

    my_sub_panel <= game_admin_table

    my_sub_panel <= html.BR()

    input_adjudicate = html.INPUT(type="submit", value="déclencher la résolution")
    input_adjudicate.bind("click", adjudicate_callback)
    my_sub_panel <= input_adjudicate


def show_game_parameters():
    """ show_game_parameters """

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
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
        alert("Il faut choisir la partie au préalable")
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
    display_chosen = common.get_display_from_variant(variant_name_loaded)

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

    # just to avoid a warning
    game_players_dict = dict(game_players_dict)

    # get the players (all players)
    players_dict = common.get_players()

    if not players_dict:
        return

    id2pseudo = {v: k for k, v in players_dict.items()}

    submitted_data = None

    # if user identified ?
    if 'PSEUDO' in storage:
        pseudo = storage['PSEUDO']

        # from pseudo get player id
        player_id = common.get_player_id(pseudo)
        if player_id is not None:

            # is player in game ?
            role_id = common.get_role_allocated_to_player(game_id, player_id)
            if role_id is not None:

                # you will at least get your own role
                submitted_data = common.get_roles_submitted_orders(game_id)
                if submitted_data is None:
                    return

                # just to avoid a warning
                submitted_data = dict(submitted_data)

    game_players_table = html.TABLE()
    game_players_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    fields = ['flag', 'role', 'player', 'orders']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'player': 'joueur', 'role': 'role', 'orders': 'ordres'}[field]
        col = html.TD(field_fr)
        col.style = {
            "border": "solid",
            "font-weight": "bold",
        }
        thead <= col
    game_players_table <= thead

    role2pseudo = {v: k for k, v in game_players_dict.items()}

    for role_id in variant_data.roles:

        row = html.TR()
        row.style = {
            "border": "solid",
        }

        # role flag
        if role_id < 0:
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

        # role name
        if role_id == -1:
            role_name = ""
        else:
            role = variant_data.roles[role_id]
            role_name = variant_data.name_table[role]

        col = html.TD(role_name)
        col.style = {
            "border": "solid",
        }
        row <= col

        # player
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        else:
            pseudo_there = None
        col = html.TD(pseudo_there if pseudo_there else "")
        col.style = {
            "border": "solid",
        }
        row <= col

        # orders are in
        if submitted_data is not None:
            submitted_roles_list = submitted_data['submitted']
            needed_roles_list = submitted_data['needed']
            if role_id in submitted_roles_list:
                flag = html.IMG(src="./data/orders_are_in.gif")
            elif role_id in needed_roles_list:
                flag = html.IMG(src="./data/orders_are_not_in.gif")
            else:
                flag = ""
        else:
            flag = ""
        col = html.TD(flag)
        col.style = {
            "border": "solid",
        }
        row <= col

        game_players_table <= row

    my_sub_panel <= game_players_table

    # add the non allocated players
    dangling_players = [p for p in game_players_dict.keys() if game_players_dict[p] == - 1]
    if dangling_players:
        my_sub_panel <= html.BR()
        my_sub_panel <= html.EM("Les pseudos suivants sont alloués à la partie sans rôle:")
        for dangling_player_id_str in dangling_players:
            my_sub_panel <= html.BR()
            dangling_player_id = int(dangling_player_id_str)
            dangling_player = id2pseudo[dangling_player_id]
            my_sub_panel <= html.B(html.EM(dangling_player))


def show_history():
    """ show_history """

    def transition_display_callback(_, advancement_selected: int):

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

        transition_loaded = common.game_transition_reload(game, advancement_selected)
        if transition_loaded is None:
            return

        # clears a pylint warning
        transition_loaded = dict(transition_loaded)

        position_loaded = transition_loaded['situation']
        orders_loaded = transition_loaded['orders']
        report_loaded = transition_loaded['report_txt']

        # digest the position
        position_data = mapping.Position(position_loaded, variant_data)

        # digest the orders
        orders_data = mapping.Orders(orders_loaded, position_data)

        # now we can display

        map_size = variant_data.map_size

        # create canvas
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")

        ctx = canvas.getContext("2d")
        if ctx is None:
            alert("Il faudrait utiliser un navigateur plus récent !")
            return

        # put background (this will call the callback that display the whole map)
        img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/map.png")
        img.bind('load', callback_render)

        ratings = position_data.role_ratings()
        colours = position_data.role_colours()
        rating_colours_window = make_rating_colours_window(ratings, colours)
        my_sub_panel <= rating_colours_window

        report_window = make_report_window(report_loaded)

        # left side

        display_left = html.DIV(id='display_left')
        display_left.attrs['style'] = 'display: table-cell; vertical-align: top;'

        game_status = get_game_status_histo(variant_data, game_parameters_loaded, advancement_selected)

        display_left <= game_status
        display_left <= canvas
        display_left <= rating_colours_window
        display_left <= report_window

        nonlocal my_sub_panel2

        # overall
        my_sub_panel.removeChild(my_sub_panel2)

        my_sub_panel2 = html.DIV()
        my_sub_panel2.attrs['style'] = 'display:table-row'
        my_sub_panel2 <= display_left

        # new buttons right

        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; vertical-align: top;'

        buttons_right <= html.BR()
        input_first = html.INPUT(type="submit", value="||<<")
        input_first.bind("click", lambda e, a=0: transition_display_callback(e, a))
        buttons_right <= html.BR()
        buttons_right <= input_first

        buttons_right <= html.BR()
        input_previous = html.INPUT(type="submit", value="<")
        input_previous.bind("click", lambda e, a=advancement_selected - 1: transition_display_callback(e, a))
        buttons_right <= html.BR()
        buttons_right <= input_previous

        buttons_right <= html.BR()
        input_next = html.INPUT(type="submit", value=">")
        input_next.bind("click", lambda e, a=advancement_selected + 1: transition_display_callback(e, a))
        buttons_right <= html.BR()
        buttons_right <= input_next

        buttons_right <= html.BR()
        input_last = html.INPUT(type="submit", value=">>||")
        input_last.bind("click", lambda e, a=last_advancement: transition_display_callback(e, a))
        buttons_right <= html.BR()
        buttons_right <= input_last

        my_sub_panel2 <= buttons_right

        my_sub_panel <= my_sub_panel2

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    game_parameters_loaded = common.game_parameters_reload(game)
    if not game_parameters_loaded:
        return

    # just to prevent a erroneous pylint warning
    game_parameters_loaded = dict(game_parameters_loaded)

    advancement_loaded = game_parameters_loaded['current_advancement']
    last_advancement = advancement_loaded - 1
    if not last_advancement >= 0:
        alert("Rien pour le moment !")
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
    display_chosen = common.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters

    parameters_file_name = f"./variants/{variant_name_loaded}/{display_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file:
        parameters_read = json.load(read_file)

    # build variant data
    variant_data = mapping.Variant(variant_content_loaded, parameters_read)

    # put it there to remove it at first display
    my_sub_panel2 = html.DIV()
    my_sub_panel <= my_sub_panel2

    # initiates callback
    transition_display_callback(None, last_advancement)


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'position':
        show_position()
    if item_name == 'ordonner':
        submit_orders()
    if item_name == 'négocier':
        negotiate()
    if item_name == 'déclarer':
        declare()
    if item_name == 'voter':
        vote()
    if item_name == 'arbitrer':
        game_master()
    if item_name == 'paramètres':
        show_game_parameters()
    if item_name == 'joueurs':
        show_players_in_game()
    if item_name == 'historique':
        show_history()

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
