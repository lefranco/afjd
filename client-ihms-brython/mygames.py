""" home """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import config
import mapping

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

    games_dict = common.get_games_data()
    if games_dict is None:
        return

    games_table = html.TABLE()
    games_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    fields = ['name', 'variant', 'deadline', 'current_state', 'current_advancement', 'role_played', 'orders_submitted', 'new_declarations', 'new_messages']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'variant': 'variante', 'deadline': 'date limite', 'current_state': 'état', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'orders_submitted': 'ordres soumis', 'new_declarations': 'nouvelle déclarations', 'new_messages': 'nouveau messages'}[field]
        col = html.TD(field_fr)
        col.style = {
            "border": "solid",
            "font-weight": "bold",
        }
        thead <= col
    games_table <= thead

    games_id_player = [int(n) for n in player_games.keys()]

    for game_id_str, data in sorted(games_dict.items(), key=lambda g: g[1]['name']):

        game_id = int(game_id_str)
        if game_id not in games_id_player:
            continue

        # variant is available
        variant_name_loaded = data['variant']

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

        role_id = common.get_role_allocated_to_player(game_id, player_id)
        if role_id is None:
            return
        data['role_played'] = role_id

        submitted_data = common.get_roles_submitted_orders(game_id)
        if submitted_data is None:
            return
        # just to avoid a warning
        submitted_data = dict(submitted_data)

        data['orders_submitted'] = None
        data['new_declarations'] = None
        data['new_messages'] = None

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

            if field == 'current_advancement':
                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'role_played':
                if role_id == -1:
                    value = "Affecté"
                else:
                    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg")
                    value = role_icon_img

            if field == 'orders_submitted':
                submitted_roles_list = submitted_data['submitted']
                needed_roles_list = submitted_data['needed']
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./data/orders_are_in.gif")
                elif role_id in needed_roles_list:
                    flag = html.IMG(src="./data/orders_are_not_in.gif")
                else:
                    flag = ""
                value = flag

            if field == 'new_declarations':

                # get time stamp of last visit of declarations
                time_stamp_last_visit = common.last_visit_load(game_id, common.DECLARATIONS_TYPE)
                time_stamp_last_event = common.last_game_declaration(game_id)

                # popup if new
                popup = ""
                if time_stamp_last_event > time_stamp_last_visit:
                    popup = html.IMG(src="./data/new.gif")
                value = popup

            if field == 'new_messages':

                # get time stamp of last visit of declarations
                time_stamp_last_visit = common.last_visit_load(game_id, common.MESSAGES_TYPE)
                time_stamp_last_event = common.last_game_message(game_id, role_id)

                # popup if new
                popup = ""
                if time_stamp_last_event > time_stamp_last_visit:
                    popup = html.IMG(src="./data/new.gif")
                value = popup

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
