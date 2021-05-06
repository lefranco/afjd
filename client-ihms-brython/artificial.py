""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="artificial")

# --

title1 = html.H2("Pas encore prêt")
my_panel <= title1



def render(panel_middle):
    """ render """
    panel_middle <= my_panel
