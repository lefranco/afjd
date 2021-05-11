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

    def select_display_callback(interface):
        """ select_display_callback """

        reference = f'DISPLAY_{variant_name_loaded}'.upper()
        storage[reference] = interface

        InfoDialog("OK", f"Interface sélectionnée pour la variante {variant_name_loaded} : {interface}", remove_after=config.REMOVE_AFTER)

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return None

    game = storage['GAME']

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return None

    select_table = html.TABLE()
    select_table.style = {
        "border": "solid",
    }

    for interface in INTERFACE_TABLE[variant_name_loaded]:

        form = html.FORM()

        # TODO : put in file in display directory
        interface_description = f"description de l'interface '{interface}' pour la variante {variant_name_loaded}"

        legend_game = html.LEGEND(interface_description, title="Sélection de l'interface")
        form <= legend_game
        form <= html.BR()

        form <= html.BR()
        input_select_interface = html.INPUT(type="submit", value="sélectionner l'interface")
        input_select_interface.bind("click", lambda _, i=interface: select_display_callback(i))

        form <= input_select_interface

        form <= html.BR()
        form <= html.BR()

        col = html.TD()
        col.style = {
            "border": "solid",
        }
        col <= form

        row = html.TR()
        row.style = {
            "border": "solid",
        }
        row <= col

        select_table <= row

    return select_table


def render(panel_middle):
    """ render """

    my_panel.clear()

    my_sub_panel = select_display()

    if my_sub_panel:
        my_panel <= html.B("Sélectionnez l'interface du site que vous souhaitez utiliser")
        my_panel <= html.BR()
        my_panel <= html.BR()
        my_panel <= my_sub_panel

    panel_middle <= my_panel
