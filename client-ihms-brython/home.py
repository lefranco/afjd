""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="home")

title1 = html.H2("Liens utiles")
my_panel <= title1

link1 = html.A(href="http://www.diplomania.fr")
link1 <= "Le site officiel pour jouer de l'Association Française des Joueurs de Diplomatie"
my_panel <= link1

my_panel <= html.H2("Une version simplifiée des règles du Jeu")

my_panel <= html.BR()
my_panel <= html.BR()

iframe = html.IFRAME(src="./docs/Summary_rules_fr.html", width='100%', height=500)
my_panel <= iframe


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
