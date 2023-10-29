""" technical """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, window  # pylint: disable=import-error


import config
import ezml_render

OPTIONS = list(config.SCORING_CODE_TABLE.keys())

ARRIVAL = None

# from home
SCORING_REQUESTED = None


def set_arrival(arrival, scoring_requested=None):
    """ set_arrival """

    global ARRIVAL
    global SCORING_REQUESTED

    ARRIVAL = arrival

    if scoring_requested:
        SCORING_REQUESTED = scoring_requested


def show_scoring():
    """ show_scoring """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    scoring_name = {v: k for k, v in config.SCORING_CODE_TABLE.items()}[SCORING_REQUESTED]

    MY_SUB_PANEL <= html.H2(f"Le scorage {scoring_name}")

    ezml_file = f"./scorings/{SCORING_REQUESTED}.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = OPTIONS[0]

MY_SUB_PANEL = html.DIV(id='variants')
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    global SCORING_REQUESTED

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    SCORING_REQUESTED = config.SCORING_CODE_TABLE[item_name]
    show_scoring()

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
    global ARRIVAL

    ITEM_NAME_SELECTED = OPTIONS[0]

    # this means user wants to see variant
    if ARRIVAL == 'scoring':
        ITEM_NAME_SELECTED = {v: k for k, v in config.SCORING_CODE_TABLE.items()}[SCORING_REQUESTED]

    ARRIVAL = None
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
