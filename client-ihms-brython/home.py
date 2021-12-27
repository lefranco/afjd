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

NOTE_CONTENT_STATED = """
Bienvenue dans la version bêta du site Diplomania.
Information importante : vous visualisez ici une interface au design rustique pour accéder au moteur de jeu. Une version avec un design plus élaboré est espérée pour plus tard.
Merci de nous remonter vos remarques sur le forum de Diplomania ou sur le serveur Discord.
"""


def show_home():
    """ show_home """

    title = html.H3("Accueil")
    MY_SUB_PANEL <= title

    title2 = html.H4("Note importante", Class='important')
    MY_SUB_PANEL <= title2

    note_bene_content = html.DIV(Class='important')
    for line in NOTE_CONTENT_STATED.split("\n"):
        note_bene_content <= line
        note_bene_content <= html.BR()
    note_content_table = html.TABLE()
    row = html.TR()
    note_content_table <= row
    col = html.TD(note_bene_content)
    row <= col
    MY_SUB_PANEL <= note_content_table

    title3 = html.H4("Dernières nouvelles", Class='news')
    MY_SUB_PANEL <= title3

    news_content_loaded = common.get_news_content()
    news_content = html.DIV(Class='news')
    if news_content_loaded is not None:
        for line in news_content_loaded.split("\n"):
            news_content <= line
            news_content <= html.BR()
    MY_SUB_PANEL <= news_content


def show_links():
    """ show_links """

    title = html.H3("Liens")
    MY_SUB_PANEL <= title

    title1 = html.H4("Lien utile : Diplomania")
    MY_SUB_PANEL <= title1

    link1 = html.A(href="http://www.diplomania.fr", target="_blank")
    link1 <= "Diplomania : Le site officiel de l'Association Francophone des Joueurs de Diplomacy (brique sociale)"
    MY_SUB_PANEL <= link1

    title11 = html.H4("Parrainage")
    MY_SUB_PANEL <= title11

    link11 = html.A(href="https://www.helloasso.com/associations/association-francophone-des-joueurs-de-diplomacy/collectes/diplomania-fr-le-site-open-source", target="_blank")
    link11 <= "Participer au financement du développement du site"
    MY_SUB_PANEL <= link11

    title5 = html.H4("Copinage")
    MY_SUB_PANEL <= title5

    link4 = html.A(href="https://visitercracovie.wordpress.com/", target="_blank")
    link4 <= "Si vous savez pas quoi faire pendant vos vacances..."
    MY_SUB_PANEL <= link4


EMAIL_SUPPORT = "jeremie.lefrancois@gmail.com"


def show_support():
    """ show_support """

    title4 = html.H3("Support")
    MY_SUB_PANEL <= title4

    text21 = html.P("C'est arrivé, le système s'est bloqué ou le résultat n'était pas celui escompté ? Vous ne parvenez pas entrer vos ordres et la date limite est ce soir ? Votre partie n'avance pas depuis des jours et il semble que votre arbitre se soit endormi ?")
    MY_SUB_PANEL <= text21

    text22 = html.P("S'il s'agit d'un bug, il est peut-être déjà corrigé, essayez de recharger le cache de votre navigateur au préalable (par exemple en utilisant CTRL+F5 - selon les navigateurs) et n'oubliez pas de bien préciser une procédure pour reproduire le problème ainsi que la différence entre le résultat obtenu et le résultat attendu...")
    MY_SUB_PANEL <= text22

    text23 = html.P("Vous pouvez utiliser le lien ci-dessous pour envoyer un courriel :")
    MY_SUB_PANEL <= text23

    email_support = html.A(href=f"mailto:{EMAIL_SUPPORT}")
    email_support <= "Contacter le support"
    MY_SUB_PANEL <= email_support

    text3 = html.P("S'il s'agit d'une partie, précisez bien la partie et le rôle que vous y jouez.")
    MY_SUB_PANEL <= text3


FAQ_DISPLAYED_TABLE = {k: False for k in faq.FAQ_CONTENT_TABLE}
FAQ_CONTENT = html.DIV("faq")


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

        reveal_button = html.INPUT(type="submit", value=question_txt)
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        FAQ_CONTENT <= reveal_button

        if FAQ_DISPLAYED_TABLE[question_txt]:

            faq_elt = html.DIV(answer_txt)
            FAQ_CONTENT <= faq_elt

        FAQ_CONTENT <= html.P()

    MY_SUB_PANEL <= FAQ_CONTENT


def show_technical():
    """ show_technical """

    title = html.H3("Coin technique")
    MY_SUB_PANEL <= title

    title1 = html.H4("Règles du jeu officielles")
    MY_SUB_PANEL <= title1

    link1 = html.A(href="https://media.wizards.com/2015/rules/diplomacy_rules.pdf", target="_blank")
    MY_SUB_PANEL <= link1
    link1 <= "Lien vers les règles officielles du jeu"

    # --

    title2 = html.H4("Algorithme de résolution (D.A.T.C.)")
    MY_SUB_PANEL <= title2

    link2 = html.A(href="http://web.inter.nl.net/users/L.B.Kruijswijk/", target="_blank")
    link2 <= "Lien vers une description technique de l'algorithme de résolution utilisé"
    MY_SUB_PANEL <= link2

    # --

    title3 = html.H4("Choix d'implémentation")
    MY_SUB_PANEL <= title3

    link3 = html.A(href="./docs/Compl_en.pdf", target="_blank")
    link3 <= "Lien vers les choix de comportement pour le moteur de résolution"
    MY_SUB_PANEL <= link3

    # --

    title4 = html.H4("Le scorage (la marque sur un tournoi)")
    MY_SUB_PANEL <= title4

    link4 = html.A(href="./docs/Scorings.pdf", target="_blank")
    link4 <= "Lien vers les spécifications des systèmes de scorage sur le site"
    MY_SUB_PANEL <= link4

    # --

    title5 = html.H4("Règles simplifiées")
    MY_SUB_PANEL <= title5

    link5 = html.A(href="./docs/Summary_rules_fr.pdf", target="_blank")
    link5 <= "Lien vers une version simplifiée des règles du jeu par Edi Birsan"
    MY_SUB_PANEL <= link5

    # --

    title6 = html.H4("Remerciements")
    MY_SUB_PANEL <= title6

    link6 = html.A(href="https://brython.info/", target="_blank")
    link6 <= "Outil utilisé pour ce site web"
    MY_SUB_PANEL <= link6

    MY_SUB_PANEL <= html.P()

    link7 = html.A(href="https://www.flaticon.com/", target="_blank")
    link7 <= "Icônes utilisées pour ce site web"
    MY_SUB_PANEL <= link7


def select_interface():
    """ select_interface """

    variant_name_loaded = None

    def select_interface_callback(_, user_interface):
        """ select_interface_callback """

        interface.set_interface(variant_name_loaded, user_interface)
        InfoDialog("OK", f"Interface sélectionnée pour la variante {variant_name_loaded} : {user_interface}", remove_after=config.REMOVE_AFTER)

        # back to where we started
        MY_SUB_PANEL.clear()
        select_interface()

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

        input_select_interface = html.INPUT(type="submit", value="sélectionner cette interface")
        input_select_interface.bind("click", lambda e, i=user_interface: select_interface_callback(e, i))
        form <= input_select_interface

        col = html.TD()
        col <= form
        col <= html.BR()

        row = html.TR()
        row <= col

        select_table <= row

    MY_SUB_PANEL <= select_table


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

MY_SUB_PANEL = html.DIV(id="lists")
MY_PANEL <= MY_SUB_PANEL


def load_option(_, item_name):
    """ load_option """

    MY_SUB_PANEL.clear()
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
        MENU_LEFT <= menu_item


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = OPTIONS[0]

    load_option(None, ITEM_NAME_SELECTED)
    panel_middle <= MY_PANEL
