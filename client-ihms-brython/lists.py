""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import datetime

from browser import html  # pylint: disable=import-error

import config
import common

my_panel = html.DIV(id="players")

OPTIONS = ['les joueurs', 'les parties en attente', 'les parties en cours', 'les parties terminées', 'les tournois', 'les arbitres', 'les parties sans arbitres']


def show_players_data():
    """ show_players_data """

    players_dict = common.get_players_data()

    if not players_dict:
        return

    players_table = html.TABLE()

    # TODO : make it possible to sort etc...
    fields = ['pseudo', 'first_name', 'family_name', 'residence', 'nationality', 'time_zone', 'email_confirmed']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'pseudo': 'pseudo', 'first_name': 'prénom', 'family_name': 'nom', 'residence': 'résidence', 'nationality': 'nationalité', 'time_zone': 'fuseau horaire', 'email_confirmed': 'email confirmé'}[field]
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

            if field == 'email_confirmed':
                if value is False:
                    value = "Non"
                elif value is True:
                    value = "Oui"

            col = html.TD(value)
            row <= col

        players_table <= row
        count += 1

    my_sub_panel <= players_table
    my_sub_panel <= html.P(f"Il y a {count} joueurs")


def show_games_data(game_state):
    """ show_games_data """

    games_dict = common.get_games_data()

    if not games_dict:
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

    my_sub_panel <= games_table
    my_sub_panel <= html.P(f"Il y a {count} parties")


def show_tournaments_data():
    """ show_tournaments_data """

    # TODO : liste des tournois
    my_sub_panel <= "ICI liste des tournois avec leurs parties - Pas encore implémenté, désolé !"


def show_game_masters_data():
    """ show_game_masters_data """

    # get the games
    games_dict = common.get_games_data()

    if not games_dict:
        return

    # to avoid a warning
    games_dict = dict(games_dict)

    # get the players (masters)
    players_dict = common.get_players_data()

    if not players_dict:
        return

    # get the link (allocations) of game masters
    game_masters_list = common.get_game_masters_data()

    if not game_masters_list:
        return

    # gather games to game masters
    master_games_dict = dict()
    for game_data in game_masters_list:
        game = games_dict[str(game_data['game'])]['name']
        master = players_dict[str(game_data['master'])]['pseudo']
        if master not in master_games_dict:
            master_games_dict[master] = list()
        master_games_dict[master].append(game)

    game_masters_table = html.TABLE()

    # TODO : make it possible to sort etc...
    fields = ['master', 'games']

    # header
    thead = html.THEAD()
    for field in fields:
        field_fr = {'master': 'arbitre', 'games': 'parties', }[field]
        col = html.TD(field_fr)
        thead <= col
    game_masters_table <= thead

    for master in sorted(master_games_dict, key=lambda m: m.upper()):
        row = html.TR()
        for field in fields:
            if field == 'master':
                value = master
            if field == 'games':
                value = ' '.join(master_games_dict[master])
            col = html.TD(value)
            row <= col
        game_masters_table <= row

    my_sub_panel <= game_masters_table


def show_no_game_masters_data():
    """ show_no_game_masters_data """

    # get the games
    games_dict = common.get_games_data()

    if not games_dict:
        return

    # to avoid a warning
    games_dict = dict(games_dict)

    # get the players (masters)
    players_dict = common.get_players_data()

    if not players_dict:
        return

    # get the link (allocations) of game masters
    game_masters_list = common.get_game_masters_data()

    if not game_masters_list:
        return

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

    no_game_masters_list = [v for k, v in games_dict.items() if int(k) not in [g['game'] for g in game_masters_list]]

    for data in sorted(no_game_masters_list, key=lambda g: g['name'].upper()):
        row = html.TR()
        value = data['name']
        col = html.TD(value)
        row <= col
        no_game_masters_table <= row

    my_sub_panel <= no_game_masters_table


my_panel = html.DIV(id="players_games")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'les joueurs':
        show_players_data()
    if item_name == 'les parties en attente':
        show_games_data(0)
    if item_name == 'les parties en cours':
        show_games_data(1)
    if item_name == 'les parties terminées':
        show_games_data(2)
    if item_name == 'les tournois':
        show_tournaments_data()
    if item_name == 'les arbitres':
        show_game_masters_data()
    if item_name == 'les parties sans arbitres':
        show_no_game_masters_data()

    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
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
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

    load_option(None, item_name_selected)
    panel_middle <= my_panel
