""" index """

# pylint: disable=pointless-statement, expression-not-assigned
# pylint: disable=wrong-import-position


from browser import document, html  # pylint: disable=import-error # noqa: E402

# remove at some point
import debug

import show    # noqa: E402


# TITLE
TITLE = "Front end générique Serveurs REST AJFD"
title = html.TITLE(TITLE, id='title')
title.attrs['style'] = 'text-align: center'
document <= title


# H2
H2 = "Preuve de concept de l'interface de jeu Diplomacy"
h2 = html.H2(H2, id='h2')
h2.attrs['style'] = 'text-align: center'
document <= h2


# overall_top
overall_top = html.DIV()
overall_top.attrs['style'] = 'display:table; width:100%'
document <= overall_top

# overall
overall = html.DIV()
overall.attrs['style'] = 'display: table-row'
overall_top <= overall

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:15%; vertical-align: top;'
overall <= menu_left



# panel-middle
panel_middle = html.DIV(id='panel_middle')
overall <= panel_middle


show.render(panel_middle)
