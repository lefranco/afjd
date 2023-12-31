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


def commute_game(jwt_token: str, game_id: int, variant_name_loaded: str, game_name: str) -> bool:
    """ commute_game """

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
        'adjudication_names': inforced_names_dict_json
    }

    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/game-commute-agree-solve/{game_id}"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
    if req_result.status_code != 201:
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        mylogger.LOGGER.info("Failed to commute game %s : %s", game_name, message)
        return False

    mylogger.LOGGER.info("=== Hurray, game '%s' was commuted !", game_name)
    return True


def check_all_games(jwt_token: str) -> None:
    """ check_all_games """

    # get all games
    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to fget games")
        return
    games_dict = req_result.json()

    # scan games
    for game_id, game_dict in games_dict.items():

        # fast game
        if game_dict['fast']:
            continue

        # archive game
        if game_dict['archive']:
            continue

        # not ongoing game
        if game_dict['current_state'] != 1:
            continue

        # game actually finished
        if game_dict['current_advancement'] % 5 == 4 and (game_dict['current_advancement'] + 1) // 5 >= game_dict['nb_max_cycles_to_play']:
            continue

        # not after deadline
        timestamp_now = time.time()
        if timestamp_now <= game_dict['deadline']:
            continue

        game_name = game_dict['name']

        # get game data
        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{game_name}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            if 'msg' in req_result.json():
                mylogger.LOGGER.error(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to get game data")
            continue

        game_dict = req_result.json()
        variant_name = game_dict['variant']

        mylogger.LOGGER.info("Trying game '%s'...", game_name)

        _ = commute_game(jwt_token, game_id, variant_name, game_name)

        # easy on the server !
        time.sleep(INTER_COMMUTATION_TIME_SEC)


def time_to_wait() -> float:
    """ time_to_wait """

    timestamp_now = time.time()
    next_hour_time = (round(timestamp_now) // (60 * 60)) * (60 * 60) + (60 * 60)
    wait_time = next_hour_time - timestamp_now

    # make sure we are after
    wait_time += EPSILON_SEC

    return wait_time


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

        while True:

            mylogger.LOGGER.info("Trying all games...")

            # try to commute all games
            check_all_games(jwt_token)

            # log that adjudications are done
            mylogger.LOGGER.info("Done for adjudications...")

            # Now scheduled tasks
            timestamp_now = time.time()
            hour_now = (int(timestamp_now) // 3600) % 24

            if hour_now == 0:
                mylogger.LOGGER.info("ELO Scheduler...")
                elo_scheduler.run(jwt_token)

            if hour_now == 1:
                mylogger.LOGGER.info("Reliability Scheduler...")
                reliability_scheduler.run(jwt_token)

            if hour_now == 2:
                mylogger.LOGGER.info("Regularity Scheduler...")
                regularity_scheduler.run(jwt_token)

            # renew token every day
            if hour_now == 23:
                jwt_token = get_token()

            # go to sleep
            wait_time = time_to_wait()
            mylogger.LOGGER.info("Done for routine tasks. Back to sleep for %s secs...", wait_time)
            time.sleep(wait_time)


@API.resource('/access-logs/<lines>')
class AccessLogsRessource(flask_restful.Resource):  # type: ignore
    """ AccessLogsRessource """

    def get(self, lines: int) -> typing.Tuple[typing.List[str], int]:
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
