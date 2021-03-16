""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="tools")


my_panel <= """
  Here go widgets to edit a position (either for sandbox or for alterating position by a game master)
"""


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
