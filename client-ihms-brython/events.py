""" players """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


OPTIONS = ['sélectionner un événement', 'm\'inscrire', 'créer un événement', 'éditer l\'événement', 'supprimer l\'événement']


def select_event():
    """ select_event """

    MY_SUB_PANEL <= html.H3("Sélection d'un événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    MY_SUB_PANEL <= "TODO"


def register_event():
    """ register_event """

    MY_SUB_PANEL <= html.H3("Inscription à un événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    MY_SUB_PANEL <= "TODO"


def create_event():
    """ create_event """

    MY_SUB_PANEL <= html.H3("Création d'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    MY_SUB_PANEL <= "TODO"


def edit_event():
    """ edit_event """

    MY_SUB_PANEL <= html.H3("Edition d'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    MY_SUB_PANEL <= "TODO"


def delete_event():
    """ delete_event """

    MY_SUB_PANEL <= html.H3("Suppression d'événement")

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    MY_SUB_PANEL <= "TODO"


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

MY_SUB_PANEL = html.DIV(id="events")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'sélectionner un événement':
        select_event()
    if item_name == 'm\'inscrire':
        register_event()
    if item_name == 'créer un événement':
        create_event()
    if item_name == 'éditer l\'événement':
        edit_event()
    if item_name == 'supprimer l\'événement':
        delete_event()

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
