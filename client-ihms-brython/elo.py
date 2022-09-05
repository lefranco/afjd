""" elo """

# pylint: disable=pointless-statement, expression-not-assigned

import datetime
import time

from browser import html  # pylint: disable=import-error

import scoring

D_CONSTANT = 400.
DEFAULT_ELO = 1500.
MINIMUM_ELO = 1000.

VERIFY = True


LAST_TIME = 0


def elapsed_then(elo_information, desc):
    """ elapsed_then """

    global LAST_TIME

    # elapsed
    now_time = time.time()
    elapsed = now_time - LAST_TIME

    # update last time
    LAST_TIME = now_time

    # display
    elo_information <= html.BR()
    elo_information <= f"{desc} : {elapsed}"
    elo_information <= html.BR()


def process_elo(variant_data, players_dict, games_dict, elo_information):
    """ process_elo """

    global LAST_TIME

    # this to know how long it takes
    start_time = time.time()
    LAST_TIME = start_time

    # index is (player, role_name, classic)
    elo_table = {}

    # index is (player, role_name, classic)
    number_games_table = {}

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    # should be 7
    num_players = len([n for n in variant_data.roles if n >= 1])

    # rolename from number
    num2rolename = {n: variant_data.name_table[variant_data.roles[n]] for n in variant_data.roles if n >= 1}

    # to measure time spent on scoring
    scoring_calculation_time = 0.

    effective_roles = [r for r in variant_data.roles if r >= 1]

    for game_name, game_data in sorted(games_dict.items(), key=lambda i: i[1]['time_stamp']):

        # extract information
        time_stamp = game_data['time_stamp']
        game_scoring_dict = game_data['scoring']
        centers_number_dict = game_data['centers_number']
        game_players_dict = game_data['players']
        classic = game_data['classic']

        # convert time
        time_creation = datetime.datetime.fromtimestamp(time_stamp, datetime.timezone.utc)
        time_creation_str = datetime.datetime.strftime(time_creation, "%d-%m-%Y %H:%M:%S")

        # calculate scoring
        ratings = {num2rolename[n]: centers_number_dict[str(n)] if str(n) in centers_number_dict else 0 for n in variant_data.roles if n >= 1}
        solo_threshold = variant_data.number_centers() // 2

        before = time.time()
        score_table = scoring.scoring(game_scoring_dict, solo_threshold, ratings)
        after = time.time()
        scoring_calculation_time += (after - before)

        # calculate performance
        sum_score = sum(score_table.values())
        performed_table = {r: s / sum_score for r, s in score_table.items()}

        # get pseudos of players
        pseudo_table = {num2rolename[rn]: num2pseudo[int(pn)] for pn, rn in game_players_dict.items()}

        # count games
        for num in effective_roles:
            role_name = num2rolename[num]
            player = pseudo_table[role_name]
            if (player, role_name, classic) not in number_games_table:
                number_games_table[(player, role_name, classic)] = 0
            number_games_table[(player, role_name, classic)] += 1

        # extract ELO of players
        rating_table = {}
        for num in effective_roles:
            role_name = num2rolename[num]
            player = pseudo_table[role_name]
            if (player, role_name, classic) not in elo_table:
                elo_table[(player, role_name, classic)] = DEFAULT_ELO
            rating_table[role_name] = elo_table[(player, role_name, classic)]

        # calculate expected performance
        expected_table = {}
        for num in effective_roles:
            role_name = num2rolename[num]
            expected_table[role_name] = 0
            for num2 in variant_data.roles:
                if num2 >= 1 and num2 != num:
                    role_name2 = num2rolename[num2]
                    expected_table[role_name] += 1 / (1 + (10 ** ((rating_table[role_name2] - rating_table[role_name]) / D_CONSTANT)))
            expected_table[role_name] /= ((num_players * (num_players - 1)) / 2)

        if VERIFY:
            elo_information <= f"{time_creation_str=} {game_name=} {classic=}"
            elo_information <= html.BR()
            elo_information <= f"{pseudo_table=}"
            elo_information <= html.BR()
            elo_information <= f"{score_table=}"
            elo_information <= html.BR()
            elo_information <= f"{expected_table=}"
            elo_information <= html.BR()
            elo_information <= f"{performed_table=}"
            elo_information <= html.BR()

        loosers = [r for r in score_table if r == min(score_table.values())]
        winners = [r for r in score_table if r == max(score_table.values())]

        # elo variation

        if VERIFY:
            elo_information <= "Effect :"
            elo_information <= html.BR()

        for num in effective_roles:
            role_name = num2rolename[num]
            player = pseudo_table[role_name]

            # K parameter must decrease other number of games
            k_player = max(20, 40 - number_games_table[(player, role_name, classic)] / 2.)

            delta = k_player * num_players * (num_players / 2) * (performed_table[role_name] - expected_table[role_name])

            # just a little check
            if role_name in loosers and delta > 0:
                elo_information <= f"WARNING {game_name}: {player} as {role_name} looses but gains points !!!!"
                elo_information <= html.BR()
            if role_name in winners and delta < 0:
                elo_information <= f"WARNING {game_name}: {player} as {role_name} wins but looses points !!!!"
                elo_information <= html.BR()

            prev_elo = elo_table[(player, role_name, classic)]
            elo_table[(player, role_name, classic)] += delta
            new_elo = elo_table[(player, role_name, classic)]

            if VERIFY:
                elo_information <= f"{player}({role_name}) -> delta = {delta} so elo changes from {prev_elo} to {new_elo}"
                elo_information <= html.BR()

            if new_elo < MINIMUM_ELO:
                elo_table[(player, role_name, classic)] = MINIMUM_ELO
                elo_information <= f"INFORMATION {game_name}: {player}({role_name}) would have less than {MINIMUM_ELO} so forced to this value"
                elo_information <= html.BR()

        if VERIFY:
            elo_information <= "-------------------"
            elo_information <= html.BR()

    elo_information <= f"Scoring calculation time : {scoring_calculation_time}"
    elo_information <= html.BR()

    elapsed_then(elo_information, "Parsing games")

    for classic in (True, False):

        elo_information <= "-------------------"
        elo_information <= html.BR()
        elo_information <= "-------------------"
        elo_information <= html.BR()
        elo_information <= f"RATINGS FOR {'CLASSIC' if classic else 'BLITZ'} MODE"
        elo_information <= html.BR()
        elo_information <= "-------------------"
        elo_information <= html.BR()

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
                        elo_recap_table[player] = {'sum': 0, 'number': 0}
                    elo_recap_table[player]['sum'] += elo_table[(player, role_name, classic)]
                    elo_recap_table[player]['number'] += 1

        # fills DEFAULT_ELO for roles not played
        final_raw_elo_table = {k: (v['sum'] + (num_players - v['number']) * DEFAULT_ELO) / num_players for k, v in elo_recap_table.items()}

        # sort table
        final_elo_table = dict(sorted(final_raw_elo_table.items(), key=lambda t: t[1], reverse=True))

        # display
        elo_information <= "-------------------"
        elo_information <= html.BR()
        for rank, (player, elo) in enumerate(final_elo_table.items()):

            # make detail for player
            player_detail = {num2rolename[num]: elo_table[(player, num2rolename[num], classic)] for num in variant_data.roles if num >= 1 and (player, num2rolename[num], classic) in elo_table}

            # display rankings
            elo_information <= f"{rank + 1} {player} -> {elo} ({player_detail})"
            elo_information <= html.BR()

        # --------------
        # per role recap
        # --------------

        for num in effective_roles:

            # display role name
            elo_information <= "-------------------"
            elo_information <= html.BR()
            role_name = num2rolename[num]
            elo_information <= role_name
            elo_information <= html.BR()

            # make table
            final_raw_role_elo_table = {p: elo_table[(p, rn, c)] for (p, rn, c) in elo_table if rn == role_name and c == classic}

            # sort table
            final_role_elo_table = dict(sorted(final_raw_role_elo_table.items(), key=lambda t: t[1], reverse=True))

            # display rankings
            for rank, (player, elo) in enumerate(final_role_elo_table.items()):
                sample_size = number_games_table[(player, role_name, classic)]
                elo_information <= f"{rank + 1} {player} -> {elo} (played {sample_size} times)"
                elo_information <= html.BR()
            elo_information <= html.BR()

        elapsed_then(elo_information, f"Mode {'CLASSIC' if classic else 'BLITZ'}")

    # how long it took
    done_time = time.time()
    elapsed = done_time - start_time
    elo_information <= html.BR()
    elo_information <= f"Time elapsed : {elapsed}"
    elo_information <= html.BR()
