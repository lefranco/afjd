""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="home")

my_panel <= """
Below rules of the games (simplified)
"""

my_panel <= html.BR()
my_panel <= html.BR()

iframe = html.IFRAME(src="./docs/Summary_rules_en.html", width='100%', height=500)
my_panel <= iframe

def render(panel_middle):
    """ render """
    panel_middle <= my_panel
