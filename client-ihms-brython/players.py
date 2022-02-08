""" players """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, alert  # pylint: disable=import-error

import config
import common


OPTIONS = ['inscrits', 'joueurs', 'remplaçants', 'arbitres', 'modérateurs', 'courriels non confirmés']


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
                value = '/'.join(games)
            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les joueurs")
    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} joueurs")


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
    for player_id, games_id in players_alloc.items():
        if not players_dict[str(player_id)]['replace']:
            continue
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
                value = '/'.join(games)
            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les remplaçants")
    MY_SUB_PANEL <= players_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} remplaçants")


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
                value = '/'.join(games)
            col = html.TD(value)
            row <= col

        masters_table <= row
        count += 1

    MY_SUB_PANEL <= html.H3("Les arbitres")
    MY_SUB_PANEL <= masters_table
    MY_SUB_PANEL <= html.P(f"Il y a {count} arbitres")


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
    if item_name == 'inscrits':
        show_registered_data()
    if item_name == 'joueurs':
        show_players_data()
    if item_name == 'remplaçants':
        show_replacement_data()
    if item_name == 'arbitres':
        show_game_masters_data()
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
