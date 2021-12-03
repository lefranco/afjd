""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import faq
import interface
import config
import common


OPTIONS = ['accueil', 'liens', 'support', 'foire aux question', 'coin technique', 'choix d\'interface']


def show_home():
    """ show_home """

    title = html.H3("Accueil")
    my_sub_panel <= title

    title2 = html.H4("Note importante", Class='important')
    my_sub_panel <= title2

    # pylint: disable=invalid-name
    note_content_stated = """
    Bienvenue dans la version Beta du site diplomania.
    Information importante : vous visualisez ici une interface au design rustique pour accéder au moteur de jeu. Une version avec un design plus élaboré est espérée pour plus tard.
    Merci de nous remonter vos remarques sur le forum de diplomania ou sur le serveur Discord.
    """

    note_bene_content = html.DIV(Class='important')
    for line in note_content_stated.split("\n"):
        note_bene_content <= line
        note_bene_content <= html.BR()
    note_content_table = html.TABLE()
    row = html.TR()
    note_content_table <= row
    col = html.TD(note_bene_content)
    row <= col
    my_sub_panel <= note_content_table

    title3 = html.H4("Dernières nouvelles", Class='news')
    my_sub_panel <= title3

    news_content_loaded = common.get_news_content()  # pylint: disable=invalid-name
    news_content = html.DIV(Class='news')
    if news_content_loaded is not None:
        for line in news_content_loaded.split("\n"):
            news_content <= line
            news_content <= html.BR()
    my_sub_panel <= news_content


def show_links():
    """ show_links """

    title = html.H3("Liens")
    my_sub_panel <= title

    title1 = html.H4("Lien utile : Diplomania")
    my_sub_panel <= title1

    link1 = html.A(href="http://www.diplomania.fr", target="_blank")
    link1 <= "Diplomania : Le site officiel de l'Association Francophone des Joueurs de Diplomacy (brique sociale)"
    my_sub_panel <= link1

    title11 = html.H4("Parainage")
    my_sub_panel <= title11

    link11 = html.A(href="https://www.helloasso.com/associations/association-francophone-des-joueurs-de-diplomacy/collectes/diplomania-fr-le-site-open-source", target="_blank")
    link11 <= "Participer au financement du développement du site"
    my_sub_panel <= link11

    title5 = html.H4("Copinage")
    my_sub_panel <= title5

    link4 = html.A(href="https://visitercracovie.wordpress.com/", target="_blank")
    link4 <= "Si vous savez pas quoi faire pendant vos vacances..."
    my_sub_panel <= link4


EMAIL_SUPPORT = "jeremie.lefrancois@gmail.com"


def show_support():
    """ show_support """

    title4 = html.H3("Support")
    my_sub_panel <= title4

    text21 = html.P("C'est arrivé, le système s'est bloqué ou le résultat n'était pas celui escompté ? Vous ne parvenez pas entrer vos ordres et la DL est ce soir ? Votre partie n'avance pas depuis des jours et il semble que votre arbitre se soit endormi ?")
    my_sub_panel <= text21

    text22 = html.P("S'il s'agit d'un bug, il est peut-être déjà corrigé, essayez de recharger le cache de votre navigateur au préalable (par exemple en utilisant CTRL+F5 - selon les navigateurs) et n'oubliez pas de bien préciser une procédure pour reproduire le problème ainsi que la différence entre le résultat obtenu et le résultat attendu ...")
    my_sub_panel <= text22

    text23 = html.P("Vous pouvez utiliser le lien ci-dessous pour envoyer un e-mail :")
    my_sub_panel <= text23

    email_support = html.A(href=f"mailto:{EMAIL_SUPPORT}")
    email_support <= "Contacter le support"
    my_sub_panel <= email_support

    text3 = html.P("S'il s'agit d'une partie, précisez bien la partie et le rôle que vous y jouez.")
    my_sub_panel <= text3


faq_displayed_table = {k: False for k in faq.FAQ_CONTENT_TABLE}  # pylint: disable=invalid-name
faq_content = html.DIV("faq")  # pylint: disable=invalid-name


def show_faq():
    """ show_faq """

    def reveal_callback(_, question):
        """ reveal_callback """

        faq_displayed_table[question] = not faq_displayed_table[question]
        show_faq()

    title1 = html.H3("Foire aux questions")
    my_sub_panel <= title1

    faq_content.clear()

    for question_txt, answer_txt in faq.FAQ_CONTENT_TABLE.items():

        reveal_button = html.INPUT(type="submit", value=question_txt)
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        faq_content <= reveal_button

        if faq_displayed_table[question_txt]:

            faq_elt = html.DIV(answer_txt)
            faq_content <= faq_elt

        faq_content <= html.P()

    my_sub_panel <= faq_content


def show_technical():
    """ show_technical """

    title1 = html.H3("Coin technique")
    my_sub_panel <= title1

    title1 = html.H4("Règles du jeu officielles")
    my_sub_panel <= title1

    link1 = html.A(href="https://media.wizards.com/2015/rules/diplomacy_rules.pdf", target="_blank")
    my_sub_panel <= link1
    link1 <= "Lien vers les règles officielles du jeu"

    # --

    title2 = html.H4("Algorithme de résolution (D.A.T.C.)")
    my_sub_panel <= title2

    link2 = html.A(href="http://web.inter.nl.net/users/L.B.Kruijswijk/", target="_blank")
    link2 <= "Lien vers une description technique de l'algorithme de résolution utilisé"
    my_sub_panel <= link2

    # --

    title3 = html.H4("Choix d'implémentation")
    my_sub_panel <= title3

    link3 = html.A(href="./docs/Compl_en.pdf", target="_blank")
    link3 <= "Lien vers les choix de comportement pour le moteur de résolution"
    my_sub_panel <= link3

    # --

    title4 = html.H4("Remerciements")
    my_sub_panel <= title4

    link4 = html.A(href="https://brython.info/", target="_blank")
    link4 <= "Outil utilisé pour ce front end"
    my_sub_panel <= link4

    my_sub_panel <= html.P()

    link5 = html.A(href="https://www.flaticon.com/", target="_blank")
    link5 <= "Icones utilisées pour ce front end"
    my_sub_panel <= link5

    title5 = html.H4("Les spécifications des systèmes de scorage sur le site")
    my_sub_panel <= title5

    my_sub_panel <= html.BR()

    iframe1 = html.IFRAME(src="./docs/Scorings.pdf", width=1000, height=1000)
    my_sub_panel <= iframe1

    title6 = html.H4("Une version simplifiée des règles du Jeu")
    my_sub_panel <= title6

    my_sub_panel <= html.BR()

    iframe2 = html.IFRAME(src="./docs/Summary_rules_fr.pdf", width=1000, height=1000)
    my_sub_panel <= iframe2


def select_interface():
    """ select_interface """

    variant_name_loaded = None

    def select_interface_callback(_, user_interface):
        """ select_interface_callback """

        interface.set_interface(variant_name_loaded, user_interface)
        InfoDialog("OK", f"Interface sélectionnée pour la variante {variant_name_loaded} : {user_interface}", remove_after=config.REMOVE_AFTER)

        # back to where we started
        my_sub_panel.clear()
        select_interface()

    title1 = html.H3("Choix d'interface")
    my_sub_panel <= title1

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable (pour la variante)")
        return

    game = storage['GAME']

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        alert("Problème chargement nom de variante")
        return

    information = html.DIV(Class='important')
    information <= "Une 'interface' vous permet d'avoir une carte et des trigrammes de désignation des régions spécifiques c'est à dire différents de ceux pratiqués sur le site"
    my_sub_panel <= information
    my_sub_panel <= html.BR()

    select_table = html.TABLE()

    for user_interface in interface.INTERFACE_TABLE[variant_name_loaded]:

        # get description
        with open(f"./variants/{variant_name_loaded}/{user_interface}/README", "r") as file_ptr:
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

        input_select_interface = html.INPUT(type="submit", value="sélectionner cette interface")
        input_select_interface.bind("click", lambda e, i=user_interface: select_interface_callback(e, i))
        form <= input_select_interface

        col = html.TD()
        col <= form
        col <= html.BR()

        row = html.TR()
        row <= col

        select_table <= row

    my_sub_panel <= select_table


my_panel = html.DIV()
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="lists")
my_panel <= my_sub_panel


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'accueil':
        show_home()
    if item_name == 'liens':
        show_links()
    if item_name == 'support':
        show_support()
    if item_name == 'foire aux question':
        show_faq()
    if item_name == 'coin technique':
        show_technical()
    if item_name == 'choix d\'interface':
        select_interface()

    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

    load_option(None, item_name_selected)
    panel_middle <= my_panel
