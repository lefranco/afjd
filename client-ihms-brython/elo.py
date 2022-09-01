""" elo """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

import scoring

D_CONSTANT = 400
K_CONSTANT = 32
DEFAULT_ELO = 1000


def process_elo(variant_data, players_dict, games_dict, elo_information):
    """ process_elo """

    for game_name, game_data in sorted(games_dict.items(), key=lambda i: i[1]['time_stamp']):

        # extract information
        players_dict = game_data['players']
        game_scoring = game_data['scoring']
        centers_number_dict = game_data['centers_number']

        # calculate scoring
        ratings = {variant_data.name_table[variant_data.roles[n]]: centers_number_dict[str(n)] if str(n) in centers_number_dict else 0 for n in variant_data.roles if n != 0}
        solo_threshold = variant_data.number_centers() // 2
        score_table = scoring.scoring(game_scoring, solo_threshold, ratings)

        elo_information <= f"{game_name}({game_scoring})-> {score_table}"
        elo_information <= html.BR()
