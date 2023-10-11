#!/usr/bin/env python3


"""
File : server.py

The server
"""

import typing

import json
import datetime
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
import populate
import lowdata
import database
import mapping


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

# simplest is to hard code displays of variants here
INTERFACE_TABLE = {
    'standard': ['diplomania', 'diplomania_daltoniens', 'hasbro'],
    'grandeguerre': ['diplomania'],
    'grandeguerreexpansionniste': ['diplomania'],
    'hundred': ['diplomania'],
    'moderne': ['diplomania'],
    'egeemonie': ['diplomania'],
}


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


def get_inforced_interface_from_variant(variant: str) -> str:
    """ get_inforced_interface_from_variant """

    # takes the first
    return INTERFACE_TABLE[variant][0]


def read_parameters(variant_name_loaded: str, interface_chosen: str) -> typing.Any:
    """ read_parameters """

    parameters_file_name = f"./variants/{variant_name_loaded}/{interface_chosen}/parameters.json"
    with open(parameters_file_name, "r", encoding="utf-8") as read_file2:
        parameters_read = json.load(read_file2)

    return parameters_read


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
    interface_inforced = get_inforced_interface_from_variant(variant_name_loaded)

    # from interface chose get display parameters
    parameters_read = read_parameters(variant_name_loaded, interface_inforced)

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

    mylogger.LOGGER.info("Game %s was commuted !", game_name)
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

        mylogger.LOGGER.info(f"Trying game {game_name}...")

        success = commute_game(jwt_token, game_id, variant_name, game_name)

        if success:
            mylogger.LOGGER.info("+++ commuted ! +++")

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

    with APP.app_context():

        # get a token
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
            return
        req_result = json.loads(req_result.text)
        jwt_token = req_result['AccessToken']  # type: ignore

        timestamp_now = time.time()
        now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
        now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S GMT')

        mylogger.LOGGER.info(f"Now {now_date_desc}. Waiting...")

        ####  wait_time = time_to_wait()
        ####  time.sleep(wait_time)

        while True:

            # get local time for display
            timestamp_now = time.time()
            now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
            now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S GMT')

            mylogger.LOGGER.info(f"At {now_date_desc} trying all games...")
            # TODO : insert into database

            # try to commute all games
            check_all_games(jwt_token)

            # get local time for display again
            timestamp_now = time.time()
            now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
            now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S GMT')

            # go to sleep
            mylogger.LOGGER.info(f"Done. Now {now_date_desc}...")

            # TODO : insert here all scheduled tasks
            ####  time.sleep(10)

            # get local time for display again
            timestamp_now = time.time()
            now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
            now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S GMT')

            # go to sleep
            mylogger.LOGGER.info(f"Done. Now {now_date_desc}. Back to sleep...")

            ####  wait_time = time_to_wait()
            ####  time.sleep(wait_time)

            break  ##### TODO REMOVE


@API.resource('/access-logs')
class AccessLogsRessource(flask_restful.Resource):  # type: ignore
    """ AccessLogsRessource """

    def post(self) -> typing.Tuple[typing.Dict[str, typing.Any], int]:
        """
        Simply return logs content
        EXPOSED
        """

        mylogger.LOGGER.info("/access-logs - POST - accessing logs")

        # TODO : extract from database

        data = {'msg': 'NOT IMPLEMENTED'}
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

    # emergency
    #if not database.db_present():

        #mylogger.LOGGER.info("Emergency populate procedure")

        #sql_executor = database.SqlExecutor()
        #populate.populate(sql_executor)
        #sql_executor.commit()
        #del sql_executor

    # may specify host and port here
    port = lowdata.SERVER_CONFIG['SCHEDULER']['PORT']

    # use separate thread to do stuff
    acting_thread = threading.Thread(target=acting_threaded_procedure, daemon=True)
    acting_thread.start()

    if args.debug:
        APP.run(debug=True, port=port)
    else:
        waitress.serve(APP, port=port)


if __name__ == '__main__':
    main()
