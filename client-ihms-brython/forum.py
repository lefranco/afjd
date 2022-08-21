""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html   # pylint: disable=import-error

MY_PANEL = html.DIV(id="forum")
MY_PANEL.attrs['style'] = 'display: table'


def render(panel_middle):
    """ render """

    MY_PANEL.clear()
    panel_middle <= MY_PANEL

    # load forum directly
    MY_PANEL <= html.A(id='forum_link')
    forum_link = document['forum_link']

    # for some reason target=_blank does not seem to work here...
    forum_link.href = html.A(href="https://diplomania-gen.fr/forum/phpBB3")

    document['forum_link'].click()
