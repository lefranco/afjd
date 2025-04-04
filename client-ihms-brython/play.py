""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

from time import time

from browser import document, html, alert, timer, window   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import login

import play_low
import play_play
import play_master
import play_other
import allgames
import index


OPTIONS = {
    'Consulter': "Consulter la position et l'historique des résolutions de la partie",
    'Ordonner': "Passer ses ordres sur la partie",
    'Ordres de com\'': "Passer des ordres de communication pour une partie Blitz",
    'Imaginer': "Imaginer des unités des autre joueurs pour interagir avec pour une partie à visibilité réstreinte",
    'Messagerie': "Utiliser la messagerie privée d'un joueur/arbitre à un ou plusieurs autres",
    'Presse': "Utiliser la presse, c'est à dire la messagerie publique en diffusion à toute la partie",
    'Arbitrer': "Réaliser toutes les opérations d'arbitrage",
    'Informations': "Consulter les paramètres et les incidents (retards, abandons, désordres civils) de la partie",
    'Superviser': "Superviser (arbitrage automatique) une partie en direct"
}

ARRIVAL = None
ARRIVAL2 = None


def set_arrival(arrival):
    """ set_arrival """
    global ARRIVAL
    ARRIVAL = arrival


def set_arrival2(arrival2):
    """ set_arrival2 """
    global ARRIVAL2
    ARRIVAL2 = arrival2


def next_previous_game(previous: bool):
    """ next_game """

    if 'GAME_LIST' not in storage:
        alert("Pas de liste de parties, allez dans la page 'mes parties', désolé")
        render(index.PANEL_MIDDLE)
        return False

    games_list = storage['GAME_LIST'].split(' ')

    if play_low.GAME not in games_list:
        alert(f"La partie en cours {play_low.GAME} n'est pas dans la liste des parties de votre dernière sélection, désolé")
        render(index.PANEL_MIDDLE)
        return False

    game_position = games_list.index(play_low.GAME)

    delta = -1 if previous else 1
    new_name = games_list[(game_position + delta) % len(games_list)]

    if not index.load_game(new_name):
        alert(f"La partie destination '{new_name}' n'existe pas, elle a du être supprimée, désolé")
        render(index.PANEL_MIDDLE)
        return False

    allgames.show_game_selected()

    arrival = None
    if ITEM_NAME_SELECTED == 'Consulter':
        arrival = 'position'
    elif ITEM_NAME_SELECTED == 'Messagerie':
        arrival = 'messages'
    elif ITEM_NAME_SELECTED == 'Presse':
        arrival = 'declarations'
    elif ITEM_NAME_SELECTED == 'Informations':
        arrival = 'informations'

    # so that will go to proper page
    set_arrival(arrival)

    # action of going to game page
    render(index.PANEL_MIDDLE)

    return True


ITEM_NAME_SELECTED = None


def load_option(_, item_name):
    """ load_option """

    global ARRIVAL2

    # should have a proper token if playing
    login.check_token()

    play_low.MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    status = False

    if item_name == 'Consulter':
        status = play_other.show_position(ARRIVAL2)
    if item_name == 'Ordonner':
        status = play_play.submit_orders()
    if item_name == 'Ordres de com\'':
        status = play_play.submit_communication_orders()
    if item_name == 'Imaginer':
        status = play_play.imagine_units()
    if item_name == 'Messagerie':
        status = play_other.negotiate({}, None)
    if item_name == 'Presse':
        status = play_other.declare()
    if item_name == 'Arbitrer':
        status = play_master.game_master()
    if item_name == 'Informations':
        status = play_other.show_informations()
    if item_name == 'Superviser':
        status = play_master.supervise()

    if not status:
        return

    global ITEM_NAME_SELECTED
    prev_item_selected = ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    play_low.MENU_LEFT.clear()

    # items in menu
    for possible_item_name, legend in OPTIONS.items():

        if possible_item_name == 'Ordonner':
            # game must be ongoing
            if play_low.GAME_PARAMETERS_LOADED['current_state'] != 1:
                continue
            if play_low.GAME_PARAMETERS_LOADED['exposition']:
                # do not display menu order if exposition and not master
                if not (play_low.ROLE_ID is not None and play_low.ROLE_ID == 0):
                    continue
            else:
                # do not display menu order if not exposition and not player
                if not (play_low.ROLE_ID is not None and play_low.ROLE_ID >= 1):
                    continue

        if possible_item_name == 'Ordres de com\'':
            # game must be ongoing
            if play_low.GAME_PARAMETERS_LOADED['current_state'] != 1:
                continue
            # do not display menu tag if message game
            if play_low.GAME_PARAMETERS_LOADED['game_type'] not in [1, 3]:  # Blitz
                continue
            # do not display menu tag if fog
            if play_low.GAME_PARAMETERS_LOADED['fog']:  # Fog
                continue
            # do not display menu order if not player
            if not (play_low.ROLE_ID is not None and play_low.ROLE_ID >= 1):
                continue

        if possible_item_name == 'Imaginer':
            # game must be ongoing
            if play_low.GAME_PARAMETERS_LOADED['current_state'] != 1:
                continue
            # do not display menu show if not fog
            if not play_low.GAME_PARAMETERS_LOADED['fog']:
                continue
            # do not display menu order if not player
            if not (play_low.ROLE_ID is not None and play_low.ROLE_ID >= 1):
                continue

        if possible_item_name == 'Messagerie':
            # do not display menu Messagerie if not player or master
            if not (play_low.ROLE_ID is not None and play_low.ROLE_ID >= 0):
                continue

        if possible_item_name == 'Presse':
            # do not display menu Presse if not player or master
            if not (play_low.ROLE_ID is not None and play_low.ROLE_ID >= 0):
                continue

        if possible_item_name == 'Arbitrer':
            # do not display menu Arbitrer if not master
            if not (play_low.ROLE_ID is not None and play_low.ROLE_ID == 0):
                continue

        if possible_item_name == 'Superviser':
            # game must be ongoing
            if play_low.GAME_PARAMETERS_LOADED['current_state'] != 1:
                continue
            # do not display menu supervise if not fast game
            if not play_low.GAME_PARAMETERS_LOADED['fast']:
                continue
            # do not display menu Superviser if not master
            if not (play_low.ROLE_ID is not None and play_low.ROLE_ID == 0):
                continue

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, title=legend, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        play_low.MENU_LEFT <= menu_item

    # these cause some problems
    if prev_item_selected in ['Ordonner', 'Ordres de com\'']:
        document.unbind("keypress")

    # quitting superviser : clear timer
    if ITEM_NAME_SELECTED != 'superviser':
        if play_master.SUPERVISE_REFRESH_TIMER is not None:
            timer.clear_interval(play_master.SUPERVISE_REFRESH_TIMER)
            play_master.SUPERVISE_REFRESH_TIMER = None

    ARRIVAL2 = None


COUNTDOWN_TIMER = None


def countdown():
    """ countdown """

    colour = None
    time_stamp_now = time()
    deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']

    # only if game is ongoing
    if int(play_low.GAME_PARAMETERS_LOADED['current_state']) == 0:

        if time_stamp_now > deadline_loaded:
            colour = config.EXPIRED_WAIT_START_COLOUR

    elif int(play_low.GAME_PARAMETERS_LOADED['current_state']) == 1:

        # calculate display colour for deadline and countdown

        if play_low.GAME_PARAMETERS_LOADED['fast']:
            factor = 60
        else:
            factor = 60 * 60

        # game finished or solo
        if play_low.GAME_PARAMETERS_LOADED['soloed']:
            colour = config.SOLOED_COLOUR
        elif play_low.GAME_PARAMETERS_LOADED['end_voted']:
            colour = config.END_VOTED_COLOUR
        elif play_low.GAME_PARAMETERS_LOADED['finished']:
            colour = config.FINISHED_COLOUR
        # we are after everything !
        elif time_stamp_now > deadline_loaded + factor * 24 * config.CRITICAL_DELAY_DAY:
            colour = config.CRITICAL_COLOUR
        # we are after deadline + grace
        elif time_stamp_now > deadline_loaded + factor * play_low.GAME_PARAMETERS_LOADED['grace_duration']:
            colour = config.PASSED_GRACE_COLOUR
        # we are after deadline
        elif time_stamp_now > deadline_loaded:
            colour = config.PASSED_DEADLINE_COLOUR
        # deadline is today
        elif time_stamp_now > deadline_loaded - config.APPROACH_DELAY_SEC:
            colour = config.APPROACHING_DEADLINE_COLOUR

    else:
        return

    # set the colour
    if colour is not None:
        play_low.DEADLINE_COL.style = {
            'background-color': colour
        }

    # calculate text value of countdown

    time_stamp_now = time()
    remains = int(deadline_loaded - time_stamp_now)

    if remains < 0:
        late = - remains
        if late < 60:
            countdown_text = f"passée de {late:02}s !"
        elif late < 3600:
            countdown_text = f"passée de {late // 60:02}mn {late % 60:02}s !"
        elif late < 24 * 3600:
            countdown_text = f"passée de ~ {late // 3600:02}h !"
        else:
            countdown_text = f"passée de ~ {late // (24 * 3600)}j !"
    elif remains < 60:
        countdown_text = f"{remains:02}s"
    elif remains < 3600:
        countdown_text = f"{remains // 60:02}mn {remains % 60:02}s"
    elif remains < 24 * 3600:
        countdown_text = f"~ {remains // 3600:02}h"
    else:
        countdown_text = f"~ {remains // (24 * 3600)}j"

    # insert text
    play_low.COUNTDOWN_COL.text = countdown_text

    # set the colour
    if colour is not None:
        play_low.COUNTDOWN_COL.style = {
            'background-color': colour
        }


def render(panel_middle):
    """ render """

    # always back to top
    global ITEM_NAME_SELECTED
    global ARRIVAL

    play_low.PANEL_MIDDLE = panel_middle

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return

    if 'GAME_ID' not in storage:
        alert("ERREUR : identifiant de partie introuvable")
        return

    # check that game exists
    game_name = storage['GAME']
    if not common.get_game_data(game_name):
        alert(f"La partie {game_name} n'existe plus, probablement...")
        del storage['GAME']
        del storage['GAME_ID']
        return

    # ok
    play_low.GAME = storage['GAME']
    play_low.GAME_ID = storage['GAME_ID']

    # Connected but not player
    # Not connected
    ITEM_NAME_SELECTED = 'Consulter'

    play_low.PSEUDO = None
    if 'PSEUDO' in storage:
        play_low.PSEUDO = storage['PSEUDO']

    # from game_id and token get role

    play_low.ROLE_ID = None
    play_low.IN_GAME = False
    if play_low.PSEUDO is not None:
        play_low.ROLE_ID, play_low.IN_GAME = common.get_role_allocated_to_player_in_game(play_low.GAME_ID)

    play_low.load_static_stuff()
    play_low.load_dynamic_stuff()
    play_low.load_special_stuff()

    # this means user wants to join game
    if ARRIVAL == 'rejoindre':
        play_other.join_game()

    # initiates new countdown
    countdown()

    # start countdown (must not be inside a timed function !)
    global COUNTDOWN_TIMER
    if COUNTDOWN_TIMER is None:
        COUNTDOWN_TIMER = timer.set_interval(countdown, 1000)

    if ARRIVAL == 'position':
        # set page for position
        ITEM_NAME_SELECTED = 'Consulter'

    elif ARRIVAL == 'informations':
        # set page for messages
        ITEM_NAME_SELECTED = 'Informations'

    elif play_low.ROLE_ID is not None:

        # we have a player here

        if ARRIVAL == 'messages':
            # set page for messages
            ITEM_NAME_SELECTED = 'Messagerie'
        elif ARRIVAL == 'declarations':
            # set page for press
            ITEM_NAME_SELECTED = 'Presse'
        else:
            if play_low.ROLE_ID == 0:
                # game master
                ITEM_NAME_SELECTED = 'Arbitrer'
            else:
                # player
                ITEM_NAME_SELECTED = 'Ordonner'

    ARRIVAL = None

    load_option(None, ITEM_NAME_SELECTED)

    panel_middle <= play_low.MY_PANEL
