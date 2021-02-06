""" games """

from browser import document, html

my_panel = html.P()

my_panel <= """
  Here go widgets to create a game to put playes in game to join a game
"""


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
