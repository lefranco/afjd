""" master """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, alert   # pylint: disable=import-error

import common
import interface
import mapping

VARIANT_NAME = "standard"

my_panel = html.DIV(id="oracle")
my_panel.attrs['style'] = 'display: table'

# TODO : remove this sub_panel
my_sub_panel = html.DIV(id="sub")
my_panel <= my_sub_panel

initial_orders = {'fake_units': dict(), 'orders': dict(), }


# this will not change
variant_name_loaded = VARIANT_NAME  # pylint: disable=invalid-name

# this will
display_chosen = None  # pylint: disable=invalid-name
variant_data = None  # pylint: disable=invalid-name
position_data = None  # pylint: disable=invalid-name


def create_initial_position():
    """ create_initial_position """

    global display_chosen  # pylint: disable=invalid-name
    global variant_data  # pylint: disable=invalid-name
    global position_data  # pylint: disable=invalid-name

    # from variant name get variant content

    variant_content_loaded = common.game_variant_content_reload(variant_name_loaded)
    if not variant_content_loaded:
        return

    # selected display (user choice)
    display_chosen = interface.get_display_from_variant(variant_name_loaded)

    # from display chose get display parameters
    parameters_read = common.read_parameters(variant_name_loaded, display_chosen)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    # get the position
    position_loaded = {'ownerships': dict(), 'units': dict(), 'forbiddens': dict(), 'dislodged_ones': dict()}

    # digest the position
    position_data = mapping.Position(position_loaded, variant_data)


def import_position(new_position_data):
    """ import position from play/position """

    global position_data  # pylint: disable=invalid-name

    # make sure we are ready
    if not position_data:
        create_initial_position()

    # get loaded units
    loaded_units = new_position_data.save_json()
    dict_loaded_units = dict()
    for loaded_unit in loaded_units:
        type_num = loaded_unit['type_unit']
        role_num = loaded_unit['role']
        zone_num = loaded_unit['zone']
        if role_num not in dict_loaded_units:
            dict_loaded_units[role_num] = list()
        dict_loaded_units[role_num].append([type_num, zone_num])

    # get loaded centers for convenience
    loaded_ownerships = new_position_data.save_json2()
    dict_loaded_ownerships = dict()
    for loaded_ownership in loaded_ownerships:
        center_num = loaded_ownership['center_num']
        role_num = loaded_ownership['role']
        dict_loaded_ownerships[center_num] = role_num

    # get the position
    position_imported = {'ownerships': dict_loaded_ownerships, 'units': dict_loaded_units, 'forbiddens': dict(), 'dislodged_ones': dict()}

    # copy position
    position_data = mapping.Position(position_imported, variant_data)


def oracle():
    """ oracle """

    def consult_callback(_):
        """ consult_callback """

        # TODO : calculate some interesting orders or advices here

        alert("Hélas, trois fois hélas, ce module n'est pas encore prêt...")

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the centers
        variant_data.render(ctx)

        # put the position
        position_data.render(ctx)

        # put the legends at the end
        variant_data.render_legends(ctx)

    def put_consult(buttons_right):
        """ put_consult """

        input_consult = html.INPUT(type="submit", value="consulter l'oracle sur cette position")
        input_consult.bind("click", consult_callback)
        buttons_right <= html.BR()
        buttons_right <= input_consult
        buttons_right <= html.BR()

    # starts here

    # make sure we are ready
    if not position_data:
        create_initial_position()

    map_size = variant_data.map_size

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=map_size.x_pos, height=map_size.y_pos, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # put background (this will call the callback that display the whole map)
    img = common.read_image(variant_name_loaded, display_chosen)
    img.bind('load', callback_render)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    display_left <= canvas

    # need to be one there
    report_window = common.make_report_window("")
    display_left <= html.BR()
    display_left <= report_window

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    legend_change_position = html.DIV("Utilisez le bac à sable pour changer la position", Class='note')
    buttons_right <= legend_change_position
    buttons_right <= html.BR()
    put_consult(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    my_sub_panel <= html.H2("L'oracle : \"Que voyez-vous maître ?\"")
    my_sub_panel <= my_sub_panel2


def render(panel_middle):
    """ render """

    my_sub_panel.clear()
    panel_middle <= my_panel
    oracle()
