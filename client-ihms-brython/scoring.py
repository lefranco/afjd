""" scoring """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html, alert  # pylint: disable=import-error
from browser.widgets.dialog import InfoDialog  # pylint: disable=import-error
from browser.local_storage import storage  # pylint: disable=import-error

import config
import common


# simplest is to hard code displays of variants here
SCORING_TABLE = {
    'standard': ['c diplo', 'win namur', 'diplo league']
}


def c_diplo(variant, ratings):
    """ the c-diplo scoring system """

    rank_points_list = [38, 14, 7]
    solo_reward = 73

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > variant.number_centers() // 2:
        ratings[best_role_name] = solo_reward
        return score

    # participation point
    for role_name in score:
        score[role_name] += 1

    # center points
    for role_name in score:
        center_num = ratings[role_name]
        score[role_name] += center_num

    # rank points

    # calculate rank and rank share
    rank_table = {role_name: 1 + len([ro for ro in ratings if ratings[ro] > ratings[role_name]]) for role_name in ratings}
    rank_share_table = {ra: len([ro for ro in rank_table if rank_table[ro] == ra]) for ra in rank_table.values()}

    # give points
    for role_name in ratings:
        rank = rank_table[role_name]
        if rank - 1 not in range(len(rank_points_list)):
            continue
        sharers = rank_share_table[rank]
        for rank2 in range(rank, rank + sharers):
            if rank2 - 1 in range(len(rank_points_list)):
                score[role_name] += rank_points_list[rank2 - 1] / sharers

    return score


def win_namur(variant, ratings):
    """ the win namur scoring system """

    center_bonus_list = [0, 5, 9, 12, 14, 16, 18]
    rank_points_list = [18]
    solo_reward = 82
    wave_distance = 2
    wave_bonus = 18

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > variant.number_centers() // 2:
        score[best_role_name] = solo_reward
        return score

    # center points
    for role_name in score:
        center_num = ratings[role_name]
        if center_num in range(len(center_bonus_list)):
            score[role_name] += center_bonus_list[center_num]
        else:
            best_bonus = center_bonus_list[-1]
            score[role_name] += best_bonus
            score[role_name] += 1 + center_num - len(center_bonus_list)

    # rank points

    # calculate rank and rank share
    rank_table = {role_name: 1 + len([ro for ro in ratings if ratings[ro] > ratings[role_name]]) for role_name in ratings}
    rank_share_table = {ra: len([ro for ro in rank_table if rank_table[ro] == ra]) for ra in rank_table.values()}

    # give points
    for role_name in ratings:
        rank = rank_table[role_name]
        if rank - 1 not in range(len(rank_points_list)):
            continue
        sharers = rank_share_table[rank]
        for rank2 in range(rank, rank + sharers):
            if rank2 - 1 in range(len(rank_points_list)):
                score[role_name] += rank_points_list[rank2 - 1] / sharers

    # wave points

    # calculate sharers
    best_centers = max(ratings.values())
    wave_sharers = [r for r in ratings if ratings[r] >= best_centers - wave_distance]

    # give points
    for role_name in wave_sharers:
        score[role_name] += wave_bonus / len(wave_sharers)

    return score


def diplo_league(_, ratings):
    """ the diplo_league scoring system """

    rank_points_list = [16, 14, 12, 10, 8, 6, 4]
    bonus_alone = 4
    bonus_not_alone = 1

    # default score
    score = {role_name: 0 for role_name in ratings}

    # rank points

    # calculate rank and rank share
    rank_table = {role_name: 1 + len([ro for ro in ratings if ratings[ro] > ratings[role_name]]) for role_name in ratings}
    rank_share_table = {ra: len([ro for ro in rank_table if rank_table[ro] == ra]) for ra in rank_table.values()}

    # give points
    for role_name in ratings:
        rank = rank_table[role_name]
        if rank - 1 not in range(len(rank_points_list)):
            continue
        sharers = rank_share_table[rank]
        for rank2 in range(rank, rank + sharers):
            if rank2 - 1 in range(len(rank_points_list)):
                score[role_name] += rank_points_list[rank2 - 1] / sharers

    # extra points for winner(s)
    winners = [r for r in rank_table if rank_table[r] == 1]
    for role_name in winners:
        score[role_name] += bonus_alone if len(winners) == 1 else bonus_not_alone

    return score


my_panel = html.DIV(id="scoring")
my_panel.attrs['style'] = 'display: table'


def get_scoring_from_variant(variant):
    """ get_scoring_from_variant """

    reference = f'SCORING_{variant}'.upper()
    if reference in storage:
        return storage[reference]

    # takes the first
    return SCORING_TABLE[variant][0]


def select_scoring():
    """ select_scoring """

    variant_name_loaded = None

    def select_scoring_callback(_, scoring):
        """ select_scoring_callback """

        reference = f'SCORING_{variant_name_loaded}'.upper()
        storage[reference] = scoring

        InfoDialog("OK", f"Scorage sélectionnée pour la variante {variant_name_loaded} : {scoring}", remove_after=config.REMOVE_AFTER)

        render(G_PANEL_MIDDLE)

    if 'GAME' not in storage:
        alert("Il faut choisir la partie au préalable")
        return None

    game = storage['GAME']

    # from game name get variant name

    variant_name_loaded = common.game_variant_name_reload(game)
    if not variant_name_loaded:
        return None

    select_table = html.TABLE()

    for scoring in SCORING_TABLE[variant_name_loaded]:

        form = html.FORM()
        fieldset = html.FIELDSET()
        legend_scoring = html.LEGEND(scoring)
        fieldset <= legend_scoring
        form <= fieldset

        form <= html.BR()

        input_select_scoring = html.INPUT(type="submit", value="sélectionner ce scorage")
        input_select_scoring.bind("click", lambda e, s=scoring: select_scoring_callback(e, s))
        form <= input_select_scoring

        col = html.TD()
        col <= form
        col <= html.BR()

        row = html.TR()
        row <= col

        select_table <= row

    return select_table


G_PANEL_MIDDLE = None


def render(panel_middle):
    """ render """

    global G_PANEL_MIDDLE
    G_PANEL_MIDDLE = panel_middle

    my_panel.clear()

    my_sub_panel = select_scoring()

    if my_sub_panel:
        my_panel <= html.H2("Sélectionnez le scorage que vous souhaitez utiliser")
        my_panel <= my_sub_panel

    panel_middle <= my_panel
