""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime

from browser import html, ajax, alert  # pylint: disable=import-error

import config
import common

my_panel = html.DIV(id="players")

OPTIONS = ['les joueurs', 'les parties', 'les arbitres']



def show_players_data():
    """ show_players_data """

    players_dict = common.get_players_data()

    if not players_dict:
        return

    players_table = html.TABLE()
    players_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    # TODO : make it possible to sort etc...
    fields = ['pseudo', 'first_name', 'family_name', 'residence', 'nationality', 'time_zone']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'first_name': 'prénom', 'family_name': 'nom', 'residence': 'résidence','nationality': 'nationalité', 'time_zone': 'fuseau horaire'}[field]
        col = html.TD(field_fr)
        col.style = {
            "border": "solid",
            "font-weight": "bold",
        }
        thead <= col
    players_table <= thead

    for data in sorted(players_dict.values(), key=lambda g: g['pseudo']):
        row = html.TR()
        row.style = {
            "border": "solid",
        }
        for field in fields:
            value = data[field]
            col = html.TD(value)
            col.style = {
                "border": "solid",
            }
            row <= col
        players_table <= row

    my_sub_panel <= players_table


def show_games_data():
    """ show_games_data """

    games_dict = common.get_games_data()

    if not games_dict:
        return

    games_table = html.TABLE()
    games_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    # TODO : make it possible to sort etc...
    fields = ['name', 'variant', 'deadline', 'current_state', 'current_advancement']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'variant': 'variante', 'deadline': 'date limite', 'current_state': 'état', 'current_advancement': 'avancement'}[field]
        col = html.TD(field_fr)
        col.style = {
            "border": "solid",
            "font-weight": "bold",
        }
        thead <= col
    games_table <= thead

    for data in sorted(games_dict.values(), key=lambda g: g['name']):
        row = html.TR()
        row.style = {
            "border": "solid",
        }
        for field in fields:
            value = data[field]
            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour}:{datetime_deadline_loaded.minute}"
                deadline_loaded = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded
            if field == 'current_state':
                state_loaded = value
                for possible_state in config.STATE_CODE_TABLE:
                    if config.STATE_CODE_TABLE[possible_state] == state_loaded:
                        state_loaded = possible_state
                        break
                value = state_loaded
            col = html.TD(value)
            col.style = {
                "border": "solid",
            }
            row <= col
        games_table <= row

    my_sub_panel <= games_table


def get_game_masters_data():
    """ get_game_masters_data """

    game_masters_dict = None

    def reply_callback(req):
        nonlocal game_masters_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting game/game masters list: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting game/game masters list: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        req_result = json.loads(req.text)
        game_masters_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/allocations"

    # getting allocations : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(game_masters_dict)


def show_game_masters_data():
    """ show_game_masters_data """

    # get the games
    games_dict = common.get_games_data()

    if not games_dict:
        return

    # to avoid a warning
    games_dict = dict(games_dict)

    # get the players (masters)
    players_dict = common.get_players_data()

    if not players_dict:
        return

    # get the link (allocations) of game masters
    game_masters_list = get_game_masters_data()

    if not game_masters_list:
        return

    game_masters_table = html.TABLE()
    game_masters_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    # TODO : make it possible to sort etc...
    fields = ['game', 'master']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'game': 'partie', 'master': 'arbitre'}[field]
        col = html.TD(field_fr)
        col.style = {
            "border": "solid",
            "font-weight": "bold",
        }
        thead <= col
    game_masters_table <= thead

    for data in sorted(game_masters_list, key=lambda d: games_dict[str(d['game'])]['name']):
        row = html.TR()
        row.style = {
            "border": "solid",
        }
        for field in fields:
            value_index = str(data[field])
            if field == 'game':
                value_data = games_dict[value_index]
                value = value_data['name']
            if field == 'master':
                value_data = players_dict[value_index]
                value = value_data['pseudo']
            col = html.TD(value)
            col.style = {
                "border": "solid",
            }
            row <= col
        game_masters_table <= row

    my_sub_panel <= game_masters_table


my_panel = html.DIV(id="players_games")
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


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'les joueurs':
        show_players_data()
    if item_name == 'les parties':
        show_games_data()
    if item_name == 'les arbitres':
        show_game_masters_data()

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
