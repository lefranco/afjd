""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="technical")
my_panel.attrs['style'] = 'display: table'

# --

title1 = html.H2("Règles du jeu officielles")
my_panel <= title1

link1 = html.A(href="https://media.wizards.com/2015/rules/diplomacy_rules.pdf", target="_blank")
my_panel <= link1
link1 <= "Lien vers les règles officielles du jeu"

# --

title2 = html.H2("Algorithme de résolution (D.A.T.C.)")
my_panel <= title2

link2 = html.A(href="http://web.inter.nl.net/users/L.B.Kruijswijk/", target="_blank")
link2 <= "Lien vers une description technique de l'algorithme de résolution utilisé"
my_panel <= link2

# --

title3 = html.H2("Choix d'implémentation")
my_panel <= title3

link3 = html.A(href="./docs/Compl_en.pdf", target="_blank")
link3 <= "Lien vers les choix de comportement pour le moteur de résolution"
my_panel <= link3

# --

title4 = html.H2("Remerciements")
my_panel <= title4

link4 = html.A(href="https://brython.info/", target="_blank")
link4 <= "Outil utilisé pour ce front end"
my_panel <= link4

my_panel <= html.P()

link5 = html.A(href="https://www.flaticon.com/", target="_blank")
link5 <= "Icones utilisées pour ce front end"
my_panel <= link5

title5 = html.H2("Une version simplifiée des règles du Jeu")
my_panel <= title5

my_panel <= html.BR()

iframe = html.IFRAME(src="./docs/Summary_rules_fr.html", width='100%', height='100%')
my_panel <= iframe


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
