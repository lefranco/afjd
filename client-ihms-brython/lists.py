""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import datetime

from browser import html, alert  # pylint: disable=import-error

import config
import common


OPTIONS = ['les inscrits', 'les joueurs', 'les remplaçants', 'les parties en attente', 'les parties en cours', 'les parties terminées', 'les tournois', 'les arbitres', 'les parties sans arbitres']


def show_registered_data():
    """ show_registered_data """

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    players_table = html.TABLE()

    # TODO : make it possible to sort etc...
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

    my_sub_panel <= html.H3("Les inscrits")
    my_sub_panel <= players_table
    my_sub_panel <= html.P(f"Il y a {count} inscrits")


def show_players_data():
    """ show_players_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # to avoid a warning
    games_dict = dict(games_dict)

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return
    allocations_data = dict(allocations_data)

    players_alloc = allocations_data['players_dict']

    # gather games to players
    player_games_dict = dict()
    for player_id, games_id in players_alloc.items():
        player = players_dict[str(player_id)]['pseudo']
        if player not in player_games_dict:
            player_games_dict[player] = list()
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            player_games_dict[player].append(game)

    players_table = html.TABLE()

    # TODO : make it possible to sort etc...
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

    my_sub_panel <= html.H3("Les joueurs")
    my_sub_panel <= players_table
    my_sub_panel <= html.P(f"Il y a {count} joueurs")


def show_replacement_data():
    """ show_replacement_data """

    my_sub_panel <= html.H3("Liste des candidats au remplacement")

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    players_table = html.TABLE()

    # TODO : make it possible to sort etc...
    fields = ['pseudo']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo'}[field]
        col = html.TD(field_fr)
        thead <= col
    players_table <= thead

    for data in sorted(players_dict.values(), key=lambda p: p['pseudo'].upper()):

        if not data['replace']:
            continue

        row = html.TR()
        for field in fields:
            value = data[field]

            col = html.TD(value)
            row <= col

        players_table <= row

    my_sub_panel <= players_table


def show_games_data(game_state_name):
    """ show_games_data """

    game_state = config.STATE_CODE_TABLE[game_state_name]

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    games_table = html.TABLE()

    # TODO : make it possible to sort etc...
    fields = ['name', 'variant', 'deadline', 'current_advancement']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'name': 'nom', 'variant': 'variante', 'deadline': 'date limite', 'current_advancement': 'avancement'}[field]
        col = html.TD(field_fr)
        thead <= col
    games_table <= thead

    count = 0
    for data in sorted(games_dict.values(), key=lambda g: g['name'].upper()):

        # restrict to proper state
        if data['current_state'] != game_state:
            continue

        row = html.TR()
        for field in fields:
            value = data[field]
            if field == 'deadline':
                deadline_loaded = value
                datetime_deadline_loaded = datetime.datetime.fromtimestamp(deadline_loaded, datetime.timezone.utc)
                deadline_loaded_day = f"{datetime_deadline_loaded.year:04}-{datetime_deadline_loaded.month:02}-{datetime_deadline_loaded.day:02}"
                deadline_loaded_hour = f"{datetime_deadline_loaded.hour}:{datetime_deadline_loaded.minute}"
                deadline_loaded_str = f"{deadline_loaded_day} {deadline_loaded_hour} GMT"
                value = deadline_loaded_str
            col = html.TD(value)
            row <= col
        games_table <= row
        count += 1

    my_sub_panel <= html.H3(f"Les parties dans l'état : {game_state_name}")
    my_sub_panel <= games_table
    my_sub_panel <= html.P(f"Il y a {count} parties")


def show_tournaments_data():
    """ show_tournaments_data """

    my_sub_panel <= html.H3("Les tournois")
    # TODO : liste des tournois
    my_sub_panel <= "ICI liste des tournois avec leurs parties - Pas encore implémenté, désolé !"


def show_game_masters_data():
    """ show_game_masters_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # to avoid a warning
    games_dict = dict(games_dict)

    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return
    allocations_data = dict(allocations_data)

    masters_alloc = allocations_data['game_masters_dict']

    # gather games to masters
    master_games_dict = dict()
    for master_id, games_id in masters_alloc.items():
        master = players_dict[str(master_id)]['pseudo']
        if master not in master_games_dict:
            master_games_dict[master] = list()
        for game_id in games_id:
            game = games_dict[str(game_id)]['name']
            master_games_dict[master].append(game)

    masters_table = html.TABLE()

    # TODO : make it possible to sort etc...
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

    my_sub_panel <= html.H3("Les arbitres")
    my_sub_panel <= masters_table
    my_sub_panel <= html.P(f"Il y a {count} arbitres")


def show_no_game_masters_data():
    """ show_no_game_masters_data """

    # get the games
    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return

    # to avoid a warning
    games_dict = dict(games_dict)

    # get the players (masters)
    players_dict = common.get_players_data()

    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return

    # get the link (allocations) of players
    allocations_data = common.get_allocations_data()
    if not allocations_data:
        alert("Erreur chargement allocations")
        return
    allocations_data = dict(allocations_data)

    masters_alloc = allocations_data['game_masters_dict']
    games_with_master = list()
    for load in masters_alloc.values():
        games_with_master += load

    no_game_masters_table = html.TABLE()

    # TODO : make it possible to sort etc...
    fields = ['game']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'game': 'partie'}[field]
        col = html.TD(field_fr)
        thead <= col
    no_game_masters_table <= thead

    for identifier, data in sorted(games_dict.items(), key=lambda g: g[1]['name'].upper()):

        if int(identifier) in games_with_master:
            continue

        row = html.TR()
        value = data['name']
        col = html.TD(value)
        row <= col
        no_game_masters_table <= row

    my_sub_panel <= html.H3("Les parties sans arbitre")
    my_sub_panel <= no_game_masters_table


my_panel = html.DIV()
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

ITEM_NAME_SELECTED = OPTIONS[0]

my_sub_panel = html.DIV(id="lists")
my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'les inscrits':
        show_registered_data()
    if item_name == 'les joueurs':
        show_players_data()
    if item_name == 'les remplaçants':
        show_replacement_data()
    if item_name == 'les parties en attente':
        show_games_data('en attente')
    if item_name == 'les parties en cours':
        show_games_data('en cours')
    if item_name == 'les parties terminées':
        show_games_data('terminée')
    if item_name == 'les tournois':
        show_tournaments_data()
    if item_name == 'les arbitres':
        show_game_masters_data()
    if item_name == 'les parties sans arbitres':
        show_no_game_masters_data()

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= my_panel
