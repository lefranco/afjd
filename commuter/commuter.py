#!/usr/bin/env python3

""" commuter """

# pylint: disable=pointless-statement, expression-not-assigned

import json
import time
import datetime
import typing
import urllib.request

import requests

import mapping

import mylogger
import lowdata

SESSION = requests.Session()

COMMUTER_ACCOUNT = "TheCommuter"
COMMUTER_PASSWORD = "PythonRules78470!!!"

PERIOD_MINUTES = 30

# simplest is to hard code displays of variants here
INTERFACE_TABLE = {
    'standard': ['diplomania', 'diplomania_daltoniens', 'hasbro']
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


def main() -> None:
    """ main """

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
        print("ERROR: Failed to get token")
        return
    req_result = json.loads(req_result.text)
    jwt_token = req_result['AccessToken']  # type: ignore

    # wait next hour+15 ou hour+45
    timestamp_now = time.time()
    second_position = timestamp_now % (60 * 60)
    if second_position < 15 * 60:
        wait_time = 15 * 60 - second_position
    elif second_position < 45 * 60:
        wait_time = 45 * 60 - second_position
    else:
        wait_time = 15 * 60 + 60 * 60 - second_position

    now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
    now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S')

    print()
    print(f"Now {now_date_desc}. Waiting {wait_time//60}mn and {wait_time%60}sec...")
    print()

    time.sleep(wait_time)

    while True:

        timestamp_now = time.time()
        now_date = datetime.datetime.fromtimestamp(timestamp_now, datetime.timezone.utc)
        now_date_desc = now_date.strftime('%Y-%m-%d %H:%M:%S')

        print()
        print(f"At {now_date_desc} trying all games...")
        print()

        # try to commute all games
        time_before = time.time()
        check_all_games(jwt_token)
        time_after = time.time()
        duration = time_after - time_before

        # go to sleep
        print()
        print(f"Took {round(duration)} secs. Going now to sleep...")
        print()
        sleep_time = PERIOD_MINUTES * 60 - duration
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
