""" submit """

from browser import document, html

my_panel = html.DIV(id="play")

my_panel <= """
  Here go widgets to play (submit orders, negotiate...) in game
"""


def render(panel_middle) -> None:
    panel_middle <= my_panel
