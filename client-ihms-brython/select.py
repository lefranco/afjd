""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config

my_panel = html.DIV(id="select")


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


def get_game_list():
    """ get_game_list """

    games_dict = None

    def reply_callback(req):
        nonlocal games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            alert(f"Problem : {req_result['msg']}")
            return

        req_result = json.loads(req.text)
        games_dict = req_result

    json_dict = dict()

    host = config.SERVER_CONFIG['GAME']['HOST']
    port = config.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games"

    ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    return games_dict


def select_game():
    """ select_game """

    games_dict = get_game_list()

    if not games_dict:
        return

    print(f"{games_dict=}")

    dummy = html.P("select game")
    my_panel <= dummy


def render(panel_middle) -> None:
    """ render """

    select_game()

    panel_middle <= my_panel
