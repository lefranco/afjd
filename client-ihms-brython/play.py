""" play """

# pylint: disable=pointless-statement, expression-not-assigned, wrong-import-order, wrong-import-position

import time

from browser import document, html, alert, timer, window   # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common
import moderate
import login

import play_low
import play_play
import play_master
import play_other

OPTIONS = ['Consulter', 'Ordonner', 'Taguer', 'Négocier', 'Déclarer', 'Voter', 'Noter', 'Arbitrer', 'Appariement', 'Paramètres', 'Retards', 'Superviser']

ARRIVAL = None


def set_arrival(arrival):
    """ set_arrival """
    global ARRIVAL
    ARRIVAL = arrival


ITEM_NAME_SELECTED = None


def load_option(_, item_name, direct_last_moves=False):
    """ load_option """

    # should have a proper token if playing
    login.check_token()

    play_low.MY_SUB_PANEL.clear()
    window.scroll(0, 0)

    status = False

    if item_name == 'Consulter':
        status = play_other.show_position(direct_last_moves)
    if item_name == 'Ordonner':
        status = play_play.submit_orders()
    if item_name == 'Taguer':
        status = play_play.submit_communication_orders()
    if item_name == 'Négocier':
        status = play_other.negotiate({}, None)
    if item_name == 'Déclarer':
        status = play_other.declare()
    if item_name == 'Voter':
        status = play_play.vote()
    if item_name == 'Noter':
        status = play_other.note()
    if item_name == 'Arbitrer':
        status = play_master.game_master()
    if item_name == 'Appariement':
        status = play_other.pairing()
    if item_name == 'Paramètres':
        status = play_other.show_game_parameters()
    if item_name == 'Retards':
        status = play_other.show_events_in_game()
    if item_name == 'Superviser':
        status = play_master.supervise()

    if not status:
        return

    global ITEM_NAME_SELECTED
    prev_item_selected = ITEM_NAME_SELECTED
    ITEM_NAME_SELECTED = item_name

    play_low.MENU_LEFT.clear()

    # items in menu
    for possible_item_name in OPTIONS:

        # do not display menu supervise if not fast game
        if possible_item_name == 'Superviser':
            if not play_low.GAME_PARAMETERS_LOADED['fast']:
                continue

        if possible_item_name == ITEM_NAME_SELECTED:
            item_name_bold_or_not = html.B(possible_item_name)
        else:
            item_name_bold_or_not = possible_item_name

        button = html.BUTTON(item_name_bold_or_not, Class='btn-menu')
        button.bind("click", lambda e, i=possible_item_name: load_option(e, i))
        menu_item = html.LI(button)
        menu_item.attrs['style'] = 'list-style-type: none'
        play_low.MENU_LEFT <= menu_item

    # these cause some problems
    if prev_item_selected in ['Ordonner', 'Taguer']:
        document.unbind("keypress")

    # quitting superviser : clear timer
    if ITEM_NAME_SELECTED != 'superviser':
        if play_master.SUPERVISE_REFRESH_TIMER is not None:
            timer.clear_interval(play_master.SUPERVISE_REFRESH_TIMER)
            play_master.SUPERVISE_REFRESH_TIMER = None


COUNTDOWN_TIMER = None


def countdown():
    """ countdown """

    # only if game is ongoing
    if int(play_low.GAME_PARAMETERS_LOADED['current_state']) != 1:
        return

    deadline_loaded = play_low.GAME_PARAMETERS_LOADED['deadline']

    # calculate display colour for deadline and countdown

    colour = None
    completed = False
    time_stamp_now = time.time()

    if play_low.GAME_PARAMETERS_LOADED['fast']:
        factor = 60
    else:
        factor = 60 * 60

    # game over
    if play_low.GAME_PARAMETERS_LOADED['current_advancement'] % 5 == 4 and (play_low.GAME_PARAMETERS_LOADED['current_advancement'] + 1) // 5 >= play_low.GAME_PARAMETERS_LOADED['nb_max_cycles_to_play']:
        colour = config.GAMEOVER_COLOUR
        # keep value only for game master
        if play_low.ROLE_ID is None or play_low.ROLE_ID != 0:
            completed = True

    # we are after everything !
    elif time_stamp_now > deadline_loaded + factor * 24 * config.CRITICAL_DELAY_DAY:
        colour = config.CRITICAL_COLOUR
    # we are after deadline + grace
    elif time_stamp_now > deadline_loaded + factor * play_low.GAME_PARAMETERS_LOADED['grace_duration']:
        colour = config.PASSED_GRACE_COLOUR
    # we are after deadline + slight
    elif time_stamp_now > deadline_loaded + config.SLIGHT_DELAY_SEC:
        colour = config.PASSED_DEADLINE_COLOUR
    # we are slightly after deadline
    elif time_stamp_now > deadline_loaded:
        colour = config.SLIGHTLY_PASSED_DEADLINE_COLOUR
    # deadline is today
    elif time_stamp_now > deadline_loaded - config.APPROACH_DELAY_SEC:
        colour = config.APPROACHING_DEADLINE_COLOUR

    # set the colour
    if colour is not None:
        play_low.DEADLINE_COL.style = {
            'background-color': colour
        }

    # calculate text value of countdown

    time_stamp_now = time.time()
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
    if completed:
        play_low.COUNTDOWN_COL.text = ""
    else:
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
    if play_low.PSEUDO is not None:
        play_low.ROLE_ID = common.get_role_allocated_to_player_in_game(play_low.GAME_ID)

    play_low.load_static_stuff()
    play_low.load_dynamic_stuff()
    play_low.load_special_stuff()

    # initiates new countdown
    countdown()

    # start countdown (must not be inside a timed function !)
    global COUNTDOWN_TIMER
    if COUNTDOWN_TIMER is None:
        COUNTDOWN_TIMER = timer.set_interval(countdown, 1000)

    # this means user wants to join game
    if ARRIVAL == 'rejoindre':
        play_other.join_game()

    if play_low.ROLE_ID is not None:

        # we have a player here

        if ARRIVAL == 'declarations':
            # set page for press
            ITEM_NAME_SELECTED = 'Déclarer'
        elif ARRIVAL == 'messages':
            # set page for messages
            ITEM_NAME_SELECTED = 'Négocier'
        else:
            if play_low.ROLE_ID == 0:
                # game master
                ITEM_NAME_SELECTED = 'Arbitrer'
            else:
                # player
                ITEM_NAME_SELECTED = 'Ordonner'

    else:

        # moderator wants to see whose orders are missing
        if moderate.check_modo(play_low.PSEUDO):
            # Admin
            ITEM_NAME_SELECTED = 'Retards'

    set_arrival(None)

    load_option(None, ITEM_NAME_SELECTED)

    panel_middle <= play_low.MY_PANEL
