""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="master")


my_panel <= """
  Here go widgets to master a game
"""


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
