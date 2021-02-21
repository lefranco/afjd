""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json

from browser import document, html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config

my_panel = html.DIV(id="select")


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


def get_game_data():
    """ get_game_data """

    games_dict = None

    def reply_callback(req):
        nonlocal games_dict
        req_result = json.loads(req.text)
        if req.status != 200:
            if 'message' in req_result:
                alert("Error getting games data: {req_result['message']}")
            elif 'msg' in req_result:
                alert(f"Problem getting games data: {req_result['msg']}")
            else:
                alert(f"Undocumented issue from server")
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
        show_game_selected()

    games_data = get_game_data()

    if not games_data:
        return None

    form = html.FORM()

    legend_game = html.LEGEND("game", title="Game select")
    form <= legend_game

    input_game = html.SELECT(type="select-one", value="")
    for game in sorted([g['name'] for g in games_data.values()]):
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


def show_game_selected():
    """  show_game_selected """

    log_message = html.DIV()
    if 'GAME' in storage:
        log_message <= "Game selected is "
        log_message <= html.B(storage['GAME'])
    else:
        log_message <= "No game selected..."

    show_game_selected_panel = html.DIV(id="show_game_selected")
    show_game_selected_panel.attrs['style'] = 'text-align: left'
    show_game_selected_panel <= log_message

    if "show_game_selected" in document:
        del document["show_game_selected"]

    document <= show_game_selected_panel


def render(panel_middle):
    """ render """

    my_panel.clear()

    my_sub_panel = select_game()

    if my_sub_panel:
        my_panel <= html.B("Select the game to interact with on the site")
        my_panel <= html.BR()
        my_panel <= my_sub_panel

    panel_middle <= my_panel
