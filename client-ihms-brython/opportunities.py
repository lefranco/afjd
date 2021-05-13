""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="opportunities")

# --

my_panel <= """
  Here will go widgets to select a game to join from a list of games with free positions
"""


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
