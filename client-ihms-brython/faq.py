""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

faq_content_table = {

    "Pourquoi certaines messages sont en français, certains en angals, voire certains dans un mélange des deux  ?":
    "Les messages issus de l'interface 'front end' sont en français (sauf omission à corriger rapidement). Les messages issus du serveur 'back end' sont en anglais",

    "Peut-on jouer plusieurs rôles sur une partie  ?":
    "Non, cela n'est pas prévu. Il doit y avoir 8 intervenants distincts sur une partie (arbitre y compris)",

    "Peut-on faire des erreurs d'ordres ?":
    "Eh non. Les ordres sont 100% vérifiés avant d'être enregistrés. Par contre le menu 'taguer' dans une partie permet une communcation par ordres 'ésotériques'. Cela ne presente un intérêt que dans les parties sans communication",

    "Quand a lieu la résolution ?":
    "Quand le dernier joueur qui a des ordres a rendre coche sur la case d'accord pour résoudre, ou si pas d'ordres sont nécessaires, quand l'arbitre coche la résolution sur sa console d'arbitrage",

    "Pourquoi les dates limites changent-elles de couleur ?":
    "Le code de couleur est asez conventionnel. Jaune signifie que la date limite est proche (24h). Orange qu'elle est passée. Rouge que la grâce est aussi passée. Soyez ponctuels !",

    "Il y a des retards indiqués. Dans quel cas un joueur est -il marqué en retard ?":
    "Passer ses ordres signifie réaliser une transition 'pas prêt à résoudre' (ou pas d'information) -> 'prêt à résoudre'. Un retard signifie que cela est réalisé après la date limite (que ce soit par le joueur ou par l'arbitre). Si l'arbitre reporte la date limite, le retard n'est pas effacé (mais il est impossible d'avoir deux retards sur une même saison.) Soyez ponctuels !",

    "Pourquoi les unités ne se déplacent pas dans le bac à sable ?":
    "Le bac à sable n'a pas vocation à déplacer les unités, il cherche à répondre à la question 'que se passerait-il si...'. Il faut bien lire le compte rendu des ordres sous forme de texte sous la carte",

    "Eh, je pense avoir trouvé un bug dans le moteur de résolution. Que faire ?":
    "Le moteur s'appuie sur le DATC. Il faut utiliser le lien en page d'accueil pour envoyer un email et signaler le problème. Reproduisez le soigneusement avec le bac à sable",

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

my_panel = html.DIV(id="faq")
my_panel.attrs['style'] = 'display: table'

# --

title1 = html.H2("La foire aux questions")
my_panel <= title1

faq_content = html.DIV("faq")
my_panel <= faq_content


def reveal_callback(_, question):
    """ reveal_callback """

    faq_displayed_table[question] = not faq_displayed_table[question]
    show_faq()


def show_faq():
    """ show_faq """

    faq_content.clear()

    for question_txt, answer_txt in faq_content_table.items():

        reveal_button = html.INPUT(type="submit", value=question_txt)
        reveal_button.bind("click", lambda e, q=question_txt: reveal_callback(e, q))
        faq_content <= reveal_button

        if faq_displayed_table[question_txt]:

            faq_elt = html.DIV(answer_txt)
            faq_content <= faq_elt

        faq_content <= html.P()


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
    show_faq()
