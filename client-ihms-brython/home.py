""" home """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

my_panel = html.DIV(id="home")

my_panel <= """
Here some welcome information for the new comer
"""


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
