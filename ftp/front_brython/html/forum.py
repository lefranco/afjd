""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html, window   # pylint: disable=import-error

import config

MY_PANEL = html.DIV()
MY_SUB_PANEL = html.DIV(id="page")
MY_SUB_PANEL.attrs['style'] = 'display: table-row'
MY_PANEL <= MY_SUB_PANEL


def render(panel_middle):
    """ render """

    MY_SUB_PANEL.clear()
    panel_middle <= MY_SUB_PANEL

    # load forum directly

    # use button
    button = html.BUTTON("Lancement du forum (nodeBB forum)", id='forum_link', Class='btn-inside')
    MY_SUB_PANEL <= button
    button.bind("click", lambda e: window.open(f"{config.FORUM_ADDRESS}"))
    document['forum_link'].click()
