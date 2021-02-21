""" submit """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config

OPTIONS = ['submit orders', 'negotiate', 'display parameters']

my_panel = html.DIV(id="play")
my_panel.attrs['style'] = 'display: table-row'

# menu-left
menu_left = html.DIV()
menu_left.attrs['style'] = 'display: table-cell; width:25%; vertical-align: top;'
my_panel <= menu_left

# menu-selection
menu_selection = html.UL()
menu_left <= menu_selection

item_name_selected = OPTIONS[0]  # pylint: disable=invalid-name

my_sub_panel = html.DIV(id="sub")

my_panel <= my_sub_panel


def submit_orders():
    """ submit_orders """

    dummy = html.P("submit orders")
    my_sub_panel <= dummy


def negotiate():
    """ negotiate """

    dummy = html.P("negotiate")
    my_sub_panel <= dummy


def display_parameters():
    """ display_parameters """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']
    parameters_loaded = None

    def display_all_parameters_reload():
        """ change_description_reload """

        status = True

        def local_noreply_callback(_):
            """ noreply_callback """
            nonlocal status
            alert("Problem (no answer from server)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal parameters_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error loading all parameters: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem loading all parameters: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                status = False
                return

            parameters_loaded = req_result

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    status = display_all_parameters_reload()
    if not status:
        return

    game_params_table = html.TABLE()
    game_params_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }
    for key, value in parameters_loaded.items():
        row = html.TR()
        row.style = {
            "border": "solid",
        }

        col1 = html.TD(key)
        col1.style = {
            "border": "solid",
        }
        row <= col1

        col2 = html.TD(value)
        col2.style = {
            "border": "solid",
        }
        row <= col2

        game_params_table <= row

    my_sub_panel <= game_params_table


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'submit orders':
        submit_orders()
    if item_name == 'negotiate':
        negotiate()
    if item_name == 'display parameters':
        display_parameters()

    global item_name_selected  # pylint: disable=invalid-name
    item_name_selected = item_name

    menu_left.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        if possible_item_name == item_name_selected:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not)
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_left <= menu_item


# starts here
load_option(None, item_name_selected)


def render(panel_middle):
    """ render """
    panel_middle <= my_panel
