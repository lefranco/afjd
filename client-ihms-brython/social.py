""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html, window   # pylint: disable=import-error

MY_PANEL = html.DIV(id="social")
MY_PANEL.attrs['style'] = 'display: table-row'


def render(panel_middle):
    """ render """

    MY_PANEL.clear()
    panel_middle <= MY_PANEL

    # load social directly

    # use button
    button = html.BUTTON("Lancement du la brique sociale", id='social_link')
    MY_PANEL <= button
    button.bind("click", lambda e: window.open("https://www.diplomania.fr/"))
    document['social_link'].click()
