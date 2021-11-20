""" submit """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import html  # pylint: disable=import-error


LONG_DURATION_LIMIT_SEC = 1.0

OPTIONS = ['classement', 'parties', 's\'inscrire', 'ajouter partie', 'retirer partie', 'diriger', 'ne plus diriger']


def ratings():
    """ ratings """

    my_sub_panel <= html.H3("Le classement")

    # TODO classement du tournoi
    my_sub_panel <= "ICI classement du tournoi (sélectionner une partie du tournoi au préalable) - Pas encore implémenté, désolé !"


def games():
    """ games """

    my_sub_panel <= html.H3("Les parties")

    # TODO état des parties du tournoi
    my_sub_panel <= "ICI état des parties du tournoi - Pas encore implémenté, désolé !"


def register():
    """ games """

    my_sub_panel <= html.H3("S'inscrire")

    # TODO s'inscrire au tournoi
    my_sub_panel <= "ICI possibilité de s'inscrire au tournoi - Pas encore implémenté, désolé !"


def add_game():
    """ add_game """

    my_sub_panel <= html.H3("Ajouter une partie")

    # TODO ajouter une partie au tournoi
    my_sub_panel <= "ICI possibilité pour le directeur de tournoi d'ajouter une partie au tournoi - Pas encore implémenté, désolé !"


def remove_game():
    """ remove_game """

    my_sub_panel <= html.H3("Retirer une partie")

    # TODO retirer une partie du tournoi
    my_sub_panel <= "ICI possibilité pour le directeur de tournoi de retirer une partie du tournoi - Pas encore implémenté, désolé !"


def direct():
    """ direct """

    my_sub_panel <= html.H3("Prendre la direction")

    # TODO prendre la direction du tournoi
    my_sub_panel <= "ICI possibilité de prendre la direction du tournoi - Pas encore implémenté, désolé !"


def quit_directing():
    """ quit_directing """

    my_sub_panel <= html.H3("Quitter la direction")

    # TODO quitter la direction du tournoi
    my_sub_panel <= "ICI possibilité de quitter la direction du tournoi - Pas encore implémenté, désolé !"


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
    if item_name == 'classement':
        ratings()
    if item_name == 'parties':
        games()
    if item_name == 's\'inscrire':
        register()
    if item_name == 'ajouter partie':
        add_game()
    if item_name == 'retirer partie':
        remove_game()
    if item_name == 'diriger':
        direct()
    if item_name == 'ne plus diriger':
        quit_directing()

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
