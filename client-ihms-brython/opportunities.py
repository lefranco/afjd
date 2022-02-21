""" master """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error

import config
import interface
import common
import mapping
import selection
import memoize
import index  # circular import


MY_PANEL = html.DIV(id="opportunities")
MY_PANEL.attrs['style'] = 'display: table'


def get_recruiting_games():
    """ get_recruiting_games : retuens empty list if erroro or not game"""

    recruiting_games_list = []

    def reply_callback(req):
        nonlocal recruiting_games_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération de la liste des parties qui recrutent : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération de la liste des parties qui recrutent : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return

        recruiting_games_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games-recruiting"

    # getting recruiting games list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return recruiting_games_list


def my_opportunities(sort_by=None):
    """ my_opportunities """

    def select_game_callback(_, game_name, game_data_sel):
        """ select_game_callback """

        # action of selecting game
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_ID'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_VARIANT'] = game_variant

        InfoDialog("OK", f"Partie sélectionnée : {game_name} - cette information est rappelée en bas de la page", remove_after=config.REMOVE_AFTER)
        selection.show_game_selected()

        # action of going to game page
        index.load_option(None, 'jouer la partie sélectionnée')

    def join_and_select_game_callback(evt, game_name, game_data_sel):
        """ join_and_select_game_callback """

        def join_game(game_name, game_data_sel):

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

            game_id = game_data_sel[game_name][0]

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

        # action of putting myself in game
        join_game(game_name, game_data_sel)

        # action of going to the game
        select_game_callback(evt, game_name, game_data_sel)

    def change_button_mode_callback(_):
        if storage['GAME_ACCESS_MODE'] == 'button':
            storage['GAME_ACCESS_MODE'] = 'link'
        else:
            storage['GAME_ACCESS_MODE'] = 'button'
        MY_PANEL.clear()
        my_opportunities(sort_by)

    def sort_by_callback(_, sort_by):
        MY_PANEL.clear()
        my_opportunities(sort_by)

    overall_time_before = time.time()

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    player_id = common.get_player_id(pseudo)
    if player_id is None:
        alert("Erreur chargement identifiant joueur")
        return

    player_games = common.get_player_games_playing_in(player_id)
    if player_games is None:
        alert("Erreur chargement liste parties joueés")
        return

    recruiting_games_list = get_recruiting_games()
    # there can be no message (if no game of failed to load)

    recruiting_games_dict = {tr[0]: {'allocated': tr[1], 'capacity': tr[2]} for tr in recruiting_games_list}

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    games_dict_recruiting = {k: v for k, v in games_dict.items() if int(k) in recruiting_games_dict}

    # get the players
    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    masters_alloc = allocations_data['game_masters_dict']

    # gather game to master
    game_master_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            game_master_dict[game] = master

    # Title
    MY_PANEL <= html.H2("Parties qui recrutent des joueurs")

    time_stamp_now = time.time()

    # button for switching mode
    if 'GAME_ACCESS_MODE' not in storage:
        storage['GAME_ACCESS_MODE'] = 'button'
    if storage['GAME_ACCESS_MODE'] == 'button':
        button = html.BUTTON("Basculer en mode liens externes (plus lent mais conserve cette page)")
    else:
        button = html.BUTTON("Basculer en mode boutons (plus rapide mais remplace cette page)")
    button.bind("click", change_button_mode_callback)
    MY_PANEL <= button
    MY_PANEL <= html.BR()
    MY_PANEL <= html.BR()

    games_table = html.TABLE()

    fields = ['go_game', 'join', 'master', 'variant', 'description', 'nopress_game', 'nomessage_game', 'deadline', 'current_state', 'current_advancement', 'allocated']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'go_game': 'aller dans la partie', 'master': 'arbitre', 'join': 'rejoindre', 'variant': 'variante', 'description': 'description', 'nopress_game': 'publics(*)', 'nomessage_game': 'privés(*)', 'deadline': 'date limite', 'current_state': 'état', 'current_advancement': 'saison à jouer', 'allocated': 'alloué(**)'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    row = html.TR()
    for field in fields:
        buttons = html.DIV()
        if field in ['go_game', 'master', 'variant', 'nopress_game', 'nomessage_game', 'deadline', 'current_advancement']:
            if field == 'go_game':

                # button for sorting by creation date
                button = html.BUTTON("&lt;date de création&gt;")
                button.bind("click", lambda e, f='creation': sort_by_callback(e, f))
                buttons <= button

                # button for sorting by name
                button = html.BUTTON("&lt;nom&gt;")
                button.bind("click", lambda e, f='name': sort_by_callback(e, f))
                buttons <= button

            else:

                button = html.BUTTON("<>")
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button
        col = html.TD(buttons)
        row <= col
    games_table <= row

    # create a table to pass information about selected game
    game_data_sel = {v['name']: (k, v['variant']) for k, v in games_dict.items()}

    number_games = 0

    # default
    if sort_by is None:
        sort_by = 'creation'

    if sort_by == 'creation':
        def key_function(g): return int(g[0])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'name':
        def key_function(g): return g[1]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'master':
        def key_function(g): return game_master_dict.get(g[1]['name'], '').upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'variant':
        def key_function(g): return g[1]['variant']  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nopress_game':
        def key_function(g): return (g[1]['nopress_game'], g[1]['nopress_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    elif sort_by == 'nomessage_game':
        def key_function(g): return (g[1]['nomessage_game'], g[1]['nomessage_current'])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
    else:
        def key_function(g): return int(g[1][sort_by])  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

    for game_id_str, data in sorted(games_dict_recruiting.items(), key=key_function):

        # ignore finished (or distinguished) games
        if data['current_state'] in [2, 3]:
            continue

        number_games += 1

        # variant is available
        variant_name_loaded = data['variant']

        # from variant name get variant content

        # this is an optimisation

        # new code after optimization
        if variant_name_loaded in memoize.VARIANT_CONTENT_MEMOIZE_TABLE:
            variant_content_loaded = memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded]
        else:
            variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
            if not variant_content_loaded:
                return
            memoize.VARIANT_CONTENT_MEMOIZE_TABLE[variant_name_loaded] = variant_content_loaded

        # selected interface (user choice)
        interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

        parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)

        # build variant data

        variant_name_loaded_str = str(variant_name_loaded)
        if (variant_name_loaded_str, interface_chosen) in memoize.VARIANT_DATA_MEMOIZE_TABLE:
            variant_data = memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)]
        else:
            variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)
            memoize.VARIANT_DATA_MEMOIZE_TABLE[(variant_name_loaded_str, interface_chosen)] = variant_data

        data['go_game'] = None
        data['master'] = None
        data['join'] = None
        data['allocated'] = None

        row = html.TR()
        for field in fields:

            value = data[field]
            colour = None
            game_name = data['name']

            if field == 'go_game':
                if storage['GAME_ACCESS_MODE'] == 'button':
                    form = html.FORM()
                    input_jump_game = html.INPUT(type="submit", value=game_name)
                    input_jump_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: select_game_callback(e, gn, gds))
                    form <= input_jump_game
                    value = form
                else:
                    link = html.A(href=f"?game={game_name}", target="_blank")
                    link <= game_name
                    value = link

            if field == 'join':
                if game_id_str in player_games:
                    value = "(déjà dedans !)"
                else:
                    game_name = data['name']
                    form = html.FORM()
                    input_join_game = html.INPUT(type="submit", value="J'en profite !")
                    input_join_game.bind("click", lambda e, gn=game_name, gds=game_data_sel: join_and_select_game_callback(e, gn, gds))
                    form <= input_join_game
                    value = form

            if field == 'master':
                game_name = data['name']
                # some games do not have a game master
                master_name = game_master_dict.get(game_name, '')
                value = master_name

            if field == 'nopress_game':
                value1 = value
                value2 = data['nopress_current']
                if value2 == value1:
                    value = "Non" if value1 else "Oui"
                else:
                    value1 = "Non" if value1 else "Oui"
                    value2 = "Non" if value2 else "Oui"
                    value = f"{value1} ({value2})"

            if field == 'nomessage_game':
                value1 = value
                value2 = data['nomessage_current']
                if value2 == value1:
                    value = "Non" if value1 else "Oui"
                else:
                    value1 = "Non" if value1 else "Oui"
                    value2 = "Non" if value2 else "Oui"
                    value = f"{value1} ({value2})"

            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour:02}:{datetime_deadline_loaded.minute:02}"
                deadline_loaded_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded_str

                time_unit = 60 if data['fast'] else 60 * 60
                approach_duration = 24 * 60 * 60

                # we are after deadline + grace
                if time_stamp_now > deadline_loaded + time_unit * data['grace_duration']:
                    colour = config.PASSED_GRACE_COLOUR
                # we are after deadline
                elif time_stamp_now > deadline_loaded:
                    colour = config.PASSED_DEADLINE_COLOUR
                # deadline is today
                elif time_stamp_now > deadline_loaded - approach_duration:
                    colour = config.APPROACHING_DEADLINE_COLOUR

            if field == 'current_state':
                state_loaded = value
                for possible_state_code, possible_state_desc in config.STATE_CODE_TABLE.items():
                    if possible_state_desc == state_loaded:
                        state_loaded = possible_state_code
                        break
                value = state_loaded

            if field == 'current_advancement':
                advancement_loaded = value
                advancement_season, advancement_year = common.get_season(advancement_loaded, variant_data)
                advancement_season_readable = variant_data.name_table[advancement_season]
                value = f"{advancement_season_readable} {advancement_year}"

            if field == 'allocated':
                allocated = recruiting_games_dict[int(game_id_str)]['allocated']
                capacity = recruiting_games_dict[int(game_id_str)]['capacity']
                value = f"{allocated}/{capacity}"
                if allocated == capacity:
                    colour = config.ALL_ORDERS_IN_COLOUR

            col = html.TD(value)
            if colour is not None:
                col.style = {
                    'background-color': colour
                }

            row <= col

        games_table <= row

    MY_PANEL <= games_table
    MY_PANEL <= html.BR()

    MY_PANEL <= html.DIV("(*) Messagerie possible sur la partie, si le paramètre applicable est différent (partie terminée) il est indiqué entre parenthèses", Class='note')
    MY_PANEL <= html.BR()

    MY_PANEL <= html.DIV("(**) On prend en compte l'arbitre dans le nombre de joueurs", Class='note')
    MY_PANEL <= html.BR()

    # get GMT date and time
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
    date_now_gmt_str = datetime.datetime.strftime(date_now_gmt, "%d-%m-%Y %H:%M:%S GMT")

    special_legend = html.DIV(f"Pour information, date et heure actuellement : {date_now_gmt_str}", Class='note')
    MY_PANEL <= special_legend

    MY_PANEL <= html.BR()

    overall_time_after = time.time()
    elapsed = overall_time_after - overall_time_before

    stats = f"Temps de chargement de la page {elapsed}"
    if number_games:
        stats += f" soit {elapsed/number_games} par partie"

    MY_PANEL <= html.DIV(stats, Class='load')
    MY_PANEL <= html.BR()


def render(panel_middle):
    """ render """
    MY_PANEL.clear()
    my_opportunities()
    panel_middle <= MY_PANEL
