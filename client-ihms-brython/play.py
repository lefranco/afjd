""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import enum
import time

from browser import document, html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import tools
import geometry
import mapping
import login
import sandbox

LONG_DURATION_LIMIT_SEC = 1.0

OPTIONS = ['position', 'ordonner', 'taguer', 'chatter', 'négocier', 'déclarer', 'voter', 'historique', 'arbitrer', 'paramètres', 'joueurs']

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
    deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
    game_deadline_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"

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
    col = html.TD(f"DL {game_deadline_str}")
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

    hovering_default_message = "(informations sur l'unité survoléee par la souris sur la carte)"

    variant_name_loaded = None
    variant_content_loaded = None
    variant_data = None
    position_loaded = None
    position_data = None

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

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        selected_hovered_object = position_data.closest_object(pos)
        if selected_hovered_object is not None:
            hover_info.text = selected_hovered_object.description()
        else:
            hover_info.text = ""

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """
        hover_info.text = hovering_default_message

    def callback_export_sandbox(_):
        """ callback_export_sandbox """
        sandbox.import_position(position_data)

    def put_export_sandbox(buttons_right):
        """ put_export_sandbox """

        input_export_sandbox = html.INPUT(type="submit", value="exporter vers le bac à sable")
        input_export_sandbox.bind("click", callback_export_sandbox)
        buttons_right <= html.BR()
        buttons_right <= input_export_sandbox
        buttons_right <= html.BR()

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
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

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

    # give some information sometimes
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(variant_name_loaded, display_chosen)
    img.bind('load', callback_render)

    hover_info = html.DIV(hovering_default_message)
    hover_info.style = {
        'color': 'blue',
    }

    ratings = position_data.role_ratings()
    colours = position_data.role_colours()
    rating_colours_window = common.make_rating_colours_window(ratings, colours)

    report_loaded = common.game_report_reload(game)
    if report_loaded is None:
        return

    report_window = common.make_report_window(report_loaded)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= hover_info
    display_left <= canvas
    display_left <= rating_colours_window
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'
    put_export_sandbox(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= my_sub_panel2


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

    stored_event = None
    down_click_time = None

    input_definitive = None

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # complete orders
        orders_data.rest_hold(role_id if role_id != 0 else None)

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

        stack_role_flag(buttons_right)

        # we are in spring or autumn
        legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
        buttons_right <= legend_select_unit

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

        stack_orders(buttons_right)

        if not orders_data.empty():
            put_erase_all(buttons_right)
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
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
        buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

        stack_role_flag(buttons_right)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            if position_data.has_dislodged():
                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
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
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
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

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez soumis les ordres : {messages}", remove_after=config.REMOVE_AFTER)

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        names_dict = variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        definitive_value = input_definitive.checked

        json_dict = {
            'role_id': role_id,
            'pseudo': pseudo,
            'orders': orders_list_dict_json,
            'definitive': definitive_value,
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
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            legend_select_active = html.LEGEND("Sélectionner la zone où construire (cliquer sous la légende)")
            buttons_right <= legend_select_active

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
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
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Sélectionner la destination de l'attaque (cliquer sous la légende)")
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

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
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

                legend_selected_destination = html.LEGEND("Sélectionner la destination de la retraite (cliquer sous la légende)")
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.DISBAND_ORDER:

                # insert disband order
                order = mapping.Order(position_data, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
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
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
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
        nonlocal selected_build_zone
        nonlocal buttons_right

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

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
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            # can be None if no retreating unit on board
            if selected_active_unit is not None:

                if selected_active_unit.role != variant_data.roles[role_id]:

                    alert("Bien essayé, mais cette unité ne vous appartient pas.")
                    selected_active_unit = None

                else:

                    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:

                        legend_selected_unit = html.LEGEND(f"L'unité active sélectionnée est {selected_active_unit}")
                        buttons_right <= legend_selected_unit

                    legend_select_order = html.LEGEND("Sélectionner l'ordre (ou directement la destination - sous la légende)")
                    buttons_right <= legend_select_order
                    buttons_right <= html.BR()

                    legend_select_order21 = html.I("Raccourcis clavier :")
                    buttons_right <= legend_select_order21
                    buttons_right <= html.BR()

                    for info in ["(a)ttaquer", "soutenir(o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer", "(x)supprimer l'ordre"]:
                        legend_select_order22 = html.I(info)
                        buttons_right <= legend_select_order22
                        buttons_right <= html.BR()

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
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
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
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

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
                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
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
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
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
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, selected_passive_unit, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                stack_orders(buttons_right)
                if not orders_data.empty():
                    put_erase_all(buttons_right)
                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                    put_rest_hold(buttons_right)
                if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    buttons_right <= html.BR()
                    put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.LEGEND(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.LEGEND(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.LEGEND("Sélectionner la destination de l'attaque soutenue (cliquer sous la légende)")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.LEGEND("Sélectionner la destination du convoi (cliquer sous la légende)")
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
                put_rest_hold(buttons_right)
            if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                buttons_right <= html.BR()
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
            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.ADJUST_SEASON]:
                selected_erase_unit = position_data.closest_unit(pos, False)

            # retreat : select dislodged unit : easy case
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_erase_unit = position_data.closest_unit(pos, True)

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
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

        stack_role_flag(buttons_right)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
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
        if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            buttons_right <= html.BR()
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

        # normal : call s
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

    def stack_role_flag(buttons_right):
        """ stack_role_flag """

        # role flag
        role = variant_data.roles[role_id]
        role_name = variant_data.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
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

        nonlocal input_definitive

        label_definitive = html.LABEL("Prêt pour la résolution ?")
        buttons_right <= label_definitive

        input_definitive = html.INPUT(type="checkbox")
        buttons_right <= input_definitive

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

    role_id = common.get_role_allocated_to_player(game_id, player_id)
    if role_id is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        return

    # cannot be game master
    if role_id == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
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
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    game_parameters_loaded = common.game_parameters_reload(game)
    if not game_parameters_loaded:
        return

    # just to prevent a erroneous pylint warning
    game_parameters_loaded = dict(game_parameters_loaded)

    # game needs to be ongoing
    if game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
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
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    # get the orders from server
    orders_loaded = common.game_orders_reload(game)
    if not orders_loaded:
        return

    # digest the orders
    orders_data = mapping.Orders(orders_loaded, position_data)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(variant_name_loaded, display_chosen)
    img.bind('load', callback_render)

    ratings = position_data.role_ratings()
    colours = position_data.role_colours()
    rating_colours_window = common.make_rating_colours_window(ratings, colours)

    report_loaded = common.game_report_reload(game)
    if report_loaded is None:
        return

    report_window = common.make_report_window(report_loaded)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas
    display_left <= rating_colours_window
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

    stack_role_flag(buttons_right)

    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON]:
        legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        if position_data.has_dislodged():
            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
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
    if not orders_data.empty() or advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        buttons_right <= html.BR()
        put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= my_sub_panel2


def submit_communication_orders():
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
    selected_build_zone = None
    automaton_state = None

    stored_event = None
    down_click_time = None

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
        buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

        stack_role_flag(buttons_right)

        legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        buttons_right <= html.BR()
        put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

    def submit_orders_callback(_):
        """ submit_orders_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error submitting communication orders: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem submitting communication orders: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez déposé les ordres de communcation : {messages}", remove_after=config.REMOVE_AFTER)

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': pseudo,
            'orders': orders_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-communication-orders/{game_id}"

        # submitting orders : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Sélectionner la destination de l'attaque (cliquer sous la légende)")
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

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
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

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
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
        nonlocal selected_build_zone
        nonlocal buttons_right

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        # this is a shortcut
        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = mapping.OrderTypeEnum.ATTACK_ORDER
            automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE
            # passthru

        if automaton_state is AutomatonStateEnum.SELECT_ACTIVE_STATE:

            selected_active_unit = position_data.closest_unit(pos, None)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            # can be None if no retreating unit on board
            if selected_active_unit is not None:

                if selected_active_unit.role != variant_data.roles[role_id]:

                    alert("Bien essayé, mais cette unité ne vous appartient pas.")
                    selected_active_unit = None

                else:

                    legend_selected_unit = html.LEGEND(f"L'unité active sélectionnée est {selected_active_unit}")
                    buttons_right <= legend_selected_unit

                    legend_select_order = html.LEGEND("Sélectionner l'ordre (ou directement la destination - sous la légende)")
                    buttons_right <= legend_select_order
                    buttons_right <= html.BR()

                    legend_select_order21 = html.I("Raccourcis clavier :")
                    buttons_right <= legend_select_order21
                    buttons_right <= html.BR()

                    for info in ["(a)ttaquer", "soutenir(o)ffensivement", "soutenir (d)éfensivement", "(t)enir", "(c)onvoyer", "(x)supprimer l'ordre"]:
                        legend_select_order22 = html.I(info)
                        buttons_right <= legend_select_order22
                        buttons_right <= html.BR()

                    for order_type in mapping.OrderTypeEnum:
                        if order_type.compatible(mapping.SeasonEnum.SPRING_SEASON):
                            input_select = html.INPUT(type="submit", value=variant_data.name_table[order_type])
                            buttons_right <= html.BR()
                            input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                            buttons_right <= html.BR()
                            buttons_right <= input_select

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
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
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

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

            # update map
            callback_render(None)

            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
            buttons_right <= legend_select_unit

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
            put_submit(buttons_right)

            my_sub_panel2 <= buttons_right
            my_sub_panel <= my_sub_panel2

            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            return

        if automaton_state is AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE:

            selected_passive_unit = position_data.closest_unit(pos, None)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(position_data, selected_order_type, selected_active_unit, selected_passive_unit, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                stack_orders(buttons_right)
                if not orders_data.empty():
                    put_erase_all(buttons_right)
                buttons_right <= html.BR()
                put_submit(buttons_right)

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE
                return

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_selected_passive = html.LEGEND(f"L'unité sélectionnée objet du support offensif est {selected_passive_unit}")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_selected_passive = html.LEGEND(f"L'unité sélectionnée objet du convoi est {selected_passive_unit}")
            buttons_right <= legend_selected_passive

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:
                legend_select_destination = html.LEGEND("Sélectionner la destination de l'attaque soutenue (cliquer sous la légende)")
            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:
                legend_select_destination = html.LEGEND("Sélectionner la destination du convoi (cliquer sous la légende)")
            buttons_right <= legend_select_destination

            stack_orders(buttons_right)
            if not orders_data.empty():
                put_erase_all(buttons_right)
            buttons_right <= html.BR()
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
            selected_erase_unit = position_data.closest_unit(pos, None)

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
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

        stack_role_flag(buttons_right)

        legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        if not orders_data.empty():
            put_erase_all(buttons_right)
        buttons_right <= html.BR()
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

        # normal : call s
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

    def stack_role_flag(buttons_right):
        """ stack_role_flag """

        # role flag
        role = variant_data.roles[role_id]
        role_name = variant_data.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
        buttons_right <= role_icon_img

        warning = html.DIV()
        warning.style = {
            'color': 'red',
        }
        warning <= html.B("ATTENTION ! Ce sont des ordres pour communiquer avec les autres joueurs, pas des ordres pour les unités. Ils seront publiés à la prochaine résolution pourvu que l'unité en question ait reçu l'ordre *réel* de rester en place ou de se disperser.")
        buttons_right <= warning

    def stack_orders(buttons_right):
        """ stack_orders """

        buttons_right <= html.P()
        lines = str(orders_data).split('\n')
        communication_orders = html.DIV()
        communication_orders.style = {
            'color': 'pink',
        }
        for line in lines:
            communication_orders <= html.B(line)
            communication_orders <= html.BR()
        buttons_right <= communication_orders

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="effacer tout")
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="déposer ces ordres de communication")
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

    if role_id == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
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
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    game_parameters_loaded = common.game_parameters_reload(game)
    if not game_parameters_loaded:
        return

    # just to prevent a erroneous pylint warning
    game_parameters_loaded = dict(game_parameters_loaded)

    # game needs to be ongoing
    if game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        return
    if game_parameters_loaded['current_state'] == 2:
        alert("La partie est déjà terminée")
        return

    game_status = get_game_status(variant_data, game_parameters_loaded, False)
    my_sub_panel <= game_status

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
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    # get the orders from server
    communication_orders_loaded = common.game_communication_orders_reload(game)
    if not communication_orders_loaded:
        return

    # digest the orders
    orders_data = mapping.Orders(communication_orders_loaded, position_data)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(variant_name_loaded, display_chosen)
    img.bind('load', callback_render)

    ratings = position_data.role_ratings()
    colours = position_data.role_colours()
    rating_colours_window = common.make_rating_colours_window(ratings, colours)

    report_loaded = common.game_report_reload(game)
    if report_loaded is None:
        return

    report_window = common.make_report_window(report_loaded)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas
    display_left <= rating_colours_window
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

    stack_role_flag(buttons_right)

    legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
    buttons_right <= legend_select_unit
    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    stack_orders(buttons_right)
    if not orders_data.empty():
        put_erase_all(buttons_right)
    buttons_right <= html.BR()
    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= my_sub_panel2



def visual_chat():
    """ negotiate """

    my_sub_panel <= """
      Here will go widgets to chat by video
    """



# the idea is not to loose the content of a message if not destinee were specified
content_backup = None  # pylint: disable=invalid-name


def negotiate():
    """ negotiate """

    def add_message_callback(_):
        """ add_message_callback """

        def reply_callback(req):
            """ reply_callback """

            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error adding message in game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem adding message in game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le message a été envoyé ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            global content_backup  # pylint: disable=invalid-name
            content_backup = None
            negotiate()
            return

        dest_role_ids = ' '.join([str(role_num) for (role_num, button) in selected.items() if button.checked])

        content = input_message.value

        # keep a backup
        global content_backup  # pylint: disable=invalid-name
        content_backup = content

        if not content:
            alert("Pas de contenu pour ce message !")
            negotiate()
            return

        if not dest_role_ids:
            alert("Pas de destinataire pour ce message !")
            negotiate()
            return

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'dest_role_ids': dest_role_ids,
            'role_id': role_id,
            'pseudo': pseudo,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{game_id}"

        # adding a message in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def messages_reload(game_id):
        """ messages_reload """

        messages = None

        def reply_callback(req):
            """ reply_callback """

            nonlocal messages

            req_result = json.loads(req.text)

            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error extracting messages from game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem extracting messages in game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            messages = req_result['messages_list']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{game_id}"

        # extracting messages from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return messages

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

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.last_visit_load(game_id, common.MESSAGES_TYPE)

    # put time stamp of last visit of declarations as now
    common.last_visit_update(game_id, pseudo, role_id, common.MESSAGES_TYPE)

    # get variant name
    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # to avoid a warning
    variant_content_loaded = dict(variant_content_loaded)

    # select display (should be a user choice)
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    form = html.FORM()

    legend_declaration = html.LEGEND("Votre message", title="Qu'avez vous à lui/leur dire ?")
    form <= legend_declaration
    form <= html.BR()

    input_message = html.TEXTAREA(type="text", rows=5, cols=80)
    if content_backup is not None:
        input_message <= content_backup
    form <= input_message
    form <= html.BR()

    table = html.TABLE()
    row = html.TR()
    selected = dict()
    for role_id_dest in range(variant_content_loaded['roles']['number'] + 1):

        role = variant_data.roles[role_id_dest]
        role_name = variant_data.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id_dest}.jpg", title=role_name)

        # the alternative
        input_dest = html.INPUT(type="checkbox", id=str(role_id_dest), name="destinees")
        col = html.TD()
        col <= input_dest

        # necessary to link flag with button
        label_dest = html.LABEL(role_icon_img, for_=str(role_id_dest))
        col <= label_dest

        row <= col

        # add a separator
        col = html.TD()
        row <= col

        selected[role_id_dest] = input_dest

    table <= row
    form <= table

    form <= html.BR()
    input_declare_in_game = html.INPUT(type="submit", value="envoyer le message")
    input_declare_in_game.bind("click", add_message_callback)
    form <= input_declare_in_game

    messages = messages_reload(game_id)
    if messages is None:
        return

    # to avoid warning
    messages = list(messages)

    messages_table = html.TABLE()
    messages_table.style = {
        "border": "solid",
    }

    thead = html.THEAD()
    for title in ['Date', 'Auteur', 'Destinataire(s)', 'Contenu']:
        col = html.TD(html.B(title))
        col.style = {
            "border": "solid",
        }
        thead <= col
    messages_table <= thead

    for from_role_id_msg, time_stamp, dest_role_id_msgs, content in messages:

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

        role = variant_data.roles[from_role_id_msg]
        role_name = variant_data.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{from_role_id_msg}.jpg", title=role_name)
        col = html.TD(role_icon_img)
        col.style = {
            "border": "solid",
        }
        row <= col

        col = html.TD()
        col.style = {
            "border": "solid",
        }

        for dest_role_id_msg in dest_role_id_msgs:
            role = variant_data.roles[dest_role_id_msg]
            role_name = variant_data.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{dest_role_id_msg}.jpg", title=role_name)
            col <= role_icon_img
        row <= col

        col = html.TD()
        col.style = {
            "border": "solid",
        }

        for line in content.split('\n'):
            # new so put in bold
            if time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        messages_table <= row

    my_sub_panel.clear()

    # role
    role = variant_data.roles[role_id]
    role_name = variant_data.name_table[role]
    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
    my_sub_panel <= role_icon_img

    # form
    my_sub_panel <= form
    form <= html.BR()
    form <= html.BR()

    # declarations already
    my_sub_panel <= messages_table


def declare():
    """ declare """

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

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La déclaration a été faite ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            declare()
            return

        anonymous = input_anonymous.checked

        content = input_declaration.value

        if not content:
            alert("Pas de contenu pour cette déclaration !")
            declare()
            return

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'role_id': role_id,
            'pseudo': pseudo,
            'anonymous': anonymous,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{game_id}"

        # adding a declaration in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def declarations_reload(game_id):
        """ declarations_reload """

        declarations = None

        def reply_callback(req):
            """ reply_callback """

            nonlocal declarations

            req_result = json.loads(req.text)

            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error extracting declarations from game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem extracting declarations in game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            declarations = req_result['declarations_list']

        json_dict = dict()

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

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.last_visit_load(game_id, common.DECLARATIONS_TYPE)

    # put time stamp of last visit of declarations as now
    common.last_visit_update(game_id, pseudo, role_id, common.DECLARATIONS_TYPE)

    # from game name get variant name
    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # select display (should be a user choice)
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    form = html.FORM()

    legend_declaration = html.LEGEND("Votre déclaration", title="Qu'avez vous à déclarer à tout le monde ?")
    form <= legend_declaration
    form <= html.BR()

    input_declaration = html.TEXTAREA(type="text", rows=5, cols=80)
    form <= input_declaration
    form <= html.BR()

    table = html.TABLE()
    row = html.TR()
    col = html.TD()

    label_anonymous = html.LABEL("En restant anonyme ? (pas anonyme auprès de l'arbitre cependant)")
    col <= label_anonymous
    row <= col

    input_anonymous = html.INPUT(type="checkbox")
    col <= input_anonymous
    row <= col

    table <= row
    form <= table

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

    thead = html.THEAD()
    for title in ['Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        col.style = {
            "border": "solid",
        }
        thead <= col
    declarations_table <= thead

    for anonymous, role_id_msg, time_stamp, content in declarations:

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

        if role_id_msg != -1:
            role = variant_data.roles[role_id_msg]
            role_name = variant_data.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id_msg}.jpg", title=role_name)
        else:
            role_icon_img = ""
        col = html.TD(role_icon_img)
        col.style = {
            "border": "solid",
        }
        row <= col

        col = html.TD()
        if anonymous:
            col.style = {
                "border": "solid",
                "color": "red",
            }
        else:
            col.style = {
                "border": "solid",
            }

        for line in content.split('\n'):
            # new so put in bold
            if time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        declarations_table <= row

    my_sub_panel.clear()

    # role
    role = variant_data.roles[role_id]
    role_name = variant_data.name_table[role]
    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
    my_sub_panel <= role_icon_img

    # form
    my_sub_panel <= form
    form <= html.BR()
    form <= html.BR()

    # declarations already
    my_sub_panel <= declarations_table


def vote():
    """ vote """

    def add_vote_callback(_):
        """ add_vote_callback """

        def reply_callback(req):
            """ reply_callback """

            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error adding vote in game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem adding vote in game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le vote a été enregistré ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            vote()
            return

        vote_value = input_vote.checked

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'role_id': role_id,
            'pseudo': pseudo,
            'value': vote_value
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-votes/{game_id}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
        return

    pseudo = storage['PSEUDO']

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

    if role_id == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
        return

    # get variant name
    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # select display (should be a user choice)
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    votes = common.vote_reload(game_id)
    if votes is None:
        return

    # avoids a warning
    votes = list(votes)

    vote_value = False
    for _, role, vote_val in votes:
        if role == role_id:
            vote_value = bool(vote_val)
            break

    form = html.FORM()

    legend_vote = html.LEGEND("Cochez pour voter l'arrêt", title="Etes vous d'accord pour terminer la partie en l'état ?")
    form <= legend_vote

    input_vote = html.INPUT(type="checkbox", checked=vote_value)
    form <= input_vote

    form <= html.BR()
    input_vote_in_game = html.INPUT(type="submit", value="voter dans la partie")
    input_vote_in_game.bind("click", add_vote_callback)
    form <= input_vote_in_game

    my_sub_panel.clear()

    # role
    role = variant_data.roles[role_id]
    role_name = variant_data.name_table[role]
    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
    my_sub_panel <= role_icon_img
    form <= html.BR()

    # form
    my_sub_panel <= form


def show_history():
    """ show_history """

    def transition_display_callback(_, advancement_selected: int):

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
        img = common.read_image(variant_name_loaded, display_chosen)
        img.bind('load', callback_render)

        ratings = position_data.role_ratings()
        colours = position_data.role_colours()
        rating_colours_window = common.make_rating_colours_window(ratings, colours)
        my_sub_panel <= rating_colours_window

        report_window = common.make_report_window(report_loaded)

        # left side

        display_left = html.DIV(id='display_left')
        display_left.attrs['style'] = 'display: table-cell; width:500px; vertical-align: top; table-layout: fixed;'

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
        buttons_right.attrs['style'] = 'display: table-cell; width=15%; vertical-align: top;'

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

        for adv_sample in range(4, last_advancement, 5):

            adv_sample_season, adv_sample_year = common.get_season(adv_sample, variant_data)
            adv_sample_season_readable = variant_data.name_table[adv_sample_season]

            buttons_right <= html.BR()
            input_last = html.INPUT(type="submit", value=f"{adv_sample_season_readable} {adv_sample_year}")
            input_last.bind("click", lambda e, a=adv_sample: transition_display_callback(e, a))
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
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    # put it there to remove it at first display
    my_sub_panel2 = html.DIV()
    my_sub_panel <= my_sub_panel2

    # initiates callback
    transition_display_callback(None, last_advancement)


def game_master():
    """ game_master """

    def civil_disorder_callback(_, role_id):
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error submitting disorder to game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem submitting disorder to game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu infligé des ordres de désordre civil: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            my_sub_panel.clear()
            game_master()

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        names_dict = variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': pseudo,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-no-orders/{game_id}"

        # submitting civil disoder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu retirer le rôle dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

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

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu attribuer le rôle dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

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

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La résolution a été réalisée : {messages}", remove_after=config.REMOVE_AFTER)

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
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    game_parameters_loaded = common.game_parameters_reload(game)
    if not game_parameters_loaded:
        return

    # just to prevent a erroneous pylint warning
    game_parameters_loaded = dict(game_parameters_loaded)

    # game needs to be ongoing
    if game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
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

    # definitives
    definitives = common.definitive_reload(game_id)
    if definitives is None:
        return

    # avoids a warning
    definitives = list(definitives)

    definitive_values_table = dict()
    for _, role, definitive_val in definitives:
        definitive_values_table[role] = bool(definitive_val)

    # votes
    votes = common.vote_reload(game_id)
    if votes is None:
        return

    # avoids a warning
    votes = list(votes)

    vote_values_table = dict()
    for _, role, vote_val in votes:
        vote_values_table[role] = bool(vote_val)

    for role_id in variant_data.roles:

        # discard game master
        if role_id == 0:
            continue

        row = html.TR()
        row.style = {
            "border": "solid",
        }

        role = variant_data.roles[role_id]
        role_name = variant_data.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
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
            flag = html.IMG(src="./data/green_tick.jpg", title="Les ordres sont validés")
        elif role_id in needed_roles_list:
            flag = html.IMG(src="./data/red_close.jpg", title="Les ordres ne sont pas validés")
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

        col = html.TD()
        col.style = {
            "border": "solid",
        }
        if role_id in definitive_values_table:
            vote_val = "Prêt pour la résolution" if definitive_values_table[role_id] else "Pas encore prêt pour la résolution"
        else:
            vote_val = "Pas d'avis"
        col <= vote_val
        row <= col

        col = html.TD()
        col.style = {
            "border": "solid",
        }
        if role_id in vote_values_table:
            vote_val = "Arrêt" if vote_values_table[role_id] else "Continuer"
        else:
            vote_val = "Pas de vote"
        col <= vote_val
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
    display_chosen = tools.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

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
            role = variant_data.roles[role_id]
            role_name = variant_data.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)

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
                flag = html.IMG(src="./data/green_tick.jpg", title="Les ordres sont validés")
            elif role_id in needed_roles_list:
                flag = html.IMG(src="./data/red_close.jpg", title="Les ordres ne sont pas validés")
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


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'position':
        show_position()
    if item_name == 'ordonner':
        submit_orders()
    if item_name == 'taguer':
        submit_communication_orders()
    if item_name == 'chatter':
        visual_chat()
    if item_name == 'négocier':
        negotiate()
    if item_name == 'déclarer':
        declare()
    if item_name == 'voter':
        vote()
    if item_name == 'historique':
        show_history()
    if item_name == 'arbitrer':
        game_master()
    if item_name == 'paramètres':
        show_game_parameters()
    if item_name == 'joueurs':
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

    # always back to top
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

    load_option(None, item_name_selected)
    panel_middle <= my_panel
