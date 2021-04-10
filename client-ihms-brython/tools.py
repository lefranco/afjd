""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="tools")


my_panel <= """
  Here go widgets to select interface (stabbeurfou / diplomatie-online / diplomania)
"""


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
