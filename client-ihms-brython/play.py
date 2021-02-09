""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

my_panel = html.DIV(id="play")

my_panel <= """
  Here go widgets to play (submit orders, negotiate...) in game
"""


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
