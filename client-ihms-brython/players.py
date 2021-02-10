""" players """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

my_panel = html.DIV(id="players")

my_panel <= """
  Here go widgets to list players
"""


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
