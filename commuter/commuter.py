#!/usr/bin/env python3

""" commuter """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time
import datetime
import typing
import argparse
import urllib.request

import requests

import mapping

import mylogger
import lowdata

SESSION = requests.Session()

# read from parameter file
COMMUTER_ACCOUNT = ""
COMMUTER_PASSWORD = ""


# tilme to add to make sure to be after
EPSILON_SEC = 5

# simplest is to hard code displays of variants here
INTERFACE_TABLE = {
    'standard': ['diplomania', 'diplomania_daltoniens', 'hasbro'],
    'grandeguerre': ['diplomania'],
    'brouillard': ['diplomania'],
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


def get_server_time() -> typing.Tuple[bool, float]:
    """ get_server_time """

    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/news"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        return False, -1
    news_content_loaded = req_result.json()
    server_time = news_content_loaded['server_time']

    return True, server_time


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
            print(req_result.json()['msg'])
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
            print(req_result.json()['msg'])
        print("ERROR: Failed to get games")
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
                print(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to get game data")
            continue

        game_dict = req_result.json()

        # easy on the server !
        time.sleep(2)

        print(f"Trying game {game_name}...", end='')

        variant_name = game_dict['variant']
        success = commute_game(jwt_token, game_id, variant_name, game_name)

        if success:
            print("commuted !", end='')
        print()


def time_to_wait() -> float:
    """ time_to_wait """

    # get server time
    status, server_time = get_server_time()
    if not status:
        print("ERROR: Failed to get server time")
        return -1.

    # theorical wait_time
    timestamp_now = time.time()
    next_hour_time = (round(timestamp_now) // (60 * 60)) * (60 * 60) + (60 * 60)
    wait_time = next_hour_time - timestamp_now

    #  print(f"now {timestamp_now=}")
    #  print(f"now {next_hour_time=}")
    #  print(f"raw {wait_time=}")

    # delta is difference between out time and server time
    delta = timestamp_now - server_time
    #  print(f"delta here - server = {delta=}")

    # ajust wait time because server time is from our time
    wait_time += delta

    #  print(f"adjusted {wait_time=}")

    # make sure we are after
    wait_time += EPSILON_SEC

    #  print(f"final {wait_time=}")

    return wait_time


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', required=False, help='force to do now', action='store_true')
    args = parser.parse_args()

    mylogger.start_logger(__name__)
    lowdata.load_servers_config()
    load_credentials_config()

    # get my IP address
    try:
        with urllib.request.urlopen('https://ident.me') as response:
            external_ip = response.read().decode('utf8')
    except:  # noqa: E722 pylint: disable=bare-except
        external_ip = 'unknown'

    # get a token
    pseudo = COMMUTER_ACCOUNT
    password = COMMUTER_PASSWORD

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
            print(req_result.json()['msg'])
        print("ERROR: Failed to get token")
        return
    req_result = json.loads(req_result.text)
    jwt_token = req_result['AccessToken']  # type: ignore

    timestamp_now = time.time()
    now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
    now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S GMT')

    print()
    print(f"Now {now_date_desc}. Waiting...")
    print()

    # if force we go directly
    if args.force:
        print("Forced. Do no wait...")
    else:
        wait_time = time_to_wait()
        if wait_time < 0:
            print("ERROR: Failed to get wait time")
            return
        time.sleep(wait_time)

    while True:

        # get local time for display
        timestamp_now = time.time()
        now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
        now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S GMT')

        # get server time for display
        status, server_time = get_server_time()
        if not status:
            print("ERROR: Failed to get server time")
            return
        server_date = datetime.datetime.fromtimestamp(server_time, datetime.timezone.utc)
        server_date_desc = server_date.strftime('%Y-%m-%d %H:%M:%S GMT')

        print()
        print(f"At {now_date_desc} local ({server_date_desc} server) trying all games...")
        print()

        # try to commute all games
        check_all_games(jwt_token)

        # get local time for display again
        timestamp_now = time.time()
        now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
        now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S GMT')

        # go to sleep
        print()
        print(f"Done. Now {now_date_desc}. Back to sleep...")
        print()

        wait_time = time_to_wait()
        if wait_time < 0:
            print("ERROR: Failed to get wait time")
            return
        time.sleep(wait_time)


if __name__ == '__main__':
    main()
