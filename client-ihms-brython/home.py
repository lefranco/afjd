""" home """

from browser import document, html

my_panel = html.DIV(id="home")

my_panel <= """
Here some welcome information for the new comer
"""


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
