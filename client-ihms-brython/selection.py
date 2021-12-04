""" games """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import document, html, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common


my_panel = html.DIV(id="selection")
my_panel.attrs['style'] = 'display: table'


def select_game():
    """ select_game """

    def select_game_callback(_, input_game, game_data_sel):
        """ select_game_callback """

        game_name = input_game.value
        storage['GAME'] = game_name
        game_id = game_data_sel[game_name][0]
        storage['GAME_VARIANT'] = game_id
        game_variant = game_data_sel[game_name][1]
        storage['GAME_ID'] = game_variant

        InfoDialog("OK", f"Partie sélectionnée : {game_name}/{game_id}/{game_variant}", remove_after=config.REMOVE_AFTER)
        show_game_selected()

        render(g_panel_middle)

    games_data = common.get_games_data()
    if not games_data:
        alert("Erreur chargement dictionnaire parties")
        return None

    # list the variants we have
    variants = {d['variant'] for d in games_data.values()}

    # list the states we have
    current_states = {d['current_state'] for d in games_data.values()}

    select_table = html.TABLE()

    rev_state_code_table = {v: k for k, v in config.STATE_CODE_TABLE.items()}

    for variant in variants:
        for current_state in current_states:

            form = html.FORM()

            legend = html.DIV()
            legend <= "Parties basées sur la variante "
            legend <= html.B(html.EM(variant))
            legend <= " dans l'état "
            legend <= html.B(rev_state_code_table[current_state])

            fieldset = html.FIELDSET()
            legend_game = html.LEGEND(legend, title="Sélection de la partie")
            fieldset <= legend_game
            input_game = html.SELECT(type="select-one", value="")
            game_list = sorted([g['name'] for g in games_data.values() if g['variant'] == variant and g['current_state'] == current_state])
            for game in game_list:
                option = html.OPTION(game)
                if 'GAME' in storage:
                    if storage['GAME'] == game:
                        option.selected = True
                input_game <= option
            fieldset <= input_game
            form <= fieldset

            form <= html.BR()

            # create a table to pass information about selected game
            game_data_sel = {v['name']: (k, v['variant']) for k, v in games_data.items()}

            input_select_game = html.INPUT(type="submit", value="sélectionner cette partie")
            input_select_game.bind("click", lambda e, ig=input_game, gds=game_data_sel: select_game_callback(e, ig, gds))
            form <= input_select_game

            col = html.TD()
            col <= form
            col <= html.BR()

            row = html.TR()
            row <= col

            select_table <= row

    sub_panel = html.DIV(id='sub_panel')
    sub_panel <= select_table

    return sub_panel


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


g_panel_middle = None  # pylint: disable=invalid-name


def render(panel_middle):
    """ render """

    global g_panel_middle  # pylint: disable=invalid-name
    g_panel_middle = panel_middle

    my_panel.clear()

    my_sub_panel = select_game()

    if my_sub_panel:
        my_panel <= html.H2("Sélectionnez la partie (au sens partie de Diplomatie ou variante) avec laquelle vous souhaitez interagir")
        my_panel <= my_sub_panel

    panel_middle <= my_panel
