""" discovery """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, document, window  # pylint: disable=import-error

import faq
import tips
import ezml_render

OPTIONS = {
    'Règles simplifiées': "Un règle simplifiée du jeu Diplomatie",
    'Foire aux questions': "Foire Aux Questions du site",
    'Les petits tuyaux': "Différentes petites choses à savoir pour mieux jouer sur le site",
    'Charte du bon diplomate': "Document indiquant les règles de bonne conduite en jouant les parties",
    'Youtube Diplomacy': "Lien une vidéo Youtube qui présente simplement les règles du jeu avec humour",
    'Youtube Diplomania Jeu': "Lien une vidéo Youtube qui présente simplement comment jouer sur ce site",
    'Youtube Diplomania Arbitrage': "Lien une vidéo Youtube qui présente simplement comment arbitrer sur ce site",
}


def show_simplified_rules():
    """ show_simplified_rules """

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/resume.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


FAQ_DISPLAYED_TABLE = {k: False for k in faq.FAQ_CONTENT_TABLE}
FAQ_CONTENT = html.DIV("faq")

TIPS_DISPLAYED_TABLE = {k: False for k in tips.TIPS_CONTENT_TABLE}
TIPS_CONTENT = html.DIV("tips")


def show_faq():
    """ show_faq """

    def reveal_callback(_, question):
        """ reveal_callback """

        FAQ_DISPLAYED_TABLE[question] = not FAQ_DISPLAYED_TABLE[question]
        MY_SUB_PANEL.clear()
        show_faq()

    title1 = html.H3("Foire aux questions")
    MY_SUB_PANEL <= title1

    FAQ_CONTENT.clear()

    for question_txt, answer_txt in faq.FAQ_CONTENT_TABLE.items():

        reveal_button = html.INPUT(type="submit", value=question_txt, Class='btn-inside')
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        FAQ_CONTENT <= reveal_button

        if FAQ_DISPLAYED_TABLE[question_txt]:

            faq_elt = html.DIV(answer_txt, Class='faq-info')
            FAQ_CONTENT <= faq_elt

        FAQ_CONTENT <= html.P()

    MY_SUB_PANEL <= FAQ_CONTENT


def show_tips():
    """ show_tips """

    def reveal_callback(_, question):
        """ reveal_callback """

        TIPS_DISPLAYED_TABLE[question] = not TIPS_DISPLAYED_TABLE[question]
        MY_SUB_PANEL.clear()
        show_tips()

    title1 = html.H3("Les petits tuyaux")
    MY_SUB_PANEL <= title1

    TIPS_CONTENT.clear()

    for question_txt, answer_txt in tips.TIPS_CONTENT_TABLE.items():

        reveal_button = html.INPUT(type="submit", value=question_txt, Class='btn-inside')
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        TIPS_CONTENT <= reveal_button

        if TIPS_DISPLAYED_TABLE[question_txt]:

            tip_elt = html.DIV(answer_txt, Class='faq-info')
            TIPS_CONTENT <= tip_elt

        TIPS_CONTENT <= html.P()

    MY_SUB_PANEL <= TIPS_CONTENT


def show_diplomat_chart():
    """ show_diplomat_chart """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/charte.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def tutorial_game():
    """ tutorial_game """

    # load tutorial_game directly

    # use button
    button = html.BUTTON("Lancement du tutoriel youtube pour le jeu", id='tutorial_game', Class='btn-inside')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open("https://youtu.be/d-ddAqTNDzA?si=Raf-hKFpgjMgdmf0"))
    document['tutorial_game'].click()


def tutorial_site_play():
    """ tutorial_site_play """

    # load tutorial_site directly

    # use button
    button = html.BUTTON("Lancement du tutoriel youtube pour le site", id='tutorial_link_play', Class='btn-inside')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open("https://www.youtube.com/watch?v=luOiAz9i7Ls"))
    document['tutorial_link_play'].click()


def tutorial_site_master():
    """ tutorial_site_master """

    # load tutorial_site directly

    # use button
    button = html.BUTTON("Lancement du tutoriel youtube pour le site", id='tutorial_link_master', Class='btn-inside')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open("https://www.youtube.com/watch?v=T4jJzCxLslc"))
    document['tutorial_link_master'].click()


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

    if item_name == 'Règles simplifiées':
        show_simplified_rules()
    if item_name == 'Foire aux questions':
        show_faq()
    if item_name == 'Les petits tuyaux':
        show_tips()
    if item_name == 'Charte du bon diplomate':
        show_diplomat_chart()
    if item_name == 'Youtube Diplomacy':
        tutorial_game()
    if item_name == 'Youtube Diplomania Jeu':
        tutorial_site_play()
    if item_name == 'Youtube Diplomania Arbitrage':
        tutorial_site_master()

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
