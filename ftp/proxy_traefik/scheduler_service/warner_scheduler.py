#!/usr/bin/env python3


"""
File : warner_scheduler.py

Warn people deadline is soon
"""

import typing
import time

import requests

import mylogger
import lowdata


# time to add to make sure to be after
EPSILON_SEC = 5

# to take it easy on server
INTER_WARNING_TIME_SEC = 2

SESSION = requests.Session()


def run(jwt_token: str) -> None:
    """ warner_scheduler """

    # ========================
    # warn people they did not enter orders and deadline is soon
    # ========================

    # time of warning
    now = time.time()

    # get all games
    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games-in-state/1/1"  # ongoing
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

        # not between deadline -24h and deadline  - to do just one warning
        if not game_dict['deadline'] - 24 * 60 * 60 <= now + EPSILON_SEC <= game_dict['deadline']:
            continue

        # fast game
        if game_dict['fast']:
            continue

        # exposition game
        if game_dict['exposition']:
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

        # game end voted
        if game_full_dict['end_voted']:
            mylogger.LOGGER.info("Ignoring game '%s' that has voted to end !", game_name)
            continue

        # phase must last at least 24 hours
        # what is the season next to play ?
        if game_full_dict['current_advancement'] % 5 in [0, 2]:
            if game_full_dict['speed_moves'] <= 24:
                mylogger.LOGGER.info("Ignoring game '%s' playing moves with duration '%d' !", game_name, game_full_dict['speed_moves'])
                continue
        elif game_full_dict['current_advancement'] % 5 in [1, 3]:
            if game_full_dict['speed_retreats'] <= 24:
                mylogger.LOGGER.info("Ignoring game '%s' playing retreats with duration '%d' !", game_name, game_full_dict['speed_retreats'])
                continue
        else:
            if game_full_dict['speed_adjustments'] <= 24:
                mylogger.LOGGER.info("Ignoring game '%s' playing adjustments with duration '%d' !", game_name, game_full_dict['speed_adjustments'])
                continue

        mylogger.LOGGER.info("Considering game %s", game_name)

        json_dict: typing.Dict[str, typing.Any] = {}

        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/warn-deadline-players-game/{game_id}"
        req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, json=json_dict)
        if req_result.status_code != 200:
            if 'msg' in req_result.json():
                mylogger.LOGGER.error(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to perform Warning")
            return

        # easy on the server !
        time.sleep(INTER_WARNING_TIME_SEC)

    # all done !
    mylogger.LOGGER.info("=== Hurray, Warning was performed !")


if __name__ == '__main__':
    assert False, "Do not run this script directly"
