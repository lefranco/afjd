""" players """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error

import config

my_panel = html.DIV(id="players")


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


def get_player_list():
    """ get_player_list """

    players_dict = None

    def reply_callback(req):
        nonlocal players_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            alert(f"Problem : {req_result['msg']}")
            return

        req_result = json.loads(req.text)
        players_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['PLAYER']['HOST']
    port = config.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players"

    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    players_table = html.TABLE()
    players_table.style = {
        "padding": "5px",
        "backgroundColor": "#aaaaaa",
        "border": "solid",
    }

    # TODO : make it possible to sort etc...
    for pseudo in sorted(players_dict.values()):
        row = html.TR()
        row.style = {
            "border": "solid",
        }
        col = html.TD(pseudo)
        col.style = {
            "border": "solid",
        }
        row <= col
        players_table <= row

    return players_table


def render(panel_middle) -> None:
    """ render """

    my_panel.clear()
    my_panel <= get_player_list()
    panel_middle <= my_panel
