#!/usr/bin/env python3


"""
File : export.py

gather information to make json file
"""

import argparse
import typing
import json
import requests

import lowdata
import database
import games  # noqa: F401 pylint: disable=unused-import
import ownerships
import transitions
import scoring

# TODO : in production, put False and test we get the players data
DEBUG = True

SESSION = requests.Session()

SOLO_THRESHOLD = 18

POWER_NAME = [
    'England', 'France', 'Germany', 'Italy', 'Austria', 'Russia', 'Turkey'
]
assert len(POWER_NAME) == 7

CENTER_NAME = [
    'Ank', 'Bel', 'Ber', 'Bre', 'Bud', 'Bul', 'Con', 'Den', 'Edi', 'Gre', 'Hol', 'Kie', 'Lon', 'Lvp', 'Mar', 'Mos',
    'Mun', 'Nap', 'Nwy', 'Par', 'Por', 'Rom', 'Rum', 'Ser', 'Sev', 'Smy', 'Spa', 'Stp', 'Wwe', 'Tri', 'Tun', 'Ven',
    'Vie', 'War']
assert len(CENTER_NAME) == 34

TYPE_NAME = ['A', 'F']
assert len(TYPE_NAME) == 2

ZONE_NAME = [
    'Adr', 'Aeg', 'Alb', 'Ank', 'Apu', 'Arm', 'Bal', 'Bar', 'Bel', 'Ber', 'Bla', 'Boh', 'Bot', 'Bre', 'Bud', 'Bul',
    'Bur', 'Cly', 'Con', 'Den', 'Eas', 'Edi', 'Eng', 'Fin', 'Gal', 'Gas', 'Gol', 'Gre', 'Hel', 'Hol', 'Ion', 'Iri',
    'Kie', 'lon', 'Lvn', 'Lvp', 'mar', 'Mid', 'Mos', 'Mun', 'Naf', 'Nap', 'Nat', 'Nrg', 'Nth', 'Nwy', 'Par', 'Pic',
    'Pie', 'Por', 'Pru', 'Rom', 'Ruh', 'Rum', 'Ser', 'Sev', 'Sil', 'Ska', 'Smy', 'Spa', 'Stp', 'Swe', 'Syr', 'Tri',
    'Tun', 'Tus', 'Tyn', 'Tyr', 'Ukr', 'Ven', 'Vie', 'Wal', 'War', 'Wed', 'Yor',
    'Bul ec', 'Bul sc', 'Spa nc', 'Spa sc', 'Stp nc', 'Stp sc']
assert len(ZONE_NAME) == 81

FRENCH_ZONE_NAME = [
    'ADR', 'EGE', 'ALB', 'ANK', 'APU', 'ARM', 'BAL', 'BAR', 'BEL', 'BER', 'NOI', 'BOH', 'BOT', 'BRE', 'BUD', 'BUL',
    'BOU', 'CLY', 'CON', 'DAN', 'MOR', 'EDI', 'MAN', 'FIN', 'GAL', 'GAS', 'GLI', 'GRE', 'HEL', 'HOL', 'ION', 'IRL',
    'KIE', 'LON', 'LVN', 'LVP', 'MAR', 'ATL', 'MOS', 'MUN', 'AFN', 'NAP', 'ATN', 'MNG', 'NRD', 'NGE', 'PAR', 'PIC',
    'PIE', 'POR', 'PRU', 'ROM', 'RUH', 'ROU', 'SER', 'SEB', 'SIL', 'SKA', 'SMY', 'ESP', 'STP', 'SUE', 'SYR', 'TRI',
    'TUN', 'TOS', 'MTY', 'TYR', 'UKR', 'VEN', 'VIE', 'PGA', 'VAR', 'MOC', 'YOR',
    'BULce', 'BULcs', 'ESPcn', 'ESPcs', 'STPcn', 'STPcs']
assert len(FRENCH_ZONE_NAME) == 81


def export_data(game_name: str) -> typing.Dict[str, typing.Any]:
    """ exports all information about a game in format for DIPLOBN """

    # open database
    sql_executor = database.SqlExecutor()

    # get the game from database
    games_found = sql_executor.execute("SELECT game_data FROM games where name = ?", (game_name,), need_result=True)
    assert games_found, "Did not find game"
    game = games_found[0][0]

    # extract
    result = {}

    # game label
    result['GameLabel'] = game.name

    # url
    result['URL'] = f'https://diplomania-gen.fr?game={game.name}'

    # date begin
    result['DateBegan'] = None
    result['DateEnded'] = None

    # scoring system
    game_scoring = game.scoring
    result['ScoringSystem'] = game_scoring

    # communication
    # TODO : we have an issue here since we open press at end of all games...
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

    # get all players
    players_dict = {}
    if not DEBUG:
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players"
        req_result = SESSION.get(url)
        assert req_result.status_code == 200, "Failed to access players API"
        players_dict = req_result.json()
        print(f"{players_list=}")
        assert False, "DONE"

    # get the players from database
    game_id = game.identifier
    allocations_found = sql_executor.execute("SELECT * FROM allocations where game_id = ?", (game_id,), need_result=True)
    assert allocations_found, "Did not find allocations"
    result['Players'] = {}
    for _, player_id, role_id in allocations_found:
        if role_id > 0:
            role_num = role_id - 1
            power_name = POWER_NAME[role_num]
            if players_dict:
                player_data = players_dict[player_id]
                player_pseudo = player_data['pseudo']
                player_first_name = player_data['first_name']
                player_family_name = player_data['family_name']
                result['Players'][power_name] = f"{player_first_name} {player_family_name} (player_pseudo)"
            else:
                result['Players'][power_name] = f"Unknown!"

    # get the result from database
    result['ResultSummary'] = {}
    game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
    ownership_dict = {}
    for _, center_num, role_id in game_ownerships:
        ownership_dict[center_num] = role_id

    ratings = {}
    for role_num, power_name in enumerate(POWER_NAME):
        role_id = role_num + 1
        n_centers = len([_ for c, r in ownership_dict.items() if r == role_id])
        ratings[power_name] = n_centers

    ranking = {}
    for role_num, power_name in enumerate(POWER_NAME):
        role_id = role_num + 1
        ranking[power_name] = 1 + len([_ for p in ratings if ratings[p] > ratings[power_name]])

    score_table = scoring.scoring(game_scoring, SOLO_THRESHOLD, ratings)  # type: ignore

    for role_num, power_name in enumerate(POWER_NAME):
        role_id = role_num + 1
        result['ResultSummary'][power_name] = {}
        result['ResultSummary'][power_name]['CenterCount'] = ratings[power_name]
        result['ResultSummary'][power_name]['YearOfElimination'] = None
        result['ResultSummary'][power_name]['InGameAtEnd'] = bool(ratings[power_name])
        result['ResultSummary'][power_name]['Score'] = score_table[power_name]
        result['ResultSummary'][power_name]['Rank'] = ranking[power_name]

    # get the games phases
    result['GamePhases'] = []
    advancement = 0
    while True:

        transition = transitions.Transition.find_by_identifier_advancement(sql_executor, game_id, advancement)
        if transition is None:
            break

        the_situation = json.loads(transition.situation_json)
        ownership_dict = the_situation['ownerships']
        unit_dict = the_situation['units']
        the_orders = json.loads(transition.orders_json)

        phase_data: typing.Dict[str, typing.Any] = {}

        game_year = 1901 + advancement // 5
        if advancement % 5 in [0, 1]:
            game_season = 1
        elif advancement % 5 in [2, 3]:
            game_season = 2
        elif advancement % 5 in [4]:
            game_season = 3
        phase_data['Phase'] = f"{game_year}{game_season}"
        phase_data['Status'] = 'Completed'
        ratings_phase = {}

        for role_num, power_name in enumerate(POWER_NAME):
            role_id = role_num + 1
            n_centers = len([_ for __, r in ownership_dict.items() if r == role_id])
            ratings_phase[power_name] = n_centers
        phase_data['CenterCounts'] = ratings_phase

        centers_phase = {}
        for role_num, power_name in enumerate(POWER_NAME):
            role_id = role_num + 1
            centers_phase[power_name] = [CENTER_NAME[int(c) - 1] for c, r in ownership_dict.items() if r == role_id]
        phase_data['SupplyCenters'] = centers_phase

        units_phase = {}
        for role_num, power_name in enumerate(POWER_NAME):
            role_id = role_num + 1
            units_phase[power_name] = [[TYPE_NAME[int(t) - 1], ZONE_NAME[int(z) - 1]] for t, z in unit_dict[str(POWER_NAME.index(power_name) + 1)]] if str(POWER_NAME.index(power_name) + 1) in unit_dict else []
        phase_data['Units'] = units_phase

        report_txt = transition.report_txt
        report_lines = report_txt.split('\n')

        report_header = report_lines[0]
        report_date, _, _ = report_header.partition(':')
        if result['DateBegan'] is None:
            result['DateBegan'] = report_date
        result['DateEnded'] = report_date

        justification_table: typing.Dict[int, str] = {}
        for line in report_lines:
            if ';' in line:
                words = line.split(' ')
                french_unit = words[1]
                zone_num = FRENCH_ZONE_NAME.index(french_unit) + 1
                _, _, justification = line.partition(';')
                assert zone_num not in justification_table
                justification_table[zone_num] = justification

        orders_phase: typing.Dict[str, typing.Any] = {}
        actual_orders_list = the_orders['orders']
        fake_units_list = the_orders['fake_units']
        for role_num, power_name in enumerate(POWER_NAME):
            role_id = role_num + 1
            orders_phase[power_name] = []

            # build the table fake untis zone -> type
            fake_table = {}
            for _, type_, zone, role, _, _ in fake_units_list:
                if role != role_id:
                    continue
                fake_table[zone] = type_

            # parse the orders
            for _, role, order, active, passive, destination in actual_orders_list:
                if role != role_id:
                    continue
                adj_justif = justification_table.get(active, "")
                adj_result = "f" if adj_justif else "s"
                if order == 1:  # move
                    order_description = [ZONE_NAME[int(active) - 1], ['m', ZONE_NAME[int(destination) - 1]], [adj_result, adj_justif]]
                if order == 2:  # attack support
                    order_description = [ZONE_NAME[int(active) - 1], ['sm', ZONE_NAME[int(passive) - 1], ZONE_NAME[int(destination) - 1]], [adj_result, adj_justif]]
                if order == 3:  # attack support
                    order_description = [ZONE_NAME[int(active) - 1], ['sh', ZONE_NAME[int(passive) - 1]], [adj_result, adj_justif]]
                if order == 4:  # hold
                    order_description = [ZONE_NAME[int(active) - 1], ['h'], [adj_result, adj_justif]]
                if order == 5:  # convoy
                    order_description = [ZONE_NAME[int(active) - 1], ['c', ZONE_NAME[int(passive) - 1], ZONE_NAME[int(destination) - 1]], [adj_result, adj_justif]]
                if order == 6:  # retreat
                    # unsure
                    order_description = [ZONE_NAME[int(active) - 1], ['m', ZONE_NAME[int(destination) - 1]], [adj_result, adj_justif]]
                if order == 7:  # disband
                    # unsure
                    order_description = [ZONE_NAME[int(active) - 1], ['d'], [adj_result, adj_justif]]
                if order == 8:  # build
                    type_ = fake_table[active]
                    order_description = [ZONE_NAME[int(active) - 1], ['b', TYPE_NAME[int(type_) - 1]], [adj_result, adj_justif]]
                if order == 9:  # remove
                    order_description = [ZONE_NAME[int(active) - 1], ['d'], [adj_result, adj_justif]]
                orders_phase[power_name].append(order_description)
        phase_data['Orders'] = orders_phase

        # TODO : unclear, probably will need to revise how to enter retreats

        result['GamePhases'].append(phase_data)

        advancement += 1

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

    lowdata.load_servers_config()

    result = export_data(game_name)

    # output
    if json_output is not None:
        output = json.dumps(result, indent=4, ensure_ascii=False)
        with open(json_output, 'w', encoding='utf-8') as file_ptr:
            file_ptr.write(output)


if __name__ == '__main__':
    main()
