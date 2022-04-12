""" master """

# pylint: disable=pointless-statement, expression-not-assigned


from browser import html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import mapping
import geometry


MY_PANEL = html.DIV(id="battleship")
MY_PANEL.attrs['style'] = 'display: table'

MAP_WIDTH = 545
MAP_HEIGHT = 470

ORDERS_DATA = []

SCHEMA_PSEUDO = 'schema'

TABLE = {}


# build the table to locate clicks
def build_table():
    """ build_table """

    # first the a c e etc...
    for delta_x in range(0, 20):
        for delta_y in range(0, 10):
            x_center = 39 + 25.26 * delta_x
            y_center = 30 + 43.44 * delta_y
            number = 1 + delta_x
            letter = chr(ord('a') + 2 * delta_y)
            center_point = geometry.PositionRecord(x_pos=x_center, y_pos=y_center)
            TABLE[center_point] = f"{letter}{number}"

    # then the b d f etc...
    for delta_x in range(0, 20):
        for delta_y in range(0, 10):
            x_center = 27 + 25.26 * delta_x
            y_center = 49 + 43.44 * delta_y
            number = 1 + delta_x
            letter = chr(ord('b') + 2 * delta_y)
            center_point = geometry.PositionRecord(x_pos=x_center, y_pos=y_center)
            TABLE[center_point] = f"{letter}{number}"


def check_schema(pseudo):
    """ check_schema """

    if pseudo != SCHEMA_PSEUDO:
        return False

    return True


def battleship():
    """ battleship """

    if 'PSEUDO' not in storage:
        alert("Il faut se connecter au préalable")
        return

    pseudo = storage['PSEUDO']

    if not check_schema(pseudo):
        alert("Pas le bon compte (pas schema)")
        return

    stored_event = None

    def erase_all_callback(_):
        """ erase_all_callback """
        global ORDERS_DATA
        ORDERS_DATA = []
        callback_render(None)
        stack_orders(orders)

    def submit_callback(_):
        """ submit_callback """
        alert("Will send an email. Not implemented")

    def callback_canvas_click(event):
        """ called when there is a click down then a click up separated by less than 'LONG_DURATION_LIMIT_SEC' sec """

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        best_coordinates = None
        best_dist = None
        for point, coordinates in TABLE.items():
            dist = point.distance(pos)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_coordinates = coordinates

        ORDERS_DATA.append(best_coordinates)
        callback_render(None)
        stack_orders(orders)

    def callback_canvas_mousedown(event):
        """ callback_mousedow : store event"""

        nonlocal stored_event
        stored_event = event

    def callback_canvas_mouseup(_):
        """ callback_mouseup : retrieve event and pass it"""

        # normal : call
        callback_canvas_click(stored_event)

    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        for order1, order2 in zip(ORDERS_DATA, ORDERS_DATA[1:]):
            start = REVERSE_TABLE[order1]
            dest = REVERSE_TABLE[order2]
            mapping.draw_arrow(start.x_pos, start.y_pos, dest.x_pos, dest.y_pos, ctx)

    def stack_orders(orders):
        """ stack_orders """
        text = " ".join([str(o) for o in ORDERS_DATA])
        orders.clear()
        orders <= html.B(text)

    def put_orders(buttons_right):
        """ put_orders """
        buttons_right <= orders

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="effacer")
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="soumettre")
        input_submit.bind("click", submit_callback)
        buttons_right <= html.BR()
        buttons_right <= input_submit
        buttons_right <= html.BR()

    # starts here

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=MAP_WIDTH, height=MAP_HEIGHT, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # now we need to be more clever and handle the state of the mouse (up or down)
    canvas.bind("mouseup", callback_canvas_mouseup)
    canvas.bind("mousedown", callback_canvas_mousedown)

    # put background (this will call the callback that display the whole map)
    img = html.IMG(src="./schema/map.png")
    img.bind('load', callback_render)

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    helper = html.DIV(".")
    display_left <= helper
    display_left <= canvas

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'

    legend_start = html.DIV("Cliquez sur votre flotte  puis sur ses cases de déplacement", Class='instruction')
    buttons_right <= legend_start

    # orders
    buttons_right <= html.P()
    orders = html.DIV()
    stack_orders(orders)

    put_orders(buttons_right)
    put_erase_all(buttons_right)
    put_submit(buttons_right)

    # overall
    my_sub_panel2 = html.DIV()
    my_sub_panel2.attrs['style'] = 'display:table-row'
    my_sub_panel2 <= display_left
    my_sub_panel2 <= buttons_right

    MY_PANEL <= html.H2("Une bataille navale ")
    MY_PANEL <= my_sub_panel2


build_table()
REVERSE_TABLE = {v: k for k, v in TABLE.items()}


def render(panel_middle):
    """ render """

    MY_PANEL.clear()
    panel_middle <= MY_PANEL
    battleship()
