""" games """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

my_panel = html.DIV(id="games")

my_panel <= """
  Here go widgets to create a game to put playes in game to join a game
"""


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
