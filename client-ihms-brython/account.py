""" account """

from browser import document, html

my_panel = html.P()

my_panel <= """
  Here go widgets to create an account, delete an account
"""


def render(panel_middle) -> None:
    """ render """
    panel_middle <= my_panel
