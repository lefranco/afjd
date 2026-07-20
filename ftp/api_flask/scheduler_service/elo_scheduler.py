#!/usr/bin/env python3


"""
File : elo_scheduler.py

ELO update (take care of replacements)
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


# How many in teaser rating
NUMBER_ELO_TEASER = 7

SESSION = requests.Session()


def process_elo_variant(variant_data: mapping.Variant, players_dict: typing.Dict[str, typing.Any], games_results_dict: typing.Dict[str, typing.Dict[str, typing.Any]], games_dict: typing.Dict[str, typing.Any], elo_information: typing.List[str], commuter_account: str) -> typing.Tuple[typing.List[typing.List[typing.Any]], str]:
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

    effective_roles = [r for r in variant_data.roles if r >= 1]

    num_players = len(effective_roles)

    # table rank -> score
    static_score_table = {r: (ALPHA ** (num_players + 1 - r) - 1) / sum(ALPHA ** (num_players + 1 - i) - 1 for i in range(1, num_players + 1)) for r in range(1, num_players + 1)}

    # put a title in logs
    elo_information.append("===============")
    elo_information.append(f"Variant is {variant_data.name}")
    elo_information.append("===============")
    elo_information.append("")

    # ------------------
    # 1 Parse all games
    # ------------------

    for game_name, game_data in sorted(games_results_dict.items(), key=lambda i: i[1]['start_time_stamp']):

        # extract information
        game_start_time = game_data['start_time_stamp']
        game_scoring_name = game_data['scoring']
        centers_number_dict = game_data['centers_number']
        game_players_dict = game_data['players']
        classic = game_data['classic']
        quitting_dict = game_data['quitting_dict']

        # calculate scoring
        raw_ratings = {num2rolename[n]: centers_number_dict[str(n)] if str(n) in centers_number_dict else 0 for n in variant_data.roles if n >= 1}
        ratings = dict(sorted(raw_ratings.items(), key=lambda i: i[1], reverse=True))

        # use clone of unit in front end (scoring)
        # no typing in this code from front end
        centers_variant = variant_data.number_centers()
        extra_requirement_solo = variant_data.extra_requirement_solo
        solo_threshold = centers_variant // 2 + extra_requirement_solo
        score_table = scoring.scoring(game_scoring_name, centers_variant, solo_threshold, ratings)  # type: ignore

        # check
        if not any(map(lambda s: s > 0, score_table.values())):
            elo_information.append(f"WARNING {game_name}: ignored because no positive score !!!!")
            if VERIFY:
                elo_information.append("-------------------")
            continue

        relevant_score_table = {r: s for r, s in score_table.items() if s > 0}

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

        # get pseudos of players
        pseudo_table = {num2rolename[rn]: num2pseudo[int(pn)] for pn, rn in game_players_dict.items()}

        # optimization
        memo = {}
        for num in effective_roles:
            role_name = num2rolename[num]
            # put commuter where player is missing
            if role_name not in pseudo_table:
                pseudo_table[role_name] = commuter_account
            player = pseudo_table[role_name]
            memo[num] = (role_name, player)

        # replacers
        replacers = [num2rolename[num] for num in quitting_dict.values()]

        # count games
        for (role_name, player) in memo.values():
            if (player, role_name, classic) not in number_games_table:
                number_games_table[(player, role_name, classic)] = 0
            number_games_table[(player, role_name, classic)] += 1

        # extract ELO of players
        rating_table = {}
        for (role_name, player) in memo.values():
            if (player, role_name, classic) not in elo_table:
                elo_table[(player, role_name, classic)] = DEFAULT_ELO
            rating_table[role_name] = elo_table[(player, role_name, classic)]

        # calculate expected performance
        # here is where most time is spent
        divider = num_players * (num_players - 1) / 2.
        expected_table = {}
        for (role_name, _) in memo.values():
            sigma = 0.
            for (role_name2, _) in memo.values():
                if role_name2 != role_name:
                    sigma += 1 / (1 + (10 ** ((rating_table[role_name2] - rating_table[role_name]) / D_CONSTANT)))
            sigma /= divider
            expected_table[role_name] = sigma

        if VERIFY:
            time_creation = datetime.datetime.fromtimestamp(game_start_time)
            time_creation_str = time_creation.strftime("%Y-%m-%d %H:%M:%S %f")
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

            if role_name in replacers and delta < 0:

                # we have a quitter (or several)
                for quitter_id, quitter_role_num in quitting_dict.items():
                    quitter_role_name = num2rolename[quitter_role_num]
                    if quitter_role_name == role_name:
                        quitter_player = num2pseudo[int(quitter_id)]

                        # log that we have a quitter
                        elo_information.append(f"INFO {game_name}: {player} as {role_name} is replacer so {delta} passes to {quitter_player}")
                        if quitter_player == player:
                            elo_information.append("WARNING : quitter and player are the same !")

                        # insert quitter in elo_table
                        if (quitter_player, role_name, classic) not in elo_table:
                            elo_table[(quitter_player, role_name, classic)] = DEFAULT_ELO
                        elo_table[(quitter_player, role_name, classic)] += delta

                        # insert quitter in number_games_table
                        if (quitter_player, role_name, classic) not in number_games_table:
                            number_games_table[(quitter_player, role_name, classic)] = 0
                        number_games_table[(quitter_player, role_name, classic)] += 1

                        # insert quitter in elo_change_table
                        elo_change_table[(quitter_player, role_name, classic)] = (game_name, delta)

            elif player != commuter_account:
                elo_table[(player, role_name, classic)] += delta

            elo_change_table[(player, role_name, classic)] = (game_name, delta)

            if VERIFY:
                new_elo = elo_table[(player, role_name, classic)]
                elo_information.append(f"{player}({role_name}) -> delta = {delta} so elo changes from {prev_elo} to {new_elo}")

            if elo_table[(player, role_name, classic)] < MINIMUM_ELO:
                elo_table[(player, role_name, classic)] = MINIMUM_ELO
                elo_information.append(f"INFORMATION {game_name}: {player}({role_name}) would have less than {MINIMUM_ELO} so forced to this value")

        if VERIFY:
            elo_information.append("-------------------")

    elo_information.append(f"Number of games processed : {len(games_results_dict)}")

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

    # agregate to have actual ELO values

    elo_global_table = {}
    for (player, role_name, classic) in elo_table:

        elo_value = elo_table[(player, role_name, classic)]

        # player is the id
        player_id = players_dict[player]

        if (classic, player_id) not in elo_global_table:
            elo_global_table[(classic, player_id)] = 0.
        elo_global_table[(classic, player_id)] += elo_value

    elo_raw_list2 = []
    for (classic, player_id), elo_value in elo_global_table.items():
        # elo is integer
        elo_value_int = round(elo_value)
        elo_raw_element = [classic, player_id, elo_value_int]
        elo_raw_list2.append(elo_raw_element)

    # table game -> start time (for sorting)
    gameid2starttime = {gamename2gameid[k]: v['start_time_stamp'] for k, v in games_results_dict.items()}

    # sort according to game start
    elo_raw_list_sorted = sorted(elo_raw_list, key=lambda e: gameid2starttime[e[5]])

    # make teasers (just an abstract)
    teaser_text_variant = ""

    # global
    for classic1 in (False, True):
        elo_sub_raw_list2 = [e for e in elo_raw_list2 if e[0] == classic1]
        if elo_sub_raw_list2:
            best_ones = sorted(elo_sub_raw_list2, key=lambda e: e[2], reverse=True)[0: NUMBER_ELO_TEASER]
            rank = 1
            for best_one in best_ones:
                teaser_text_variant += f"global {'classique' if best_one[0] else 'blitz'} {num2pseudo[best_one[1]]} {best_one[2]} {rank}\n"
                rank += 1

    # per role
    for classic1 in (False, True):
        for role_id1 in effective_roles:
            elo_sub_raw_list = [e for e in elo_raw_list if e[0] == classic1 and e[1] == role_id1]
            if elo_sub_raw_list:
                best_one = sorted(elo_sub_raw_list, key=lambda e: e[3], reverse=True)[0]
                teaser_text_variant += f"role  {'classique' if best_one[0] else 'blitz'} {num2pseudo[best_one[2]]} {best_one[3]} {num2rolename[best_one[1]]}\n"

    # date to teaser
    time_stamp = time.time()
    date_now_gmt = datetime.datetime.fromtimestamp(time_stamp)
    date_now_gmt_str = date_now_gmt.strftime("%Y-%m-%d %H:%M:%S UTC")
    teaser_text_variant += f"date {date_now_gmt_str}"

    lowdata.elapsed_then(elo_information, "list built")

    return elo_raw_list_sorted, teaser_text_variant


def run(jwt_token: str, commuter_account: str) -> None:
    """ Elo calculation scheduler. Calculates from games data for proviing ELO on the site. """

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
    url = f"{host}:{port}/games-in-state/2/2"  # archived
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get games list")
        return
    games_dict = req_result.json()

    # ========================
    # extract game results data
    # ========================

    host = lowdata.SERVER_CONFIG['GAME']['HOST']
    port = lowdata.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/extract_games_data/elo"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to get extract game results data")
        return
    res_dict = req_result.json()
    games_results_dict = res_dict['games_dict']

    # ========================
    # loop on variants
    # ========================

    elo_raw_list_table = {}
    teaser_text_table = {}

    for variant_name in lowdata.get_variant_list():

        # ------------------------
        # get variant data
        # ------------------------

        host = lowdata.SERVER_CONFIG['GAME']['HOST']
        port = lowdata.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/variants/{variant_name}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            if 'msg' in req_result.json():
                mylogger.LOGGER.error(req_result.json()['msg'])
            mylogger.LOGGER.error("ERROR: Failed to get variant data")
            return
        variant_content_loaded = req_result.json()

        # selected interface (forced)
        interface_inforced = lowdata.get_inforced_interface_from_variant(variant_name)

        # from interface chose get display parameters
        parameters_read = lowdata.read_parameters(variant_name, interface_inforced)

        # build variant data
        variant_data = mapping.Variant(variant_name, variant_content_loaded, parameters_read)

        # ------------------------
        # filter games_results_dict for variant
        # ------------------------
        variant_games_results_dict = {k: v for k, v in games_results_dict.items() if v['variant'] == variant_name}

        # ------------------------
        # perform ELO calculation for variant
        # ------------------------

        elo_information_variant: typing.List[str] = []
        elo_raw_list_variant, teaser_text_variant = process_elo_variant(variant_data, players_dict, variant_games_results_dict, games_dict, elo_information_variant, commuter_account)

        # dump ELO logs into a log file
        with open(f"./logdir/ELO_{variant_name}.log", "w", encoding='utf-8') as file_ptr:
            file_ptr.write('\n'.join(elo_information_variant))

        elo_raw_list_table[variant_name] = elo_raw_list_variant
        teaser_text_table[variant_name] = teaser_text_variant

    # ------------------------
    # load ELO in database
    # ------------------------

    elo_raw_list_table_json = json.dumps(elo_raw_list_table)
    teaser_text_table_json = json.dumps(teaser_text_table)
    json_dict = {
        'elo_list_table': elo_raw_list_table_json,
        'teaser_table': teaser_text_table_json
    }

    host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
    port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
    url = f"{host}:{port}/elo_rating"
    req_result = SESSION.post(url, headers={'AccessToken': f"{jwt_token}"}, json=json_dict)
    if req_result.status_code != 200:
        if 'msg' in req_result.json():
            mylogger.LOGGER.error(req_result.json()['msg'])
        mylogger.LOGGER.error("ERROR: Failed to update ELO database")
        return


if __name__ == '__main__':
    assert False, "Do not run this script directly"
