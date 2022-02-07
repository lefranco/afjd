#!/usr/bin/env python3


"""
File : export.py

gather information to make json file
"""

import argparse
import typing
import json
import sys
import requests

import lowdata
import database
import games  # noqa: F401 pylint: disable=unused-import
import ownerships
import transitions
import groupings
import tournaments
import votes
import scoring


SESSION = requests.Session()

SOLO_THRESHOLD = 17
IMPOSED_VARIANT = 'standard'

POWER_NAME = [
    'England', 'France', 'Germany', 'Italy', 'Austria', 'Russia', 'Turkey'
]
assert len(POWER_NAME) == 7

CENTER_NAME = [
    'Ank', 'Bel', 'Ber', 'Bre', 'Bud', 'Bul', 'Con', 'Den', 'Edi', 'Gre', 'Hol', 'Kie', 'Lon', 'Lvp', 'Mar', 'Mos',
    'Mun', 'Nap', 'Nwy', 'Par', 'Por', 'Rom', 'Rum', 'Ser', 'Sev', 'Smy', 'Spa', 'Stp', 'Swe', 'Tri', 'Tun', 'Ven',
    'Vie', 'War']
assert len(CENTER_NAME) == 34

TYPE_NAME = ['A', 'F']
assert len(TYPE_NAME) == 2

ZONE_NAME = [
    'ADR', 'AEG', 'Alb', 'Ank', 'Apu', 'Arm', 'BAL', 'BAR', 'Bel', 'Ber', 'BLA', 'Boh', 'BOT', 'Bre', 'Bud', 'Bul',
    'Bur', 'Cly', 'Con', 'Den', 'EAS', 'Edi', 'ENG', 'Fin', 'Gal', 'Gas', 'LYO', 'Gre', 'HEL', 'Hol', 'ION', 'IRI',
    'Kie', 'Lon', 'Lvn', 'Lvp', 'Mar', 'MAO', 'Mos', 'Mun', 'Naf', 'Nap', 'NAO', 'NWG', 'NTH', 'Nwy', 'Par', 'Pic',
    'Pie', 'Por', 'Pru', 'Rom', 'Ruh', 'Rum', 'Ser', 'Sev', 'Sil', 'SKA', 'Smy', 'Spa', 'Stp', 'Swe', 'Syr', 'Tri',
    'Tun', 'Tus', 'TYS', 'Tyr', 'Ukr', 'Ven', 'Vie', 'Wal', 'War', 'WES', 'Yor',
    ['Bul', 'ec'], ['Bul', 'sc'], ['Spa', 'nc'], ['Spa', 'sc'], ['Stp', 'nc'], ['Stp', 'sc']]
assert len(ZONE_NAME) == 81

FRENCH_ZONE_NAME = [
    'ADR', 'EGE', 'ALB', 'ANK', 'APU', 'ARM', 'BAL', 'BAR', 'BEL', 'BER', 'NOI', 'BOH', 'BOT', 'BRE', 'BUD', 'BUL',
    'BOU', 'CLY', 'CON', 'DAN', 'MOR', 'EDI', 'MAN', 'FIN', 'GAL', 'GAS', 'GLI', 'GRE', 'HEL', 'HOL', 'ION', 'IRL',
    'KIE', 'LON', 'LVN', 'LVP', 'MAR', 'ATL', 'MOS', 'MUN', 'AFN', 'NAP', 'ATN', 'MNG', 'NRD', 'NGE', 'PAR', 'PIC',
    'PIE', 'POR', 'PRU', 'ROM', 'RUH', 'ROU', 'SER', 'SEB', 'SIL', 'SKA', 'SMY', 'ESP', 'STP', 'SUE', 'SYR', 'TRI',
    'TUN', 'TOS', 'MTY', 'TYR', 'UKR', 'VEN', 'VIE', 'PGA', 'VAR', 'MOC', 'YOR',
    'BULce', 'BULcs', 'ESPcn', 'ESPcs', 'STPcn', 'STPcs']
assert len(FRENCH_ZONE_NAME) == 81


# TODO : remove this at some point
# for old games, some times other codes were used
TRANSLATE = {'ODE' : 'SEB', 'TOU': 'MAR', 'CAU': 'ARM', 'PAY': 'HOL', 'COR': 'PGA', 'RHE': 'RUH', 'ALP': 'TYR', 'LIO': 'GLI', 'STG': 'IRL', 'NRG': 'MNG', 'NWY': 'NGE', 'AEG': 'EGE'}
assert not set(TRANSLATE.keys()) & set(FRENCH_ZONE_NAME)
assert set(TRANSLATE.values()) <= set(FRENCH_ZONE_NAME)

def export_data(game_id: int, sql_executor: database.SqlExecutor, debug_mode: bool) -> typing.Tuple[bool, str, typing.Optional[typing.Dict[str, typing.Any]]]:
    """ exports all information about a game in format for DIPLOBN """

    # extract
    result: typing.Dict[str, typing.Any] = {}

    # get the game from database
    game = games.Game.find_by_identifier(sql_executor, game_id)
    if game is None:
        return False, "ERROR : Could not find the game with this identifier", None

    # game not standard : abort
    if game.variant != IMPOSED_VARIANT:
        return False, f"Variant of this game is '{game.variant}' - this is not standard Diplomacy!", None

    # game not finished : abort
    if game.current_state == 0:
        return False, "This game is waiting to start - start it first!", None

    # competition = tournament
    result['Competition'] = ''
    game_tournaments = groupings.Grouping.list_by_game_id(sql_executor, game_id)
    if game_tournaments:
        # the id of tournament
        tournament_ids = [g[0] for g in game_tournaments]
        tournament_id = tournament_ids[0]
        tournament = tournaments.Tournament.find_by_identifier(sql_executor, tournament_id)
        if tournament is None:
            return False, "Internal error : This game has a tournament but the tournament could not be found!", None

        result['Competition'] = tournament.name

    # game label : we put the number too
    result['GameLabel'] = f"{game.name} ({game_id})"

    # url
    result['URL'] = f'https://diplomania-gen.fr?game={game.name}'

    # date begin
    # will be filled in later
    result['DateBegan'] = None

    # date end
    # will be filled in later
    result['DateEnded'] = None

    # scoring system
    game_scoring = game.scoring
    result['ScoringSystem'] = game_scoring

    # communication
    if game.nomessage_game and game.nopress_game:
        result['CommunicationType'] = 'None'
    elif game.nomessage_game and game.nopress_game:
        result['CommunicationType'] = 'PublicOnly'
    else:
        result['CommunicationType'] = 'Full'

    # deadline
    result['DeadlineType'] = 'Live' if game.fast else 'Extended'

    # limit of game
    result['LimitType'] = 'Unlimited' if game.nb_max_cycles_to_play == 99 else 'YearLimited'

    # anonymity of game
    result['AnonymityType'] = 'Full' if game.anonymous else 'None'

    # note: just take description
    result['Note'] = game.description
    if game.current_state == 1:
        result['Note'] = "BEWARE GAME WAS EXTRACTED BUT NOT COMPLETED !!!\n" + result['Note']

    players_dict = {}
    if not debug_mode:

        # get all players
        host = lowdata.SERVER_CONFIG['PLAYER']['HOST']
        port = lowdata.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            return False, "Internal error : Failed to access players API!", None

        players_dict = req_result.json()

    # get the players from database
    allocations_found = sql_executor.execute("SELECT * FROM allocations where game_id = ?", (game_id,), need_result=True)
    if not allocations_found:
        return False, "Internal error : Did not find allocations for game", None
    result['Players'] = {}
    for _, player_id, role_id in allocations_found:
        if not role_id > 0:
            continue
        role_num = role_id - 1
        power_name = POWER_NAME[role_num]
        if not game.anonymous and players_dict:
            player_data = players_dict[str(player_id)]
            player_pseudo = player_data['pseudo']
            player_first_name = player_data['first_name']
            player_family_name = player_data['family_name']
            result['Players'][power_name] = f"{player_first_name} {player_family_name} ({player_pseudo})"
        else:
            result['Players'][power_name] = "Unknown!"

    # get the result from database
    result['ResultSummary'] = {}
    game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
    if not game_ownerships:
        return False, "Internal error : Did not find ownerships for game", None
    ownership_dict = {}
    for _, center_num, role_id in game_ownerships:
        ownership_dict[center_num] = role_id

    # how many centers every power has
    center_table = {}
    for role_num, power_name in enumerate(POWER_NAME):
        role_id = role_num + 1
        n_centers = len([_ for c, r in ownership_dict.items() if r == role_id])
        center_table[power_name] = n_centers

    # need to be sorted
    ratings = dict(sorted(center_table.items(), key=lambda i: i[1], reverse=True))

    # use clone of unit in front end (scoring)
    score_table = scoring.scoring(game_scoring, SOLO_THRESHOLD, ratings)  # type: ignore

    # need ranking
    ranking = {}
    for role_num, power_name in enumerate(POWER_NAME):
        role_id = role_num + 1
        ranking[power_name] = 1 + len([_ for p in score_table if score_table[p] > score_table[power_name]])

    # fill information required
    for role_num, power_name in enumerate(POWER_NAME):
        role_id = role_num + 1
        result['ResultSummary'][power_name] = {}
        result['ResultSummary'][power_name]['CenterCount'] = ratings[power_name]

        # this will be superseded later on
        result['ResultSummary'][power_name]['YearOfElimination'] = None

        result['ResultSummary'][power_name]['InGameAtEnd'] = bool(ratings[power_name])
        result['ResultSummary'][power_name]['Score'] = round(score_table[power_name], 2)
        result['ResultSummary'][power_name]['Rank'] = ranking[power_name]

    # get the games phases
    result['GamePhases'] = []
    advancement = 0
    transitions_found = 0
    while True:

        transition = transitions.Transition.find_by_identifier_advancement(sql_executor, game_id, advancement)
        if transition is None:
            break

        transitions_found += 1

        the_situation = json.loads(transition.situation_json)
        ownership_dict = the_situation['ownerships']
        unit_dict = the_situation['units']
        the_orders = json.loads(transition.orders_json)

        # game year : easy
        game_year = 1901 + advancement // 5

        # season : not so easy
        if advancement % 5 in [0, 2, 4]:

            phase_data: typing.Dict[str, typing.Any] = {}

            if advancement % 5 == 0:
                game_season = 1
            elif advancement % 5 == 2:
                game_season = 2
            elif advancement % 5 == 4:
                game_season = 3

            phase_data['Phase'] = game_year * 10 + game_season
            phase_data['Status'] = 'Completed'

            ratings_phase = {}

            for role_num, power_name in enumerate(POWER_NAME):
                role_id = role_num + 1
                n_centers = len([_ for __, r in ownership_dict.items() if r == role_id])
                ratings_phase[power_name] = n_centers

                if result['ResultSummary'][power_name]['YearOfElimination'] is None and not n_centers:
                    result['ResultSummary'][power_name]['YearOfElimination'] = game_year

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

        # this is text information
        report_txt = transition.report_txt
        report_lines = report_txt.split('\n')

        report_header = report_lines[0]
        report_date, _, _ = report_header.partition(' ')

        # so the begin date will be the date of the first report
        if result['DateBegan'] is None:
            result['DateBegan'] = report_date
        # so the end date will be the date of the last report
        result['DateEnded'] = report_date

        # extract justification at end of line
        justification_table: typing.Dict[int, str] = {}
        for line in report_lines:
            if ';' in line:
                words = line.split(' ')
                french_unit = words[1]
                french_unit = TRANSLATE.get(french_unit, french_unit)
                zone_num = FRENCH_ZONE_NAME.index(french_unit) + 1
                _, _, justification = line.partition(';')
                justification_table[zone_num] = justification

        if advancement % 5 in [0, 2, 4]:
            # remember stuff from moves for retreats
            orders_table = {}

        # now extract all the orders

        orders_phase: typing.Dict[str, typing.Any] = {}
        actual_orders_list = the_orders['orders']
        fake_units_list = the_orders['fake_units']
        for role_num, power_name in enumerate(POWER_NAME):
            role_id = role_num + 1
            orders_phase[power_name] = []

            # build the table fake units zone -> type
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
                active_design = ZONE_NAME[int(active) - 1] if isinstance(ZONE_NAME[int(active) - 1], str) else ZONE_NAME[int(active) - 1][0]

                if order == 1:  # move
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description = [active_design, ['m', ZONE_NAME[int(destination) - 1]], adj_data]
                    orders_table[active_design] = order_description
                if order == 2:  # attack support
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description = [active_design, ['sm', ZONE_NAME[int(passive) - 1], ZONE_NAME[int(destination) - 1]], adj_data]
                    orders_table[active_design] = order_description
                if order == 3:  # attack support
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description = [active_design, ['sh', ZONE_NAME[int(passive) - 1]], adj_data]
                    orders_table[active_design] = order_description
                if order == 4:  # hold
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description = [active_design, ['h'], adj_data]
                    orders_table[active_design] = order_description
                if order == 5:  # convoy
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description = [active_design, ['c', ZONE_NAME[int(passive) - 1], ZONE_NAME[int(destination) - 1]], adj_data]
                    orders_table[active_design] = order_description

                if order == 6:  # retreat
                    # we need to complete previously created element
                    order_description = orders_table[active_design]
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description.extend([['m', ZONE_NAME[int(destination) - 1]], adj_data])
                if order == 7:  # disband
                    # we need to complete previously created element
                    order_description = orders_table[active_design]
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description.extend([['d'], adj_data])

                if order == 8:  # build
                    type_ = fake_table[active]
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description = [active_design, ['b', TYPE_NAME[int(type_) - 1]], adj_data]
                if order == 9:  # remove
                    adj_data = [adj_result]
                    if adj_justif:
                        adj_data.extend([adj_justif])
                    order_description = [active_design, ['d'], adj_data]

                if advancement % 5 in [0, 2, 4]:
                    orders_phase[power_name].append(order_description)

        # retreat phases do not exist actually
        if advancement % 5 in [0, 2, 4]:
            phase_data['Orders'] = orders_phase
            result['GamePhases'].append(phase_data)

        last_year = game_year

        advancement += 1

    if not transitions_found:
        return False, "Did not find any transitions for game", None

    # need to mark players that were elimianted last game year
    for role_num, power_name in enumerate(POWER_NAME):
        if result['ResultSummary'][power_name]['YearOfElimination'] is None and not ratings[power_name]:
            result['ResultSummary'][power_name]['YearOfElimination'] = last_year

    phase_data = result['GamePhases'][-1]

    # mark the last phase as 'Game Ended'
    phase_data['Status'] = 'GameEnded'

    # extract votes at the end
    game_votes_list = votes.Vote.list_by_game_id(sql_executor, int(game_id))
    draw_voters = {n for (_, n, v) in game_votes_list if v}
    votes_dict = {}
    for role_num, power_name in enumerate(POWER_NAME):
        role_id = role_num + 1
        votes_dict[power_name] = role_id in draw_voters

    # detect that a draw made unanimity at the end
    if all(votes_dict[p] for p in POWER_NAME if ratings[p]):
        votes_phase = {}
        votes_phase['Passed'] = True
        phase_data['DrawVote'] = votes_phase

    return True, f"Game with id '{game_id}' and name '{game.name}' was exported successfully!", result


def main() -> None:
    """ main : for unitary testing """

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--identifier', required=True, help='Id (number) of game')
    parser.add_argument('-d', '--debug_mode', required=False, action='store_true', help='Debug mode : do not load players')
    parser.add_argument('-J', '--json_output', required=False, help='Output json file')
    args = parser.parse_args()

    game_id = args.identifier
    debug_mode = args.debug_mode
    json_output = args.json_output

    lowdata.load_servers_config()

    # open database
    sql_executor = database.SqlExecutor()
    status, message, result = export_data(game_id, sql_executor, debug_mode)
    # no commit : all accesses were read only
    del sql_executor

    print(message)

    if not status:
        sys.exit(1)

    # output
    if json_output is not None:
        output = json.dumps(result, indent=4, ensure_ascii=False)
        with open(json_output, 'w', encoding='utf-8') as file_ptr:
            file_ptr.write(output)


if __name__ == '__main__':
    main()
