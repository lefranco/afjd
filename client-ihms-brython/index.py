""" index """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html  # pylint: disable=import-error

import home
import login
import players
import account
import games
import selection
import pairing
import play
import master
import sandbox

TITLE = "Welcome this demo interface Web client for playing Diplomacy on ANJD REST Server"
OPTIONS = ['home', 'login', 'list players', 'my account', 'edit games', 'select game', 'pairing', 'play game', 'master game', 'use sandbox']


# title
title = html.H1(TITLE, id='title')
title.attrs['style'] = 'text-align: center'
document <= title

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
menu_left.attrs['style'] = 'display: table-cell; width:10%; vertical-align: top;'
overall <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection


item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name


def load_option(_, item_name):
    """ load_option """

    panel_middle.clear()
    if item_name == 'home':
        home.render(panel_middle)
    if item_name == 'login':
        login.render(panel_middle)
    if item_name == 'list players':
        players.render(panel_middle)
    if item_name == 'my account':
        account.render(panel_middle)
    if item_name == 'edit games':
        games.render(panel_middle)
    if item_name == 'select game':
        selection.render(panel_middle)
    if item_name == 'pairing':
        pairing.render(panel_middle)
    if item_name == 'play game':
        play.render(panel_middle)
    if item_name == 'master game':
        master.render(panel_middle)
    if item_name == 'use sandbox':
        sandbox.render(panel_middle)
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

login.show_login()
