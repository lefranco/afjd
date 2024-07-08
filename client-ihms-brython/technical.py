""" technical """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import interface
import whynot
import mydialog
import ezml_render


OPTIONS = {
    'Documents': "Lien vers différents documents techniques sur le jeu",
    'Pourquoi yapa': "Complément à la Foire Aux Questions du site",
    'Choix d\'interface': "Choisir une interface différente de celle par défaut pour voir les parties",
    'Calcul du ELO': "Détail de la méthode de calcul du E.L.O. utilisé sur le site",
    'Le brouillard': "Des informations sur l'option 'Brouillard de Guerre' pour une partie",
    'Langage Markup Facile': "Des informations sur un langage de construction facile de pages HTML pour les descriptions techniques",
    'Evolution de la fréquentation': "Evolution sous forme graphique du nombre de joueurs actifs sur le site"
}


ARRIVAL = None

# from home
OPTION_REQUESTED = None


def set_arrival(arrival, option_requested=None):
    """ set_arrival """

    global ARRIVAL
    global OPTION_REQUESTED

    ARRIVAL = arrival

    if option_requested:
        OPTION_REQUESTED = option_requested


def show_technical():
    """ show_technical """

    MY_SUB_PANEL <= html.H2("Recueil de documents techniques")

    title1 = html.H3("Règles du jeu officielles")
    MY_SUB_PANEL <= title1

    link1 = html.A(href="./docs/DiplomacyRGS_Rulebook_v6_LR.pdf", target="_blank")
    MY_SUB_PANEL <= link1
    link1 <= "Lien vers les règles officielles du jeu"

    # --

    title2 = html.H3("Algorithme de résolution (D.A.T.C.)")
    MY_SUB_PANEL <= title2

    link2 = html.A(href="./docs/DATC.html", target="_blank")
    link2 <= "Lien vers une description technique de l'algorithme de résolution utilisé"
    MY_SUB_PANEL <= link2

    # --

    title3 = html.H3("Choix d'implémentation")
    MY_SUB_PANEL <= title3

    link3 = html.A(href="./docs/Compl_en.pdf", target="_blank")
    link3 <= "Lien vers les choix de comportement pour le moteur de résolution"
    MY_SUB_PANEL <= link3

    # --

    title4 = html.H3("Création de variante")
    MY_SUB_PANEL <= title4

    link41 = html.A(href="./docs/Requis_Variantes.pdf", target="_blank")
    link41 <= "Comment créer les fichiers nécessaire pour une variante"
    MY_SUB_PANEL <= link41

    # --

    title5 = html.H3("Les sources du site")
    MY_SUB_PANEL <= title5

    link5 = html.A(href="https://github.com/lefranco/afjd", target="_blank")
    link5 <= "Lien vers l'espace GITHUB qui archive tous les sources de la brique jeu (Diplomania v1 'front-end' et 'back-end')"
    MY_SUB_PANEL <= link5

    # --

    title7 = html.H3("Document d'interface de l'API")
    MY_SUB_PANEL <= title7

    link71 = html.A(href="https://afjdserveurressources.wordpress.com/", target="_blank")
    link71 <= "Si vous voulez vous aussi développer votre front end..."
    MY_SUB_PANEL <= link71

    # --

    title8 = html.H3("Remerciements")
    MY_SUB_PANEL <= title8

    link81 = html.A(href="https://brython.info/", target="_blank")
    link81 <= "Outil utilisé pour ce site web"
    MY_SUB_PANEL <= link81

    MY_SUB_PANEL <= html.P()

    link82 = html.A(href="https://www.flaticon.com/", target="_blank")
    link82 <= "Icônes utilisées pour ce site web"
    MY_SUB_PANEL <= link82


WHYNOT_DISPLAYED_TABLE = {k: False for k in whynot.WHYNOT_CONTENT_TABLE}
WHYNOT_CONTENT = html.DIV("faq")


def show_whynot():
    """ show_whynot """

    def reveal_callback(_, question):
        """ reveal_callback """

        WHYNOT_DISPLAYED_TABLE[question] = not WHYNOT_DISPLAYED_TABLE[question]
        MY_SUB_PANEL.clear()
        show_whynot()

    title1 = html.H3("Pourquoi c'est pas comme ça ?")
    MY_SUB_PANEL <= title1

    WHYNOT_CONTENT.clear()

    for question_txt, answer_txt in whynot.WHYNOT_CONTENT_TABLE.items():

        reveal_button = html.INPUT(type="submit", value=question_txt, Class='btn-inside')
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        WHYNOT_CONTENT <= reveal_button

        if WHYNOT_DISPLAYED_TABLE[question_txt]:

            whynot_elt = html.DIV(answer_txt, Class='faq-info')
            WHYNOT_CONTENT <= whynot_elt

        WHYNOT_CONTENT <= html.P()

    MY_SUB_PANEL <= WHYNOT_CONTENT


def select_interface():
    """ select_interface """

    variant_name_loaded = None

    def select_interface_callback(_, user_interface):
        """ select_interface_callback """

        interface.set_interface(variant_name_loaded, user_interface)
        mydialog.InfoDialog("Information", f"Interface sélectionnée pour la variante {variant_name_loaded} : {user_interface}")

        # we do not go back to where we started
        # this is intended otherwise the new maps are not active
        alert("Interface sélectionnée, rechargement du site...")

    title1 = html.H3("Choix d'interface")
    MY_SUB_PANEL <= title1

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable (pour la variante)")
        return

    if 'GAME_VARIANT' not in storage:
        alert("ERREUR : variante introuvable")
        return

    variant_name_loaded = storage['GAME_VARIANT']

    information = html.DIV(Class='important')
    information <= "Une 'interface' vous permet d'avoir une carte et des trigrammes de désignation des régions spécifiques c'est-à-dire différents de ceux pratiqués sur le site"
    MY_SUB_PANEL <= information
    MY_SUB_PANEL <= html.BR()

    select_table = html.TABLE()

    for user_interface in interface.INTERFACE_TABLE[variant_name_loaded]:

        # get description
        with open(f"./variants/{variant_name_loaded}/{user_interface}/README", "r", encoding="utf-8") as file_ptr:
            lines = file_ptr.readlines()
        description = html.DIV(Class='note')
        for line in lines:
            description <= line
            description <= html.BR()

        form = html.FORM()
        fieldset = html.FIELDSET()
        legend_display = html.LEGEND(user_interface, title=description)
        fieldset <= legend_display
        form <= fieldset

        fieldset = html.FIELDSET()
        fieldset <= description
        form <= fieldset

        form <= html.BR()

        input_select_interface = html.INPUT(type="submit", value="Sélectionner cette interface", Class='btn-inside')
        input_select_interface.bind("click", lambda e, i=user_interface: select_interface_callback(e, i))
        form <= input_select_interface

        col = html.TD()
        col <= form
        col <= html.BR()

        row = html.TR()
        row <= col

        select_table <= row

    MY_SUB_PANEL <= select_table


def show_elo_calculation():
    """ show_elo_calculation """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/calcul_elo.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_fog_of_war():
    """ show_fog """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./options/brouillard/brouillard.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def show_ezml_spec():
    """ show_ezml_spec """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    ezml_file = "./docs/ezml_description.ezml"
    my_ezml = ezml_render.MyEzml(ezml_file)
    my_ezml.render(MY_SUB_PANEL)


def frequentation_evolution():
    """ frequentation_evolution """

    # load frequentation directly

    # use button
    button = html.BUTTON("Lancement du calcul de fréquentation", id='frequentation_link', Class='btn-inside')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open("https://diplomania-gen.fr/frequentation"))
    document['frequentation_link'].click()


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
        show_technical()
    if item_name == 'Pourquoi yapa':
        show_whynot()
    if item_name == 'Choix d\'interface':
        select_interface()
    if item_name == 'Calcul du ELO':
        show_elo_calculation()
    if item_name == 'Le brouillard':
        show_fog_of_war()
    if item_name == 'Langage Markup Facile':
        show_ezml_spec()
    if item_name == 'Evolution de la fréquentation':
        frequentation_evolution()

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

    # this means user wants to see option
    if ARRIVAL in ['option']:
        ITEM_NAME_SELECTED = OPTION_REQUESTED

    ARRIVAL = None
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
