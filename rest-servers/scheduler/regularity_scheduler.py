#!/usr/bin/env python3


"""
File : regularity_scheduler.py

Regularity update
"""


# pylint: disable=pointless-statement, expression-not-assigned

import typing
import sys
import time
import json

import requests

import mylogger
import lowdata

SESSION = requests.Session()


def process_regularity(players_dict: typing.Dict[str, typing.Any], games_results_dict: typing.Dict[str, typing.Dict[str, typing.Any]], regularity_information: typing.List[str]) -> typing.List[typing.List[typing.Any]]:
    """ process_regularity """

    lowdata.start()

    # index is player_id
    number_games_table = {}

    # index is player_id
    started_playing_table = {}

    # index is player_id
    finished_playing_table = {}

    # index is player_id
    sequences_list_table: typing.Dict[int, typing.Any] = {}

    # index is player_id
    activity_table = {}

    # just set of players
    players_set = set()

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    # ------------------
    # 1 Parse all games
    # ------------------

    for game_name, game_data in sorted(games_results_dict.items(), key=lambda i: i[1]['start_time_stamp']):  # type: ignore

        # extract information
        game_start_time = game_data['start_time_stamp']
        game_end_time = game_data['end_time_stamp']
        game_players_dict = game_data['players']
        game_players = list(map(int, game_players_dict.keys()))

        regularity_information.append(f"{game_name=} {list(map(lambda n: num2pseudo[n], game_players))}")
        regularity_information.append("\n")

        for player_id in game_players:

            players_set.add(player_id)

            # overall start
            if player_id not in started_playing_table:
                started_playing_table[player_id] = game_start_time
            if game_start_time < started_playing_table[player_id]:
                started_playing_table[player_id] = game_start_time

            # overall end
            if player_id not in finished_playing_table:
                finished_playing_table[player_id] = game_end_time
            if game_end_time > finished_playing_table[player_id]:
                finished_playing_table[player_id] = game_end_time

            # sequences
            if player_id not in sequences_list_table:
                sequences_list_table[player_id] = []
            sequences_list_table[player_id].append([game_start_time, game_end_time])

            #  how many games played
            if player_id not in number_games_table:
                number_games_table[player_id] = 0
            number_games_table[player_id] += 1

    regularity_information.append("\n")

    lowdata.elapsed_then(regularity_information, "Games parsed")

    # ------------------
    # 2 Merge players intervals
    # ------------------

    for player_id, intervals in sequences_list_table.items():
        # sort
        intervals.sort()
        # use a stack
        intervals_stacked = []
        # insert first interval into stack
        intervals_stacked.append(intervals[0])
        for interval in intervals[1:]:
            # Check for overlapping interval,
            # if interval overlap
            if intervals_stacked[-1][0] <= interval[0] <= intervals_stacked[-1][1]:
                intervals_stacked[-1][1] = max(intervals_stacked[-1][1], interval[1])
            else:
                intervals_stacked.append(interval)
        # output
        sequences_list_table[player_id] = intervals_stacked

    lowdata.elapsed_then(regularity_information, "Interval merged")

    # ------------------
    # 3 Measure active time
    # ------------------
    for player_id, intervals in sequences_list_table.items():
        activity_table[player_id] = sum((i[1] - i[0]) for i in intervals)

    # ------------------
    # 4 Make regularity_list (returned)
    # ------------------

    ref_time = time.time()

    regularity_list = []

    for player_id in players_set:

        started_playing_days = (ref_time - started_playing_table[player_id]) // (24 * 3600)
        finished_playing_days = (ref_time - finished_playing_table[player_id]) // (24 * 3600)
        activity_days = activity_table[player_id] // (24 * 3600)
        number_games = number_games_table[player_id]

        regularity_element = [player_id, started_playing_days, finished_playing_days, activity_days, number_games]
        regularity_list.append(regularity_element)

        # to check
        regularity_information.append(f"{num2pseudo[player_id]} -> {number_games=} {started_playing_days=} {finished_playing_days=} {activity_days=}")
        regularity_information.append("\n")

    lowdata.elapsed_then(regularity_information, "list built")

    return regularity_list


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
    # perform Regularity calculation
    # ========================

    regularity_information: typing.List[str] = []
    regularity_list = process_regularity(players_dict, games_results_dict, regularity_information)

    # dump Regularity logs into a log file
    for line in regularity_information:
        print(line, file=sys.stderr)

    # ========================
    # load Regularity in database
    # ========================

    regularity_list_json = json.dumps(regularity_list)
    json_dict = {
        'regularity_list': regularity_list_json,
    }

    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/regularity_rating"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to update Regularity database")
        return

    # all done !
    mylogger.LOGGER.info("=== Hurray, Regularity was updated !")


if __name__ == '__main__':
    assert False, "Do not run this script directly"
