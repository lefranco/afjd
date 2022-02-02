#!/usr/bin/env python3


"""
File : export.py

gather information to make json file
"""

import argparse
import typing
import json

import database
import games  # noqa: F401 pylint: disable=unused-import
import ownerships
import scoring

SOLO_THRESHOLD = 18
POWER_NAME = {1: "England", 2: "France", 3: "Germany", 4: "Italy", 5: "Austria", 6: "Russia", 7: "Turkey"}


def export_data(game_name: str) -> typing.Dict[str, typing.Any]:
    """ exports all information about a game in format for DIPLOBN """

    # open database
    sql_executor = database.SqlExecutor()

    # get the game from database
    games_found = sql_executor.execute("SELECT game_data FROM games where name = ?", (game_name,), need_result=True)
    assert games_found, "Did not find game"
    game = games_found[0][0]

    #  print(game)

    # extract
    result = {}

    # game label
    result['GameLabel'] = game.name

    # url
    result['URL'] = f'https://diplomania-gen.fr?game={game.name}'

    # scoring system
    game_scoring = game.scoring
    result['ScoringSystem'] = game_scoring

    # communication
    if game.nomessage and game.nopress:
        result['CommunicationType'] = 'None'
    elif game.nomessage and game.nopress:
        result['CommunicationType'] = 'PublicOnly'
    else:
        result['CommunicationType'] = 'Full'

    # deadline
    if game.fast:
        result['DeadlineType'] = 'Live'
    else:
        result['DeadlineType'] = 'Extended'

    # limit of game
    result['LimitType'] = 'YearLimited'

    # note
    result['Note'] = game.description

    # get the players from database
    game_id = game.identifier
    allocations_found = sql_executor.execute("SELECT * FROM allocations where game_id = ?", (game_id,), need_result=True)
    assert allocations_found, "Did not find allocations"
    result['Players'] = {}
    for _, player_id, role_id in allocations_found:
        if role_id > 0:
            power_name = POWER_NAME[role_id]
            # TODO : find a way to get pseudo, first name and last name
            result['Players'][power_name] = f"Player with id {player_id} !"

    # get the result from database
    result['ResultSummary'] = {}
    game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
    ownership_dict = {}
    for _, center_num, role_num in game_ownerships:
        ownership_dict[center_num] = role_num

    ratings = {}
    for role_id, power_name in POWER_NAME.items():
        n_centers = len([_ for c, r in ownership_dict.items() if r == role_id])
        ratings[power_name] = n_centers

    ranking = {}
    for role_id, power_name in POWER_NAME.items():
        ranking[power_name] = 1 + len([_ for p in ratings if ratings[p] > ratings[power_name]])

    score_table = scoring.scoring(game_scoring, SOLO_THRESHOLD, ratings)  # type: ignore

    for role_id, power_name in POWER_NAME.items():
        result['ResultSummary'][power_name] = {}
        result['ResultSummary'][power_name]['CenterCount'] = ratings[power_name]
        result['ResultSummary'][power_name]['YearOfElimination'] = None
        result['ResultSummary'][power_name]['InGameAtEnd'] = bool(ratings[power_name])
        result['ResultSummary'][power_name]['Score'] = score_table[power_name]
        result['ResultSummary'][power_name]['Rank'] = ranking[power_name]

    # get the games phases
    # TODO

    del sql_executor

    return result


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', required=True, help='Name of game')
    parser.add_argument('-J', '--json_output', required=False, help='Output json file')
    args = parser.parse_args()

    game_name = args.name
    json_output = args.json_output

    result = export_data(game_name)

    # output
    if json_output is not None:
        output = json.dumps(result, indent=4, ensure_ascii=False)
        with open(json_output, 'w', encoding='utf-8') as file_ptr:
            file_ptr.write(output)


if __name__ == '__main__':
    main()
