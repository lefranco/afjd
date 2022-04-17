""" master """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime
import time

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import mapping
import geometry

MAX_LEN_NAME = 30
MAX_LEN_EMAIL = 60


MY_PANEL = html.DIV(id="battleship")
MY_PANEL.attrs['style'] = 'display: table'

MAP_WIDTH = 545
MAP_HEIGHT = 470

ALPHABET = list(map(chr, range(ord('A'), ord('Z') + 1)))
NUMBERS = list(map(str, range(1, 100)))

POSSIBLE_TARGET_LIST = [' '] + ALPHABET + NUMBERS

SCHEMA_PSEUDO = 'schema'

MAP_LOCATION_TABLE = {}


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
            MAP_LOCATION_TABLE[center_point] = f"{letter}{number}"

    # then the b d f etc...
    for delta_x in range(0, 20):
        for delta_y in range(0, 10):
            x_center = 27 + 25.26 * delta_x
            y_center = 49 + 43.44 * delta_y
            number = 1 + delta_x
            letter = chr(ord('b') + 2 * delta_y)
            center_point = geometry.PositionRecord(x_pos=x_center, y_pos=y_center)
            MAP_LOCATION_TABLE[center_point] = f"{letter}{number}"


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

    stored_email_origin = ""
    if 'EMAIL_ORIGIN' in storage:
        stored_email_origin = storage['EMAIL_ORIGIN']

    stored_pirate_name = ""
    if 'PIRATE_NAME' in storage:
        stored_pirate_name = storage['PIRATE_NAME']

    if not check_schema(pseudo):
        alert("Pas le bon compte (pas schema)")
        return

    players_dict = common.get_players()
    if not players_dict:
        return

    stored_event = None

    input_email_origin = None
    input_pirate_name = None
    orders_list = []
    input_buy_order = None
    input_pavilion = None
    input_target = None

    def submit_callback(_):
        """ submit_callback """

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Erreur à l'envoi de courrier électronique : {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problème à l'envoi de courrier électronique : {req_result['msg']}")
                else:
                    alert("Réponse du serveur imprévue et non documentée")
                return

            InfoDialog("OK", f"Message émis vers : {addressed_user_name}", remove_after=config.REMOVE_AFTER)

            time_stamp = time.time()
            storage['BATTLESHIP_ORDERS_VERSION'] = str(time_stamp)

            # back to where we started
            MY_PANEL.clear()
            battleship()

        # will send the the official game masters !
        addressed_user_name = SCHEMA_PSEUDO

        subject = "Rallye schema 2022 : ordres du bateau (par IHM)"

        body = ""

        # pirate name
        body += f"Nom de pirate : {input_pirate_name.value}\n"
        body += "\n"

        # move
        text = " ".join([str(o) for o in orders_list])
        body += f"Déplacement : {text}\n"

        # buy order
        body += f"Achat : {input_buy_order.value}\n"

        # pavilion
        body += f"Pavillon rouge : {'Oui' if input_pavilion.checked else 'Non'}\n"

        # target
        body += f"Cible : {input_target.value}"

        pretend_sender = input_email_origin.value

        # keep a note of email origin
        if input_email_origin.value:
            stored_email_origin = input_email_origin.value
            storage['EMAIL_ORIGIN'] = stored_email_origin

        # keep a note of pirate name
        if input_pirate_name.value:
            stored_pirate_name = input_pirate_name.value
            storage['PIRATE_NAME'] = stored_pirate_name

        addressed_id = players_dict[addressed_user_name]
        addressees = [addressed_id]

        json_dict = {
            'pseudo': pseudo,
            'addressees': " ".join([str(a) for a in addressees]),
            'subject': subject,
            'body': body,
            'force': True,
            'pretend_sender': pretend_sender,
        }

        host = config.SERVER_CONFIG['PLAYER']['HOST']
        port = config.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/mail-players"

        # sending email : need token
        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=common.noreply_callback)

    def erase_all_callback(_):
        """ erase_all_callback """
        nonlocal orders_list
        orders_list = []
        callback_render(None)
        stack_orders()

    def callback_canvas_click(event):
        """ called when there is a click down then a click up separated by less than 'LONG_DURATION_LIMIT_SEC' sec """

        pos = geometry.PositionRecord(x_pos=event.x - canvas.abs_left, y_pos=event.y - canvas.abs_top)

        best_coordinates = None
        best_dist = None
        for point, coordinates in MAP_LOCATION_TABLE.items():
            dist = point.distance(pos)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_coordinates = coordinates

        orders_list.append(best_coordinates)
        callback_render(None)
        stack_orders()

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

        for order1, order2 in zip(orders_list, orders_list[1:]):
            start = REVERSE_MAP_LOCATION_TABLE[order1]
            dest = REVERSE_MAP_LOCATION_TABLE[order2]
            mapping.draw_arrow(start.x_pos, start.y_pos, dest.x_pos, dest.y_pos, ctx)

    def stack_orders():
        """ stack_orders """
        orders_div.clear()
        text = " ".join([str(o) for o in orders_list])
        orders_div <= html.B(text)

    def put_orders(buttons_right):
        """ put_orders """

        nonlocal input_email_origin
        nonlocal input_pirate_name
        nonlocal input_buy_order
        nonlocal input_pavilion
        nonlocal input_target

        form = html.FORM()

        # email origin
        fieldset = html.FIELDSET()
        legend_email_origin = html.LEGEND("Courriel origine", title="D'où envoyez vous le courriel ?")
        fieldset <= legend_email_origin
        input_email_origin = html.INPUT(type="text", value=stored_email_origin, required=True, size=MAX_LEN_EMAIL)
        fieldset <= input_email_origin
        form <= fieldset

        # pirate name
        fieldset = html.FIELDSET()
        legend_pirate_name = html.LEGEND("Nom de pirate", title="Quel est votre nom de pirate ?")
        fieldset <= legend_pirate_name
        input_pirate_name = html.INPUT(type="text", value=stored_pirate_name, required=True, size=MAX_LEN_NAME)
        fieldset <= input_pirate_name
        form <= fieldset

        # first the move ordres from the map
        fieldset = html.FIELDSET()
        legend_move_order = html.LEGEND("Ordres de déplacement", title="A entrer à la souris !")
        fieldset <= legend_move_order
        text = " ".join([str(o) for o in orders_list])
        fieldset <= orders_div
        form <= fieldset

        # buy command
        fieldset = html.FIELDSET()
        legend_buy_order = html.LEGEND("Ordres d'achat", title="Escomptez vous acheter au port ?")
        fieldset <= legend_buy_order
        input_buy_order = html.INPUT(type="text", value="", required=True)
        fieldset <= input_buy_order
        form <= fieldset

        # pavilion command
        fieldset = html.FIELDSET()
        legend_pavilion = html.LEGEND("Pavillon rouge !", title="Attaquez vous tout ce qui bouge ?")
        fieldset <= legend_pavilion
        input_pavilion = html.INPUT(type="checkbox", checked=False)
        fieldset <= input_pavilion
        form <= fieldset

        # target
        fieldset = html.FIELDSET()
        legend_target = html.LEGEND("Cible particulière", title="Déclarez vous une intention d'attaque précise ?")
        fieldset <= legend_target
        input_target = html.SELECT(type="select-one", value="")
        for target_name in POSSIBLE_TARGET_LIST:
            option = html.OPTION(target_name)
            input_target <= option
        fieldset <= input_target
        form <= fieldset

        buttons_right <= form

    def put_erase_all(buttons_right):
        """ put_erase_all """

        input_erase_all = html.INPUT(type="submit", value="effacer les ordres de déplacement")
        input_erase_all.bind("click", erase_all_callback)
        buttons_right <= html.BR()
        buttons_right <= input_erase_all
        buttons_right <= html.BR()

    def put_submit(buttons_right):
        """ put_submit """

        input_submit = html.INPUT(type="submit", value="soumettre ces ordres")
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

    # put background (this will call the callback that display the whole map)
    img2 = html.IMG(src="./schema/map_before.png")

    # left side

    display_left = html.DIV(id='display_left')
    display_left.attrs['style'] = 'display: table-cell; width=500px; vertical-align: top; table-layout: fixed;'

    if 'BATTLESHIP_ORDERS_VERSION' in storage:
        battleship_time_stamp = float(storage['BATTLESHIP_ORDERS_VERSION'])
        date_orders_gmt = datetime.datetime.fromtimestamp(battleship_time_stamp, datetime.timezone.utc)
        date_orders_gmt_str = datetime.datetime.strftime(date_orders_gmt, "%d-%m-%Y %H:%M:%S GMT")
        display_left <= html.P()
        legend_now = html.DIV(f"Date d'envoi des derniers ordres : {date_orders_gmt_str}", Class='note')
        display_left <= legend_now
        display_left <= html.P()

    # stored by javascript
    battleship_map_version = storage['BATTLESHIP_MAP_VERSION']

    display_left <= html.P()
    legend_now = html.DIV(f"Date de la situation affichée : {battleship_map_version}", Class='important')
    display_left <= legend_now
    display_left <= html.P()

    display_left <= canvas

    display_left <= html.P()
    legend_previous = html.DIV("Situation précédente :", Class='note')
    display_left <= legend_previous
    display_left <= html.P()

    display_left <= img2

    # right side

    buttons_right = html.DIV(id='buttons_right')
    buttons_right.attrs['style'] = 'display: table-cell; width: 15%; vertical-align: top;'
    legend_start = html.DIV("Cliquez sur votre flotte  puis sur ses cases de déplacement", Class='instruction')
    buttons_right <= legend_start

    # orders
    buttons_right <= html.P()
    orders_div = html.DIV()
    buttons_right <= orders_div
    stack_orders()

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
REVERSE_MAP_LOCATION_TABLE = {v: k for k, v in MAP_LOCATION_TABLE.items()}


def render(panel_middle):
    """ render """

    MY_PANEL.clear()
    panel_middle <= MY_PANEL
    battleship()
