""" games """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common

my_panel = html.DIV(id="select")


def select_game():
    """ select_game """

    def select_game_callback(_):
        """ select_game_callback """

        game = input_game.value
        storage['GAME'] = game
        InfoDialog("OK", f"Partie sélectionnée : {game}", remove_after=config.REMOVE_AFTER)
        show_game_selected()

    games_data = common.get_games_data()

    if not games_data:
        return None

    form = html.FORM()

    legend_game = html.LEGEND("Partie", title="Sélection de la partie")
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

    input_select_game = html.INPUT(type="submit", value="sélectionner la partie")
    input_select_game.bind("click", select_game_callback)
    form <= input_select_game

    return form


def unselect_game():
    """ unselect_game """
    if 'GAME' in storage:
        del storage['GAME']
        show_game_selected()


def show_game_selected():
    """  show_game_selected """

    log_message = html.DIV()
    if 'GAME' in storage:
        log_message <= "La partie sélectionnée est "
        log_message <= html.B(storage['GAME'])
    else:
        log_message <= "Pas de partie sélectionnée..."

    show_game_selected_panel = html.DIV(id="show_game_selected")
    show_game_selected_panel.attrs['style'] = 'text-align: left'
    show_game_selected_panel <= log_message

    if 'show_game_selected' in document:
        del document['show_game_selected']

    document <= show_game_selected_panel


def render(panel_middle):
    """ render """

    my_panel.clear()

    my_sub_panel = select_game()

    if my_sub_panel:
        my_panel <= html.B("Sélectionnez la partie du site avec laquelle vous souhaitez interagir")
        my_panel <= html.BR()
        my_panel <= my_sub_panel

    panel_middle <= my_panel
