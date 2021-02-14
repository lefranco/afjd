""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="sandbox")


my_panel <= """
  Here go widgets simulate orders in a fake game
"""


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
