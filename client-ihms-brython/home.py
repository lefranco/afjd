from browser import document, html

my_panel = html.P()

my_panel <= """
Here some welcome information for the new comer
"""


def render(panel_middle):
    panel_middle <= my_panel

