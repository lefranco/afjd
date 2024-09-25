#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing

import json
import time
import argparse
import threading
import traceback


import waitress
import flask
import flask_cors
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore
import requests

import mylogger
import lowdata
import mapping
import elo_scheduler
import regularity_scheduler
import reliability_scheduler
import forgiver_scheduler

SESSION = requests.Session()

APP = flask.Flask(__name__)
flask_cors.CORS(APP)
API = flask_restful.Api(APP)


# read from parameter file
COMMUTER_ACCOUNT = ""
COMMUTER_PASSWORD = ""

# time to add to make sure to be after
EPSILON_SEC = 5

# to take it easy on server
INTER_COMMUTATION_TIME_SEC = 2


def load_credentials_config() -> None:
    """ read credentials config """

    global COMMUTER_ACCOUNT
    global COMMUTER_PASSWORD

    credentials_config = lowdata.ConfigFile('./config/credentials.ini')
    for credential in credentials_config.section_list():

        assert credential == 'credentials', "Section name is not 'credentials' in credentials configuration file"
        credentials_data = credentials_config.section(credential)

        COMMUTER_ACCOUNT = credentials_data['COMMUTER_ACCOUNT']
        COMMUTER_PASSWORD = credentials_data['COMMUTER_PASSWORD']


def commute_game(jwt_token: str, now: float, game_id: int, game_full_dict: typing.Dict[str, typing.Any]) -> bool:
    """ commute_game """

    game_name = game_full_dict['name']
    mylogger.LOGGER.info("So now trying to commute game '%s'...", game_name)

    variant_name_loaded = game_full_dict['variant']

    # get variant data
    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/variants/{variant_name_loaded}"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get variant data")
        return False
    variant_content_loaded = req_result.json()

    # selected interface (forced)
    interface_inforced = lowdata.get_inforced_interface_from_variant(variant_name_loaded)

    # from interface chose get display parameters
    parameters_read = lowdata.read_parameters(variant_name_loaded, interface_inforced)

    # build variant data
    variant_data = mapping.Variant(variant_name_loaded, variant_content_loaded, parameters_read)

    inforced_names_dict = variant_data.extract_names()
    inforced_names_dict_json = json.dumps(inforced_names_dict)

    json_dict = {
        'now': now,
        'adjudication_names': inforced_names_dict_json
    }

    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-commute-agree-solve/{game_id}"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
    if req_result.status_code == 201:
        return True

    message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
    mylogger.LOGGER.info("Failed to commute game %s : %s...", game_name, message)
    mylogger.LOGGER.info("Let's check for civil disorder settings now...")

    # Games does not use civil disorders
    # what is the season next to play ?
    if game_full_dict['current_advancement'] % 5 in [0, 2]:
        if not game_full_dict['cd_possible_moves']:
            mylogger.LOGGER.info("No. Civil disorder not allowed for moves (which are currently expected) for game %s", game_name)
            return False
    elif game_full_dict['current_advancement'] % 5 in [1, 3]:
        if not game_full_dict['cd_possible_retreats']:
            mylogger.LOGGER.info("No. Civil disorder not allowed for retreats (which are currently expected) for game %s", game_name)
            return False
    else:
        if not game_full_dict['cd_possible_builds']:
            mylogger.LOGGER.info("No. Civil disorder not allowed for builds (which are currently expected) for game %s", game_name)
            return False

    # not after deadline + grace
    if now <= game_full_dict['deadline'] + game_full_dict['grace_duration'] * 3600:
        mylogger.LOGGER.info("No. Not after grace for game %s", game_name)
        return False

    # Ok if we reach this point we may put civil disorder

    # Get the missing orders and the missing agreements

    json_dict = {}

    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-orders-submitted/{game_id}"
    req_result = SESSION.get(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)

    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get missing orders for game %s", game_name)
        return False

    submitted_data = json.loads(req_result.text)

    submitted_roles_list = submitted_data['submitted']
    agreed_now_roles_list = submitted_data['agreed_now']
    needed_roles_list = submitted_data['needed']

    # If no orders (moves expected) it makes no senses to push the game
    if game_full_dict['current_advancement'] % 5 in [0, 2]:
        if len(submitted_roles_list) == len(variant_content_loaded['disorder']):
            mylogger.LOGGER.info("No. Moves expected and nobody submitted anything for game %s", game_name)
            return False

    for role_id in needed_roles_list:

        if role_id in submitted_roles_list:
            continue

        json_dict = {
            'role_id': role_id,
            'names': inforced_names_dict_json
        }

        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-no-orders/{game_id}"
        req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)

        if req_result.status_code != 201:
            if 'msg' in req_result.json():
                mylogger.LOGGER.error(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to set civil disorder orders for role_id %d in game %s", role_id, game_name)
            return False

        mylogger.LOGGER.info("Civil disorder orders set for role_id %d in game %s", role_id, game_name)

    mylogger.LOGGER.info("Civil disorder orders set for game %s", game_name)

    for role_id in needed_roles_list:

        if role_id in agreed_now_roles_list:
            continue

        json_dict = {
            'role_id': role_id,
            'adjudication_names': inforced_names_dict_json
        }

        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-force-agree-solve/{game_id}"
        req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)

        if req_result.status_code != 201:
            if 'msg' in req_result.json():
                mylogger.LOGGER.error(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to force agreement for role_id %d in game %s", role_id, game_name)
            return False

        mylogger.LOGGER.info("Agreements forced for role_id %d in game %s", role_id, game_name)

    mylogger.LOGGER.info("Agreements forced for game %s", game_name)

    return True


def check_all_games(jwt_token: str, now: float) -> None:
    """ check_all_games """

    mylogger.LOGGER.info("Trying all games with reference time=%d...", now)

    state_expected = 1

    # get all games
    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games-in-state/{state_expected}"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get games")
        return
    games_dict = req_result.json()

    # scan games (use game identifier order)
    for game_id, game_dict in sorted(games_dict.items(), key=lambda t: int(t[0])):

        game_name = game_dict['name']

        # not after deadline (we should be after when deciding so we add epsilon)
        if now + EPSILON_SEC <= game_dict['deadline']:
            continue

        # fast game
        if game_dict['fast']:
            continue

        # archive game
        if game_dict['archive']:
            continue

        # get full game data
        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game_name}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            if 'msg' in req_result.json():
                mylogger.LOGGER.error(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to get game data")
            continue

        game_full_dict = req_result.json()

        # game finished
        if game_full_dict['finished']:
            mylogger.LOGGER.info("Ignoring game '%s' that is finished !", game_name)
            continue

        # game soloed
        if game_full_dict['soloed']:
            mylogger.LOGGER.info("Ignoring game '%s' that is soloed !", game_name)
            continue

        # when calculating deadline will round it to next hour
        result = commute_game(jwt_token, now - EPSILON_SEC, game_id, game_full_dict)
        if result:
            mylogger.LOGGER.info("=== Hurray, game '%s' was happily commuted!", game_name)

        # easy on the server !
        time.sleep(INTER_COMMUTATION_TIME_SEC)


def time_next_and_to_wait() -> typing.Tuple[float, float]:
    """ time_next_and_to_wait """

    timestamp_now = time.time()
    next_hour_time = (round(timestamp_now) // (60 * 60)) * (60 * 60) + (60 * 60)

    # time to wait before next try: make sure we are after theoretical
    must_wait_time_sec = (next_hour_time - timestamp_now) + EPSILON_SEC

    return next_hour_time, must_wait_time_sec


def acting_threaded_procedure() -> None:
    """ does the actual scheduled work """

    def get_token() -> str:
        """ get a token """

        pseudo = COMMUTER_ACCOUNT
        password = COMMUTER_PASSWORD
        external_ip = "(commuter)"

        host = lowdata.SERVER_CONFIG['USER']['HOST']
        port = lowdata.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/login"
        json_dict = {
            'user_name': pseudo,
            'password': password,
            'ip_address': external_ip
        }
        req_result = SESSION.post(url, headers={'content-type': 'application/json'}, data=json.dumps(json_dict))
        if req_result.status_code != 200:
            if 'msg' in req_result.json():
                mylogger.LOGGER.error(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to get token")
            return ""
        req_result = json.loads(req_result.text)
        jwt_token = req_result['AccessToken']  # type: ignore
        return str(jwt_token)

    with APP.app_context():

        # No, we do not wait, we go straight, because there are probably some pending...
        mylogger.LOGGER.info("Ok, go straight, make a first round...")

        # get initial token
        jwt_token = get_token()
        timestamp_token = time.time()

        # time of adjudications
        now = time.time()

        while True:

            # try to commute all games
            try:
                check_all_games(jwt_token, now)
            except:  # noqa: E722 pylint: disable=bare-except
                mylogger.LOGGER.error("Exception occured checking all games for commuting, stack is below")
                mylogger.LOGGER.error("%s", traceback.format_exc())

            # log that adjudications are done
            mylogger.LOGGER.info("Done for adjudications...")

            # Now scheduled tasks
            timestamp_now = time.time()
            hour_now = (int(timestamp_now) // 3600) % 24

            if hour_now == 0:
                mylogger.LOGGER.info("ELO Scheduler...")
                try:
                    elo_scheduler.run(jwt_token)
                except:  # noqa: E722 pylint: disable=bare-except
                    mylogger.LOGGER.error("Exception occured with ELO, stack is below")
                    mylogger.LOGGER.error("%s", traceback.format_exc())

            if hour_now == 1:
                mylogger.LOGGER.info("Reliability Scheduler...")
                try:
                    reliability_scheduler.run(jwt_token)
                except:  # noqa: E722 pylint: disable=bare-except
                    mylogger.LOGGER.error("Exception occured with Reliability, stack is below")
                    mylogger.LOGGER.error("%s", traceback.format_exc())

            if hour_now == 2:
                mylogger.LOGGER.info("Regularity Scheduler...")
                try:
                    regularity_scheduler.run(jwt_token)
                except:  # noqa: E722 pylint: disable=bare-except
                    mylogger.LOGGER.error("Exception occured with Regularity, stack is below")
                    mylogger.LOGGER.error("%s", traceback.format_exc())

            if hour_now == 3:
                mylogger.LOGGER.info("Forgiver Scheduler...")
                try:
                    forgiver_scheduler.run(jwt_token)
                except:  # noqa: E722 pylint: disable=bare-except
                    mylogger.LOGGER.error("Exception occured with Forgiver, stack is below")
                    mylogger.LOGGER.error("%s", traceback.format_exc())

            # renew token at faster every hour at slower every day
            if hour_now == 23:
                if timestamp_now > timestamp_token + 3600:
                    jwt_token = get_token()
                    timestamp_token = time.time()

            # go to sleep
            next_hour_time, must_wait_time_sec = time_next_and_to_wait()
            mylogger.LOGGER.info("Done for routine tasks. Back to sleep for %s secs...", must_wait_time_sec)
            time.sleep(must_wait_time_sec)
            now = next_hour_time


@API.resource('/access-logs/<lines>')
class AccessLogsRessource(flask_restful.Resource):  # type: ignore
    """ AccessLogsRessource """

    def get(self, lines: int) -> typing.Tuple[typing.List[str], int]:  # pylint: disable=R0201
        """
        Simply return logs content
        EXPOSED
        """

        mylogger.LOGGER.info("/access-logs - GET - accessing logs lines=%s", lines)

        # extract from log file
        with open(lowdata.FILE, encoding='UTF-8') as file:
            log_lines = file.readlines()

        # remove trailing '\n'
        log_lines = [ll.rstrip('\n') for ll in log_lines]

        # take only last part
        log_lines = log_lines[- int(lines):]

        data = log_lines
        return data, 200


# ---------------------------------
# main
# ---------------------------------


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', required=False, help='mode debug to test stuff', action='store_true')
    args = parser.parse_args()

    mylogger.start_logger(__name__)
    lowdata.load_servers_config()
    load_credentials_config()

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['SCHEDULER']['PORT']

    mylogger.LOGGER.info("")
    mylogger.LOGGER.info("=========== STARTING ================")
    mylogger.LOGGER.info("")

    # use separate thread to do stuff
    acting_thread = threading.Thread(target=acting_threaded_procedure, daemon=True)
    acting_thread.start()

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
