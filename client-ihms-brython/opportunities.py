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
my_panel.attrs['style'] = 'display: table'


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

    def select_game_callback(_, game):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

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

    overall_time_before = time.time()

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

    fields = ['name', 'variant', 'description', 'deadline', 'current_state', 'current_advancement', 'allocated', 'capacity', 'jump_here', 'join']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'variant': 'variante', 'description': 'description', 'deadline': 'date limite', 'current_state': 'état', 'current_advancement': 'saison à jouer', 'allocated': 'alloué (dont arbitre)', 'capacity': 'capacité (dont arbitre)', 'jump_here': 'partie', 'join': 'rejoindre'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    # for optimization
    variant_data_memoize_table = dict()
    variant_content_memoize_table = dict()

    number_games = 0

    for game_id_str, data in sorted(games_dict_recruiting.items(), key=lambda g: g[1]['name']):

        number_games += 1

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        # this is an optimisation

        # new code after optimization
        if variant_name_loaded not in variant_content_memoize_table:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                return
            variant_content_memoize_table[variant_name_loaded] = variant_content_loaded
        else:
            variant_content_loaded = variant_content_memoize_table[variant_name_loaded]

        # selected display (user choice)
        display_chosen = tools.get_display_from_variant(variant_name_loaded)

        parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

        # build variant data

        variant_name_loaded_str = str(variant_name_loaded)
        variant_content_loaded_str = str(variant_content_loaded)
        parameters_read_str = str(parameters_read)
        if (variant_name_loaded_str, variant_content_loaded_str, parameters_read_str) not in variant_data_memoize_table:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            variant_data_memoize_table[(variant_name_loaded_str, variant_content_loaded_str, parameters_read_str)] = variant_data
        else:
            variant_data = variant_data_memoize_table[(variant_name_loaded_str, variant_content_loaded_str, parameters_read_str)]

        data['allocated'] = None
        data['capacity'] = None
        data['jump_here'] = None
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

                time_unit = 60 if data['fast'] else 24 * 60 * 60

                # we are after deadline + grace
                if time_stamp_now > deadline_loaded + time_unit * data['grace_duration']:
                    colour = config.PASSED_GRACE_COLOR
                # we are after deadline
                elif time_stamp_now > deadline_loaded:
                    colour = config.PASSED_DEADLINE_COLOR
                # deadline is today
                elif time_stamp_now > deadline_loaded - time_unit:
                    colour = config.APPROACHING_DEADLINE_COLOR

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

            if field == 'jump_here':
                game_name = data['name']
                form = html.FORM()
                input_jump_game = html.INPUT(type="submit", value="consulter")
                input_jump_game.bind("click", lambda e, g=game_name: select_game_callback(e, g))
                form <= input_jump_game
                value = form

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

    my_panel <= html.BR()
    my_panel <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before
    my_panel <= f"Temps de chargement de la page {elapsed}"
    if number_games:
        my_panel <= f" soit {elapsed/number_games} par partie"


def render(panel_middle):
    """ render """
    my_opportunities()
    panel_middle <= my_panel
