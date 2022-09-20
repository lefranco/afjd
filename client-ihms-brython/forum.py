""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html, window   # pylint: disable=import-error

MY_PANEL = html.DIV(id="forum")
MY_PANEL.attrs['style'] = 'display: table-row'


def render(panel_middle):
    """ render """

    MY_PANEL.clear()
    panel_middle <= MY_PANEL

    # load forum directly

    # use button
    button = html.BUTTON("Lancement du forum", id='forum_link')
    MY_PANEL <= button
    button.bind("click", lambda e: window.open("https://diplomania-gen.fr/forum/phpBB3"))
    document['forum_link'].click()
