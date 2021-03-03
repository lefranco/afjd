""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="technical")

title1 = html.H2("Rules of the game")
my_panel  <= title1

link1 = html.A(href="https://media.wizards.com/2015/rules/diplomacy_rules.pdf")
link1 <= "Link to the official rules of the game"
my_panel  <= link1

title2 = html.H2("Adjudication algorithm")
my_panel  <= title2

link2 = html.A(href="http://web.inter.nl.net/users/L.B.Kruijswijk/")
link2 <= "Link to the algorithm used for adjudication component"
my_panel  <= link2

title3 = html.H2("Implementation choices")
my_panel  <= title3

iframe = html.IFRAME(src="./docs/Compl_en.pdf", width='100%', height=500)
my_panel <= iframe


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
