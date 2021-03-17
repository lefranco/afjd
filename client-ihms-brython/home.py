""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

import common

my_panel = html.DIV(id="home")

title1 = html.H2("Lien utile")
my_panel <= title1

link1 = html.A(href="http://www.diplomania.fr")
link1 <= "Le site officiel pour jouer de l'Association Française des Joueurs de Diplomatie"
my_panel <= link1

title2 = html.H2("Dernières nouvelles")
my_panel <= title2

news_content = common.get_news_content()  # pylint: disable=invalid-name
if news_content is not None:
    for line in news_content.split("\n"):
        my_panel <= html.EM(line)
        my_panel <= html.BR()

my_panel <= html.H2("Une version simplifiée des règles du Jeu")

my_panel <= html.BR()

iframe = html.IFRAME(src="./docs/Summary_rules_fr.html", width='100%', height=500)
my_panel <= iframe


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
