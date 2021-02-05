from browser import document, html, highlight

import home
import login
import account
import games
import submit
import negotiate
import master

TITLE = "Welcome on board"
OPTIONS = ['home', 'login', 'account', 'games', 'submit', 'negotiate', 'master']


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
menu_left.attrs['style'] = 'display: table-cell; width:20%; vertical-align: top;'
overall <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

menu_items = dict()

item_name_selected = OPTIONS[0]

def load_option(ev, item_name):
    panel_middle.clear()
    if item_name == 'home':
        home.render(panel_middle)
    if item_name == 'login':
        login.render(panel_middle)
    if item_name == 'account':
        account.render(panel_middle)
    if item_name == 'games':
        games.render(panel_middle)
    if item_name == 'submit':
        submit.render(panel_middle)
    if item_name == 'negotiate':
        negotiate.render(panel_middle)
    if item_name == 'master':
        master.render(panel_middle)
    global item_name_selected
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for item_name in OPTIONS:

        if item_name == item_name_selected:
            item_name_bold_or_not = html.B(item_name)
        else:
            item_name_bold_or_not = item_name

        button = html.BUTTON(item_name_bold_or_not)
        button.bind("click", lambda ev, item_name=item_name : load_option(ev, item_name))
        menu_item = html.LI(button)
        menu_left <= menu_item
        menu_items[item_name] = menu_item

# panel-middle
panel_middle = html.DIV(id='panel_middle')
overall <= panel_middle

# starts here
load_option(None, item_name_selected)
