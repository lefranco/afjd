""" master """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error

import config
import tools
import common
import mapping
import selection
import index  # circular import


my_panel = html.DIV(id="opportunities")


def get_recruiting_games():
    """ get_recruiting_games """

    recruiting_games_list = None

    def reply_callback(req):
        nonlocal recruiting_games_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupartion de la liste des parties qui recrutent : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupartion de la liste des parties qui recrutent : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        req_result = json.loads(req.text)
        recruiting_games_list = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games-recruiting"

    # getting recruiting games list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return recruiting_games_list


def my_opportunities():
    """ my_opportunities """

    def join_game_callback(_, game):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Erreur à l'inscription à la partie : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'inscription à la partie : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            messages = "<br>".join(req_result['msg'].split('\n'))
            InfoDialog("OK", f"Vous avez rejoint la partie : {messages}", remove_after=config.REMOVE_AFTER)

        game_id = common.get_game_id(game)
        if game_id is None:
            return

        json_dict = {
            'game_id': game_id,
            'player_pseudo': pseudo,
            'pseudo': pseudo,
            'delete': 0
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/allocations"

        # adding allocation : need a token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def join_and_select_game_callback(_, game):
        """ join_and_select_game_callback """

        # action of selecting game
        storage['GAME'] = game
        selection.show_game_selected()

        # action of putting myself in game
        join_game_callback(_, game)

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    my_panel.clear()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    recruiting_games_list = get_recruiting_games()
    if recruiting_games_list is None:
        return

    # to avoid warning
    recruiting_games_list = list(recruiting_games_list)

    recruiting_games_dict = {tr[0]: {'allocated': tr[1], 'capacity': tr[2]} for tr in recruiting_games_list}

    games_dict = common.get_games_data()
    if games_dict is None:
        return

    games_dict_recruiting = {k: v for k, v in games_dict.items() if int(k) in recruiting_games_dict}

    time_stamp_now = time.time()

    games_table = html.TABLE()

    fields = ['name', 'variant', 'deadline', 'current_state', 'current_advancement', 'allocated', 'capacity', 'join']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'variant': 'variante', 'deadline': 'date limite', 'current_state': 'état', 'current_advancement': 'saison à jouer', 'allocated': 'alloué (dont arbitre)', 'capacity': 'capacité (dont arbitre)', 'join': 'rejoindre'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    for game_id_str, data in sorted(games_dict_recruiting.items(), key=lambda g: g[1]['name']):

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content
        variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
        if not variant_content_loaded:
            return

        # selected display (user choice)
        display_chosen = tools.get_display_from_variant(variant_name_loaded)

        parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

        # build variant data
        variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

        data['allocated'] = None
        data['capacity'] = None
        data['join'] = None

        row = html.TR()
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

            if field == 'allocated':
                value = recruiting_games_dict[int(game_id_str)]['allocated']

            if field == 'capacity':
                value = recruiting_games_dict[int(game_id_str)]['capacity']

            if field == 'join':
                game_name = data['name']
                form = html.FORM()
                input_join_game = html.INPUT(type="submit", value="Eh, il y a de la place. J'en profite !")
                input_join_game.bind("click", lambda e, g=game_name: join_and_select_game_callback(e, g))
                form <= input_join_game
                value = form

            col = html.TD(value)
            col.style = {
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
    my_opportunities()
    panel_middle <= my_panel
