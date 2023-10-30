""" technical """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, alert, window  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error


import config
import common
import mapping
import interface
import scoring
import whynot
import ezml_render

LONG_DURATION_LIMIT_SEC = 1.0

# sandbox must stay first
OPTIONS = ['Documents', 'Pourquoi yapa', 'Choix d\'interface', 'Tester un scorage', 'brouillard']


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

    link1 = html.A(href="https://media.wizards.com/2015/rules/diplomacy_rules.pdf", target="_blank")
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

    title5 = html.H3("Règles simplifiées")
    MY_SUB_PANEL <= title5

    link5 = html.A(href="./docs/Summary_rules_fr.pdf", target="_blank")
    link5 <= "Lien vers une version simplifiée des règles du jeu par Edi Birsan"
    MY_SUB_PANEL <= link5

    # --

    title6 = html.H3("Création de fichier de tournoi")
    MY_SUB_PANEL <= title6

    link61 = html.A(href="./docs/Fichier_tournoi.pdf", target="_blank")
    link61 <= "Comment allouer les joueurs dans les parties d'un tournoi (i.e. créer un CSV acceptable sur le site)"
    MY_SUB_PANEL <= link61

    MY_SUB_PANEL <= html.P()

    link62 = html.A(href="./scripts/allocate.py", target="_blank")
    link62 <= "Le script à utiliser pour réaliser cette allocation (lire le document au préalable)"
    MY_SUB_PANEL <= link62

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

        reveal_button = html.INPUT(type="submit", value=question_txt)
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
        common.info_dialog(f"Interface sélectionnée pour la variante {variant_name_loaded} : {user_interface}")

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

        input_select_interface = html.INPUT(type="submit", value="Sélectionner cette interface")
        input_select_interface.bind("click", lambda e, i=user_interface: select_interface_callback(e, i))
        form <= input_select_interface

        col = html.TD()
        col <= form
        col <= html.BR()

        row = html.TR()
        row <= col

        select_table <= row

    MY_SUB_PANEL <= select_table


RATING_TABLE = {}


def test_scoring():
    """ test_scoring """

    def test_scoring_callback(ev, game_scoring, ratings_input):  # pylint: disable=invalid-name
        """ test_scoring_callback """

        ev.preventDefault()

        for name, element in ratings_input.items():
            val = 0
            try:
                val = int(element.value)
            except:  # noqa: E722 pylint: disable=bare-except
                pass
            RATING_TABLE[name] = val

        # scoring
        solo_threshold = variant_data.number_centers() // 2
        score_table = scoring.scoring(game_scoring, solo_threshold, RATING_TABLE)

        score_desc = "\n".join([f"{k} : {v} points" for k, v in score_table.items()])
        alert(f"Dans cette configuration la marque est :\n{score_desc}")

        # back to where we started
        MY_SUB_PANEL.clear()
        test_scoring()

    # title
    title = html.H3("Test de scorage")
    MY_SUB_PANEL <= title

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    game = storage['GAME']

    game_parameters_loaded = common.game_parameters_reload(game)

    variant_name_loaded = storage['GAME_VARIANT']

    # from variant name get variant content
    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)

    # selected interface (user choice)
    interface_chosen = interface.get_interface_from_variant(variant_name_loaded)

    # from display chose get display parameters
    interface_parameters_read = common.read_parameters(variant_name_loaded, interface_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, interface_parameters_read)

    # this comes from game
    game_scoring = game_parameters_loaded['scoring']

    form = html.FORM()

    title_enter_centers = html.H3("Entrer les nombre de centres")
    form <= title_enter_centers

    ratings_input = {}
    for num, role in variant_data.roles.items():

        if num == 0:
            continue

        role_name = variant_data.role_name_table[role]

        fieldset = html.FIELDSET()
        legend_centers = html.LEGEND(role_name, title="nombre de centres")
        fieldset <= legend_centers
        input_centers = html.INPUT(type="number", value=str(RATING_TABLE[role_name]) if role_name in RATING_TABLE else "")
        fieldset <= input_centers
        form <= fieldset

        ratings_input[role_name] = input_centers

    # get scoring name
    name2code = {v: k for k, v in config.SCORING_CODE_TABLE.items()}
    scoring_name = name2code[game_scoring]

    form <= html.DIV(f"Pour cette partie le scorage est {scoring_name}", Class='note')
    form <= html.BR()

    input_test_scoring = html.INPUT(type="submit", value="Calculer le scorage")
    input_test_scoring.bind("click", lambda e, gs=game_scoring, ri=ratings_input: test_scoring_callback(e, gs, ri))
    form <= input_test_scoring

    MY_SUB_PANEL <= form


def show_fog_of_war():
    """ show_fog """

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    MY_SUB_PANEL <= html.H2("Le brouillard de guerre")

    ezml_file = "./options/brouillard/brouillard.ezml"
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

MY_SUB_PANEL = html.DIV(id='technical')
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
    if item_name == 'Tester un scorage':
        test_scoring()
    if item_name == 'brouillard':
        show_fog_of_war()

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

    # this means user wants to see option
    if ARRIVAL == 'option':
        ITEM_NAME_SELECTED = OPTION_REQUESTED

    ARRIVAL = None
    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
