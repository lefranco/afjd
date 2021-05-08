""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="artificial")

# --

my_panel <= """
  Here will go widgets to play versus an AI module
"""



def render(panel_middle):
    """ render """
    panel_middle <= my_panel
