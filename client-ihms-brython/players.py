""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common
import interface
import config
import mapping

DEFAULT_ELO = 1500


OPTIONS = ['inscrits', 'joueurs', 'arbitres', 'oisifs', 'remplaçants', 'classement', 'modérateurs', 'courriels non confirmés']


def get_detailed_rating(classic, role_id):
    """ get_detailed_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du classement détaillé : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du classement détaillé : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        rating_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/elo_rating/{int(classic)}/{role_id}"

    # getting rating list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def get_global_rating(classic):
    """ get_global_rating """

    rating_list = None

    def reply_callback(req):
        nonlocal rating_list
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert(f"Erreur à la récupération du classement global : {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problème à la récupération du classement global : {req_result['msg']}")
            else:
                alert("Réponse du serveur imprévue et non documentée")
            return
        rating_list = req_result

    json_dict = {}

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/elo_rating/{int(classic)}"

    # getting rating list : no need for token
    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    return list(rating_list)


def show_registered_data():
    """ show_registered_data """

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    players_table = html.TABLE()

    fields = ['pseudo', 'first_name', 'family_name', 'residence', 'nationality', 'time_zone']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'first_name': 'prénom', 'family_name': 'nom', 'residence': 'résidence', 'nationality': 'nationalité', 'time_zone': 'fuseau horaire'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    code_country_table = {v: k for k, v in config.COUNTRY_CODE_TABLE.items()}

    count = 0
    for data in sorted(players_dict.values(), key=lambda g: g['pseudo'].upper()):
        row = html.TR()
        for field in fields:
            value = data[field]

            if field in ['residence', 'nationality']:
                code = value
                country_name = code_country_table[code]
                value = html.IMG(src=f"./national_flags/{code}.png", title=country_name, width="25", height="17")

            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les inscrits")
    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} inscrits")


def show_players_data():
    """ show_players_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    players_alloc = allocations_data['players_dict']

    # gather games to players
    player_games_dict = {}
    for player_id, games_id in players_alloc.items():
        player = players_dict[str(player_id)]['pseudo']
        if player not in player_games_dict:
            player_games_dict[player] = []
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            player_games_dict[player].append(game)

    players_table = html.TABLE()

    fields = ['player', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'player': 'joueur', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    count = 0
    for player, games in sorted(player_games_dict.items(), key=lambda p: p[0].upper()):
        row = html.TR()
        for field in fields:
            if field == 'player':
                value = player
            if field == 'games':
                value = ' '.join(games)
            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les joueurs")
    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} joueurs")
    MY_SUB_PANEL <= html.DIV("Les joueurs dans des parties anonymes ne sont pas pris en compte", Class='note')


def show_game_masters_data():
    """ show_game_masters_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

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

    # gather games to masters
    master_games_dict = {}
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        if master not in master_games_dict:
            master_games_dict[master] = []
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            master_games_dict[master].append(game)

    masters_table = html.TABLE()

    fields = ['master', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'master': 'arbitre', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    masters_table <= thead

    count = 0
    for master, games in sorted(master_games_dict.items(), key=lambda m: m[0].upper()):
        row = html.TR()
        for field in fields:
            if field == 'master':
                value = master
            if field == 'games':
                value = ' '.join(games)
            col = html.TD(value)
            row <= col

        masters_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les arbitres")
    MY_SUB_PANEL <= masters_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} arbitres")


def show_idle_data():
    """ show_idle_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    idle_set = set()
    for player_data in players_dict.values():
        player = player_data['pseudo']
        idle_set.add(player)

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    players_alloc = allocations_data['players_dict']
    for player_id, _ in players_alloc.items():
        player = players_dict[str(player_id)]['pseudo']
        if player in idle_set:
            idle_set.remove(player)

    masters_alloc = allocations_data['game_masters_dict']
    for player_id, _ in masters_alloc.items():
        player = players_dict[str(player_id)]['pseudo']
        if player in idle_set:
            idle_set.remove(player)

    idle_table = html.TABLE()

    fields = ['player']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'player': 'joueur'}[field]
        col = html.TD(field_fr)
        thead <= col
    idle_table <= thead

    count = 0
    for player in sorted(idle_set, key=lambda p: p.upper()):
        row = html.TR()
        for field in fields:
            if field == 'player':
                value = player
            col = html.TD(value)
            row <= col

        idle_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les oisifs")
    MY_SUB_PANEL <= idle_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} oisifs")
    MY_SUB_PANEL <= html.DIV("Les joueurs dans des parties anonymes ne sont pas pris en compte", Class='note')


def show_replacement_data():
    """ show_replacement_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return

    players_alloc = allocations_data['players_dict']

    # gather games to players
    player_games_dict = {}
    for player_id in players_dict:
        if not players_dict[str(player_id)]['replace']:
            continue
        player = players_dict[str(player_id)]['pseudo']
        if player not in player_games_dict:
            player_games_dict[player] = []
        if player_id not in players_alloc:
            continue
        games_id = players_alloc[player_id]
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            player_games_dict[player].append(game)

    players_table = html.TABLE()

    fields = ['player', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'player': 'joueur', 'games': 'parties'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    count = 0
    for player, games in sorted(player_games_dict.items(), key=lambda p: p[0].upper()):
        row = html.TR()
        for field in fields:
            if field == 'player':
                value = player
            if field == 'games':
                value = ' '.join(games)
            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les remplaçants")
    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} remplaçants")


def show_rating(classic, role_id):
    """ show_rating """

    def make_ratings_table(classic, role_id):

        if role_id:

            # for a given role
            rating_list = get_detailed_rating(classic, role_id)

        else:

            # for all roles
            detailed_rating_list = get_global_rating(classic)

            # should be 7
            number_roles = len({r[1] for r in detailed_rating_list})

            # need to sum up per player
            rating_list_dict = {}
            for (classic, role_id, player_id, elo, change, game_id, number_games) in detailed_rating_list:

                # avoid using loop variable
                classic_found = classic

                # create entry if necessary
                if player_id not in rating_list_dict:
                    rating_list_dict[player_id] = {}
                    rating_list_dict[player_id]['elo_sum'] = 0
                    rating_list_dict[player_id]['number_games'] = 0
                    rating_list_dict[player_id]['number_rated'] = 0

                # update entry

                # suming up
                rating_list_dict[player_id]['elo_sum'] += elo
                rating_list_dict[player_id]['number_games'] += number_games
                rating_list_dict[player_id]['number_rated'] += 1

                # last
                rating_list_dict[player_id]['last_change'] = change
                rating_list_dict[player_id]['last_game'] = game_id
                rating_list_dict[player_id]['last_role'] = role_id

            rating_list = [[classic_found, v['last_role'], k, round((v['elo_sum'] + (number_roles - v['number_rated']) * DEFAULT_ELO) / number_roles), v['last_change'], v['last_game'], v['number_games']] for k, v in rating_list_dict.items()]

        ratings_table = html.TABLE()

        # the display order
        fields = ['rank', 'player', 'elo', 'change', 'role', 'game', 'number']

        # header
        thead = html.THEAD()
        for field in fields:
            field_fr = {'rank': 'rang', 'player': 'joueur', 'elo': 'elo', 'change': 'dernier changement', 'role': 'avec le rôle', 'game': 'dans la partie', 'number': 'nombre de parties'}[field]
            col = html.TD(field_fr)
            thead <= col
        ratings_table <= thead

        row = html.TR()
        for field in fields:
            buttons = html.DIV()
            if field in ['player', 'elo', 'change', 'role', 'game', 'number']:

                # button for sorting
                button = html.BUTTON("<>")
                button.bind("click", lambda e, f=field: sort_by_callback(e, f))
                buttons <= button

            col = html.TD(buttons)
            row <= col
        ratings_table <= row

        sort_by = storage['SORT_BY_RATINGS']
        reverse_needed = bool(storage['REVERSE_NEEDED_RATINGS'] == 'True')

        # 0 classic / 1 role_id / 2 player_id / 3 elo / 4 change / 5 game_id / 6 number games

        if sort_by == 'player':
            def key_function(r): return num2pseudo[r[2]].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'elo':
            def key_function(r): return r[3]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'change':
            def key_function(r): return r[4]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'role':
            def key_function(r): return r[1]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'game':
            def key_function(r): return games_dict[str(r[5])]['name'].upper()  # noqa: E704 # pylint: disable=multiple-statements, invalid-name
        elif sort_by == 'number':
            def key_function(r): return r[6]  # noqa: E704 # pylint: disable=multiple-statements, invalid-name

        rank = 1

        for rating in sorted(rating_list, key=key_function, reverse=reverse_needed):

            row = html.TR()
            for field in fields:

                if field == 'rank':
                    value = rank

                if field == 'player':
                    value = num2pseudo[rating[2]]

                if field == 'elo':
                    value = rating[3]

                if field == 'change':
                    value = rating[4]

                if field == 'role':
                    role_id = rating[1]
                    role = variant_data.roles[role_id]
                    role_name = variant_data.name_table[role]
                    role_icon_img = html.IMG(src=f"./variants/{variant_name}/{interface_chosen}/roles/{role_id}.jpg", title=role_name)
                    value = role_icon_img

                if field == 'game':
                    value = games_dict[str(rating[5])]['name']

                if field == 'number':
                    value = rating[6]

                col = html.TD(value)
                row <= col

            ratings_table <= row
            rank += 1

        return ratings_table

    def refresh():

        ratings_table = make_ratings_table(classic, role_id)

        # button for changing mode
        switch_mode_button = html.BUTTON(f"passer en {'blitz' if classic else 'classique'}")
        switch_mode_button.bind("click", switch_mode_callback)

        # button for going global
        switch_global_button = html.BUTTON("classement global")
        switch_global_button.bind("click", lambda e: switch_role_callback(e, None))

        # buttons for selecting role
        switch_role_buttons_table = html.TABLE()
        row = html.TR()
        col = html.TD("Détailler pour le pays")
        row <= col
        for poss_role_id, role in variant_data.roles.items():
            if poss_role_id >= 1:
                form = html.FORM()
                input_change_role = html.INPUT(type="image", src=f"./variants/{variant_name}/{interface_chosen}/roles/{poss_role_id}.jpg")
                input_change_role.bind("click", lambda e, r=poss_role_id: switch_role_callback(e, r))
                form <= input_change_role
                col = html.TD(form)
                row <= col
        switch_role_buttons_table <= row

        MY_SUB_PANEL.clear()
        MY_SUB_PANEL <= html.H3(f"Le classement par ELO en mode {'classique' if classic else 'blitz'}")
        MY_SUB_PANEL <= switch_mode_button
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= switch_role_buttons_table
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= switch_global_button
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= html.BR()
        MY_SUB_PANEL <= ratings_table

    def sort_by_callback(_, new_sort_by):

        # if same sort criterion : inverse order otherwise back to normal order
        if new_sort_by is not None:
            if new_sort_by != storage['SORT_BY_RATINGS']:
                storage['SORT_BY_RATINGS'] = new_sort_by
                storage['REVERSE_NEEDED_RATINGS'] = str(False)
            else:
                storage['REVERSE_NEEDED_RATINGS'] = str(not bool(storage['REVERSE_NEEDED_RATINGS'] == 'True'))

        refresh()

    def switch_mode_callback(_):

        nonlocal classic
        classic = not classic
        refresh()

    def switch_role_callback(_, new_role_id):

        nonlocal role_id
        role_id = new_role_id
        refresh()

    if 'GAME_VARIANT' not in storage:
        alert("Pas de partie de référence")
        return
    variant_name = storage['GAME_VARIANT']

    variant_content = common.game_variant_content_reload(variant_name)
    interface_chosen = interface.get_interface_from_variant(variant_name)
    interface_parameters = common.read_parameters(variant_name, interface_chosen)

    variant_data = mapping.Variant(variant_name, variant_content, interface_parameters)

    players_dict = common.get_players()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # default
    if 'SORT_BY_RATINGS' not in storage:
        storage['SORT_BY_RATINGS'] = 'elo'
    if 'REVERSE_NEEDED_RATINGS' not in storage:
        storage['REVERSE_NEEDED_RATINGS'] = str(True)

    sort_by_callback(None, None)


def show_moderators():
    """ show_moderators """

    MY_SUB_PANEL <= html.H3("Les modérateurs")

    moderator_list = common.get_moderators()

    if not moderator_list:
        return

    moderators_table = html.TABLE()

    fields = ['pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    moderators_table <= thead

    for moderator in sorted(moderator_list, key=lambda m: m.upper()):

        row = html.TR()
        col = html.TD(moderator)
        row <= col

        moderators_table <= row

    MY_SUB_PANEL <= moderators_table


def show_non_confirmed_data():
    """ show_non_confirmed_data """

    MY_SUB_PANEL <= html.H3("Les inscrits non confirmés")

    players_dict = common.get_players_data()

    if not players_dict:
        return

    players_table = html.TABLE()

    fields = ['pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    for data in sorted(players_dict.values(), key=lambda p: p['pseudo'].upper()):

        if data['email_confirmed']:
            continue

        row = html.TR()
        for field in fields:
            value = data[field]

            col = html.TD(value)
            row <= col

        players_table <= row

    MY_SUB_PANEL <= players_table


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = OPTIONS[0]

MY_SUB_PANEL = html.DIV(id="lists")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'inscrits':
        show_registered_data()
    if item_name == 'joueurs':
        show_players_data()
    if item_name == 'arbitres':
        show_game_masters_data()
    if item_name == 'oisifs':
        show_idle_data()
    if item_name == 'remplaçants':
        show_replacement_data()
    if item_name == 'classement':
        show_rating(True, None)
    if item_name == 'modérateurs':
        show_moderators()
    if item_name == 'courriels non confirmés':
        show_non_confirmed_data()

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
