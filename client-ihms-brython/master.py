""" master """

from browser import document, html


my_panel = html.DIV(id="master")


my_panel <= """
  Here go widgets to master a game
"""


def render(panel_middle) -> None:
    panel_middle <= my_panel
