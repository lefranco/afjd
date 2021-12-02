""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

import common


OPTIONS = ['accueil', 'liens', 'support', 'foire aux question', 'coin technique']


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


faq_content_table = {

    "Pourquoi certaines messages sont en français, certains en angals, voire certains dans un mélange des deux  ?":
    "Les messages issus de l'interface 'front end' sont en français (sauf omission à corriger rapidement). Les messages issus du serveur 'back end' sont en anglais",

    "Peut-on jouer plusieurs rôles sur une partie  ?":
    "Non, cela n'est pas prévu. Il doit y avoir 8 intervenants distincts sur une partie (arbitre y compris)",

    "Peut-on faire des erreurs d'ordres ?":
    "Eh non. Les ordres sont 100% vérifiés avant d'être enregistrés. Par contre le menu 'taguer' dans une partie permet une communcation par ordres 'ésotériques'. Cela ne presente un intérêt que dans les parties sans communication",

    "Quand a lieu la résolution ?":
    "Quand le dernier joueur qui a des ordres a rendre coche sur la case 'prêt à résoudre' tout simplement (ou quand l'arbitre le fait à sa place pour éviter que la partie ne s'éternise)",

    "Pourquoi les dates limites changent-elles de couleur ?":
    "Le code de couleur est asez conventionnel. Jaune signifie que la date limite est proche (24h). Orange qu'elle est passée. Rouge que la grâce est aussi passée. Soyez ponctuels !",

    "Il y a des retards indiqués. Dans quel cas un joueur est -il marqué en retard ?":
    "Passer ses ordres signifie réaliser une transition 'pas prêt à résoudre' (ou pas d'information) -> 'prêt à résoudre'. Un retard signifie que cela est réalisé après la date limite (que ce soit par le joueur ou par l'arbitre). Si l'arbitre reporte la date limite, le retard n'est pas effacé (mais il est impossible d'avoir deux retards sur une même saison.) Soyez ponctuels !",

    "Pourquoi les unités ne se déplacent pas dans le bac à sable ?":
    "Le bac à sable n'a pas vocation à déplacer les unités, il cherche à répondre à la question 'que se passerait-il si...'. Il faut bien lire le compte rendu des ordres sous forme de texte sous la carte",

    "Eh, je pense avoir trouvé un bug dans le moteur de résolution. Que faire ?":
    "Le moteur s'appuie sur le DATC. Il faut utiliser le lien en page d'accueil pour envoyer un e-mail et signaler le problème. Reproduisez le soigneusement avec le bac à sable",

    "Où trouver des explications sur les paramètres des parties ?":
    "Soit en survolant les titres à la creation de la partie, soit en consultant le menu 'paramètres' d'une partie existante",

    "Comment remplacer un joueur ?":
    "C'est le rôle de l'arbitre. Il faut lui retirer le rôle dans la console d'arbitrage et attribuer le rôle à un autre joueur dans la partie, qu'il aura fallu faire venir au préalable. Faire venir ou partir les joueurs de la partie se réalise par contre dans le menu appariement",

    "Que peut faire l'arbitre ?":
    "L'arbitre démarre et arrête la partie. L'arbitre force une résolution quand il n'y a pas besoin d'ordres. Il peut forcer des ordres de désordre civil pour un pays. Il peut forcer un accord pour résoudre pour un pays. Il peut retirer ou ajouter un joueur dans une partie, et allouer un rôle ou retirer un rôle à un joueur dans une partie. Il peut modifier une date limite (même si celle-ci est gérée par le système). Il gère également les paramètres de la partie.",

    "Comment créér une partie dans laquelle je joue ?":
    "Il faut créer la partie, puis se retirer de l'arbitrage et demander à un arbitre de parties du site d'en prendre l'arbitrage",

    "C'est quoi ce truc : l'oracle ?":
    "Pas encore développé. Fournira une suggestion de jeux d'ordres à partir d'une position...",

    "Est-il prévu de développer des variantes ?":
    "Certainement. Hundred tient la corde pour le moment",

    "Je veux donner de l'argent pour le site. Que faire ?":
    "Reportez vous à la page d'accueil du site pour le lien vers le site de recueil des dons",

    "Comment discuter avec les membres de la communauté":
    "Reportez vous à la page d'accueil du site pour le lien vers la brique sociale.",

    "Ce site est-il le site de jeu officiel de l'AFJD ?":
    "Oui. Une autre interface moins rustique est prévue mais plus tard.",
}

faq_displayed_table = {k: False for k in faq_content_table}
faq_content = html.DIV("faq")


def show_faq():
    """ show_faq """

    def reveal_callback(_, question):
        """ reveal_callback """

        faq_displayed_table[question] = not faq_displayed_table[question]
        show_faq()

    title1 = html.H3("Foire aux questions")
    my_sub_panel <= title1

    faq_content.clear()

    for question_txt, answer_txt in faq_content_table.items():

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
