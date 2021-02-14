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

    def select_game_callback(_):
        """ select_game_callback """

        game = input_game.value
        storage['GAME'] = game
        InfoDialog("OK", f"Game selected : {game}", remove_after=config.REMOVE_AFTER)

    games_dict = get_game_list()

    if not games_dict:
        return None

    form = html.FORM()

    legend_game = html.LEGEND("country", title="Game select")
    form <= legend_game

    input_game = html.SELECT(type="select-one", value="")
    for game in sorted(games_dict.values()):
        option = html.OPTION(game)
        if 'GAME' in storage:
            if storage['GAME'] == game:
                option.selected = True
        input_game <= option

    form <= input_game
    form <= html.BR()

    form <= html.BR()

    input_select_game = html.INPUT(type="submit", value="select game")
    input_select_game.bind("click", select_game_callback)
    form <= input_select_game

    return form


def render(panel_middle):
    """ render """

    my_panel.clear()

    my_sub_panel = select_game()

    if my_sub_panel:
        my_panel <= html.B("Select the game to interact with on the site")
        my_panel <= html.BR()
        my_panel <= my_sub_panel

    panel_middle <= my_panel
