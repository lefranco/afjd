""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html   # pylint: disable=import-error

MY_PANEL = html.DIV(id="sandbox")
MY_PANEL.attrs['style'] = 'display: table'


def render(panel_middle):
    """ render """

    MY_PANEL.clear()
    panel_middle <= MY_PANEL

    # ----

    link = html.A(href="https://diplomania-gen.fr/forum/phpBB3", target="_blank")
    link <= "Diplomania : un forum à base du fameux phpBB3"
    MY_PANEL <= link
