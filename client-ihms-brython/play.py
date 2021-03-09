""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import mapping

OPTIONS = ['show position', 'submit orders', 'negotiate', 'show game parameters', 'show players in game']

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

    def debug_callback(_):
        """ debug_callback """
        print(f"debug_callback")

    def callback_click(event):
        """ callback_click """
        print(f"click {event=} {event.buttons=} {event.button=}  {event.x=} {event.y=}")

    def callback_dblclick(event):
        """ callback_dblclick """
        print(f"dblclick {event=} {event.buttons=} {event.button=}  {event.x=} {event.y=}")

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

        # put the clickable zones
        canvas.bind("click", callback_click)
        canvas.bind("dblclick", callback_dblclick)

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
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

    input_debug = html.INPUT(type="submit", value="debug")
    input_debug.bind("click", debug_callback)

    # left hand side
    display_left = html.TD()
    display_left <= canvas
    display_left <= report_window

    # right hand side
    buttons_right = html.TD()
    buttons_right <= input_debug

    my_table_row = html.TR()
    my_table_row <= display_left
    my_table_row <= buttons_right
    my_table = html.TABLE()
    my_table <= my_table_row
    my_sub_panel <= my_table

def negotiate():
    """ negotiate """

    dummy = html.P("negotiate")
    my_sub_panel <= dummy


def show_game_parameters():
    """ show_game_parameters """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']
    parameters_loaded = None

    def display_all_parameters_reload():
        """ change_description_reload """

        status = True

        def local_noreply_callback(_):
            """ local_noreply_callback """
            nonlocal status
            alert("Problem (no answer from server)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal parameters_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error loading all parameters: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem loading all parameters: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                status = False
                return

            parameters_loaded = req_result

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        # getting game data : do not need a token
        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    status = display_all_parameters_reload()
    if not status:
        return

    game_params_table = html.TABLE()
    game_params_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }
    for key, value in parameters_loaded.items():
        row = html.TR()
        row.style = {
            "border": "solid",
        }

        col1 = html.TD(key)
        col1.style = {
            "border": "solid",
        }
        row <= col1

        if key == 'deadline':
            deadline_loaded = value
            datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
            deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
            deadline_loaded_hour = f"{datetime_deadline_loaded.hour}:{datetime_deadline_loaded.minute}"
            deadline_loaded = f"{deadline_loaded_day} {deadline_loaded_hour}"
            value = deadline_loaded

        if key == 'current_state':
            state_loaded = value
            for possible_state in config.STATE_CODE_TABLE:
                if config.STATE_CODE_TABLE[possible_state] == state_loaded:
                    state_loaded = possible_state
                    break
            value = state_loaded

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
    fields = ['player', 'role']

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

        # role
        col = html.TD(role_id)
        col.style = {
            "border": "solid",
        }
        row <= col

        game_players_table <= row

    my_sub_panel <= game_players_table


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'show position':
        show_position()
    if item_name == 'submit orders':
        submit_orders()
    if item_name == 'negotiate':
        negotiate()
    if item_name == 'show game parameters':
        show_game_parameters()
    if item_name == 'show players in game':
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
