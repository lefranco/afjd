""" submit """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import html, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import common

OPTIONS = ['créer les parties']


def perform_batch(games_to_create):
    """ perform_batch """

    alert("Ok, on tente le truc..")

    games_dict = common.get_games_data()
    if not games_dict:
        alert("Erreur chargement dictionnaire parties")
        return
    games_dict = dict(games_dict)
    #  print(f"{games_dict=}")
    games_set = {d['name'] for d in games_dict.values()}

    players_dict = common.get_players_data()
    if not players_dict:
        alert("Erreur chargement dictionnaire joueurs")
        return
    players_dict = dict(players_dict)
    #  print(f"{players_dict=}")
    players_set = {d['pseudo'] for d in players_dict.values()}

    # check the game does not exist
    for ligne, game_name in enumerate(games_to_create):

        if not game_name:
            alert(f"Il y a un nom de partie vide dans le fichier en ligne {ligne+1}")
            error = True

        if game_name in games_set:
            alert(f"Il semble que la partie {game_name} existe déjà")
            error = True

    # check the players exist
    already_warned = set()
    for ligne, allocations in enumerate(games_to_create.values()):
        for player_name in allocations.values():

            if not player_name:
                alert(f"Il y a un nom de joueur vide dans le fichier en ligne {ligne+1}")
                error = True

            if player_name not in players_set:

                # patch
                if player_name.startswith("Joueur"):
                    continue

                if player_name not in already_warned:
                    alert(f"Il semble que le pseudo {player_name} n'existe pas")
                    already_warned.add(player_name)
                    error = True

    # check the roles are complete
    for game_name, allocations in games_to_create.items():
        if sorted(allocations.keys()) != list(range(8)):
            alert(f"Il semble que la partie {game_name} n'a pas ses 8 joueurs")
            error = True

    # check the players in games are not duplicated
    for game_name, allocations in games_to_create.items():
        if len(set(allocations.keys())) != 8:
            alert(f"Il semble que la partie {game_name} n'a pas 8 joueurs différents")
            error = True

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter pour créer les parties")
        return

    pseudo = storage['PSEUDO']

    # check the game master is pseudo (to check last)
    for game_name, allocations in games_to_create.items():
        if allocations[0] != pseudo:
            alert(f"Il semble que vous ne soyez pas l'arbitre créateur de la partie {game_name}. Je ne pourrais donc pas la crééer. ")

    if not error:
        alert("Mouais. Ca pourrait être jouable ton truc ;-)")


def create_games():
    """ ratings """

    def create_games_callback(_):
        """ create_games_callback """

        def onload_callback(_):
            """ onload_callback """

            games_to_create = dict()

            content = str(reader.result)
            lines = content.split('\n')

            if not len(lines) >= 1:
                alert("Votre fichier n'a pas de lignes")
                return

            for line in lines:

                # ignore empty lines
                if not line:
                    continue

                tab = line.split(',')

                if not len(tab) >= 2:
                    alert("Votre fichier n'est pas un csv")
                    return

                game_name = tab[0]

                games_to_create[game_name] = {n: tab[n + 1] for n in range(len(tab) - 1)}

            #  actual creation of all the games
            perform_batch(games_to_create)

            # back to where we started
            my_sub_panel.clear()
            create_games()

        if not input_file.files:
            alert("Pas de fichier")

            # back to where we started
            my_sub_panel.clear()
            create_games()
            return

        file = input_file.files[0]
        # Create a new DOM FileReader instance
        reader = window.FileReader.new()
        # Read the file content as text
        reader.readAsBinaryString(file)
        reader.bind("load", onload_callback)

        # back to where we started
        my_sub_panel.clear()
        create_games()

    my_sub_panel <= html.H3("Création des parties")

    form = html.FORM()

    fieldset = html.FIELDSET()
    legend_name = html.LEGEND("Ficher CSV")
    fieldset <= legend_name
    form <= fieldset

    input_file = html.INPUT(type="file")
    form <= input_file
    form <= html.BR()

    form <= html.BR()

    input_create_games = html.INPUT(type="submit", value="créer les parties")
    input_create_games.bind("click", create_games_callback)
    form <= input_create_games

    my_sub_panel <= form


my_panel = html.DIV()
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="tournament")
my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'créer les parties':
        create_games()

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
