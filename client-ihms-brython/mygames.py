""" home """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import tools
import config
import mapping
import selection
import index  # circular import


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

    def select_game_callback(_, game):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie')

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

    time_stamp_now = time.time()

    games_table = html.TABLE()
    games_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    fields = ['name', 'variant', 'deadline', 'current_state', 'current_advancement', 'role_played', 'orders_submitted', 'new_declarations', 'new_messages', 'jump']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'variant': 'variante', 'deadline': 'date limite', 'current_state': 'état', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'orders_submitted': 'ordres soumis', 'new_declarations': 'nouvelle déclarations', 'new_messages': 'nouveau messages', 'jump': 'sauter'}[field]
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
        display_chosen = tools.get_display_from_variant(variant_name_loaded)

        parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

        # build variant data
        variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

        role_id = common.get_role_allocated_to_player(game_id, player_id)
        if role_id is None:
            continue
        data['role_played'] = role_id

        submitted_data = common.get_roles_submitted_orders(game_id)
        if submitted_data is None:
            return

        # just to avoid a warning
        submitted_data = dict(submitted_data)

        data['orders_submitted'] = None
        data['new_declarations'] = None
        data['new_messages'] = None
        data['jump'] = None

        row = html.TR()
        row.style = {
            "border": "solid",
        }
        for field in fields:

            value = data[field]
            colour = 'black'

            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
                deadline_loaded_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded_str

                # we are after deadline : red
                if time_stamp_now > deadline_loaded:
                    colour = 'red'
                # deadline is today : orange
                elif time_stamp_now > deadline_loaded - 24 * 3600:
                    colour = 'orange'

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
                    role = variant_data.roles[role_id]
                    role_name = variant_data.name_table[role]
                    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
                    value = role_icon_img

            if field == 'orders_submitted':
                submitted_roles_list = submitted_data['submitted']
                needed_roles_list = submitted_data['needed']
                if role_id in submitted_roles_list:
                    flag = html.IMG(src="./data/green_tick.jpg", title="Les ordres sont validés")
                elif role_id in needed_roles_list:
                    flag = html.IMG(src="./data/red_close.jpg", title="Les ordres ne sont pas validés")
                else:
                    flag = ""
                value = flag

            if field == 'new_declarations':

                # get time stamp of last visit of declarations
                time_stamp_last_visit = common.last_visit_load(game_id, common.DECLARATIONS_TYPE)
                if time_stamp_last_visit is None:
                    return
                time_stamp_last_event = common.last_game_declaration(game_id)
                if time_stamp_last_event is None:
                    return

                # popup if new
                popup = ""
                if time_stamp_last_event > time_stamp_last_visit:
                    popup = html.IMG(src="./data/new_content.gif", title="Nouvelle(s) déclaration(s)")
                value = popup

            if field == 'new_messages':

                # get time stamp of last visit of declarations
                time_stamp_last_visit = common.last_visit_load(game_id, common.MESSAGES_TYPE)
                if time_stamp_last_visit is None:
                    return
                time_stamp_last_event = common.last_game_message(game_id, role_id)
                if time_stamp_last_event is None:
                    return

                # popup if new
                popup = ""
                if time_stamp_last_event > time_stamp_last_visit:
                    popup = html.IMG(src="./data/new_content.gif", title="Nouveau(x) message(s)")
                value = popup

            if field == 'jump':
                game_name = data['name']
                form = html.FORM()
                input_jump_game = html.INPUT(type="submit", value="sauter à pied joints dans la partie")
                input_jump_game.bind("click", lambda e, g=game_name: select_game_callback(e, g))
                form <= input_jump_game
                value = form

            col = html.TD(value)
            col.style = {
                "border": "solid",
                'color': colour
            }

            row <= col

        games_table <= row

    my_panel <= games_table
    my_panel <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")

    special_legend = html.CODE(f"Pour information, date et heure actuellement : {date_now_gmt_str}")
    my_panel <= special_legend


def render(panel_middle):
    """ render """
    my_games()
    panel_middle <= my_panel
