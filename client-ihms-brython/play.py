""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

OPTIONS = ['submit orders', 'negotiate']

my_panel = html.DIV(id="play")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:10%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel

def submit_orders():
    """ submit_orders """

    dummy = html.P("submit orders")
    my_sub_panel <= dummy

def negotiate():
    """ negotiate """

    dummy = html.P("negotiate")
    my_sub_panel <= dummy

def load_option(_, item_name) -> None:
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'submit orders':
        submit_orders()
    if item_name == 'negotiate':
        negotiate()
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


# starts here
load_option(None, item_name_selected)



def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
