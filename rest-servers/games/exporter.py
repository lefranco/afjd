#!/usr/bin/env python3


"""
File : export.py

gather information to make json file
"""

import argparse
import typing
import json

import database
import games
import ownerships

POWER_NAME = { 1: "England", 2: "France", 3: "Germany", 4: "Italy", 5: "Austria", 6: "Russia", 7: "Turkey" }

def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', required=True, help='Name of game')
    parser.add_argument('-v', '--variant_input', required=True, help='Input variant json file')
    parser.add_argument('-J', '--json_output', required=False, help='Output json file')
    args = parser.parse_args()

    game_name = args.name
    json_variant_input = args.variant_input
    json_output = args.json_output

    # load variant from json data file
    with open(json_variant_input, "r", encoding='utf-8') as read_file:
        json_variant_data = json.load(read_file)

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
    result['ScoringSystem'] = game.scoring

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
    for role_id, power_name in POWER_NAME.items():
        result['ResultSummary'][power_name] = dict()
        result['ResultSummary'][power_name]['CenterCount'] = len([c for c in ownership_dict if ownership_dict[c] == role_id])
        result['ResultSummary'][power_name]['YearOfElimination'] = None
        result['ResultSummary'][power_name]['InGameAtEnd'] = True
        result['ResultSummary'][power_name]['Score'] = 0 # TODO
        result['ResultSummary'][power_name]['Rank'] = 0 # TODO

    # get the games phases
    # TODO

    # output
    if json_output is not None:
        output = json.dumps(result, indent=4, ensure_ascii=False)
        with open(json_output, 'w', encoding='utf-8') as file_ptr:
            file_ptr.write(output)


if __name__ == '__main__':
    main()
