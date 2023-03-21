""" elo """

# pylint: disable=pointless-statement, expression-not-assigned

import time

from browser import html  # pylint: disable=import-error

import mydatetime
import scoring

ALPHA = 1.5
D_CONSTANT = 400.
DEFAULT_ELO = 1500.
MINIMUM_ELO = 1000.

K_MAX_CONSTANT = 40
K_SLOPE = 2.

VERIFY = False

TEASER_KEEP = 7


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


def process_elo(variant_data, players_dict, games_results_dict, games_dict, elo_information):
    """ process_elo """

    global LAST_TIME

    # this to know how long it takes
    start_time = time.time()
    LAST_TIME = start_time

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
    static_score_table = {r: (ALPHA ** (num_players - r) - 1) / sum(ALPHA ** (num_players - i) - 1 for i in range(1, num_players + 1)) for r in range(1, num_players + 1)}

    # ------------------
    # 1 Parse all games
    # ------------------

    for game_name, game_data in sorted(games_results_dict.items(), key=lambda i: i[1]['start_time_stamp']):

        # extract information
        game_start_time = game_data['start_time_stamp']
        game_scoring_dict = game_data['scoring']
        centers_number_dict = game_data['centers_number']
        game_players_dict = game_data['players']
        classic = game_data['classic']

        if len(game_players_dict) != len(effective_roles):
            elo_information <= f"WARNING {game_name}: ignored because missing player(s) !!!!"
            elo_information <= html.BR()
            continue

        # convert time
        before = time.time()
        if VERIFY:
            time_creation = mydatetime.fromtimestamp(game_start_time)
            time_creation_str = mydatetime.strftime(*time_creation)
        after = time.time()
        dating_calculation_time += (after - before)

        # calculate scoring
        before = time.time()
        ratings = {num2rolename[n]: centers_number_dict[str(n)] if str(n) in centers_number_dict else 0 for n in variant_data.roles if n >= 1}
        solo_threshold = variant_data.number_centers() // 2
        score_table = scoring.scoring(game_scoring_dict, solo_threshold, ratings)
        after = time.time()
        scoring_calculation_time += (after - before)

        # calculate performance
        before = time.time()
        # get everyones's rank
        ranking_table = {r: len([ss for ss in score_table.values() if ss > s]) + 1 for r, s in score_table.items()}
        # get everyones's sharing
        shared_table = {r: len([ss for ss in score_table.values() if ss == s]) for r, s in score_table.items()}
        # get performance from rank and sharing
        performed_table = {r: sum(static_score_table[ranking_table[r] + i] for i in range(shared_table[r])) / shared_table[r] for r in score_table}
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
            elo_information <= f"{time_creation_str=} {game_name=} {classic=}"
            elo_information <= html.BR()
            elo_information <= f"{pseudo_table=}"
            elo_information <= html.BR()
            elo_information <= f"{score_table=}"
            elo_information <= html.BR()
            elo_information <= f"{ranking_table=}"
            elo_information <= html.BR()
            elo_information <= f"{expected_table=}"
            elo_information <= html.BR()
            elo_information <= f"{performed_table=}"
            elo_information <= html.BR()

        # elo variation

        if VERIFY:
            elo_information <= "Effect :"
            elo_information <= html.BR()

        # calculate effect on ELO
        before = time.time()
        loosers = [r for r in score_table if r == min(score_table.values())]
        winners = [r for r in score_table if r == max(score_table.values())]
        for (role_name, player) in memo.values():

            # K parameter must decrease other number of games
            k_player = max(K_MAX_CONSTANT // 2, K_MAX_CONSTANT - number_games_table[(player, role_name, classic)] / K_SLOPE)

            delta = k_player * num_players * (num_players / 2.) * (performed_table[role_name] - expected_table[role_name])

            # just a little check
            if role_name in loosers and delta > 0:
                elo_information <= f"WARNING {game_name}: {player} as {role_name} looses but gains points !!!!"
                elo_information <= html.BR()
            if role_name in winners and delta < 0:
                elo_information <= f"WARNING {game_name}: {player} as {role_name} wins but looses points !!!!"
                elo_information <= html.BR()

            if VERIFY:
                prev_elo = elo_table[(player, role_name, classic)]

            elo_table[(player, role_name, classic)] += delta
            elo_change_table[(player, role_name, classic)] = (game_name, delta)

            if VERIFY:
                new_elo = elo_table[(player, role_name, classic)]
                elo_information <= f"{player}({role_name}) -> delta = {delta} so elo changes from {prev_elo} to {new_elo}"
                elo_information <= html.BR()

            if elo_table[(player, role_name, classic)] < MINIMUM_ELO:
                elo_table[(player, role_name, classic)] = MINIMUM_ELO
                elo_information <= f"INFORMATION {game_name}: {player}({role_name}) would have less than {MINIMUM_ELO} so forced to this value"
                elo_information <= html.BR()

        after = time.time()
        variation_calculation_time += (after - before)

        if VERIFY:
            elo_information <= "-------------------"
            elo_information <= html.BR()

    elo_information <= f"Number of games processed : {len(games_results_dict)}"
    elo_information <= html.BR()

    elo_information <= f"Dating calculation time : {dating_calculation_time}"
    elo_information <= html.BR()

    elo_information <= f"Scoring calculation time : {scoring_calculation_time}"
    elo_information <= html.BR()

    elo_information <= f"Pseudo calculation time : {pseudo_calculation_time}"
    elo_information <= html.BR()

    elo_information <= f"Performance calculation time : {performance_calculation_time}"
    elo_information <= html.BR()

    elo_information <= f"Count calculation time : {count_calculation_time}"
    elo_information <= html.BR()

    elo_information <= f"Extract calculation time : {extract_calculation_time}"
    elo_information <= html.BR()

    elo_information <= f"Expected calculation time : {expected_calculation_time}"
    elo_information <= html.BR()

    elo_information <= f"Variation calculation time : {variation_calculation_time}"
    elo_information <= html.BR()

    elapsed_then(elo_information, "Parsing games time")

    # ------------------
    # 2 Make recap
    # ------------------

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

        if VERIFY:

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
                    game_name, last_change = elo_change_table[(player, role_name, classic)]
                    elo_information <= f"{rank + 1} {player} -> {elo} (last change {last_change:+f} in game {game_name} & played {sample_size} times)"
                    elo_information <= html.BR()
                elo_information <= html.BR()

        elapsed_then(elo_information, f"Mode {'CLASSIC' if classic else 'BLITZ'} time")

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
    elo_raw_list_sorted = sorted(elo_raw_list, key=lambda e: gameid2starttime[e[5]])

    # make teaser (just an abstract)
    teaser_text = "\n".join([f"{num2pseudo[e[2]]} : {e[3]} avec {num2rolename[e[1]]} en {'classique' if e[0] else 'blitz'}" for e in sorted(elo_raw_list, key=lambda ee: ee[3], reverse=True)][0: TEASER_KEEP])

    # date to teaser
    time_stamp = time.time()
    date_now_gmt = mydatetime.fromtimestamp(time_stamp)
    date_now_gmt_str = mydatetime.strftime(*date_now_gmt)
    teaser_text += f"\n(en date du {date_now_gmt_str})"

    # how long it took
    done_time = time.time()
    elapsed = done_time - start_time
    elo_information <= html.BR()
    elo_information <= f"Time elapsed : {elapsed}"
    elo_information <= html.BR()

    return elo_raw_list_sorted, teaser_text


def process_reliability(players_dict, games_results_dict, reliability_information):
    """ process_reliability """

    # this to know how long it takes
    start_time = time.time()

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

    for game_name, game_data in sorted(games_results_dict.items(), key=lambda i: i[1]['start_time_stamp']):

        # extract information
        number_advancement_played = game_data['number_advancement_played']
        delays_number_dict = game_data['delays_number']
        dropouts_number_dict = game_data['dropouts_number']
        game_players_dict = game_data['players']
        game_players = set(map(int, game_players_dict.keys()))

        # display stuff

        reliability_information <= f"{game_name=} {list(map(lambda n: num2pseudo[n], game_players))}"
        reliability_information <= html.BR()

        reliability_information <= "delays from this game: "
        for key, value in delays_number_dict.items():
            if int(key) in num2pseudo:
                player_pseudo = num2pseudo[int(key)]
                reliability_information <= f"{player_pseudo} "
            else:
                reliability_information <= f"({key}???) "
            reliability_information <= f"-> {value} "
            if int(key) not in game_players:
                reliability_information <= "(outside) "
        reliability_information <= html.BR()

        reliability_information <= "dropouts from this game: "
        for key, value in dropouts_number_dict.items():
            if int(key) in num2pseudo:
                player_pseudo = num2pseudo[int(key)]
                reliability_information <= f"{player_pseudo} "
            else:
                reliability_information <= f"({key}???) "
            reliability_information <= f"-> {value} "
            if int(key) not in game_players:
                reliability_information <= "(outside) "
        reliability_information <= html.BR()

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

    # ------------------
    # 4 Make reliability_list (returned)
    # ------------------

    reliability_list = []

    for player_id in players_set:

        number_delays = number_delays_table[player_id]
        number_dropouts = number_dropouts_table[player_id]
        number_advancements = number_advancements_table[player_id]

        reliability_element = [player_id, number_delays, number_dropouts, number_advancements]
        reliability_list.append(reliability_element)

        # to check
        reliability_information <= f"{num2pseudo[player_id]} -> {number_delays=} {number_dropouts=} {number_advancements=} "
        reliability_information <= html.BR()

    # how long it took
    done_time = time.time()
    elapsed = done_time - start_time
    reliability_information <= html.BR()
    reliability_information <= f"Time elapsed : {elapsed}"
    reliability_information <= html.BR()

    return reliability_list


def process_regularity(players_dict, games_results_dict, regularity_information):
    """ process_regularity """

    # this to know how long it takes
    start_time = time.time()

    # index is player_id
    number_games_table = {}

    # index is player_id
    started_playing_table = {}

    # index is player_id
    finished_playing_table = {}

    # index is player_id
    sequences_list_table = {}

    # index is player_id
    activity_table = {}

    # just set of players
    players_set = set()

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    # ------------------
    # 1 Parse all games
    # ------------------

    for game_name, game_data in sorted(games_results_dict.items(), key=lambda i: i[1]['start_time_stamp']):

        # extract information
        game_start_time = game_data['start_time_stamp']
        game_end_time = game_data['end_time_stamp']
        game_players_dict = game_data['players']
        game_players = list(map(int, game_players_dict.keys()))

        regularity_information <= f"{game_name=} {list(map(lambda n: num2pseudo[n], game_players))}"
        regularity_information <= html.BR()

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

    regularity_information <= html.BR()

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
        regularity_information <= f"{num2pseudo[player_id]} -> {number_games=} {started_playing_days=} {finished_playing_days=} {activity_days=}"
        regularity_information <= html.BR()

    # how long it took
    done_time = time.time()
    elapsed = done_time - start_time
    regularity_information <= html.BR()
    regularity_information <= f"Time elapsed : {elapsed}"
    regularity_information <= html.BR()

    return regularity_list
