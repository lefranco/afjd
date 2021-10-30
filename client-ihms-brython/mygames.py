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
                alert(f"Erreur à la récuperation de la liste des parties du joueur : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récuperation de la liste des parties du joueur : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        player_games_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/player-allocations/{player_id}"

    # getting player games playing in list : need token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return dict(player_games_dict)


def my_games(state):
    """ my_games """

    def select_game_callback(_, game):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    overall_time_before = time.time()

    my_panel.clear()

    # title
    for state_name in config.STATE_CODE_TABLE:
        if config.STATE_CODE_TABLE[state_name] == state:
            state_displayed_name = state_name
            break
    title = html.H2(f"Parties qui sont : {state_displayed_name}")
    my_panel <= title

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
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

    fields = ['name', 'variant', 'deadline', 'current_advancement', 'role_played', 'all_orders_submitted', 'orders_submitted', 'new_declarations', 'new_messages', 'jump']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'variant': 'variante', 'deadline': 'date limite', 'current_advancement': 'saison à jouer', 'role_played': 'rôle joué', 'all_orders_submitted': 'ordres soumis accessibles', 'orders_submitted': 'ordres soumis par moi', 'new_declarations': 'nouvelle déclarations', 'new_messages': 'nouveau messages', 'jump': 'aller dans la partie'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    games_id_player = [int(n) for n in player_games.keys()]

    # for optimization
    variant_data_memoize_table = dict()
    variant_content_memoize_table = dict()

    number_games = 0

    for game_id_str, data in sorted(games_dict.items(), key=lambda g: g[1]['name']):

        # do not display finished games
        if data['current_state'] != state:
            continue

        game_id = int(game_id_str)
        if game_id not in games_id_player:
            continue

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

        # old code before optimization
        #  variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
        #  if not variant_content_loaded:
        #      return

        # selected display (user choice)
        display_chosen = tools.get_display_from_variant(variant_name_loaded)

        parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

        # build variant data

        # this is an optimisation

        # new code after optimization
        variant_name_loaded_str = str(variant_name_loaded)
        variant_content_loaded_str = str(variant_content_loaded)
        parameters_read_str = str(parameters_read)
        if (variant_name_loaded_str, variant_content_loaded_str, parameters_read_str) not in variant_data_memoize_table:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            variant_data_memoize_table[(variant_name_loaded_str, variant_content_loaded_str, parameters_read_str)] = variant_data
        else:
            variant_data = variant_data_memoize_table[(variant_name_loaded_str, variant_content_loaded_str, parameters_read_str)]

        # old code before optimization
        #  variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

        role_id = common.get_role_allocated_to_player(game_id)

        number_games += 1

        data['role_played'] = role_id

        submitted_data = None
        submitted_data = common.get_roles_submitted_orders(game_id)
        if submitted_data is None:
            return

        # just to avoid a warning
        submitted_data = dict(submitted_data)

        data['all_orders_submitted'] = None
        data['orders_submitted'] = None
        data['new_declarations'] = None
        data['new_messages'] = None
        data['jump'] = None

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

            if field == 'current_advancement':
                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'role_played':
                value = ""
                if role_id is None:
                    value = "Affecté à la partie"
                else:
                    role = variant_data.roles[role_id]
                    role_name = variant_data.name_table[role]
                    role_icon_img = html.IMG(src=f"./variants/{variant_name_loaded}/{display_chosen}/roles/{role_id}.jpg", title=role_name)
                    value = role_icon_img

            if field == 'all_orders_submitted':

                value = ""
                if role_id is None:
                    value = "Pas de rôle"
                else:
                    submitted_roles_list = submitted_data['submitted']
                    nb_submitted = len(submitted_roles_list)
                    needed_roles_list = submitted_data['needed']
                    nb_needed = len(needed_roles_list)
                    stats = f"{nb_submitted}/{nb_needed}"
                    value = stats
                    colour = 'black'
                    if nb_submitted >= nb_needed:
                        # we have all orders : green
                        colour = 'green'
                    elif nb_submitted == 0:
                        # we have no orders : red
                        colour = 'red'

            if field == 'orders_submitted':

                value = ""
                submitted_roles_list = submitted_data['submitted']
                needed_roles_list = submitted_data['needed']
                if role_id is None:
                    value = "Pas de rôle"
                else:
                    if role_id in submitted_roles_list:
                        flag = html.IMG(src="./data/green_tick.jpg", title="Les ordres sont validés")
                        value = flag
                    elif role_id in needed_roles_list:
                        flag = html.IMG(src="./data/red_close.jpg", title="Les ordres ne sont pas validés")
                        value = flag

            if field == 'new_declarations':

                value = ""
                if role_id is not None:
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

                value = ""
                if role_id is not None:
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

    my_panel <= html.BR()
    my_panel <= html.BR()

    for other_state in range(len(config.STATE_CODE_TABLE)):

        if other_state != state:

            # state name
            for state_name in config.STATE_CODE_TABLE:
                if config.STATE_CODE_TABLE[state_name] == other_state:
                    state_displayed_name = state_name
                    break

            input_change_state = html.INPUT(type="submit", value=state_displayed_name)
            input_change_state.bind("click", lambda _, s=other_state: my_games(s))

            my_panel <= input_change_state
            my_panel <= html.BR()
            my_panel <= html.BR()


def render(panel_middle):
    """ render """
    my_games(1)
    panel_middle <= my_panel
