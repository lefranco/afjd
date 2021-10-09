""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error


my_panel = html.DIV(id="artificial")

# --

# TODO
my_panel <= "Pas encore implémenté, désolé !"


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
