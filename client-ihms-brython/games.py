""" games """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import datetime

from browser import html, ajax, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import selection

my_panel = html.DIV(id="games")

OPTIONS = ['create', 'change description', 'change access parameters', 'change deadline', 'change pace parameters', 'delete']

MAX_LEN_NAME = 30

DEFAULT_VARIANT = 'standard'
DEFAULT_SPEED_MOVES = 2
DEFAULT_SPEED_OTHERS = 1
DEFAULT_CD_POSSIBLE_MOVES_BUILDS = 0
DEFAULT_CD_OTHERS = 1
DEFAULT_VICTORY_CENTERS = 18
DEFAULT_NB_CYCLES = 99


def noreply_callback(_):
    """ noreply_callback """
    alert("Problem (no answer from server)")


def information_about_game():
    """ information_about_account """

    information = html.DIV()
    information <= "Fields with (*) cannot be changed after game is created"
    information <= html.BR()
    information <= "Fields with (**) cannot be changed after game is started"
    information <= html.BR()
    information <= "Hover the titles for more details"
    return information


def create_game():
    """ create_game """

    def create_game_callback(_):
        """ create_game_callback """

        def reply_callback(req):
            """ reply_callback """

            req_result = json.loads(req.text)
            if req.status != 201:
                if 'message' in req_result:
                    alert(f"Error creating game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem creating game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Game created : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        name = input_name.value

        if not name:
            alert("Name is missing")
            return
        if len(name) > MAX_LEN_NAME:
            alert("Name is too long")
            return

        variant = input_variant.value

        if not variant:
            alert("Variant is missing")
            return
        if len(variant) > MAX_LEN_NAME:
            alert("Variant is too long")
            return

        archive = int(input_archive.checked)
        manual = int(input_manual.checked)
        anonymous = int(input_anonymous.checked)
        silent = int(input_silent.checked)
        cumulate = int(input_cumulate.checked)
        fast = int(input_fast.checked)

        try:
            speed_moves = int(input_speed_moves.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_moves = None

        cd_possible_moves = int(input_cd_possible_moves.checked)

        try:
            speed_retreats = int(input_speed_retreats.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_retreats = None

        cd_possible_retreats = int(input_cd_possible_retreats.checked)

        try:
            speed_adjustments = int(input_speed_adjustments.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_adjustments = None

        cd_possible_builds = int(input_cd_possible_builds.checked)
        cd_possible_removals = int(input_cd_possible_removals.checked)
        play_weekend = int(input_play_weekend.checked)

        try:
            access_code = int(input_access_code.value)
        except:  # noqa: E722 pylint: disable=bare-except
            access_code = None

        try:
            access_restriction_reliability = int(input_access_restriction_reliability.value)
        except:  # noqa: E722 pylint: disable=bare-except
            access_restriction_reliability = None

        try:
            access_restriction_regularity = int(input_access_restriction_regularity.value)
        except:  # noqa: E722 pylint: disable=bare-except
            access_restriction_regularity = None

        try:
            access_restriction_performance = int(input_access_restriction_performance.value)
        except:  # noqa: E722 pylint: disable=bare-except
            access_restriction_performance = None

        try:
            nb_max_cycles_to_play = int(input_nb_max_cycles_to_play.value)
        except:  # noqa: E722 pylint: disable=bare-except
            nb_max_cycles_to_play = None

        try:
            victory_centers = int(input_victory_centers.value)
        except:  # noqa: E722 pylint: disable=bare-except
            victory_centers = None

        # these are automatic
        today = datetime.date.today()
        description = f"game created at {today} by {pseudo} variant {variant}"
        deadline = today.strftime("%Y-%m-%d")

        json_dict = {
            'name': name,
            'variant': variant,
            'archive': archive,
            'manual': manual,

            'anonymous': anonymous,
            'silent': silent,
            'cumulate': cumulate,
            'fast': fast,

            'speed_moves': speed_moves,
            'cd_possible_moves': cd_possible_moves,
            'speed_retreats': speed_retreats,
            'cd_possible_retreats': cd_possible_retreats,
            'speed_adjustments': speed_adjustments,
            'cd_possible_builds': cd_possible_builds,
            'cd_possible_removals': cd_possible_removals,
            'play_weekend': play_weekend,

            'access_code': access_code,
            'access_restriction_reliability': access_restriction_reliability,
            'access_restriction_regularity': access_restriction_regularity,
            'access_restriction_performance': access_restriction_performance,

            'nb_max_cycles_to_play': nb_max_cycles_to_play,
            'victory_centers': victory_centers,

            'description': description,
            'deadline': deadline,

            'pseudo': pseudo
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games"

        ajax.post(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    legend_title_main = html.LEGEND("Main parameters of the game (*)")
    legend_title_main.style = {
        'color': 'red',
    }
    form <= legend_title_main

    legend_name = html.LEGEND("name")
    form <= legend_name
    input_name = html.INPUT(type="text", value="", title="Name of the game (keep it short and simple)")
    form <= input_name
    form <= html.BR()

    legend_variant = html.LEGEND("variant", title="(imposed for the moment)")
    form <= legend_variant
    input_variant = html.INPUT(type="select-one", readonly=True, value=DEFAULT_VARIANT)
    form <= input_variant
    form <= html.BR()

    legend_archive = html.LEGEND("archive", title="Is this game for archiving - not played - not implemented")
    form <= legend_archive
    input_archive = html.INPUT(type="checkbox", checked=False)
    form <= input_archive
    form <= html.BR()

    legend_manual = html.LEGEND("manual pairing", title="Game master allocates roles in the game")
    form <= legend_manual
    input_manual = html.INPUT(type="checkbox", checked=False)
    form <= input_manual
    form <= html.BR()

    legend_title_terms = html.LEGEND("Terms of the game (*)")
    legend_title_terms.style = {
        'color': 'red',
    }
    form <= legend_title_terms

    legend_cumulate = html.LEGEND("cumulate", title="Can a player use more than one role - not implemented")
    form <= legend_cumulate
    input_cumulate = html.INPUT(type="checkbox", checked=False)
    form <= input_cumulate
    form <= html.BR()

    legend_anonymous = html.LEGEND("anonymous", title="Are the identitities of the players hidden - not implemented")
    form <= legend_anonymous
    input_anonymous = html.INPUT(type="checkbox", checked=False)
    form <= input_anonymous
    form <= html.BR()

    legend_silent = html.LEGEND("silent", title="Can the players send messages - not implemented")
    form <= legend_silent
    input_silent = html.INPUT(type="checkbox", checked=False)
    form <= input_silent
    form <= html.BR()

    legend_fast = html.LEGEND("fast", title="Are adjudication done as soon as all orders are in - not implemented")
    form <= legend_fast
    input_fast = html.INPUT(type="checkbox", checked=False)
    form <= input_fast
    form <= html.BR()

    legend_title_pace = html.LEGEND("Pace of the game")
    legend_title_pace.style = {
        'color': 'red',
    }
    form <= legend_title_pace

    # moves

    legend_speed_moves = html.LEGEND("speed moves", title="Days before move adjudication deadline")
    form <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=DEFAULT_SPEED_MOVES)
    form <= input_speed_moves
    form <= html.BR()

    legend_cd_possible_moves = html.LEGEND("cd possible moves", title="Civil disorder possible for move adjudication")
    form <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=False)
    form <= input_cd_possible_moves
    form <= html.BR()

    # retreats

    legend_speed_retreats = html.LEGEND("speed retreats", title="Days before retreats adjudication deadline")
    form <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=DEFAULT_SPEED_OTHERS)
    form <= input_speed_retreats
    form <= html.BR()

    legend_cd_possible_retreats = html.LEGEND("cd possible retreats", title="Civil disorder possible for move adjudication")
    form <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=False)
    form <= input_cd_possible_retreats
    form <= html.BR()

    # adjustments

    legend_speed_adjustments = html.LEGEND("speed adjustments", title="Days before adjustments adjudication deadline")
    form <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=DEFAULT_SPEED_OTHERS)
    form <= input_speed_adjustments
    form <= html.BR()

    # builds

    legend_cd_possible_builds = html.LEGEND("cd possible builds", title="Civil disorder possible for build adjudication")
    form <= legend_cd_possible_builds
    input_cd_possible_builds = html.INPUT(type="checkbox", checked=False)
    form <= input_cd_possible_builds
    form <= html.BR()

    # removals

    legend_cd_possible_removals = html.LEGEND("cd possible removals", title="Civil disorder possible for removal adjudication")
    form <= legend_cd_possible_removals
    input_cd_possible_removals = html.INPUT(type="checkbox", checked=False)
    form <= input_cd_possible_removals
    form <= html.BR()

    # ---

    legend_play_weekend = html.LEGEND("play weekend", title="Does the game play during week end ?")
    form <= legend_play_weekend
    input_play_weekend = html.INPUT(type="checkbox", checked=False)
    form <= input_play_weekend
    form <= html.BR()

    legend_title_access = html.LEGEND("Access to the game (**)")
    legend_title_access.style = {
        'color': 'red',
    }
    form <= legend_title_access

    legend_access_code = html.LEGEND("access code", title="Access code to the game")
    form <= legend_access_code
    input_access_code = html.INPUT(type="number", value="")
    form <= input_access_code
    form <= html.BR()

    legend_access_restriction_reliability = html.LEGEND("reliability restriction", title="How reliable you need to be to play in the game - punctual players")
    form <= legend_access_restriction_reliability
    input_access_restriction_reliability = html.INPUT(type="number", value="")
    form <= input_access_restriction_reliability
    form <= html.BR()

    legend_access_restriction_regularity = html.LEGEND("regularity restriction", title="How regular you need to be to play in the game - heavy players")
    form <= legend_access_restriction_regularity
    input_access_restriction_regularity = html.INPUT(type="number", value="")
    form <= input_access_restriction_regularity
    form <= html.BR()

    legend_access_restriction_performance = html.LEGEND("performance restriction", title="How performant you need to be to play in the game - good players")
    form <= legend_access_restriction_performance
    input_access_restriction_performance = html.INPUT(type="number", value="")
    form <= input_access_restriction_performance
    form <= html.BR()

    legend_title_access = html.LEGEND("Advancement of the game (*)")
    legend_title_access.style = {
        'color': 'red',
    }
    form <= legend_title_access

    legend_nb_max_cycles_to_play = html.LEGEND("maximum cycles", title="How many game years to play at most ?")
    form <= legend_nb_max_cycles_to_play
    input_nb_max_cycles_to_play = html.INPUT(type="number", value=DEFAULT_NB_CYCLES)
    form <= input_nb_max_cycles_to_play
    form <= html.BR()

    legend_victory_centers = html.LEGEND("victory centers", title="How many centers to win ?")
    form <= legend_victory_centers
    input_victory_centers = html.INPUT(type="number", value=DEFAULT_VICTORY_CENTERS)
    form <= input_victory_centers
    form <= html.BR()

    form <= html.BR()

    input_create_game = html.INPUT(type="submit", value="create game")
    input_create_game.bind("click", create_game_callback)
    form <= input_create_game

    my_sub_panel <= form


def change_description_game():
    """ change_description_game """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    description_loaded = None

    def change_description_reload():
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
            nonlocal description_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error loading game description: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem loading game description: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                status = False
                return

            description_loaded = req_result['description']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_description_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error changing game description: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem changing game description: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Description changed : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        description = input_description.value

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'description': description,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    status = change_description_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    legend_description = html.LEGEND("description", title="You can make this long. 'A game between scholars of the ESTIAM' for instance")
    form <= legend_description

    input_description = html.TEXTAREA(type="text", rows=5, cols=80)
    input_description <= description_loaded
    form <= input_description
    form <= html.BR()

    form <= html.BR()

    input_change_description_game = html.INPUT(type="submit", value="change game description")
    input_change_description_game.bind("click", change_description_game_callback)
    form <= input_change_description_game

    my_sub_panel <= form


def change_access_parameters_game():
    """ change_access_parameters_game """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    access_code_loaded = None
    access_restriction_reliability_loaded = None
    access_restriction_regularity_loaded = None
    access_restriction_performance_loaded = None

    def change_access_parameters_reload():
        """ change_access_parameters_reload """

        status = True

        def local_noreply_callback(_):
            """ noreply_callback """
            nonlocal status
            alert("Problem (no answer from server)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal access_code_loaded
            nonlocal access_restriction_reliability_loaded
            nonlocal access_restriction_regularity_loaded
            nonlocal access_restriction_performance_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error loading game access parameters: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem loading game access parameters: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                status = False
                return

            access_code_loaded = req_result['access_code']
            access_restriction_reliability_loaded = req_result['access_restriction_reliability']
            access_restriction_regularity_loaded = req_result['access_restriction_regularity']
            access_restriction_performance_loaded = req_result['access_restriction_performance']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_access_parameters_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error changing game access parameters: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem changing game access parameters: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Description changed : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        access_code = input_access_code.value
        access_restriction_reliability = input_access_restriction_reliability.value
        access_restriction_regularity = input_access_restriction_regularity.value
        access_restriction_performance = input_access_restriction_performance.value

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'access_code': access_code,
            'access_restriction_reliability': access_restriction_reliability,
            'access_restriction_regularity': access_restriction_regularity,
            'access_restriction_performance': access_restriction_performance,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    status = change_access_parameters_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    legend_access_code = html.LEGEND("access code", title="Access code to the game")
    form <= legend_access_code
    input_access_code = html.INPUT(type="number", value=access_code_loaded)
    form <= input_access_code
    form <= html.BR()

    legend_access_restriction_reliability = html.LEGEND("reliability restriction", title="How reliable you need to be to play in the game - punctual players")
    form <= legend_access_restriction_reliability
    input_access_restriction_reliability = html.INPUT(type="number", value=access_restriction_reliability_loaded)
    form <= input_access_restriction_reliability
    form <= html.BR()

    legend_access_restriction_regularity = html.LEGEND("regularity restriction", title="How regular you need to be to play in the game - heavy players")
    form <= legend_access_restriction_regularity
    input_access_restriction_regularity = html.INPUT(type="number", value=access_restriction_regularity_loaded)
    form <= input_access_restriction_regularity
    form <= html.BR()

    legend_access_restriction_performance = html.LEGEND("performance restriction", title="How performant you need to be to play in the game - good players")
    form <= legend_access_restriction_performance
    input_access_restriction_performance = html.INPUT(type="number", value=access_restriction_performance_loaded)
    form <= input_access_restriction_performance
    form <= html.BR()

    form <= html.BR()

    input_change_access_game = html.INPUT(type="submit", value="change game access parameters")
    input_change_access_game.bind("click", change_access_parameters_game_callback)
    form <= input_change_access_game

    my_sub_panel <= form


def change_deadline_game():
    """ change_deadline_game """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    deadline_loaded = None

    def change_deadline_reload():
        """ change_deadline_reload """

        status = True

        def local_noreply_callback(_):
            """ noreply_callback """
            nonlocal status
            alert("Problem (no answer from server)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal deadline_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error loading game description: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem loading game description: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                status = False
                return

            deadline_loaded = req_result['deadline']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_deadline_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error changing game description: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem changing game description: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Description changed : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        deadline = input_deadline.value

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'deadline': deadline,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    status = change_deadline_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    legend_deadline = html.LEGEND("deadline", title="Deadline. Last day allowed for submitting orders. After player is late.")
    form <= legend_deadline

    input_deadline = html.INPUT(type="date", value=deadline_loaded)
    input_deadline <= deadline_loaded
    form <= input_deadline
    form <= html.BR()

    form <= html.BR()

    input_change_deadline_game = html.INPUT(type="submit", value="change game deadline")
    input_change_deadline_game.bind("click", change_deadline_game_callback)
    form <= input_change_deadline_game

    my_sub_panel <= form


def change_pace_parameters_game():
    """ change_pace_parameters_game """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    # declare the values
    speed_moves_loaded = None
    cd_possible_moves_loaded = None
    speed_retreats_loaded = None
    cd_possible_retreats_loaded = None
    speed_adjustments_loaded = None
    cd_possible_builds_loaded = None
    cd_possible_removals_loaded = None
    play_weekend_loaded = None

    def change_pace_parameters_reload():
        """ change_pace_parameters_reload """

        status = True

        def local_noreply_callback(_):
            """ noreply_callback """
            nonlocal status
            alert("Problem (no answer from server)")
            status = False

        def reply_callback(req):
            """ reply_callback """
            nonlocal status
            nonlocal speed_moves_loaded
            nonlocal cd_possible_moves_loaded
            nonlocal speed_retreats_loaded
            nonlocal cd_possible_retreats_loaded
            nonlocal speed_adjustments_loaded
            nonlocal cd_possible_builds_loaded
            nonlocal cd_possible_removals_loaded
            nonlocal play_weekend_loaded

            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error loading game access parameters: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem loading game access parameters: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                status = False
                return

            speed_moves_loaded = req_result['speed_moves']
            cd_possible_moves_loaded = req_result['cd_possible_moves']
            speed_retreats_loaded = req_result['speed_retreats']
            cd_possible_retreats_loaded = req_result['cd_possible_retreats']
            speed_adjustments_loaded = req_result['speed_adjustments']
            cd_possible_builds_loaded = req_result['cd_possible_builds']
            cd_possible_removals_loaded = req_result['cd_possible_removals']
            play_weekend_loaded = req_result['play_weekend']

        json_dict = dict()

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.get(url, blocking=True, headers={'content-type': 'application/json'}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=local_noreply_callback)

        return status

    def change_pace_parameters_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error changing game access parameters: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem changing game access parameters: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Description changed : {req_result['msg']}", remove_after=config.REMOVE_AFTER)

        try:
            speed_moves = int(input_speed_moves.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_moves = None

        cd_possible_moves = int(input_cd_possible_moves.checked)

        try:
            speed_retreats = int(input_speed_retreats.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_retreats = None

        cd_possible_retreats = int(input_cd_possible_retreats.checked)

        try:
            speed_adjustments = int(input_speed_adjustments.value)
        except:  # noqa: E722 pylint: disable=bare-except
            speed_adjustments = None

        cd_possible_builds = int(input_cd_possible_builds.checked)
        cd_possible_removals = int(input_cd_possible_removals.checked)
        play_weekend = int(input_play_weekend.checked)

        json_dict = {
            'pseudo': pseudo,
            'name': game,
            'speed_moves': speed_moves,
            'cd_possible_moves': cd_possible_moves,
            'speed_retreats': speed_retreats,
            'cd_possible_retreats': cd_possible_retreats,
            'speed_adjustments': speed_adjustments,
            'cd_possible_builds': cd_possible_builds,
            'cd_possible_removals': cd_possible_removals,
            'play_weekend': play_weekend,
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.put(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    status = change_pace_parameters_reload()
    if not status:
        return

    form = html.FORM()

    form <= information_about_game()
    form <= html.BR()

    # moves

    legend_speed_moves = html.LEGEND("speed moves", title="Days before move adjudication deadline")
    form <= legend_speed_moves
    input_speed_moves = html.INPUT(type="number", value=speed_moves_loaded)
    form <= input_speed_moves
    form <= html.BR()

    legend_cd_possible_moves = html.LEGEND("cd possible moves", title="Civil disorder possible for move adjudication")
    form <= legend_cd_possible_moves
    input_cd_possible_moves = html.INPUT(type="checkbox", checked=cd_possible_moves_loaded)
    form <= input_cd_possible_moves
    form <= html.BR()

    # retreats

    legend_speed_retreats = html.LEGEND("speed retreats", title="Days before retreats adjudication deadline")
    form <= legend_speed_retreats
    input_speed_retreats = html.INPUT(type="number", value=speed_retreats_loaded)
    form <= input_speed_retreats
    form <= html.BR()

    legend_cd_possible_retreats = html.LEGEND("cd possible retreats", title="Civil disorder possible for move adjudication")
    form <= legend_cd_possible_retreats
    input_cd_possible_retreats = html.INPUT(type="checkbox", checked=cd_possible_retreats_loaded)
    form <= input_cd_possible_retreats
    form <= html.BR()

    # adjustments

    legend_speed_adjustments = html.LEGEND("speed adjustments", title="Days before adjustments adjudication deadline")
    form <= legend_speed_adjustments
    input_speed_adjustments = html.INPUT(type="number", value=speed_adjustments_loaded)
    form <= input_speed_adjustments
    form <= html.BR()

    # builds

    legend_cd_possible_builds = html.LEGEND("cd possible builds", title="Civil disorder possible for build adjudication")
    form <= legend_cd_possible_builds
    input_cd_possible_builds = html.INPUT(type="checkbox", checked=cd_possible_builds_loaded)
    form <= input_cd_possible_builds
    form <= html.BR()

    # removals

    legend_cd_possible_removals = html.LEGEND("cd possible removals", title="Civil disorder possible for removal adjudication")
    form <= legend_cd_possible_removals
    input_cd_possible_removals = html.INPUT(type="checkbox", checked=cd_possible_removals_loaded)
    form <= input_cd_possible_removals
    form <= html.BR()

    # ---

    legend_play_weekend = html.LEGEND("play weekend", title="Does the game play during week end ?")
    form <= legend_play_weekend
    input_play_weekend = html.INPUT(type="checkbox", checked=play_weekend_loaded)
    form <= input_play_weekend
    form <= html.BR()

    form <= html.BR()

    input_change_pace_game = html.INPUT(type="submit", value="change game pace parameters")
    input_change_pace_game.bind("click", change_pace_parameters_game_callback)
    form <= input_change_pace_game

    my_sub_panel <= form


def delete_game():
    """ delete_game """

    if 'GAME' not in storage:
        alert("Please select game beforehand")
        return

    game = storage['GAME']

    if 'PSEUDO' not in storage:
        alert("Please login beforehand")
        return

    pseudo = storage['PSEUDO']

    def delete_game_callback(_):

        def reply_callback(req):
            req_result = json.loads(req.text)
            if req.status != 200:
                if 'message' in req_result:
                    alert(f"Error deleting game: {req_result['message']}")
                elif 'msg' in req_result:
                    alert(f"Problem deleting game: {req_result['msg']}")
                else:
                    alert("Undocumented issue from server")
                return
            InfoDialog("OK", f"Game deleted : {req_result['msg']}", remove_after=config.REMOVE_AFTER)
            selection.un_select_game()

        json_dict = {
            'pseudo': pseudo
        }

        host = config.SERVER_CONFIG['GAME']['HOST']
        port = config.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game}"

        ajax.delete(url, blocking=True, headers={'content-type': 'application/json', 'AccessToken': storage['JWT_TOKEN']}, timeout=config.TIMEOUT_SERVER, data=json.dumps(json_dict), oncomplete=reply_callback, ontimeout=noreply_callback)

    form = html.FORM()

    input_delete_game = html.INPUT(type="submit", value="delete game")
    input_delete_game.bind("click", delete_game_callback)
    form <= input_delete_game

    my_sub_panel <= form


my_panel = html.DIV(id="games")
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


def load_option(_, item_name):
    """ load_option """

    my_sub_panel.clear()
    if item_name == 'create':
        create_game()
    if item_name == 'change description':
        change_description_game()
    if item_name == 'change access parameters':
        change_access_parameters_game()
    if item_name == 'change deadline':
        change_deadline_game()
    if item_name == 'change pace parameters':
        change_pace_parameters_game()
    if item_name == 'delete':
        delete_game()
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


def render(panel_middle):
    """ render """
    load_option(None, item_name_selected)
    panel_middle <= my_panel
