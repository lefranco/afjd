#!/usr/bin/env python3


"""
File : elo_scheduler.py

ELO update
"""

import typing
import json
import time
import datetime

import requests

import mylogger
import lowdata
import mapping
import scoring

VERIFY = True

ALPHA = 1.5
D_CONSTANT = 600.
DEFAULT_ELO = 1500.
MINIMUM_ELO = 1000.

K_MAX_CONSTANT = 40
K_SLOPE = 2.

FORCED_VARIANT_NAME = 'standard'

SESSION = requests.Session()


def process_elo(variant_data: mapping.Variant, players_dict: typing.Dict[str, typing.Any], games_results_dict: typing.Dict[str, typing.Dict[str, typing.Any]], games_dict: typing.Dict[str, typing.Any], elo_information: typing.List[str]) -> typing.Tuple[typing.List[typing.List[typing.Any]], str]:
    """ returns elo_raw_list, teaser_text """

    lowdata.start()

    # index is (player, role_name, classic)
    elo_table = {}

    # index is (player, role_name, classic) value is (game_name, change)
    elo_change_table = {}

    # index is (player, role_name, classic)
    number_games_table = {}

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    # rolename from number
    num2rolename = {n: variant_data.role_name_table[variant_data.roles[n]] for n in variant_data.roles if n >= 1}

    # to measure times spent
    dating_calculation_time = 0.
    scoring_calculation_time = 0.
    pseudo_calculation_time = 0.
    performance_calculation_time = 0.
    count_calculation_time = 0.
    extract_calculation_time = 0.
    expected_calculation_time = 0.
    variation_calculation_time = 0.

    effective_roles = [r for r in variant_data.roles if r >= 1]

    # should be 7
    num_players = len(effective_roles)

    # table rank -> score
    static_score_table = {r: (ALPHA ** (num_players + 1 - r) - 1) / sum(ALPHA ** (num_players + 1 - i) - 1 for i in range(1, num_players + 1)) for r in range(1, num_players + 1)}

    # ------------------
    # 1 Parse all games
    # ------------------

    for game_name, game_data in sorted(games_results_dict.items(), key=lambda i: i[1]['start_time_stamp']):  # type: ignore

        # extract information
        game_start_time = game_data['start_time_stamp']
        game_scoring_name = game_data['scoring']
        centers_number_dict = game_data['centers_number']
        game_players_dict = game_data['players']
        classic = game_data['classic']

        if len(game_players_dict) != len(effective_roles):
            elo_information.append(f"WARNING {game_name}: ignored because missing player(s) !!!!")
            continue

        # convert time
        before = time.time()
        if VERIFY:
            time_creation = datetime.datetime.fromtimestamp(game_start_time)
            time_creation_str = time_creation.strftime("%Y-%m-%d %H:%M:%S %f")
        after = time.time()
        dating_calculation_time += (after - before)

        # calculate scoring
        before = time.time()
        raw_ratings = {num2rolename[n]: centers_number_dict[str(n)] if str(n) in centers_number_dict else 0 for n in variant_data.roles if n >= 1}
        ratings = dict(sorted(raw_ratings.items(), key=lambda i: i[1], reverse=True))  # type: ignore
        solo_threshold = variant_data.number_centers() // 2

        # use clone of unit in front end (scoring)
        # no typing in this code from front end
        score_table = scoring.scoring(game_scoring_name, solo_threshold, ratings)  # type: ignore

        # check
        if not any(map(lambda s: s > 0, score_table.values())):
            elo_information.append(f"WARNING {game_name}: ignored because no positive score !!!!")
            continue

        relevant_score_table = {r: s for r, s in score_table.items() if s > 0}
        after = time.time()
        scoring_calculation_time += (after - before)

        # calculate performance
        before = time.time()
        # get everyones's rank
        ranking_table = {r: len([ss for ss in relevant_score_table.values() if ss > s]) + 1 for r, s in relevant_score_table.items()}
        # get everyones's sharing
        shared_table = {r: len([ss for ss in relevant_score_table.values() if ss == s]) for r, s in relevant_score_table.items()}

        # get performance from rank and sharing
        # for scorers
        raw_performed_table = {r: sum(static_score_table[ranking_table[r] + i] for i in range(shared_table[r])) / shared_table[r] for r in relevant_score_table}
        performed_table = {r: raw_performed_table[r] / sum(raw_performed_table.values()) for r in raw_performed_table}
        # for non scorers
        performed_table.update({r: 0 for r, s in score_table.items() if s <= 0})

        after = time.time()
        performance_calculation_time += (after - before)

        # get pseudos of players
        before = time.time()
        pseudo_table = {num2rolename[rn]: num2pseudo[int(pn)] for pn, rn in game_players_dict.items()}
        after = time.time()
        pseudo_calculation_time += (after - before)

        # optimization
        memo = {}
        for num in effective_roles:
            role_name = num2rolename[num]
            player = pseudo_table[role_name]
            memo[num] = (role_name, player)

        # count games
        before = time.time()
        for (role_name, player) in memo.values():
            if (player, role_name, classic) not in number_games_table:
                number_games_table[(player, role_name, classic)] = 0
            number_games_table[(player, role_name, classic)] += 1
        after = time.time()
        count_calculation_time += (after - before)

        # extract ELO of players
        before = time.time()
        rating_table = {}
        for (role_name, player) in memo.values():
            if (player, role_name, classic) not in elo_table:
                elo_table[(player, role_name, classic)] = DEFAULT_ELO
            rating_table[role_name] = elo_table[(player, role_name, classic)]
        after = time.time()
        extract_calculation_time += (after - before)

        # calculate expected performance
        # here is where most time is spent
        before = time.time()
        divider = num_players * (num_players - 1) / 2.
        expected_table = {}
        for (role_name, _) in memo.values():
            sigma = 0.
            for (role_name2, _) in memo.values():
                if role_name2 != role_name:
                    sigma += 1 / (1 + (10 ** ((rating_table[role_name2] - rating_table[role_name]) / D_CONSTANT)))
            sigma /= divider
            expected_table[role_name] = sigma
        after = time.time()
        expected_calculation_time += (after - before)

        if VERIFY:
            elo_information.append(f"{time_creation_str=} {game_name=} {classic=}")
            elo_information.append(f"{game_scoring_name=}")
            elo_information.append(f"{solo_threshold=}")
            elo_information.append(f"{ratings=}")
            elo_information.append(f"{pseudo_table=}")
            elo_information.append(f"{score_table=}")
            elo_information.append(f"{relevant_score_table=}")
            elo_information.append(f"{ranking_table=}")
            elo_information.append(f"{expected_table=}")
            elo_information.append(f"{performed_table=}")

        # elo variation

        if VERIFY:
            elo_information.append("Effect :")

        # calculate effect on ELO
        before = time.time()
        loosers = [r for r in score_table if r == min(score_table.values())]
        winners = [r for r in score_table if r == max(score_table.values())]
        for (role_name, player) in memo.values():

            # K parameter must decrease other number of games
            k_player = max(K_MAX_CONSTANT // 2, K_MAX_CONSTANT - number_games_table[(player, role_name, classic)] / K_SLOPE)

            delta = k_player * (num_players * (num_players - 1) / 2) * (performed_table[role_name] - expected_table[role_name])

            # just a little check
            if role_name in loosers and delta > 0:
                elo_information.append(f"WARNING {game_name}: {player} as {role_name} looses but gains points !!!!")
            if role_name in winners and delta < 0:
                elo_information.append(f"WARNING {game_name}: {player} as {role_name} wins but looses points !!!!")

            if VERIFY:
                prev_elo = elo_table[(player, role_name, classic)]

            elo_table[(player, role_name, classic)] += delta
            elo_change_table[(player, role_name, classic)] = (game_name, delta)

            if VERIFY:
                new_elo = elo_table[(player, role_name, classic)]
                elo_information.append(f"{player}({role_name}) -> delta = {delta} so elo changes from {prev_elo} to {new_elo}")

            if elo_table[(player, role_name, classic)] < MINIMUM_ELO:
                elo_table[(player, role_name, classic)] = MINIMUM_ELO
                elo_information.append(f"INFORMATION {game_name}: {player}({role_name}) would have less than {MINIMUM_ELO} so forced to this value")

        after = time.time()
        variation_calculation_time += (after - before)

        if VERIFY:
            elo_information.append("-------------------")

    elo_information.append(f"Number of games processed : {len(games_results_dict)}")
    elo_information.append(f"Dating calculation time : {dating_calculation_time}")
    elo_information.append(f"Scoring calculation time : {scoring_calculation_time}")
    elo_information.append(f"Pseudo calculation time : {pseudo_calculation_time}")
    elo_information.append(f"Performance calculation time : {performance_calculation_time}")
    elo_information.append(f"Count calculation time : {count_calculation_time}")
    elo_information.append(f"Extract calculation time : {extract_calculation_time}")
    elo_information.append(f"Expected calculation time : {expected_calculation_time}")
    elo_information.append(f"Variation calculation time : {variation_calculation_time}")

    lowdata.elapsed_then(elo_information, "Parsing games time")

    # ------------------
    # 2 Make recap
    # ------------------

    for classic in (True, False):

        elo_information.append("-------------------")
        elo_information.append("-------------------")
        elo_information.append(f"RATINGS FOR {'CLASSIC' if classic else 'BLITZ'} MODE")
        elo_information.append("-------------------")

        # ------------
        # global recap
        # ------------

        # sum up elos per role
        elo_recap_table = {}
        for player in players_dict:
            for num in effective_roles:
                role_name = num2rolename[num]
                if (player, role_name, classic) in elo_table:
                    if player not in elo_recap_table:
                        elo_recap_table[player] = {'sum': 0., 'number': 0.}
                    elo_recap_table[player]['sum'] += elo_table[(player, role_name, classic)]
                    elo_recap_table[player]['number'] += 1

        # fills DEFAULT_ELO for roles not played
        final_raw_elo_table = {k: (v['sum'] + (num_players - v['number']) * DEFAULT_ELO) / num_players for k, v in elo_recap_table.items()}

        # sort table
        final_elo_table = dict(sorted(final_raw_elo_table.items(), key=lambda t: t[1], reverse=True))

        # display
        elo_information.append("-------------------")
        for rank, (player, elo) in enumerate(final_elo_table.items()):

            # make detail for player
            player_detail = {num2rolename[num]: elo_table[(player, num2rolename[num], classic)] for num in variant_data.roles if num >= 1 and (player, num2rolename[num], classic) in elo_table}

            # display rankings
            elo_information.append(f"{rank + 1} {player} -> {elo} ({player_detail})")

        if VERIFY:

            # --------------
            # per role recap
            # --------------

            for num in effective_roles:

                # display role name
                elo_information.append("-------------------")
                role_name = num2rolename[num]
                elo_information.append(role_name)

                # make table
                final_raw_role_elo_table = {p: elo_table[(p, rn, c)] for (p, rn, c) in elo_table if rn == role_name and c == classic}

                # sort table
                final_role_elo_table = dict(sorted(final_raw_role_elo_table.items(), key=lambda t: t[1], reverse=True))

                # display rankings
                for rank, (player, elo) in enumerate(final_role_elo_table.items()):
                    sample_size = number_games_table[(player, role_name, classic)]
                    game_name, last_change = elo_change_table[(player, role_name, classic)]
                    elo_information.append(f"{rank + 1} {player} -> {elo} (last change {last_change:+f} in game {game_name} & played {sample_size} times)")

        lowdata.elapsed_then(elo_information, f"Mode {'CLASSIC' if classic else 'BLITZ'} time")

    lowdata.elapsed_then(elo_information, "Recap made")

    # ------------------
    # 3 Make elo_raw_list (returned)
    # ------------------

    rolename2num = {v: k for k, v in num2rolename.items()}
    gamename2gameid = {v['name']: int(k) for k, v in games_dict.items()}

    elo_raw_list = []

    for (player, role_name, classic) in elo_table:

        # extract
        elo_value = elo_table[(player, role_name, classic)]
        (game_name, change) = elo_change_table[(player, role_name, classic)]
        number_games = number_games_table[(player, role_name, classic)]

        # convert

        # elo is integer
        elo_value_int = round(elo_value)

        # player is the id
        player_id = players_dict[player]

        # role is the id
        role_id = rolename2num[role_name]

        # game is the id
        game_id = gamename2gameid[game_name]

        # change is integer
        change_int = round(change)

        elo_raw_element = [classic, role_id, player_id, elo_value_int, change_int, game_id, number_games]
        elo_raw_list.append(elo_raw_element)

    # table game -> start time (for sorting)
    gameid2starttime = {gamename2gameid[k]: v['start_time_stamp'] for k, v in games_results_dict.items()}

    # sort according to game start
    elo_raw_list_sorted = sorted(elo_raw_list, key=lambda e: gameid2starttime[e[5]])  # type: ignore

    # make teaser (just an abstract)
    teaser_text = ""
    for classic1 in (True, False):
        for role_id1 in effective_roles:
            elo_sub_raw_list = [e for e in elo_raw_list if e[0] == classic1 and e[1] == role_id1]
            best_one = sorted(elo_sub_raw_list, key=lambda e: e[3], reverse=True)[0]  # type: ignore
            teaser_text += f"{num2pseudo[best_one[2]]} {best_one[3]} {num2rolename[best_one[1]]} {'classique' if best_one[0] else 'blitz'}\n"

    # separator
    teaser_text += "\n"

    # date to teaser
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp)
    date_now_gmt_str = date_now_gmt.strftime("%Y-%m-%d %H:%M:%S %f GMT")
    teaser_text += f"{date_now_gmt_str}"

    lowdata.elapsed_then(elo_information, "list built")

    return elo_raw_list_sorted, teaser_text


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
    # get games list
    # ========================

    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/games"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get games list")
        return
    games_dict = req_result.json()

    # ========================
    # get variant data
    # ========================

    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/variants/{FORCED_VARIANT_NAME}"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get variant data")
        return
    variant_content_loaded = req_result.json()

    # selected interface (forced)
    interface_inforced = lowdata.get_inforced_interface_from_variant(FORCED_VARIANT_NAME)

    # from interface chose get display parameters
    parameters_read = lowdata.read_parameters(FORCED_VARIANT_NAME, interface_inforced)

    # build variant data
    variant_data = mapping.Variant(FORCED_VARIANT_NAME, variant_content_loaded, parameters_read)

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
    # perform ELO calculation
    # ========================

    elo_information: typing.List[str] = []
    elo_raw_list, teaser_text = process_elo(variant_data, players_dict, games_results_dict, games_dict, elo_information)

    # dump ELO logs into a log file
    with open("./logdir/ELO.log", "w", encoding='utf-8') as file_ptr:
        file_ptr.write('\n'.join(elo_information))

    # ========================
    # load ELO in database
    # ========================

    elo_raw_list_json = json.dumps(elo_raw_list)
    json_dict = {
        'elo_list': elo_raw_list_json,
        'teaser': teaser_text
    }

    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/elo_rating"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, data=json_dict)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to update ELO database")
        return

    # all done !
    mylogger.LOGGER.info("=== Hurray, ELO was updated !")


if __name__ == '__main__':
    assert False, "Do not run this script directly"
