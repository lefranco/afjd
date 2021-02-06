""" submit """

from browser import document, html

my_panel = html.P()

my_panel <= """
  Here go widgets to submit orders in game
"""


def render(panel_middle) -> None:
    panel_middle <= my_panel
