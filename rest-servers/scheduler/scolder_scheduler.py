#!/usr/bin/env python3


"""
File : scolder_scheduler.py

Tell people they are late
"""

import typing
import time

import requests

import mylogger
import lowdata


# time to add to make sure to be after
EPSILON_SEC = 5

# to take it easy on server
INTER_SCOLDING_TIME_SEC = 2

SESSION = requests.Session()


def run(jwt_token: str) -> None:
    """ scolder_scheduler """

    # ========================
    # tell people they are late
    # ========================

    # time of scolding
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

        # not between deadline and deadline + 24h  - to do just one scolding
        if not game_dict['deadline'] <= now + EPSILON_SEC <= game_dict['deadline'] + 24 * 60 * 60:
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

        mylogger.LOGGER.info(f"Considering game {game_name}")

        json_dict: typing.Dict[str, typing.Any] = {}

        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/scold-late-players-game/{game_id}"
        req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
        if req_result.status_code != 200:
            if 'msg' in req_result.json():
                mylogger.LOGGER.error(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to perform Scolding")
            return

        # easy on the server !
        time.sleep(INTER_SCOLDING_TIME_SEC)

    # all done !
    mylogger.LOGGER.info("=== Hurray, Scolding was performed !")


if __name__ == '__main__':
    assert False, "Do not run this script directly"
