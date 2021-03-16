""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="technical")

# --

title1 = html.H2("Règles du jeu")
my_panel <= title1

link1 = html.A(href="https://media.wizards.com/2015/rules/diplomacy_rules.pdf")
my_panel <= link1
link1 <= "Lien vers les règles officielles du jeu"

# --

title2 = html.H2("Algorithme de résolution (D.A.T.C.)")
my_panel <= title2

link2 = html.A(href="http://web.inter.nl.net/users/L.B.Kruijswijk/")
link2 <= "Lien vers une description technique de l'algorithme de résolution utilisé"
my_panel <= link2

# --

title3 = html.H2("Choix d'implémentation")
my_panel <= title3

link3 = html.A(href="./docs/Compl_en.pdf")
link3 <= "Lien vers les choix de comportement pour le moteur de résolution"
my_panel <= link3

# --

title4 = html.H2("Remerciements")
my_panel <= title4

link4 = html.A(href="https://brython.info/")
link4 <= "Outil utilisé pour ce front end"
my_panel <= link4


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
