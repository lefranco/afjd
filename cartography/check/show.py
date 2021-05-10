""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import enum
import time

from browser import document, html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

MAP_WIDTH=814
MAP_HEIGHT=720
MAP_FILE='map.png'

my_panel = html.DIV(id="play")
my_panel.attrs['style'] = 'display: table-row'

my_sub_panel = html.DIV(id="sub")
my_panel <= my_sub_panel


class PositionRecord:
    """ A position """

    def __init__(self, x_pos, y_pos) -> None:
        self.x_pos = x_pos
        self.y_pos = y_pos

    def __str__(self) :
        return f"x={self.x_pos} y={self.y_pos}"


def show_position():
    """ show_position """

    hovering_message = "(informations par la souris sur la carte)"


    def callback_render(_):
        """ callback_render """

        # put the background map first
        ctx.drawImage(img, 0, 0)

        # put the legends
        #variant_data.render(ctx)

        # put the position
        #position_data.render(ctx)

    def callback_canvas_mouse_move(event):
        """ callback_canvas_mouse_move """

        pos = PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)
        hover_info.text = str(pos)

        # TODO

    def callback_canvas_mouse_leave(_):
        """ callback_canvas_mouse_leave """
        hover_info.text = hovering_message

    # now we can display

    # create canvas
    canvas = html.CANVAS(id="map_canvas", width=MAP_WIDTH, height=MAP_HEIGHT, alt="Map of the game")
    ctx = canvas.getContext("2d")
    if ctx is None:
        alert("Il faudrait utiliser un navigateur plus récent !")
        return

    # probably useless
    ctx.imageSmoothingEnabled = False;

    # give some information sometimes
    canvas.bind("mousemove", callback_canvas_mouse_move)
    canvas.bind("mouseleave", callback_canvas_mouse_leave)

    # put background (this will call the callback that display the whole map)
    img = html.IMG(src=MAP_FILE)
    img.bind('load', callback_render)

    hover_info = html.DIV(hovering_message)
    hover_info.style = {
        'color': 'blue',
    }

    my_sub_panel <= hover_info
    my_sub_panel <= canvas



def render(panel_middle):
    """ render """

    show_position()
    panel_middle <= my_panel
