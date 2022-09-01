""" elo """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

import scoring

D_CONSTANT = 400.
K_CONSTANT = 32.
DEFAULT_ELO = 1000.


def process_elo(variant_data, players_dict, games_dict, elo_information):
    """ process_elo """

    elo_table = {}

    # pseudo from number
    num2pseudo = {v: k for k, v in players_dict.items()}

    # should be 7
    num_players = len([n for n in variant_data.roles if n >= 1])

    # rolename from number
    num2rolename = {n: variant_data.name_table[variant_data.roles[n]] for n in variant_data.roles if n >= 1}

    for game_name, game_data in sorted(games_dict.items(), key=lambda i: i[1]['time_stamp']):

        # extract information
        game_scoring_dict = game_data['scoring']
        centers_number_dict = game_data['centers_number']
        game_players_dict = game_data['players']

        # calculate scoring
        ratings = {num2rolename[n]: centers_number_dict[str(n)] if str(n) in centers_number_dict else 0 for n in variant_data.roles if n >= 1}
        solo_threshold = variant_data.number_centers() // 2
        score_table = scoring.scoring(game_scoring_dict, solo_threshold, ratings)

        # calculate performance
        sum_score = sum(score_table.values())
        performed_table = {r: s / sum_score for r, s in score_table.items()}

        # get pseudos of players
        pseudo_table = {num2rolename[rn]: num2pseudo[int(pn)] for pn, rn in game_players_dict.items()}

        # extract ELO of players
        rating_table = {}
        for num in variant_data.roles:
            if num >= 1:
                role_name = num2rolename[num]
                player = pseudo_table[role_name]
                if (player, role_name) not in elo_table:
                    elo_table[(player, role_name)] = DEFAULT_ELO
                rating_table[role_name] = elo_table[(player, role_name)]

        # calculate expected performance
        expected_table = {}
        for num in variant_data.roles:
            if num >= 1:
                role_name = num2rolename[num]
                expected_table[role_name] = 0
                for num2 in variant_data.roles:
                    if num2 >= 1 and num2 != num:
                        role_name2 = num2rolename[num2]
                        expected_table[role_name] += 1 / (1 + (10 ** ((rating_table[role_name2] - rating_table[role_name]) / D_CONSTANT)))
                expected_table[role_name] /= ((num_players * (num_players - 1)) / 2)

        elo_information <= f"{game_name} -> {score_table} {pseudo_table} {performed_table} {expected_table} "
        elo_information <= html.BR()

        # elo variation
        for num in variant_data.roles:
            if num >= 1:
                role_name = num2rolename[num]
                player = pseudo_table[role_name]
                elo_table[(player, role_name)] += K_CONSTANT * (performed_table[role_name] - expected_table[role_name])

                elo_information <= f"{player}({role_name}) -> delta = {K_CONSTANT * (performed_table[role_name] - expected_table[role_name])} "
                elo_information <= html.BR()

        elo_information <= html.HR()

    # now for detailed recap
    elo_recap_table = {}
    for pseudo in players_dict:
        for num in variant_data.roles:
            if num >= 1:
                role_name = num2rolename[num]
                if (pseudo, role_name) in elo_table:
                    if pseudo not in elo_recap_table:
                        elo_recap_table[pseudo] = {'sum': 0, 'number': 0}
                    elo_recap_table[pseudo]['sum'] += elo_table[(pseudo, role_name)]
                    elo_recap_table[pseudo]['number'] += 1

    # global recap
    final_raw_elo_table = {p: elo_recap_table[p]['sum'] / elo_recap_table[p]['number'] for p in elo_recap_table}
    final_elo_table = {p: final_raw_elo_table[p] for p in sorted(final_raw_elo_table, key=lambda p: final_raw_elo_table[p], reverse=True)}

    # display
    elo_information <= html.HR()
    elo_information <= html.HR()
    elo_information <= html.HR()
    for rank, (player, elo) in enumerate(final_elo_table.items()):
        player_detail = {num2rolename[num]: elo_table[(player, num2rolename[num])] for num in variant_data.roles if num >= 1 and (player, num2rolename[num]) in elo_table}
        elo_information <= f"{rank + 1} {player} -> {elo} ({player_detail})"
        elo_information <= html.BR()
