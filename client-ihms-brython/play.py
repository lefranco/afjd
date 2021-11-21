""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import enum
import time
import random

from browser import document, html, ajax, alert, timer   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog, Dialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import tools
import geometry
import mapping
import login
import sandbox
import index  # circular import

# how long between two consecutives refresh
SUPERVISE_REFRESH_PERIOD_SEC = 15

# how long between two consecutives refresh
OBSERVE_REFRESH_PERIOD_SEC = 60

LONG_DURATION_LIMIT_SEC = 1.0

OPTIONS = ['position', 'ordonner', 'taguer', 'négocier', 'déclarer', 'voter', 'historique', 'arbitrer', 'superviser', 'observer', 'paramètres', 'joueurs', 'ordres']


@enum.unique
class AutomatonStateEnum(enum.Enum):
    """ AutomatonStateEnum """

    SELECT_ACTIVE_STATE = enum.auto()
    SELECT_ORDER_STATE = enum.auto()
    SELECT_PASSIVE_UNIT_STATE = enum.auto()
    SELECT_DESTINATION_STATE = enum.auto()
    SELECT_BUILD_UNIT_TYPE_STATE = enum.auto()


# the idea is not to loose the content of a message if not destinee were specified
content_backup = None  # pylint: disable=invalid-name


# global data below

# loaded in render()
g_game_id = None  # pylint: disable=invalid-name
g_pseudo = None  # pylint: disable=invalid-name
g_role_id = None  # pylint: disable=invalid-name

# loaded in load_static_stuff
g_players_dict = None  # pylint: disable=invalid-name
g_game = None  # pylint: disable=invalid-name
g_variant_name_loaded = None  # pylint: disable=invalid-name
g_variant_content_loaded = None  # pylint: disable=invalid-name
g_display_chosen = None  # pylint: disable=invalid-name
g_parameters_read = None  # pylint: disable=invalid-name
g_variant_data = None  # pylint: disable=invalid-name
g_game_parameters_loaded = None  # pylint: disable=invalid-name
g_game_players_dict = None  # pylint: disable=invalid-name

# loaded in load_dynamic_stuff
g_game_status = None  # pylint: disable=invalid-name
g_position_loaded = None  # pylint: disable=invalid-name
g_position_data = None  # pylint: disable=invalid-name
g_report_loaded = None  # pylint: disable=invalid-name


def load_static_stuff():
    """ load_static_stuff : loads global data """

    # need to be first since used in get_game_status()
    # get the players (all players)
    global g_players_dict  # pylint: disable=invalid-name
    g_players_dict = common.get_players()
    if not g_players_dict:
        alert("Erreur chargement info joueurs")
        return
    g_players_dict = dict(g_players_dict)  # avoids a warning

    # from game name get variant name

    global g_variant_name_loaded  # pylint: disable=invalid-name
    g_variant_name_loaded = common.game_variant_name_reload(g_game)
    if not g_variant_name_loaded:
        alert("Erreur chargement variante")
        return

    # from variant name get variant content

    global g_variant_content_loaded  # pylint: disable=invalid-name
    g_variant_content_loaded = common.game_variant_content_reload(g_variant_name_loaded)
    if not g_variant_content_loaded:
        alert("Erreur chargement contenu variante")
        return

    # just to prevent a erroneous pylint warning
    g_variant_content_loaded = dict(g_variant_content_loaded)

    # selected display (user choice)
    global g_display_chosen  # pylint: disable=invalid-name
    g_display_chosen = tools.get_display_from_variant(g_variant_name_loaded)

    # from display chose get display parameters
    global g_parameters_read  # pylint: disable=invalid-name
    g_parameters_read = common.read_parameters(g_variant_name_loaded, g_display_chosen)

    # build variant data
    global g_variant_data  # pylint: disable=invalid-name
    g_variant_data = mapping.Variant(g_variant_name_loaded, g_variant_content_loaded, g_parameters_read)


def load_dynamic_stuff():
    """ load_dynamic_stuff : loads global data """

    # now game parameters (dynamic since advancement is dynamic)
    global g_game_parameters_loaded  # pylint: disable=invalid-name
    g_game_parameters_loaded = common.game_parameters_reload(g_game)
    if not g_game_parameters_loaded:
        alert("Erreur chargement paramètres")
        return

    # just to prevent a erroneous pylint warning
    g_game_parameters_loaded = dict(g_game_parameters_loaded)

    global g_game_status  # pylint: disable=invalid-name
    g_game_status = get_game_status()

    # get the position from server
    global g_position_loaded  # pylint: disable=invalid-name
    g_position_loaded = common.game_position_reload(g_game_id)
    if not g_position_loaded:
        alert("Erreur chargement position")
        return

    # digest the position
    global g_position_data  # pylint: disable=invalid-name
    g_position_data = mapping.Position(g_position_loaded, g_variant_data)

    # need to be after game parameters (advancement -> season)
    global g_report_loaded  # pylint: disable=invalid-name
    g_report_loaded = common.game_report_reload(g_game_id)
    if g_report_loaded is None:
        alert("Erreur chargement rapport")
        return


def load_special_stuff():
    """ load_special_stuff : loads global data """

    # TODO improve this with real admin account
    if g_pseudo is not None and (g_pseudo == 'Palpatine' or g_role_id == 0 or not g_game_parameters_loaded['anonymous']):
        global g_game_players_dict  # pylint: disable=invalid-name
        # get the players of the game
        # need a token for this
        g_game_players_dict = get_game_players_data(g_game_id)
        if not g_game_players_dict:
            alert("Erreur chargement joueurs de la partie")
            return
        g_game_players_dict = dict(g_game_players_dict)  # avoids a warning


def stack_clock(frame, period):
    """ stack_clock """

    clock_icon_img = html.IMG(src="./images/clock.png", title=f"Cette page est rafraichie périodiquement toutes les {period} secondes")
    frame <= clock_icon_img


def stack_role_flag(frame):
    """ stack_role_flag """

    # role flag
    role = g_variant_data.roles[g_role_id]
    role_name = g_variant_data.name_table[role]
    role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{g_role_id}.jpg", title=role_name)
    frame <= role_icon_img


g_deadline_col = None  # pylint: disable=invalid-name
g_countdown_col = None  # pylint: disable=invalid-name


def countdown():
    """ countdown """

    print("countdwon called !")

    deadline_loaded = g_game_parameters_loaded['deadline']

    # calculate display colour for deadline and countdown

    time_unit = 60 if g_game_parameters_loaded['fast'] else 24 * 60 * 60

    colour = None
    time_stamp_now = time.time()
    # we are after deadline + grace
    if time_stamp_now > deadline_loaded + time_unit * g_game_parameters_loaded['grace_duration']:
        colour = config.PASSED_GRACE_COLOUR
    # we are after deadline
    elif time_stamp_now > deadline_loaded:
        colour = config.PASSED_DEADLINE_COLOUR
    # deadline is today
    elif time_stamp_now > deadline_loaded - time_unit:
        colour = config.APPROACHING_DEADLINE_COLOUR

    # set the colour
    if colour is not None:
        g_deadline_col.style = {
            'background-color': colour
        }

    # calculate text value of countdown

    time_stamp_now = time.time()
    remains = int(deadline_loaded - time_stamp_now)

    if remains < 0:
        late = - remains
        if late < 60:
            countdown_text = f"passée de {late:02}s !"
        elif late < 3600:
            countdown_text = f"passée de {late // 60:02}mn {late % 60:02}s !"
        elif late < 24 * 3600:
            countdown_text = f"passée de ~ {late // 3600:02}h !"
        else:
            countdown_text = f"passée de ~ {late // (24 * 3600)}j !"
    elif remains < 60:
        countdown_text = f"{remains:02}s"
    elif remains < 3600:
        countdown_text = f"{remains // 60:02}mn {remains % 60:02}s"
    elif remains < 24 * 3600:
        countdown_text = f"~ {remains // 3600:02}h"
    else:
        countdown_text = f"~ {remains // (24 * 3600)}j"

    # insert text
    g_countdown_col.text = countdown_text

    # set the colour
    if colour is not None:
        g_countdown_col.style = {
            'background-color': colour
        }


def get_game_status():
    """ get_game__status """

    game_name = g_game_parameters_loaded['name']
    game_description = g_game_parameters_loaded['description']
    game_variant = g_game_parameters_loaded['variant']

    state_loaded = g_game_parameters_loaded['current_state']
    for possible_state in config.STATE_CODE_TABLE:
        if config.STATE_CODE_TABLE[possible_state] == state_loaded:
            game_state_readable = possible_state
            break

    advancement_loaded = g_game_parameters_loaded['current_advancement']
    advancement_season, advancement_year = common.get_season(advancement_loaded, g_variant_data)
    advancement_season_readable = g_variant_data.name_table[advancement_season]
    game_season = f"{advancement_season_readable} {advancement_year}"

    deadline_loaded = g_game_parameters_loaded['deadline']
    datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
    deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
    deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
    game_deadline_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"

    game_status_table = html.TABLE()

    row = html.TR()

    col = html.TD(f"Partie {game_name} ({game_variant})")
    row <= col
    col = html.TD(f"Etat {game_state_readable}")
    row <= col
    col = html.TD(f"Saison {game_season}")
    row <= col

    global g_deadline_col  # pylint: disable=invalid-name
    g_deadline_col = html.TD(f"DL {game_deadline_str}")
    row <= g_deadline_col

    global g_countdown_col  # pylint: disable=invalid-name
    g_countdown_col = html.TD("xxx")
    row <= g_countdown_col

    game_master_pseudo = get_game_master(g_game_id)
    info = ''  # some games do not have a game master
    if game_master_pseudo is not None:
        info = f"Arbitre {game_master_pseudo}"
    col = html.TD(info)
    row <= col

    game_status_table <= row

    row = html.TR()

    col = html.TD(game_description, colspan="6")
    row <= col
    game_status_table <= row

    if g_game_parameters_loaded['fast']:
        row = html.TR()
        specific_information = html.EM("Partie rapide : rafraichissez la position etc... avec le bouton 'Jouer la partie sélectionnée'")
        col = html.TD(specific_information, colspan="6")
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

    row = html.TR()

    col = html.TD(f"Partie {game_name} ({game_variant})")
    row <= col
    col = html.TD(f"Saison {game_season}")
    row <= col

    game_status_table <= row
    return game_status_table


def get_game_master(game_id):
    """ get_game_master """

    # get the link (allocations) of game masters
    allocations_data = common.get_allocations_data()
    if allocations_data is None:
        alert("Erreur chargement allocations")
        return None
    allocations_data = dict(allocations_data)

    masters_alloc = allocations_data['game_masters_dict']

    # get the game it self
    for master_id, games_id in masters_alloc.items():
        if game_id in games_id:
            for pseudo, identifier in g_players_dict.items():
                if str(identifier) == master_id:
                    return pseudo

    return None


def get_game_players_data(game_id):
    """ get_game_players_data """

    game_players_dict = None

    def reply_callback(req):
        nonlocal game_players_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des joueurs de la partie : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des joueurs de la partie : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        game_players_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-allocations/{game_id}"

    # getting game allocation : need a token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return game_players_dict


def show_position():
    """ show_position """

    hovering_default_message = "(informations sur l'unité survoléee par la souris sur la carte)"

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        g_variant_data.render(ctx)

        # put the position
        g_position_data.render(ctx)

        # put the legends at the end
        g_variant_data.render_legends(ctx)

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        selected_hovered_object = g_position_data.closest_object(pos)
        if selected_hovered_object is not None:
            hover_info.text = selected_hovered_object.description()
        else:
            hover_info.text = ""

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """
        hover_info.text = hovering_default_message

    def callback_export_sandbox(_):
        """ callback_export_sandbox """

        # action on importing game
        sandbox.import_position(g_position_data)

        # action of going to sandbox page
        index.load_option(None, 'bac à sable')

    def put_export_sandbox(buttons_right):
        """ put_export_sandbox """

        input_export_sandbox = html.INPUT(type="submit", value="exporter vers le bac à sable")
        input_export_sandbox.bind("click", callback_export_sandbox)
        buttons_right <= html.BR()
        buttons_right <= input_export_sandbox
        buttons_right <= html.BR()

    # now we can display

    # header

    # game status
    my_sub_panel <= g_game_status

    # create canvas
    map_size = g_variant_data.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return True

    # give some information sometimes
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(g_variant_name_loaded, g_display_chosen)
    img.bind('load', callback_render)

    hover_info = html.DIV(hovering_default_message)

    ratings = g_position_data.role_ratings()
    colours = g_position_data.role_colours()
    rating_colours_window = common.make_rating_colours_window(ratings, colours)

    report_window = common.make_report_window(g_report_loaded)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= hover_info
    display_left <= canvas
    display_left <= rating_colours_window
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    # role flag if applicable
    if g_role_id is not None:
        stack_role_flag(buttons_right)
        buttons_right <= html.BR()

    put_export_sandbox(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= my_sub_panel2

    return True


def submit_orders():
    """ submit_orders """

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

    def submit_orders_callback(_):
        """ submit_orders_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez soumis les ordres : {messages}", remove_after=config.REMOVE_AFTER)

            adjudicated = req_result['adjudicated']
            if adjudicated:
                alert("La position de la partie a changé !")
                load_dynamic_stuff()
                my_sub_panel.clear()
                submit_orders()

        names_dict = g_variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        definitive_value = input_definitive.checked

        json_dict = {
            'role_id': g_role_id,
            'pseudo': g_pseudo,
            'orders': orders_list_dict_json,
            'definitive': definitive_value,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-orders/{g_game_id}"

        # submitting orders : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def rest_hold_callback(_):
        """ rest_hold_callback """

        nonlocal automaton_state
        nonlocal buttons_right

        # complete orders
        orders_data.rest_hold(g_role_id if g_role_id != 0 else None)

        # update displayed map
        callback_render(None)

        my_sub_panel2.removeChild(buttons_right)
        buttons_right = html.DIV(id='buttons_right')
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

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
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        stack_role_flag(buttons_right)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.LEGEND("Sélectionner l'ordre d'adjustement (clic-long pour effacer)")
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum:
                if order_type.compatible(advancement_season):
                    input_select = html.INPUT(type="submit", value=g_variant_data.name_table[order_type])
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
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = g_variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Sélectionner la destination de l'attaque (cliquer sous la légende)")
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = g_variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.LEGEND("Sélectionner l'unité supportée offensivement")
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = g_variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.LEGEND("Sélectionner l'unité supportée defensivement")
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(g_position_data, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = g_variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_select_passive = html.LEGEND("Sélectionner l'unité convoyée")
                buttons_right <= legend_select_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:

                order_name = g_variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Sélectionner la destination de la retraite (cliquer sous la légende)")
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.DISBAND_ORDER:

                # insert disband order
                order = mapping.Order(g_position_data, order_type, selected_active_unit, None, None)
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
                    input_select = html.INPUT(type="submit", value=g_variant_data.name_table[unit_type])
                    buttons_right <= html.BR()
                    input_select.bind("click", lambda e, u=unit_type: select_built_unit_type_callback(e, u))
                    buttons_right <= html.BR()
                    buttons_right <= input_select

                automaton_state = AutomatonStateEnum.SELECT_BUILD_UNIT_TYPE_STATE

            if selected_order_type is mapping.OrderTypeEnum.REMOVE_ORDER:

                order_name = g_variant_data.name_table[order_type]
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
                selected_active_unit = g_position_data.closest_unit(pos, False)
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_active_unit = g_position_data.closest_unit(pos, True)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            # gm can pass orders on archive games
            if g_role_id != 0 and selected_active_unit.role != g_variant_data.roles[g_role_id]:

                alert("Bien essayé, mais cette unité ne vous appartient pas (ou vous n'avez pas d'ordre à valider).")

                selected_active_unit = None

                # switch back to initial state selecting unit
                if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                    legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
                    buttons_right <= legend_select_unit

                    automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    legend_select_unit = html.LEGEND("Sélectionner l'ordre d'adjustement (clic-long pour effacer)")
                    buttons_right <= legend_select_unit
                    for order_type in mapping.OrderTypeEnum:
                        if order_type.compatible(advancement_season):
                            input_select = html.INPUT(type="submit", value=g_variant_data.name_table[order_type])
                            buttons_right <= html.BR()
                            input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                            buttons_right <= html.BR()
                            buttons_right <= input_select

                    automaton_state = AutomatonStateEnum.SELECT_ORDER_STATE

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
                        input_select = html.INPUT(type="submit", value=g_variant_data.name_table[order_type])
                        buttons_right <= html.BR()
                        input_select.bind("click", lambda e, o=order_type: select_order_type_callback(e, o))
                        buttons_right <= html.BR()
                        buttons_right <= input_select

                if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                    order = mapping.Order(g_position_data, selected_order_type, selected_active_unit, None, None)
                    orders_data.insert_order(order)

                    # update map
                    callback_render(None)

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

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_dest_zone = g_variant_data.closest_zone(pos)
            if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
                selected_build_zone = g_variant_data.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(g_position_data, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(g_position_data, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.RETREAT_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.DISBAND_ORDER
                    selected_dest_zone = None
                order = mapping.Order(g_position_data, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type is mapping.OrderTypeEnum.BUILD_ORDER:
                # create fake unit
                region = selected_build_zone.region
                center = region.center
                if center is not None:
                    deducted_role = center.owner_start
                    if deducted_role is not None:
                        if selected_build_unit_type is mapping.UnitTypeEnum.ARMY_UNIT:
                            fake_unit = mapping.Army(g_position_data, deducted_role, selected_build_zone, None)
                        if selected_build_unit_type is mapping.UnitTypeEnum.FLEET_UNIT:
                            fake_unit = mapping.Fleet(g_position_data, deducted_role, selected_build_zone, None)
                        # create order
                        order = mapping.Order(g_position_data, selected_order_type, fake_unit, None, None)
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
                legend_select_unit = html.LEGEND("Sélectionner l'ordre d'adjustement (clic-long pour effacer)")
                buttons_right <= legend_select_unit
                for order_type in mapping.OrderTypeEnum:
                    if order_type.compatible(advancement_season):
                        input_select = html.INPUT(type="submit", value=g_variant_data.name_table[order_type])
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

            selected_passive_unit = g_position_data.closest_unit(pos, False)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(g_position_data, selected_order_type, selected_active_unit, selected_passive_unit, None)
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
                selected_erase_unit = g_position_data.closest_unit(pos, False)

            # retreat : select dislodged unit : easy case
            if advancement_season in [mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
                selected_erase_unit = g_position_data.closest_unit(pos, True)

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
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        stack_role_flag(buttons_right)

        if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
            legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
            buttons_right <= legend_select_unit
            automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
            legend_select_order = html.LEGEND("Sélectionner l'ordre d'adjustement (clic-long pour effacer)")
            buttons_right <= legend_select_order
            for order_type in mapping.OrderTypeEnum:
                if order_type.compatible(advancement_season):
                    input_select = html.INPUT(type="submit", value=g_variant_data.name_table[order_type])
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
        g_variant_data.render(ctx)

        # put the position
        g_position_data.render(ctx)

        # put the orders
        orders_data.render(ctx)

        # put the legends at the end
        g_variant_data.render_legends(ctx)

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

        definitive_value = g_role_id in submitted_data['agreed']

        input_definitive = html.INPUT(type="checkbox", checked=definitive_value)
        buttons_right <= input_definitive

        input_submit = html.INPUT(type="submit", value="soumettre ces ordres")
        input_submit.bind("click", submit_orders_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit

    # need to be connected
    if g_pseudo is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'position')
        return False

    # need to have a role
    if g_role_id is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'position')
        return False

    # cannot be game master unless archive game
    if g_role_id == 0 and not g_game_parameters_loaded['archive']:
        alert("Ordonner pour un arbitre n'est possible que pour les parties archive")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not waiting
    if g_game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not finished
    if g_game_parameters_loaded['current_state'] == 2:
        alert("La partie est déjà terminée")
        load_option(None, 'position')
        return False

    # need to have orders to submit

    submitted_data = common.get_roles_submitted_orders(g_game_id)
    if submitted_data is None:
        alert("Erreur chargement données de soumission")
        load_option(None, 'position')
        return False

    # just to avoid a warning
    submitted_data = dict(submitted_data)

    if g_role_id == 0:
        if not submitted_data['needed']:
            alert("Il n'y a pas d'ordre à passer")
            load_option(None, 'position')
            return False
    else:
        if g_role_id not in submitted_data['needed']:
            alert("Vous n'avez pas d'ordre à passer")
            load_option(None, 'position')
            return False

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # now we can display

    # header

    # game status
    my_sub_panel <= g_game_status

    advancement_loaded = g_game_parameters_loaded['current_advancement']
    advancement_season, _ = common.get_season(advancement_loaded, g_variant_data)

    # create canvas
    map_size = g_variant_data.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return True

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    # get the orders from server
    orders_loaded = common.game_orders_reload(g_game_id)
    if not orders_loaded:
        alert("Erreur chargement ordres")
        load_option(None, 'position')
        return False

    # digest the orders
    orders_data = mapping.Orders(orders_loaded, g_position_data)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(g_variant_name_loaded, g_display_chosen)
    img.bind('load', callback_render)

    ratings = g_position_data.role_ratings()
    colours = g_position_data.role_colours()
    rating_colours_window = common.make_rating_colours_window(ratings, colours)

    report_window = common.make_report_window(g_report_loaded)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas
    display_left <= rating_colours_window
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    stack_role_flag(buttons_right)

    if advancement_season in [mapping.SeasonEnum.SPRING_SEASON, mapping.SeasonEnum.AUTUMN_SEASON, mapping.SeasonEnum.SUMMER_SEASON, mapping.SeasonEnum.WINTER_SEASON]:
        legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

    if advancement_season is mapping.SeasonEnum.ADJUST_SEASON:
        legend_select_order = html.LEGEND("Sélectionner l'ordre d'adjustement (clic-long pour effacer)")
        buttons_right <= legend_select_order
        for order_type in mapping.OrderTypeEnum:
            if order_type.compatible(advancement_season):
                input_select = html.INPUT(type="submit", value=g_variant_data.name_table[order_type])
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

    return True


def submit_communication_orders():
    """ submit_orders """

    selected_active_unit = None
    selected_passive_unit = None
    selected_dest_zone = None
    selected_order_type = None
    selected_build_zone = None
    automaton_state = None

    stored_event = None
    down_click_time = None

    def submit_orders_callback(_):
        """ submit_orders_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de communication : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de communication : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez déposé les ordres de communcation : {messages}", remove_after=config.REMOVE_AFTER)

        orders_list_dict = orders_data.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict)

        json_dict = {
            'role_id': g_role_id,
            'pseudo': g_pseudo,
            'orders': orders_list_dict_json,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-communication-orders/{g_game_id}"

        # submitting orders : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

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
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        stack_role_flag(buttons_right)

        legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
        buttons_right <= legend_select_unit
        automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

        stack_orders(buttons_right)
        buttons_right <= html.BR()
        put_submit(buttons_right)

        my_sub_panel2 <= buttons_right
        my_sub_panel <= my_sub_panel2

    def select_order_type_callback(_, order_type):
        """ select_order_type_callback """

        nonlocal automaton_state
        nonlocal buttons_right
        nonlocal selected_order_type

        if automaton_state == AutomatonStateEnum.SELECT_ORDER_STATE:

            selected_order_type = order_type

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:

                order_name = g_variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_destination = html.LEGEND("Sélectionner la destination de l'attaque (cliquer sous la légende)")
                buttons_right <= legend_selected_destination

                automaton_state = AutomatonStateEnum.SELECT_DESTINATION_STATE

            if selected_order_type is mapping.OrderTypeEnum.OFF_SUPPORT_ORDER:

                order_name = g_variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.LEGEND("Sélectionner l'unité supportée offensivement")
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                order_name = g_variant_data.name_table[order_type]
                legend_selected_order = html.LEGEND(f"L'ordre sélectionné est {order_name}")
                buttons_right <= legend_selected_order
                buttons_right <= html.BR()

                legend_selected_passive = html.LEGEND("Sélectionner l'unité supportée defensivement")
                buttons_right <= legend_selected_passive

                automaton_state = AutomatonStateEnum.SELECT_PASSIVE_UNIT_STATE

            if selected_order_type is mapping.OrderTypeEnum.HOLD_ORDER:

                # insert hold order
                order = mapping.Order(g_position_data, order_type, selected_active_unit, None, None)
                orders_data.insert_order(order)

                # update map
                callback_render(None)

                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
                buttons_right <= legend_select_unit

                my_sub_panel2 <= buttons_right
                my_sub_panel <= my_sub_panel2

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

            if selected_order_type is mapping.OrderTypeEnum.CONVOY_ORDER:

                order_name = g_variant_data.name_table[order_type]
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

            selected_active_unit = g_position_data.closest_unit(pos, None)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            # gm can pass orders on archive games
            if g_role_id != 0 and selected_active_unit.role != g_variant_data.roles[g_role_id]:

                alert("Bien essayé, mais cette unité ne vous appartient pas (ou vous n'avez pas d'ordre à valider).")

                selected_active_unit = None

                # switch back to initial state selecting unit
                legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
                buttons_right <= legend_select_unit

                automaton_state = AutomatonStateEnum.SELECT_ACTIVE_STATE

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
                        input_select = html.INPUT(type="submit", value=g_variant_data.name_table[order_type])
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
            my_sub_panel <= my_sub_panel2

            return

        if automaton_state is AutomatonStateEnum.SELECT_DESTINATION_STATE:

            selected_dest_zone = g_variant_data.closest_zone(pos)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            # insert attack, off support or convoy order
            if selected_order_type is mapping.OrderTypeEnum.ATTACK_ORDER:
                # little shortcut if dest = origin
                if selected_dest_zone == selected_active_unit.zone:
                    selected_order_type = mapping.OrderTypeEnum.HOLD_ORDER
                    selected_dest_zone = None
                order = mapping.Order(g_position_data, selected_order_type, selected_active_unit, None, selected_dest_zone)
                orders_data.insert_order(order)
            if selected_order_type in [mapping.OrderTypeEnum.OFF_SUPPORT_ORDER, mapping.OrderTypeEnum.CONVOY_ORDER]:
                order = mapping.Order(g_position_data, selected_order_type, selected_active_unit, selected_passive_unit, selected_dest_zone)
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

            selected_passive_unit = g_position_data.closest_unit(pos, None)

            my_sub_panel2.removeChild(buttons_right)
            buttons_right = html.DIV(id='buttons_right')
            buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

            stack_role_flag(buttons_right)

            if selected_order_type is mapping.OrderTypeEnum.DEF_SUPPORT_ORDER:

                # insert def support order
                order = mapping.Order(g_position_data, selected_order_type, selected_active_unit, selected_passive_unit, None)
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
            selected_erase_unit = g_position_data.closest_unit(pos, None)

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
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

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
        g_variant_data.render(ctx)

        # put the position
        g_position_data.render(ctx)

        # put the orders
        orders_data.render(ctx)

        # put the legends at the end
        g_variant_data.render_legends(ctx)

        warning = html.DIV()
        warning.style = {
            'color': 'red',
        }
        warning <= html.B("ATTENTION ! Ce sont des ordres pour communiquer avec les autres joueurs, pas des ordres pour les unités. Ils seront publiés à la prochaine résolution pourvu que l'unité en question ait reçu l'ordre *réel* de rester en place ou de se disperser.")
        buttons_right <= html.P()
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

    # need to be connected
    if g_pseudo is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'position')
        return False

    # need to have a role
    if g_role_id is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'position')
        return False

    # cannot be game master
    if g_role_id == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not waiting
    if g_game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not finished
    if g_game_parameters_loaded['current_state'] == 2:
        alert("La partie est déjà terminée")
        load_option(None, 'position')
        return False

    # need to have orders to submit

    submitted_data = common.get_roles_submitted_orders(g_game_id)
    if submitted_data is None:
        alert("Erreur chargement données de soumission")
        load_option(None, 'position')
        return False

    # just to avoid a warning
    submitted_data = dict(submitted_data)

    if g_role_id not in submitted_data['needed']:
        alert("Vous n'avez pas d'ordre à passer")
        load_option(None, 'position')
        return False

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # now we can display

    # header

    # game status
    my_sub_panel <= g_game_status

    # create canvas
    map_size = g_variant_data.map_size
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return True

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # to catch keyboard
    document.bind("keypress", callback_keypress)

    # get the orders from server
    communication_orders_loaded = common.game_communication_orders_reload(g_game_id)
    if not communication_orders_loaded:
        alert("Erreur chargement ordres communication")
        load_option(None, 'position')
        return False

    # digest the orders
    orders_data = mapping.Orders(communication_orders_loaded, g_position_data)

    # put background (this will call the callback that display the whole map)
    img = common.read_image(g_variant_name_loaded, g_display_chosen)
    img.bind('load', callback_render)

    ratings = g_position_data.role_ratings()
    colours = g_position_data.role_colours()
    rating_colours_window = common.make_rating_colours_window(ratings, colours)

    report_window = common.make_report_window(g_report_loaded)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas
    display_left <= rating_colours_window
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    stack_role_flag(buttons_right)

    legend_select_unit = html.LEGEND("Cliquez sur l'unité à ordonner (clic-long pour effacer)")
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

    my_sub_panel <= my_sub_panel2

    return True


def negotiate():
    """ negotiate """

    def add_message_callback(_):
        """ add_message_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de message dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de message dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le message a été envoyé ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            global content_backup  # pylint: disable=invalid-name
            content_backup = None
            negotiate()

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

        json_dict = {
            'dest_role_ids': dest_role_ids,
            'role_id': g_role_id,
            'pseudo': g_pseudo,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{g_game_id}"

        # adding a message in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def messages_reload(game_id):
        """ messages_reload """

        messages = None

        def reply_callback(req):
            nonlocal messages
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération des messages dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération des messages dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = req_result['messages_list']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{game_id}"

        # extracting messages from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return messages

    if g_role_id is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'position')
        return False

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(g_game_id, config.MESSAGES_TYPE)

    # put time stamp of last visit of declarations as now
    common.date_last_visit_update(g_game_id, g_pseudo, g_role_id, config.MESSAGES_TYPE)

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre message", title="Qu'avez vous à lui/leur dire ?")
    fieldset <= legend_declaration
    input_message = html.TEXTAREA(type="text", rows=5, cols=80)
    if content_backup is not None:
        input_message <= content_backup
    fieldset <= input_message
    form <= fieldset

    fieldset = html.FIELDSET()
    legend_destinees = html.LEGEND("Destinataire(s)", title="Et à qui ?")
    fieldset <= legend_destinees

    table = html.TABLE()
    row = html.TR()
    selected = dict()
    for role_id_dest in range(g_variant_content_loaded['roles']['number'] + 1):

        # dest only if allowed
        if g_game_parameters_loaded['nomessage']:
            if not (g_role_id == 0 or role_id_dest == 0):
                continue

        role_dest = g_variant_data.roles[role_id_dest]
        role_name = g_variant_data.name_table[role_dest]
        role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{role_id_dest}.jpg", title=role_name)

        # the alternative
        input_dest = html.INPUT(type="checkbox", id=str(role_id_dest), name="destinees")
        col = html.TD()
        col <= input_dest

        # necessary to link flag with button
        label_dest = html.LABEL(role_icon_img, for_=str(role_id_dest))
        col <= label_dest

        row <= col

        selected[role_id_dest] = input_dest

    table <= row
    fieldset <= table
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="envoyer le message")
    input_declare_in_game.bind("click", add_message_callback)
    form <= input_declare_in_game

    # now we display messages

    messages = messages_reload(g_game_id)
    if messages is None:
        alert("Erreur chargement messages")
        load_option(None, 'position')
        return False

    # to avoid warning
    messages = list(messages)

    messages_table = html.TABLE()

    thead = html.THEAD()
    for title in ['Date', 'Auteur', 'Destinataire(s)', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    messages_table <= thead

    for from_role_id_msg, time_stamp, dest_role_id_msgs, content in messages:

        row = html.TR()

        date_desc = datetime.datetime.fromtimestamp(time_stamp)
        col = html.TD(f"{date_desc}")
        row <= col

        role = g_variant_data.roles[from_role_id_msg]
        role_name = g_variant_data.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{from_role_id_msg}.jpg", title=role_name)
        col = html.TD(role_icon_img)
        row <= col

        col = html.TD()

        for dest_role_id_msg in dest_role_id_msgs:

            role = g_variant_data.roles[dest_role_id_msg]
            role_name = g_variant_data.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{dest_role_id_msg}.jpg", title=role_name)
            col <= role_icon_img

            # separator
            col <= html.BR()

        row <= col

        col = html.TD()

        for line in content.split('\n'):
            # new so put in bold
            if time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        messages_table <= row

    # now we can display

    my_sub_panel.clear()

    # header

    # game status
    my_sub_panel <= g_game_status
    my_sub_panel <= html.BR()

    # role
    stack_role_flag(my_sub_panel)

    my_sub_panel <= html.BR()
    my_sub_panel <= html.BR()

    # form
    my_sub_panel <= form
    my_sub_panel <= html.BR()
    my_sub_panel <= html.BR()

    # declarations already
    my_sub_panel <= messages_table

    return True


def declare():
    """ declare """

    def add_declaration_callback(_):
        """ add_declaration_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de déclaration dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de déclaration dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La déclaration a été faite ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            declare()

        anonymous = input_anonymous.checked

        content = input_declaration.value

        if not content:
            alert("Pas de contenu pour cette déclaration !")
            declare()
            return

        json_dict = {
            'role_id': g_role_id,
            'pseudo': g_pseudo,
            'anonymous': anonymous,
            'content': content
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{g_game_id}"

        # adding a declaration in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def declarations_reload(game_id):
        """ declarations_reload """

        declarations = None

        def reply_callback(req):
            nonlocal declarations
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de déclarations dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de déclarations dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            declarations = req_result['declarations_list']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{game_id}"

        # extracting declarations from a game : need token (or not?)
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return declarations

    if g_role_id is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'position')
        return False

    # because we do not want the token stale in the middle of the process
    login.check_token()

    # get time stamp of last visit of declarations
    time_stamp_last_visit = common.date_last_visit_load(g_game_id, config.DECLARATIONS_TYPE)

    # put time stamp of last visit of declarations as now
    common.date_last_visit_update(g_game_id, g_pseudo, g_role_id, config.DECLARATIONS_TYPE)

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_declaration = html.LEGEND("Votre déclaration", title="Qu'avez vous à déclarer à tout le monde ?")
    fieldset <= legend_declaration
    input_declaration = html.TEXTAREA(type="text", rows=5, cols=80)
    fieldset <= input_declaration
    form <= fieldset

    fieldset = html.FIELDSET()
    label_anonymous = html.LABEL("En restant anonyme ? (pas anonyme auprès de l'arbitre cependant)")
    fieldset <= label_anonymous
    input_anonymous = html.INPUT(type="checkbox")
    fieldset <= input_anonymous
    form <= fieldset

    form <= html.BR()

    input_declare_in_game = html.INPUT(type="submit", value="déclarer dans la partie")
    input_declare_in_game.bind("click", add_declaration_callback)
    form <= input_declare_in_game

    # now we display declarations

    declarations = declarations_reload(g_game_id)
    if declarations is None:
        alert("Erreur chargement déclarations")
        load_option(None, 'position')
        return False

    # to avoid warning
    declarations = list(declarations)

    declarations_table = html.TABLE()

    thead = html.THEAD()
    for title in ['Date', 'Auteur', 'Contenu']:
        col = html.TD(html.B(title))
        thead <= col
    declarations_table <= thead

    for anonymous, role_id_msg, time_stamp, content in declarations:

        row = html.TR()

        date_desc = datetime.datetime.fromtimestamp(time_stamp)
        col = html.TD(f"{date_desc}")
        row <= col

        if role_id_msg != -1:
            role = g_variant_data.roles[role_id_msg]
            role_name = g_variant_data.name_table[role]
            role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{role_id_msg}.jpg", title=role_name)
        else:
            role_icon_img = ""
        col = html.TD(role_icon_img)
        row <= col

        col = html.TD()
        if anonymous:
            col.style = {
                "color": "red",
            }

        for line in content.split('\n'):
            # new so put in bold
            if time_stamp > time_stamp_last_visit:
                line = html.B(line)
            col <= line
            col <= html.BR()

        row <= col

        declarations_table <= row

    # now we can display

    my_sub_panel.clear()

    # header

    # game status
    my_sub_panel <= g_game_status
    my_sub_panel <= html.BR()

    # role
    stack_role_flag(my_sub_panel)

    my_sub_panel <= html.BR()
    my_sub_panel <= html.BR()

    # form only if allowed
    if g_game_parameters_loaded['nopress'] and g_role_id != 0:
        my_sub_panel <= html.P("Cette partie est sans presse des joueurs")
    else:
        # form
        my_sub_panel <= form
        my_sub_panel <= html.BR()
        my_sub_panel <= html.BR()

    # declarations already
    my_sub_panel <= declarations_table

    return True


def vote():
    """ vote """

    def add_vote_callback(_):
        """ add_vote_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'ajout de vote d'arrêt dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'ajout de vote d'arrêt dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le vote a été enregistré ! {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            vote()

        vote_value = input_vote.checked

        json_dict = {
            'role_id': g_role_id,
            'pseudo': g_pseudo,
            'value': vote_value
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-votes/{g_game_id}"

        # adding a vote in a game : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    # from game id and token get role_id of player

    if g_role_id is None:
        alert("Il ne semble pas que vous soyez joueur dans ou arbitre de cette partie")
        load_option(None, 'position')
        return False

    if g_role_id == 0:
        alert("Ce n'est pas possible pour l'arbitre de cette partie")
        load_option(None, 'position')
        return False

    votes = common.vote_reload(g_game_id)
    if votes is None:
        alert("Erreur chargement votes")
        load_option(None, 'position')
        return False

    # avoids a warning
    votes = list(votes)

    vote_value = False
    for _, role, vote_val in votes:
        if role == g_role_id:
            vote_value = bool(vote_val)
            break

    form = html.FORM()

    legend_vote = html.LEGEND("Cochez pour voter l'arrêt", title="Etes vous d'accord pour terminer la partie en l'état ?")
    form <= legend_vote
    form <= html.BR()

    input_vote = html.INPUT(type="checkbox", checked=vote_value)
    form <= input_vote
    form <= html.BR()

    input_vote_in_game = html.INPUT(type="submit", value="voter dans la partie")
    input_vote_in_game.bind("click", add_vote_callback)
    form <= input_vote_in_game

    # now we can display

    my_sub_panel.clear()

    # game status
    my_sub_panel <= g_game_status
    my_sub_panel <= html.BR()

    # role
    stack_role_flag(my_sub_panel)

    my_sub_panel <= html.BR()
    my_sub_panel <= html.BR()

    # form
    my_sub_panel <= form

    return True


def show_history():
    """ show_history """

    def transition_display_callback(_, advancement_selected):

        def callback_render(_):
            """ callback_render """

            # put the background map first
            ctx.drawImage(img, 0, 0)

            # put the centers
            g_variant_data.render(ctx)

            # put the position
            position_data.render(ctx)

            # put the orders
            orders_data.render(ctx)

            # put the legends at the end
            g_variant_data.render_legends(ctx)

        transition_loaded = common.game_transition_reload(g_game_id, advancement_selected)
        if transition_loaded is None:
            return

        # clears a pylint warning
        transition_loaded = dict(transition_loaded)

        position_loaded = transition_loaded['situation']
        orders_loaded = transition_loaded['orders']
        report_loaded = transition_loaded['report_txt']

        # digest the position
        position_data = mapping.Position(position_loaded, g_variant_data)

        # digest the orders
        orders_data = mapping.Orders(orders_loaded, position_data)

        # now we can display

        # create canvas
        map_size = g_variant_data.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        ctx = canvas.getContext("2d")
        if ctx is None:
            alert("Il faudrait utiliser un navigateur plus récent !")
            return

        # put background (this will call the callback that display the whole map)
        img = common.read_image(g_variant_name_loaded, g_display_chosen)
        img.bind('load', callback_render)

        ratings = position_data.role_ratings()
        colours = position_data.role_colours()
        rating_colours_window = common.make_rating_colours_window(ratings, colours)
        my_sub_panel <= rating_colours_window

        report_window = common.make_report_window(report_loaded)

        # left side

        display_left = html.DIV(id='display_left')
        display_left.attrs['style'] = 'display: table-cell; width:500px; vertical-align: top; table-layout: fixed;'

        game_status = get_game_status_histo(g_variant_data, g_game_parameters_loaded, advancement_selected)

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
        buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

        # role flag if applicable
        if g_role_id is not None:
            stack_role_flag(buttons_right)

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

            adv_sample_season, adv_sample_year = common.get_season(adv_sample, g_variant_data)
            adv_sample_season_readable = g_variant_data.name_table[adv_sample_season]

            buttons_right <= html.BR()
            input_last = html.INPUT(type="submit", value=f"{adv_sample_season_readable} {adv_sample_year}")
            input_last.bind("click", lambda e, a=adv_sample: transition_display_callback(e, a))
            buttons_right <= html.BR()
            buttons_right <= input_last

        my_sub_panel2 <= buttons_right

        my_sub_panel <= my_sub_panel2

    advancement_loaded = g_game_parameters_loaded['current_advancement']
    last_advancement = advancement_loaded - 1
    if not last_advancement >= 0:
        alert("Rien pour le moment !")
        load_option(None, 'position')
        return False

    # put it there to remove it at first display
    my_sub_panel2 = html.DIV()
    my_sub_panel <= my_sub_panel2

    # initiates callback
    transition_display_callback(None, last_advancement)

    return True


def game_master():
    """ game_master """

    def change_deadline_reload():
        """ change_deadline_reload """

        deadline_loaded = None

        def reply_callback(req):
            nonlocal deadline_loaded
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la date limite de la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la date limite de la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            deadline_loaded = req_result['deadline']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{g_game}"

        # getting game data : no need for token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return deadline_loaded

    def push_deadline_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur au report de date limite à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème au report de la date limite à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"La date limite a été reportée : {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            my_sub_panel.clear()
            load_dynamic_stuff()
            game_master()

        # get deadline from server (change to now if in the past)
        deadline_loaded = change_deadline_reload()
        time_stamp_now = time.time()
        # round to end of minute to avoid little surprises
        deadline_now = (time_stamp_now // 60) * 60 + 60
        deadline_used = max(deadline_now, deadline_loaded)

        # add one day - if fast game change to one minute
        time_unit = 60 if g_game_parameters_loaded['fast'] else 24 * 60 * 60
        deadline_forced = deadline_used + time_unit

        # push on server
        json_dict = {
            'pseudo': g_pseudo,
            'name': g_game,
            'deadline': deadline_forced,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{g_game}"

        # changing game deadline : need token
        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def civil_disorder_callback(_, role_id):
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu infligé des ordres de désordre civil: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            my_sub_panel.clear()
            game_master()

        names_dict = g_variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': g_pseudo,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{g_game_id}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(_, role_id):
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu imposé un accord pour résoudre: {messages}", remove_after=config.REMOVE_AFTER)

            adjudicated = req_result['adjudicated']
            if adjudicated:
                alert("La position de la partie a changé !")

            # back to where we started
            my_sub_panel.clear()
            game_master()

        names_dict = g_variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)
        definitive_value = True

        json_dict = {
            'role_id': role_id,
            'pseudo': g_pseudo,
            'definitive': definitive_value,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{g_game_id}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def unallocate_role_callback(_, pseudo_removed, role_id):
        """ unallocate_role_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la désallocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème Erreur à la désallocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu retirer le rôle dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            my_sub_panel.clear()
            load_special_stuff()
            game_master()

        json_dict = {
            'game_id': g_game_id,
            'role_id': role_id,
            'player_pseudo': pseudo_removed,
            'delete': 1,
            'pseudo': g_pseudo,
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
                    alert(f"Erreur à l'allocation de rôle dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'allocation de rôle dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Le joueur s'est vu attribuer le rôle dans la partie: {messages}", remove_after=config.REMOVE_AFTER)

            # back to where we started
            my_sub_panel.clear()
            load_special_stuff()
            game_master()

        player_pseudo = input_for_role.value

        json_dict = {
            'game_id': g_game_id,
            'role_id': role_id,
            'player_pseudo': player_pseudo,
            'delete': 0,
            'pseudo': g_pseudo,
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
            nonlocal pseudo_list
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à la récupération de la liste des joueurs allouables dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la récupération de la liste des joueurs allouables dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return None

            pseudo_list = [id2pseudo[int(k)] for k, v in req_result.items() if v == -1]
            return pseudo_list

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{g_game_id}"

        # get roles that are allocated to game : do not need token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

        return pseudo_list

    # need to be connected
    if g_pseudo is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'position')
        return False

    # need to be game master
    if g_role_id != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not waiting
    if g_game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not finished
    if g_game_parameters_loaded['current_state'] == 2:
        alert("La partie est déjà terminée")
        load_option(None, 'position')
        return False

    # now we can display

    # header

    # game status
    my_sub_panel <= g_game_status
    my_sub_panel <= html.BR()

    stack_role_flag(my_sub_panel)
    my_sub_panel <= html.BR()

    id2pseudo = {v: k for k, v in g_players_dict.items()}
    role2pseudo = {v: k for k, v in g_game_players_dict.items()}

    submitted_data = common.get_roles_submitted_orders(g_game_id)
    if submitted_data is None:
        alert("Erreur chargement données de soumission")
        load_option(None, 'position')
        return False

    # just to avoid a warning
    submitted_data = dict(submitted_data)

    # who can I put in this role
    possible_given_role = get_list_pseudo_allocatable_game(id2pseudo)

    # votes
    votes = common.vote_reload(g_game_id)
    if votes is None:
        alert("Erreur chargement votes")
        load_option(None, 'position')
        return False

    # avoids a warning
    votes = list(votes)

    vote_values_table = dict()
    for _, role, vote_val in votes:
        vote_values_table[role] = bool(vote_val)

    submitted_roles_list = submitted_data['submitted']
    agreed_roles_list = submitted_data['agreed']
    needed_roles_list = submitted_data['needed']

    game_admin_table = html.TABLE()

    for role_id in g_variant_data.roles:

        # discard game master
        if role_id == 0:
            continue

        row = html.TR()

        role = g_variant_data.roles[role_id]
        role_name = g_variant_data.name_table[role]

        # flag
        col = html.TD()
        role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{role_id}.jpg", title=role_name)
        col <= role_icon_img
        row <= col

        # role name
        col = html.TD()
        col <= role_name
        row <= col

        # player
        col = html.TD()
        pseudo_there = ""
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        col <= pseudo_there
        row <= col

        col = html.TD()
        flag = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
            else:
                flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
        col <= flag
        row <= col

        col = html.TD()
        input_civil_disorder = ""
        if role_id in needed_roles_list:
            if role_id not in submitted_roles_list:
                input_civil_disorder = html.INPUT(type="submit", value="mettre en désordre civil")
                input_civil_disorder.bind("click", lambda e, r=role_id: civil_disorder_callback(e, r))
        col <= input_civil_disorder
        row <= col

        col = html.TD()
        input_unallocate_role = ""
        if pseudo_there:
            input_unallocate_role = html.INPUT(type="submit", value="retirer le rôle")
            input_unallocate_role.bind("click", lambda e, p=pseudo_there, r=role_id: unallocate_role_callback(e, p, r))
        col <= input_unallocate_role
        row <= col

        col = html.TD()
        form = ""
        if not pseudo_there:

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

        col <= form
        row <= col

        col = html.TD()
        flag = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id in agreed_roles_list:
                    flag = html.IMG(src="./images/ready.jpg", title="Prêt pour résoudre")
                else:
                    flag = html.IMG(src="./images/not_ready.jpg", title="Pas prêt pour résoudre")
        col <= flag
        row <= col

        col = html.TD()
        input_force_agreement = ""
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id not in agreed_roles_list:
                    input_force_agreement = html.INPUT(type="submit", value="forcer son accord")
                    input_force_agreement.bind("click", lambda e, r=role_id: force_agreement_callback(e, r))
        col <= input_force_agreement
        row <= col

        col = html.TD()
        flag = ""
        if role_id in vote_values_table:
            if vote_values_table[role_id]:
                flag = html.IMG(src="./images/stop.png", title="Arrêter la partie")
            else:
                flag = html.IMG(src="./images/continue.jpg", title="Continuer la partie")
        col <= flag
        row <= col

        game_admin_table <= row

    my_sub_panel <= game_admin_table
    my_sub_panel <= html.BR()
    my_sub_panel <= html.BR()

    my_sub_panel <= html.EM("Le bouton ci-dessous repousse la date limite d'une journée (une minute pour une partie rapide).")
    my_sub_panel <= html.BR()
    my_sub_panel <= html.EM("Ce, à partir de maintenant si la date limite est passée.")
    my_sub_panel <= html.BR()
    my_sub_panel <= html.EM("Pour une gestion plus fine de cette date limite vous devez éditer la partie.")
    my_sub_panel <= html.BR()
    my_sub_panel <= html.BR()

    input_push_deadline = html.INPUT(type="submit", value="Reporter la date limite")
    input_push_deadline.bind("click", push_deadline_game_callback)
    my_sub_panel <= input_push_deadline

    return True


supervise_refresh_timer = None  # pylint: disable=invalid-name


class Logger(list):
    """ Logger """

    def insert(self, message):
        """ insert """

        # insert datation
        time_stamp = time.time()
        date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
        date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")

        # put in stack (limited height)
        log_line = html.CODE(f"{date_now_gmt_str} : {message}")
        self.append(log_line)

    def display(self, log_window):
        """ display """

        for log_line in reversed(self):
            log_window <= log_line
            log_window <= html.BR()


def supervise():
    """ supervise """

    def civil_disorder_callback(_, role_id):
        """ civil_disorder_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'ordres de désordre civil dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'ordres de désordre civil dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

        names_dict = g_variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'role_id': role_id,
            'pseudo': g_pseudo,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{g_game_id}"

        # submitting civil disorder : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def force_agreement_callback(_, role_id):
        """ force_agreement_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à la soumission d'accord forcé pour résoudre dans la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à la soumission d'accord forcé pour résoudre dans la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            adjudicated = req_result['adjudicated']
            if adjudicated:
                InfoDialog("OK", "La résolution a été forcée..", remove_after=config.REMOVE_AFTER)
                message = "Résolution forcée par la console suite forçage accord"
                log_stack.insert(message)

        names_dict = g_variant_data.extract_names()
        names_dict_json = json.dumps(names_dict)
        definitive_value = True

        json_dict = {
            'role_id': role_id,
            'pseudo': g_pseudo,
            'definitive': definitive_value,
            'names': names_dict_json
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{g_game_id}"

        # submitting force agreement : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def reload_game_admin_table(submitted_data, votes):
        """ reload_game_admin_table """

        vote_values_table = dict()
        for _, role, vote_val in votes:
            vote_values_table[role] = bool(vote_val)

        submitted_roles_list = submitted_data['submitted']
        agreed_roles_list = submitted_data['agreed']
        needed_roles_list = submitted_data['needed']

        game_admin_table = html.TABLE()

        for role_id in g_variant_data.roles:

            # discard game master
            if role_id == 0:
                continue

            row = html.TR()

            role = g_variant_data.roles[role_id]
            role_name = g_variant_data.name_table[role]

            # flag
            col = html.TD()
            role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{role_id}.jpg", title=role_name)
            col <= role_icon_img
            row <= col

            # role name
            col = html.TD()
            col <= role_name
            row <= col

            # player
            col = html.TD()
            pseudo_there = ""
            if role_id in role2pseudo:
                player_id_str = role2pseudo[role_id]
                player_id = int(player_id_str)
                pseudo_there = id2pseudo[player_id]
            col <= pseudo_there
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
                else:
                    flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
            col <= flag
            row <= col

            col = html.TD()
            flag = ""
            if role_id in needed_roles_list:
                if role_id in submitted_roles_list:
                    if role_id in agreed_roles_list:
                        flag = html.IMG(src="./images/ready.jpg", title="Prêt pour résoudre")
                    else:
                        flag = html.IMG(src="./images/not_ready.jpg", title="Pas prêt pour résoudre")
            col <= flag
            row <= col

            col = html.TD()
            flag = ""
            if role_id in vote_values_table:
                if vote_values_table[role_id]:
                    flag = html.IMG(src="./images/stop.png", title="Arrêter la partie")
                else:
                    flag = html.IMG(src="./images/continue.jpg", title="Continuer la partie")
            col <= flag
            row <= col

            game_admin_table <= row

        return game_admin_table

    def refresh():
        """ refresh """

        submitted_data = None
        votes = None

        def refresh_subroutine():

            # reload from server to see what changed from outside
            load_dynamic_stuff()
            nonlocal submitted_data
            submitted_data = common.get_roles_submitted_orders(g_game_id)
            if submitted_data is None:
                alert("Erreur chargement données de soumission")
                return

            # votes
            nonlocal votes
            votes = common.vote_reload(g_game_id)
            if votes is None:
                alert("Erreur chargement votes")
                return

            # avoids a warning
            votes = list(votes)

            my_sub_panel.clear()

            # clock
            stack_clock(my_sub_panel, SUPERVISE_REFRESH_PERIOD_SEC)
            my_sub_panel <= html.BR()

            # game status
            my_sub_panel <= g_game_status
            my_sub_panel <= html.BR()

            stack_role_flag(my_sub_panel)
            my_sub_panel <= html.BR()

        # changed from outside
        refresh_subroutine()

        # calculate deadline + grace
        time_unit = 60 if g_game_parameters_loaded['fast'] else 24 * 60 * 60
        deadline_loaded = g_game_parameters_loaded['deadline']
        grace_duration_loaded = g_game_parameters_loaded['grace_duration']
        force_point = deadline_loaded + time_unit * grace_duration_loaded
        time_stamp_now = time.time()

        # are we past ?
        if time_stamp_now > force_point:

            # avoids a warning
            submitted_data = dict(submitted_data)

            submitted_roles_list = submitted_data['submitted']
            agreed_roles_list = submitted_data['agreed']
            needed_roles_list = submitted_data['needed']

            missing_orders = list()
            for role_id in g_variant_data.roles:
                if role_id in needed_roles_list and role_id not in submitted_roles_list:
                    missing_orders.append(role_id)

            alterated = False
            if missing_orders:
                role_id = random.choice(missing_orders)
                civil_disorder_callback(None, role_id)
                role = g_variant_data.roles[role_id]
                role_name = g_variant_data.name_table[role]
                message = f"Désordre civil pour {role_name}"
                alterated = True
            else:
                missing_agreements = list()
                for role_id in g_variant_data.roles:
                    if role_id in submitted_roles_list and role_id not in agreed_roles_list:
                        missing_agreements.append(role_id)
                if missing_agreements:
                    role_id = random.choice(missing_agreements)
                    force_agreement_callback(None, role_id)
                    role = g_variant_data.roles[role_id]
                    role_name = g_variant_data.name_table[role]
                    message = f"Forçage accord pour {role_name}"
                    alterated = True

            if alterated:

                log_stack.insert(message)

                # changed from myself
                refresh_subroutine()

        game_admin_table = reload_game_admin_table(submitted_data, votes)
        my_sub_panel <= game_admin_table
        my_sub_panel <= html.BR()

        # put stack in log window
        log_window = html.DIV(id="log")
        log_stack.display(log_window)

        # display
        my_sub_panel <= log_window

    def cancel_supervise_callback(_, dialog):
        """ cancel_supervise_callback """

        dialog.close()

        load_option(None, 'position')

    def supervise_callback(_, dialog):
        """ supervise_callback """

        dialog.close()

        nonlocal id2pseudo
        id2pseudo = {v: k for k, v in g_players_dict.items()}

        nonlocal role2pseudo
        role2pseudo = {v: k for k, v in g_game_players_dict.items()}

        nonlocal log_stack
        log_stack = Logger()

        # initiates refresh
        refresh()

        # repeat
        global supervise_refresh_timer  # pylint: disable=invalid-name
        if supervise_refresh_timer is None:
            supervise_refresh_timer = timer.set_interval(refresh, SUPERVISE_REFRESH_PERIOD_SEC * 1000)  # refresh every x seconds

    id2pseudo = dict()
    role2pseudo = dict()
    log_stack = None

    # need to be connected
    if g_pseudo is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'position')
        return False

    # need to be game master
    if g_role_id != 0:
        alert("Vous ne semblez pas être l'arbitre de cette partie")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not waiting
    if g_game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not finished
    if g_game_parameters_loaded['current_state'] == 2:
        alert("La partie est déjà terminée")
        load_option(None, 'position')
        return False

    # game needs to be fast
    if not g_game_parameters_loaded['fast']:
        alert("Cette partie n'est pas une partie rapide")
        load_option(None, 'position')
        return False

    # since touchy, this requires a confirmation
    dialog = Dialog("On supervise vraiment la partie (cela peut entrainer des désordres civils) ?", ok_cancel=True)
    dialog.ok_button.bind("click", lambda e, d=dialog: supervise_callback(e, d))
    dialog.cancel_button.bind("click", lambda e, d=dialog: cancel_supervise_callback(e, d))

    return True


observe_refresh_timer = None  # pylint: disable=invalid-name


def observe():
    """ observe """

    ctx = None
    img = None

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        g_variant_data.render(ctx)

        # put the position
        g_position_data.render(ctx)

        # put the legends at the end
        g_variant_data.render_legends(ctx)

    def refresh():
        """ refresh """

        # reload from server to see what changed from outside
        load_dynamic_stuff()
        my_sub_panel.clear()

        # clock
        stack_clock(my_sub_panel, OBSERVE_REFRESH_PERIOD_SEC)
        my_sub_panel <= html.BR()

        # game status
        my_sub_panel <= g_game_status

        # create canvas
        map_size = g_variant_data.map_size
        canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
        nonlocal ctx
        ctx = canvas.getContext("2d")
        if ctx is None:
            alert("Il faudrait utiliser un navigateur plus récent !")
            return

        # put background (this will call the callback that display the whole map)
        nonlocal img
        img = common.read_image(g_variant_name_loaded, g_display_chosen)
        img.bind('load', callback_render)

        ratings = g_position_data.role_ratings()
        colours = g_position_data.role_colours()
        rating_colours_window = common.make_rating_colours_window(ratings, colours)

        report_window = common.make_report_window(g_report_loaded)

        # left side

        my_sub_panel <= canvas
        my_sub_panel <= rating_colours_window
        my_sub_panel <= report_window

    # game needs to be ongoing - not waiting
    if g_game_parameters_loaded['current_state'] == 0:
        alert("La partie n'est pas encore démarrée")
        load_option(None, 'position')
        return False

    # game needs to be ongoing - not finished
    if g_game_parameters_loaded['current_state'] == 2:
        alert("La partie est déjà terminée")
        load_option(None, 'position')
        return False

    # initiates refresh
    refresh()

    # repeat
    global observe_refresh_timer  # pylint: disable=invalid-name
    if observe_refresh_timer is None:
        observe_refresh_timer = timer.set_interval(refresh, OBSERVE_REFRESH_PERIOD_SEC * 1000)  # refresh every x seconds

    return True


def show_game_parameters():
    """ show_game_parameters """

    # game status
    my_sub_panel <= g_game_status
    my_sub_panel <= html.BR()

    game_params_table = html.TABLE()

    # table header
    thead = html.THEAD()
    for field_name in "Nom du paramètre", "Valeur pour la partie", "Explication sommaire", "Effet (ce qui change concrètement)", "Implémenté ?":
        col = html.TD(field_name)
        thead <= col
    game_params_table <= thead

    for key, value in g_game_parameters_loaded.items():

        if key in ['name', 'description', 'variant', 'deadline', 'current_state', 'current_advancement']:
            continue

        row = html.TR()

        parameter_name, explanation, effect, implemented = {
            'archive': ("archive", "la partie n'est pas jouée, elle est juste consultable", "L'arbitre peut passer des ordres, les dates limites ne sont pas gérées, le système autorise les résolutions sans tenir compte des soumissions des joueurs, le système ne réalise pas l'attribution des roles au démarrage de la partie", "OUI"),
            'anonymous': ("anonyme", "on sait pas qui joue quel rôle dans la partie", "Seul l'arbitre peut savoir qui joue et les joueurs ne savent pas qui a passé les ordres - effacé à la fin de la partie", "OUI"),
            'nomessage': ("pas de message", "on peut pas négocier - sauf avec l'arbitre", "Tout message joueur vers joueur est impossible - effacé à la fin de la partie", "OUI"),
            'nopress': ("pas de presse", "on ne peut pas déclarer - sauf l'arbitre", "Toute déclaration de joueur est impossible - effacé à la fin de la partie", "OUI"),
            'fast': ("rapide", "la partie est jouée en temps réel comme sur un plateau", "Les paramètres de calcul des dates limites sont en minutes et non en jours", "OUI"),
            'manual': ("attribution manuelle des rôle", "L'arbitre doit attribuer les roles", "Le système ne réalise pas l'attribution des roles au démarrage de la partie", "OUI"),
            'deadline_hour': ("heure de la date limite", "entre 0 et 23", "Heure à laquelle le système placera la date limite dans la journée si la synchronisation est souhaitée", "OUI"),
            'deadline_sync': ("synchronisation de la date limite", "oui ou non", "Le système synchronise la date limite à une heure précise dans la journée", "OUI"),
            'grace_duration': ("durée de la grâce", "en jours", "L'arbitre tolère un retard d'autant de jours avant de placer des désordres civils", "OUI"),
            'speed_moves': ("vitesse pour les mouvements", "en jours", "Le système ajoute autant de jours avant une résolution de mouvement pour une date limite", "OUI"),
            'speed_retreats': ("vitesse pour les retraites", "en jours", "Le système ajoute autant de jours avant une résolution de retraites pour une date limite", "OUI"),
            'speed_adjustments': ("vitesse pour les ajustements", "en jours", "Le système ajoute autant de jours avant une résolution d'ajustements pour une date limite", "OUI"),
            'cd_possible_moves': ("désordre civil possible pour les mouvements", "oui ou non", "Charge à l'arbitre de le respecter (pas de vérification serveur)", "-"),
            'cd_possible_retreats': ("désordre civil possible pour les retraites", "oui ou non", "Charge à l'arbitre de le respecter (pas de vérification serveur)", "-"),
            'cd_possible_builds': ("désordre civil possible pour les constructions", "oui ou non", "Charge à l'arbitre de le respecter (pas de vérification serveur)", "-"),
            'cd_possible_removals': ("désordre civil possible pour les suppressions", "oui ou non", "Charge à l'arbitre de le respecter (pas de vérification serveur)", "-"),
            'play_weekend': ("on joue le week-end", "oui ou non", "Le système pourra placer une date limite pendant le week-end", "OUI"),
            'access_code': ("code d'accès pour la partie", "(code de quatre chiffres)", "Le système demande un code pour rejoindre la partie", "NON"),
            'access_restriction_reliability': ("restriction d'accès sur la fiabilité", "(valeur)", "Un seuil de fiabilité est exigé pour rejoindre la partie", "NON"),
            'access_restriction_regularity': ("restriction d'accès sur la régularité", "(valeur)", "Un seuil de régularité est exigé pour rejoindre la partie", "NON"),
            'access_restriction_performance': ("restriction d'accès sur la performance", "(valeur)", "Un seuil de performance est exigé pour rejoindre la partie", "NON"),
            'nb_max_cycles_to_play': ("nombre maximum de cycles (années) à jouer", "(valeur)", "L'arbitre déclare la partie terminée si autant de cycles ont été joués", "-"),
            'victory_centers': ("nombre de centres pour la victoire", "(valeur)", "L'arbitre déclare la partie gagnée si un joueur possède autant de centres", "-")
        }[key]

        col1 = html.TD(html.B(parameter_name))
        row <= col1

        if value is False:
            parameter_value = "Non"
        elif value is True:
            parameter_value = "Oui"
        else:
            parameter_value = value

        col2 = html.TD(html.B(parameter_value))
        col2.style = {
            'color': 'blue',
        }
        row <= col2

        # some more info

        col3 = html.TD(explanation)
        row <= col3

        col4 = html.TD(effect)
        row <= col4

        col5 = html.TD(implemented)
        row <= col5

        game_params_table <= row

    my_sub_panel <= game_params_table

    return True


def show_players_in_game():
    """ show_players_in_game """

    # need to be connected
    if g_pseudo is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'position')
        return False

    # is game anonymous
    # TODO improve this with real admin account
    if not(g_pseudo == 'Palpatine' or g_role_id == 0 or not g_game_parameters_loaded['anonymous']):
        alert("Seul l'arbitre (ou l'administrateur du site) peut voir les joueurs d'une partie anonyme")
        load_option(None, 'position')
        return False

    id2pseudo = {v: k for k, v in g_players_dict.items()}

    game_players_table = html.TABLE()

    fields = ['flag', 'role', 'player']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'player': 'joueur', 'role': 'role'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_players_table <= thead

    role2pseudo = {v: k for k, v in g_game_players_dict.items()}

    for role_id in g_variant_data.roles:

        row = html.TR()

        if role_id <= 0:
            continue

        # role flag
        role = g_variant_data.roles[role_id]
        role_name = g_variant_data.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        # role name
        role = g_variant_data.roles[role_id]
        role_name = g_variant_data.name_table[role]

        col = html.TD(role_name)
        row <= col

        # player
        pseudo_there = ""
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        col = html.TD(pseudo_there)
        row <= col

        game_players_table <= row

    # game status
    my_sub_panel <= g_game_status
    my_sub_panel <= html.BR()

    my_sub_panel <= game_players_table

    # add the non allocated players
    dangling_players = [p for p in g_game_players_dict.keys() if g_game_players_dict[p] == - 1]
    if dangling_players:
        my_sub_panel <= html.BR()
        my_sub_panel <= html.EM("Les pseudos suivants sont alloués à la partie sans rôle:")
        for dangling_player_id_str in dangling_players:
            my_sub_panel <= html.BR()
            dangling_player_id = int(dangling_player_id_str)
            dangling_player = id2pseudo[dangling_player_id]
            my_sub_panel <= html.B(html.EM(dangling_player))

    return True


def show_orders_submitted_in_game():
    """ show_orders_submitted_in_game """

    # if user identified ?
    if g_pseudo is None:
        alert("Il faut se connecter au préalable")
        load_option(None, 'position')
        return False

    # is player in game ?
    # TODO improve this with real admin account
    if not(g_pseudo == 'Palpatine' or g_role_id is not None):
        alert("Seuls les participants à une partie (ou l'administrateur du site) peuvent voir le statut des ordres pour une partie non anonyme")
        load_option(None, 'position')
        return False

    # game anonymous
    # TODO improve this with real admin account
    if not(g_pseudo == 'Palpatine' or g_role_id == 0 or not g_game_parameters_loaded['anonymous']):
        alert("Seul l'arbitre (ou l'administrateur du site) peut voir le statut des ordres  pour une partie anonyme")
        load_option(None, 'position')
        return False

    # you will at least get your own role
    submitted_data = common.get_roles_submitted_orders(g_game_id)
    if submitted_data is None:
        alert("Erreur chargement données de soumission")
        load_option(None, 'position')
        return False

    # just to avoid a warning
    submitted_data = dict(submitted_data)

    role2pseudo = {v: k for k, v in g_game_players_dict.items()}

    id2pseudo = {v: k for k, v in g_players_dict.items()}

    game_players_table = html.TABLE()

    fields = ['flag', 'role', 'player', 'orders', 'agreement']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'flag': 'drapeau', 'role': 'role', 'player': 'joueur', 'orders': 'ordres', 'agreement': 'accord'}[field]
        col = html.TD(field_fr)
        thead <= col
    game_players_table <= thead

    for role_id in g_variant_data.roles:

        row = html.TR()

        if role_id <= 0:
            continue

        # role flag
        role = g_variant_data.roles[role_id]
        role_name = g_variant_data.name_table[role]
        role_icon_img = html.IMG(src=f"./variants/{g_variant_name_loaded}/{g_display_chosen}/roles/{role_id}.jpg", title=role_name)

        if role_icon_img:
            col = html.TD(role_icon_img)
        else:
            col = html.TD()
        row <= col

        role = g_variant_data.roles[role_id]
        role_name = g_variant_data.name_table[role]

        col = html.TD(role_name)
        row <= col

        # player
        pseudo_there = ""
        if role_id in role2pseudo:
            player_id_str = role2pseudo[role_id]
            player_id = int(player_id_str)
            pseudo_there = id2pseudo[player_id]
        col = html.TD(pseudo_there)
        row <= col

        # orders are in
        submitted_roles_list = submitted_data['submitted']
        needed_roles_list = submitted_data['needed']
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                flag = html.IMG(src="./images/orders_in.png", title="Les ordres sont validés")
            else:
                flag = html.IMG(src="./images/orders_missing.png", title="Les ordres ne sont pas validés")
        else:
            flag = ""
        col = html.TD(flag)
        row <= col

        # agreed
        col = html.TD()
        flag = ""
        submitted_roles_list = submitted_data['submitted']
        agreed_roles_list = submitted_data['agreed']
        needed_roles_list = submitted_data['needed']
        if role_id in needed_roles_list:
            if role_id in submitted_roles_list:
                if role_id in agreed_roles_list:
                    flag = html.IMG(src="./images/ready.jpg", title="Prêt pour résoudre")
                else:
                    flag = html.IMG(src="./images/not_ready.jpg", title="Pas prêt pour résoudre")
        col <= flag
        row <= col

        game_players_table <= row

    # game status
    my_sub_panel <= g_game_status
    my_sub_panel <= html.BR()

    my_sub_panel <= game_players_table

    return True


my_panel = html.DIV()
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = None  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="play")
my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'position':
        status = show_position()
    if item_name == 'ordonner':
        status = submit_orders()
    if item_name == 'taguer':
        status = submit_communication_orders()
    if item_name == 'négocier':
        status = negotiate()
    if item_name == 'déclarer':
        status = declare()
    if item_name == 'voter':
        status = vote()
    if item_name == 'historique':
        status = show_history()
    if item_name == 'arbitrer':
        status = game_master()
    if item_name == 'superviser':
        status = supervise()
    if item_name == 'observer':
        status = observe()
    if item_name == 'paramètres':
        status = show_game_parameters()
    if item_name == 'joueurs':
        status = show_players_in_game()
    if item_name == 'ordres':
        status = show_orders_submitted_in_game()

    if not status:
        return

    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item

    # quitting superviser : clear timer
    global supervise_refresh_timer  # pylint: disable=invalid-name
    if item_name_selected != 'superviser':
        if supervise_refresh_timer is not None:
            timer.clear_interval(supervise_refresh_timer)
            supervise_refresh_timer = None

    # quitting observer : clear timer
    global observe_refresh_timer  # pylint: disable=invalid-name
    if item_name_selected != 'observer':
        if observe_refresh_timer is not None:
            timer.clear_interval(observe_refresh_timer)
            observe_refresh_timer = None


countdown_timer = None  # pylint: disable=invalid-name


def render(panel_middle):
    """ render """

    # always back to top
    global item_name_selected  # pylint: disable=invalid-name

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    global g_game  # pylint: disable=invalid-name
    g_game = storage['GAME']

    # from game name get game id
    global g_game_id  # pylint: disable=invalid-name
    g_game_id = common.get_game_id(g_game)
    if g_game_id is None:
        alert("Erreur chargement identifiant partie")
        return

    # Connecté mais pas joueur
    # Pas connecté
    item_name_selected = 'position'  # pylint: disable=invalid-name

    global g_pseudo  # pylint: disable=invalid-name
    g_pseudo = None
    if 'PSEUDO' in storage:
        g_pseudo = storage['PSEUDO']

    # from game_id and token get role

    global g_role_id  # pylint: disable=invalid-name
    g_role_id = None
    if g_pseudo is not None:
        g_role_id = common.get_role_allocated_to_player_in_game(g_game_id)

    load_static_stuff()
    load_dynamic_stuff()
    load_special_stuff()

    # initiates new countdown
    countdown()

    # start countdown (must not be inside a timed function !)
    global countdown_timer  # pylint: disable=invalid-name
    if countdown_timer is None:
        print("start (from main) countdown()")
        countdown_timer = timer.set_interval(countdown, 1000)

    # game not started, visiting probably to see parameters
    if g_game_parameters_loaded['current_state'] == 0:
        item_name_selected = 'paramètres'

    # game finished, visiting probably to see history
    elif g_game_parameters_loaded['current_state'] == 2:
        item_name_selected = 'historique'

    else:

        if g_role_id is not None:

            if g_role_id == 0:
                # Arbitre
                item_name_selected = 'arbitrer'
            else:
                # Joueur
                item_name_selected = 'ordonner'

        else:

            # Admin wants to see whose orders are missing
            # TODO improve this with real admin account
            if g_pseudo == "Palpatine":
                # Admin
                item_name_selected = 'ordres'

    load_option(None, item_name_selected)
    panel_middle <= my_panel
