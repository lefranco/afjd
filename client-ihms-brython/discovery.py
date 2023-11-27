""" discovery """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, document, window  # pylint: disable=import-error


OPTIONS = {
    'Documents': "Lien vers différents documents d'initiation sur le jeu",
    'Vidéo Youtube Diplomacy': "Lien une vidéo Youtube qui présente simplement les règles du jeu avec humour",
    'Vidéo Youtube Diplomania': "Lien une vidéo Youtube qui présente simplement comment jouer sur ce site",
}


def show_discovery():
    """ show_discovery """

    MY_SUB_PANEL <= html.H2("Recueil de documents pour découvrir le jeu")

    title5 = html.H3("Règles simplifiées")
    MY_SUB_PANEL <= title5

    link5 = html.A(href="./docs/Summary_rules_fr.pdf", target="_blank")
    link5 <= "Lien vers une version simplifiée des règles du jeu par Edi Birsan"
    MY_SUB_PANEL <= link5


def tutorial_game():
    """ tutorial_game """

    # load tutorial_game directly

    # use button
    button = html.BUTTON("Lancement du tutoriel youtube pour le jeu", id='tutorial_game', Class='btn-inside')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open("https://youtu.be/d-ddAqTNDzA?si=Raf-hKFpgjMgdmf0"))
    document['tutorial_game'].click()


def tutorial_site():
    """ tutorial_site """

    # load tutorial_site directly

    # use button
    button = html.BUTTON("Lancement du tutoriel youtube pour le site", id='tutorial_link', Class='btn-inside')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open("https://youtu.be/luOiAz9i7Ls"))
    document['tutorial_link'].click()


MY_PANEL = html.DIV()
MY_PANEL.attrs['style'] = 'display: table-row'

# menu-left
MENU_LEFT = html.DIV()
MENU_LEFT.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
MY_PANEL <= MENU_LEFT

# menu-selection
MENU_SELECTION = html.UL()
MENU_LEFT <= MENU_SELECTION

ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

MY_SUB_PANEL = html.DIV(id='page')
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    if item_name == 'Documents':
        show_discovery()
    if item_name == 'Vidéo Youtube Diplomacy':
        tutorial_game()
    if item_name == 'Vidéo Youtube Diplomania':
        tutorial_site()

    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    MENU_LEFT.clear()

    # items in menu
    for possible_item_name, legend in OPTIONS.items():

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, title=legend, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        MENU_LEFT <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED

    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
