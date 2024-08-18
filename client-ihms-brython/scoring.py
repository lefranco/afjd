""" scoring """

# pylint: disable=pointless-statement, expression-not-assigned

# no mypy on this file
# mypy: ignore-errors


def c_diplo(centers_variant, ratings):
    """ the c-diplo scoring system """

    # solo
    solo_threshold = centers_variant // 2

    rank_points_list = [38, 14, 7]
    solo_reward = 73

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > solo_threshold:
        score[best_role_name] = solo_reward
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


def win_namur(centers_variant, ratings):
    """ the win namur scoring system """

    # solo
    solo_threshold = centers_variant // 2

    center_bonus_list = [0, 5, 9, 12, 14, 16, 18]
    rank_points_list = [18]
    solo_reward = 82
    wave_distance = 2
    wave_bonus = 18

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > solo_threshold:
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
    """ the diplo_league scoring system (variant_data is not used) """

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
                if ratings[role_name]:  # cannot have point s if no center
                    score[role_name] += rank_points_list[rank2 - 1] / sharers

    # extra points for winner(s)
    winners = [r for r in rank_table if rank_table[r] == 1]
    for role_name in winners:
        score[role_name] += bonus_alone if len(winners) == 1 else bonus_not_alone

    return score


def nexus_omg(centers_variant, ratings):
    """ the nexus_omg scoring system """

    # solo
    solo_threshold = centers_variant // 2

    solo_reward = 100
    center_worth = 1.5
    survival_worth = 9.
    rank_points_list = [4.5, 3, 1.5]
    bonus_percent_cap = 50.

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > solo_threshold:
        score[best_role_name] = solo_reward
        return score

    # center points (and survival)
    for role_name in score:
        center_num = ratings[role_name]
        if center_num:
            score[role_name] += survival_worth + center_num * center_worth

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

    # extra points for lone winner
    winners = [r for r in rank_table if rank_table[r] == 1]
    if len(winners) == 1:

        # the lone winner
        winner = winners[0]
        winner_centers = ratings[winner]

        # the runner(s) (second)
        runners = [r for r in rank_table if rank_table[r] == 2]
        runner = runners[0]
        runner_centers = ratings[runner]

        # SCs difference
        sc_difference = winner_centers - runner_centers

        # all pay tribute
        for other in ratings:
            if other == winner:
                continue
            other_tribute = min(sc_difference, score[other] * (bonus_percent_cap / 100.))
            score[winner] += other_tribute
            score[other] -= other_tribute

    return score


def c_diplo_namur(centers_variant, ratings):
    """ the c-diplo namur scoring system """

    # solo
    solo_threshold = centers_variant // 2

    rank_points_list = [38, 14, 7]
    center_bonus_list = [0, 5, 9, 12, 14, 16, 18]
    solo_reward = 85

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > solo_threshold:
        score[best_role_name] = solo_reward
        return score

    # participation point
    for role_name in score:
        score[role_name] += 1

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

    return score


def butcher(centers_variant, ratings):
    """ the butcher scoring system """

    # solo
    solo_threshold = centers_variant // 2

    solo_reward = 7
    no_elimination_reward = 0.5
    elimination_reward = 1

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > solo_threshold:
        score[best_role_name] = solo_reward
        return score

    # how many eliminated
    nb_eliminated = len([s for s in ratings.values() if s == 0])

    # calculate reward
    reward = elimination_reward * nb_eliminated if nb_eliminated else no_elimination_reward

    # give points
    for role_name in ratings:
        if ratings[role_name]:
            score[role_name] = reward

    return score


def bangkok(centers_variant, ratings):
    """ the bangkok scoring system """

    # solo
    solo_threshold = centers_variant // 2

    nb_players = len(ratings)

    domination_points = 420 + (nb_players - 7) * 30
    std_domination_points = 420

    center_value = nb_players / centers_variant
    std_center_value = 7 / 34
    center_points = (domination_points / 4) * (center_value / std_center_value)

    participation_points = 105
    survival_points = 315

    solo_reward = 4000 * (domination_points / std_domination_points)

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > solo_threshold:
        score[best_role_name] = solo_reward
        return score

    # domination points (similar to wave points)
    best_centers = max(ratings.values())
    for wave_distance in range(3):
        wave_sharers = [r for r in ratings if ratings[r] >= best_centers - wave_distance]
        # give points
        for role_name in wave_sharers:
            score[role_name] += domination_points / len(wave_sharers)

    # center points
    for role_name in score:
        center_num = ratings[role_name]
        score[role_name] += center_points * center_num

    # participation points
    for role_name in score:
        score[role_name] += participation_points

    # survival points (if you survive you get survival + second half participation)
    survivers = [r for r in ratings if ratings[r]]
    for role_name in survivers:
        score[role_name] += survival_points

    return score


def manorcon(centers_variant, ratings):
    """ the manorcon scoring system """

    # solo
    solo_threshold = centers_variant // 2

    # take floor value it seems
    nb_players = len(ratings)
    add_param = int(centers_variant / nb_players)

    solo_reward = 75

    # default score
    score = {role_name: 0 for role_name in ratings}

    # detect solo
    best_role_name = list(ratings.keys())[0]
    if ratings[best_role_name] > solo_threshold:
        score[best_role_name] = solo_reward * nb_players
        return score

    # total points
    total = 0
    for role_name in score:
        center_num = ratings[role_name]
        share = center_num ** 2 + 4 * center_num + add_param
        total += share

    # only survivors score
    survivers = [r for r in ratings if ratings[r]]
    for role_name in survivers:
        center_num = ratings[role_name]
        share = center_num ** 2 + 4 * center_num + add_param
        score[role_name] = 100 * nb_players * (share / total)

    return score


def scoring(game_scoring, centers_variant, ratings):
    """ scoring """

    score_table = {}

    # selected scoring game parameter
    if game_scoring == 'CDIP':
        score_table = c_diplo(centers_variant, ratings)
    if game_scoring == 'WNAM':
        score_table = win_namur(centers_variant, ratings)
    if game_scoring == 'DLIG':
        score_table = diplo_league(centers_variant, ratings)
    if game_scoring == 'NOMG':
        score_table = nexus_omg(centers_variant, ratings)
    if game_scoring == 'CNAM':
        score_table = c_diplo_namur(centers_variant, ratings)
    if game_scoring == 'BOUC':
        score_table = butcher(centers_variant, ratings)
    if game_scoring == 'BANG':
        score_table = bangkok(centers_variant, ratings)
    if game_scoring == 'MANO':
        score_table = manorcon(centers_variant, ratings)

    return score_table
