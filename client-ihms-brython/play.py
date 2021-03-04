""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import mapping

OPTIONS = ['submit orders', 'negotiate', 'show game parameters', 'show players in game']

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


def get_display_from_variant(variant):
    """ get_display_from_variant """

    # TODO : make it possible to choose which display users wants (descartes/hasbro)
    # At least test it
    assert variant == 'standard'
    return "stabbeur"


def submit_orders():
    """ submit_orders """

    variant_name_loaded = None
    variant_content_loaded = None
    variant_data = None
    position_loaded = None
    position_data = None

    def callback_load(_):
        """ callback_load """

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

    # now get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # should be a user choice
    display_chosen = get_display_from_variant(variant_name_loaded)

    # get parameters from display chose

    parameters_file_name = f"./variants/{variant_name_loaded}/{display_chosen}/parameters.json"
    with open(parameters_file_name, "r") as read_file:
        parameters_read = json.load(read_file)

    # build variant data
    variant_data = mapping.Variant(variant_content_loaded, parameters_read)

    # now the position

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

    # put background
    img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/map.png")
    img.bind('load', callback_load)

    my_sub_panel <= canvas

    additional = html.P("additional stuff under the map")
    my_sub_panel <= additional


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
