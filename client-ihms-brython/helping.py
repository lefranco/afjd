""" discovery """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, document, window  # pylint: disable=import-error

import faq
import tips
import ezml_render

OPTIONS = {
    'Foire aux questions': "Foire Aux Questions du site",
    'Les petits tuyaux': "Différentes petites choses à savoir pour mieux jouer sur le site",
    'Charte du bon diplomate': "Document indiquant les règles de bonne conduite en jouant les parties",
    'Règles simplifiées': "Une règle simplifiée du jeu Diplomatie par Edi Birsan",
    'Tutoriels YouTube': "Une page avec des tutoriels YouTube sur le jeu et le site"
}

ARRIVAL = None


def set_arrival(arrival):
    """ set_arrival """

    global ARRIVAL

    ARRIVAL = arrival


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


def tutorials_youtube():
    """ tutorials_youtube """

    MY_SUB_PANEL <= html.H3("Les tutoriels YouTube")

    # use button
    MY_SUB_PANEL <= html.H4("Une vidéo pleine d'humour qui présente simplement les règles du jeu")
    button1 = html.BUTTON("Lancer la vidéo", id='tutorial_game', Class='btn-inside')
    button1.bind("click", lambda e: window.open("https://youtu.be/d-ddAqTNDzA?si=Raf-hKFpgjMgdmf0"))
    MY_SUB_PANEL <= button1
#    document['tutorial_game'].click()

    # use button
    MY_SUB_PANEL <= html.H4("Une vidéo faite maison qui présente comment jouer sur ce site")
    button2 = html.BUTTON("Lancer la vidéo", id='tutorial_link_play', Class='btn-inside')
    button2.bind("click", lambda e: window.open("https://www.youtube.com/watch?v=luOiAz9i7Ls"))
    MY_SUB_PANEL <= button2
#    document['tutorial_link_play'].click()

    # use button
    MY_SUB_PANEL <= html.H4("Une vidéo faite maison qui présente comment arbitrer sur ce site")
    button3 = html.BUTTON("Lancer la vidéo", id='tutorial_link_master', Class='btn-inside')
    button3.bind("click", lambda e: window.open("https://www.youtube.com/watch?v=T4jJzCxLslc"))
    MY_SUB_PANEL <= button3
#    document['tutorial_link_master'].click()


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

    if item_name == 'Foire aux questions':
        show_faq()
    if item_name == 'Les petits tuyaux':
        show_tips()
    if item_name == 'Charte du bon diplomate':
        show_diplomat_chart()
    if item_name == 'Règles simplifiées':
        show_simplified_rules()
    if item_name == 'Tutoriels YouTube':
        tutorials_youtube()

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
    global ARRIVAL

    ITEM_NAME_SELECTED = list(OPTIONS.keys())[0]

    # this means user wants to see variant
    if ARRIVAL == 'charte':
        ITEM_NAME_SELECTED = 'Charte du bon diplomate'

    ARRIVAL = None
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
