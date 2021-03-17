""" home """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import config

my_panel = html.DIV(id="my_games")


def get_player_games_playing_in(player_id):
    """ get_player_games_playing_in """

    player_games_dict = None

    def reply_callback(req):
        nonlocal player_games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Error getting player games playing in list: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting player games playing in  list: {req_result['msg']}")
            else:
                alert("Undocumented issue from server")
            return

        req_result = json.loads(req.text)
        player_games_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/player-allocations/{player_id}"

    # getting player games playing in list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict(player_games_dict)


def my_games():
    """ my_games """

    my_panel.clear()

    if 'PSEUDO' not in storage:
        alert("Il faut se loguer au préalable")
        return

    pseudo = storage['PSEUDO']

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        return

    player_games = get_player_games_playing_in(player_id)
    if player_games is None:
        return

    print(f"{player_games=}")

    games_dict = common.get_games_data()
    if games_dict is None:
        return

    print(f"{games_dict=}")

    games_table = html.TABLE()
    games_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

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

    games_id_player = [int(n) for n in player_games.keys()]

    print(f"{games_id_player=}")

    for game_id_str, data in sorted(games_dict.items(), key=lambda g: g[1]['name']):

        game_id = int(game_id_str)
        print(f"{game_id=}")
        if game_id not in games_id_player:
            continue

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
                deadline_loaded = f"{deadline_loaded_day} {deadline_loaded_hour}"
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

    my_panel <= games_table


def render(panel_middle):
    """ render """
    my_games()
    panel_middle <= my_panel
