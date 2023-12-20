""" elo """

# pylint: disable=pointless-statement, expression-not-assigned

import time

from browser import html  # pylint: disable=import-error


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
