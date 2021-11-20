""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common


# simplest is to hard code displays of variants here
INTERFACE_TABLE = {
    'standard': ['diplomania', 'diplomatie_online', 'stabbeurfou']
}

my_panel = html.DIV(id="tools")
my_panel.attrs['style'] = 'display: table'


def get_display_from_variant(variant):
    """ get_display_from_variant """

    reference = f'DISPLAY_{variant}'.upper()
    if reference in storage:
        return storage[reference]

    # takes the first
    return INTERFACE_TABLE[variant][0]


def select_display():
    """ select_display """

    variant_name_loaded = None

    def select_display_callback(_, interface):
        """ select_display_callback """

        reference = f'DISPLAY_{variant_name_loaded}'.upper()
        storage[reference] = interface

        InfoDialog("OK", f"Interface sélectionnée pour la variante {variant_name_loaded} : {interface}", remove_after=config.REMOVE_AFTER)

        render(G_PANEL_MIDDLE)

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return None

    game = storage['GAME']

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return None

    select_table = html.TABLE()

    for interface in INTERFACE_TABLE[variant_name_loaded]:

        form = html.FORM()

        with open(f"./variants/{variant_name_loaded}/{interface}/README", "r") as file_ptr:
            lines = file_ptr.readlines()

        description = html.DIV()
        for line in lines:
            description <= line
            description <= html.BR()

        form <= description
        form <= html.BR()

        form <= html.BR()
        input_select_interface = html.INPUT(type="submit", value="sélectionner cette interface")
        input_select_interface.bind("click", lambda e, i=interface: select_display_callback(e, i))

        form <= input_select_interface

        form <= html.BR()
        form <= html.BR()

        col = html.TD()
        col <= form

        row = html.TR()
        row <= col

        select_table <= row

    return select_table


G_PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global G_PANEL_MIDDLE
    G_PANEL_MIDDLE = panel_middle

    my_panel.clear()

    my_sub_panel = select_display()

    if my_sub_panel:
        my_panel <= html.H2("Sélectionnez l'interface (pour la carte du jeu) que vous souhaitez utiliser")
        my_panel <= my_sub_panel

    panel_middle <= my_panel
