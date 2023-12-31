#!/usr/bin/env python3


"""
File : reliability_scheduler.py

Reliability update
"""


import typing
import sys
import json

import requests

import mylogger
import lowdata


SESSION = requests.Session()


def process_reliability(players_dict: typing.Dict[str, typing.Any], games_results_dict: typing.Dict[str, typing.Dict[str, typing.Any]], reliability_information: typing.List[str]) -> typing.List[typing.List[typing.Any]]:
    """ process_reliability """

    lowdata.start()

    # index is player_id
    number_delays_table = {}

    # index is player_id
    number_dropouts_table = {}

    # index is player_id
    number_advancements_table = {}
    # just set of players

    players_set = set()

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    # ------------------
    # 1 Parse all games
    # ------------------

    for game_name, game_data in sorted(games_results_dict.items(), key=lambda i: i[1]['start_time_stamp']):  # type: ignore

        # extract information
        number_advancement_played = game_data['number_advancement_played']
        delays_number_dict = game_data['delays_number']
        dropouts_number_dict = game_data['dropouts_number']
        game_players_dict = game_data['players']
        game_players = set(map(int, game_players_dict.keys()))

        # display stuff

        reliability_information.append(f"{game_name=} {list(map(lambda n: num2pseudo[n], game_players))}")
        reliability_information.append("\n")

        reliability_information.append("delays from this game: ")
        for key, value in delays_number_dict.items():
            if int(key) in num2pseudo:
                player_pseudo = num2pseudo[int(key)]
                reliability_information.append(f"{player_pseudo} ")
            else:
                reliability_information.append(f"({key}???) ")
            reliability_information.append(f"-> {value} ")
            if int(key) not in game_players:
                reliability_information.append("(outside) ")
        reliability_information.append("\n")

        reliability_information.append("dropouts from this game: ")
        for key, value in dropouts_number_dict.items():
            if int(key) in num2pseudo:
                player_pseudo = num2pseudo[int(key)]
                reliability_information.append(f"{player_pseudo} ")
            else:
                reliability_information.append(f"({key}???) ")
            reliability_information.append(f"-> {value} ")
            if int(key) not in game_players:
                reliability_information.append("(outside) ")
        reliability_information.append("\n")

        # update over all player_set
        extended_game_players = game_players.copy()
        late_players = set(map(int, delays_number_dict.keys()))
        extended_game_players.update(late_players)
        quitter_players = set(map(int, dropouts_number_dict.keys()))
        extended_game_players.update(quitter_players)
        players_set.update(extended_game_players)

        for player_id in extended_game_players:

            #  how many delays
            if player_id not in number_delays_table:
                number_delays_table[player_id] = 0
            if str(player_id) in delays_number_dict:
                number_delays = delays_number_dict[str(player_id)]
                number_delays_table[player_id] += number_delays

            #  how many dropouts
            if player_id not in number_dropouts_table:
                number_dropouts_table[player_id] = 0
            if str(player_id) in dropouts_number_dict:
                number_dropouts = dropouts_number_dict[str(player_id)]
                number_dropouts_table[player_id] += number_dropouts

            #  how many advancements played
            if player_id not in number_advancements_table:
                number_advancements_table[player_id] = 0
            if player_id in game_players:
                number_advancements_table[player_id] += number_advancement_played

    lowdata.elapsed_then(reliability_information, "Games parsed")

    # ------------------
    # 2 Make reliability_list (returned)
    # ------------------

    reliability_list = []

    for player_id in players_set:

        number_delays = number_delays_table[player_id]
        number_dropouts = number_dropouts_table[player_id]
        number_advancements = number_advancements_table[player_id]

        reliability_element = [player_id, number_delays, number_dropouts, number_advancements]
        reliability_list.append(reliability_element)

        # to check
        reliability_information.append(f"{num2pseudo[player_id]} -> {number_delays=} {number_dropouts=} {number_advancements=} ")
        reliability_information.append("\n")

    lowdata.elapsed_then(reliability_information, "list built")

    return reliability_list


def run(jwt_token: str) -> None:
    """ elo_scheduler """

    # ========================
    # get players list
    # ========================

    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/players-short"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get players list")
        return
    res_dict = req_result.json()
    players_dict = {v['pseudo']: int(k) for k, v in res_dict.items()}

    # ========================
    # extract game results data
    # ========================

    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/extract_elo_data"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get extract game results data")
        return
    res_dict = req_result.json()
    games_results_dict = res_dict['games_dict']

    # ========================
    # perform Reliability calculation
    # ========================

    reliability_information: typing.List[str] = []
    reliability_list = process_reliability(players_dict, games_results_dict, reliability_information)

    # dump Reliability logs into a log file
    for line in reliability_list:
        print(line, file=sys.stderr)

    # ========================
    # load Reliability in database
    # ========================

    reliability_list_json = json.dumps(reliability_list)
    json_dict = {
        'reliability_list': reliability_list_json,
    }

    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/reliability_rating"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to update Reliability database")
        return

    # all done !
    mylogger.LOGGER.info("=== Hurray, Reliability was updated !")


if __name__ == '__main__':
    assert False, "Do not run this script directly"
