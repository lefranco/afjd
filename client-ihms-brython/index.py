""" index """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html  # pylint: disable=import-error

import home
import login
import lists
import account
import games
import selection
import pairing
import play
import tools
import sandbox
import technical


# TITLE
TITLE = "Front end générique Serveurs REST AJFD"
title = html.TITLE(TITLE, id='title')
title.attrs['style'] = 'text-align: center'
document <= title


# H2
H2 = "Preuve de concept de l'interface de jeu Diplomacy"
h2 = html.H2(H2, id='h2')
h2.attrs['style'] = 'text-align: center'
document <= h2

OPTIONS = ['accueil', 'login', 'selection partie', 'listes', 'mon compte', 'editer parties', 'appariement', 'jouer', 'editer position', 'bac à sable', 'coin technique']

# overall_top
overall_top = html.DIV()
overall_top.attrs['style'] = 'display:table; width:100%'
document <= overall_top

# overall
overall = html.DIV()
overall.attrs['style'] = 'display: table-row'
overall_top <= overall

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
overall <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection


item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name


def load_option(_, item_name):
    """ load_option """

    panel_middle.clear()
    if item_name == 'accueil':
        home.render(panel_middle)
    if item_name == 'login':
        login.render(panel_middle)
    if item_name == 'selection partie':
        selection.render(panel_middle)
    if item_name == 'listes':
        lists.render(panel_middle)
    if item_name == 'mon compte':
        account.render(panel_middle)
    if item_name == 'editer parties':
        games.render(panel_middle)
    if item_name == 'appariement':
        pairing.render(panel_middle)
    if item_name == 'jouer':
        play.render(panel_middle)
    if item_name == 'boite à outils':
        tools.render(panel_middle)
    if item_name == 'bac à sable':
        sandbox.render(panel_middle)
    if item_name == 'coin technique':
        technical.render(panel_middle)
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not)
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


# panel-middle
panel_middle = html.DIV(id='panel_middle')
overall <= panel_middle


# starts here
load_option(None, item_name_selected)


document <= html.BR()
document <= html.BR()

login.show_login()
selection.show_game_selected()
