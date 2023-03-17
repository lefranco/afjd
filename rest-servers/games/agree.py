#!/usr/bin/env python3


"""
File : agree.py

Handles the agreement to solve
"""
import typing
import collections
import json
import time

import sys

import requests

import ownerships
import units
import actives
import submissions
import communication_orders
import orders
import forbiddens
import transitions
import reports
import games
import variants
import database
import definitives
import incidents
import lowdata


SESSION = requests.Session()


def disorder(game_id: int, role_id: int, game: games.Game, variant_dict: typing.Dict[str, typing.Any], names: str, sql_executor: database.SqlExecutor) -> typing.Tuple[bool, bool, str]:
    """ this will put role in disorder for game
         returns status done message
    """

    # check orders are required
    actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
    print(f"{actives_list=}", file=sys.stderr)
    needed_list = [o[1] for o in actives_list]
    print(f"{needed_list=}", file=sys.stderr)
    if role_id not in needed_list:
        return True, False, "This role does not seem to require any orders"

    # check orders are not submitted
    submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
    submitted_list = [o[1] for o in submissions_list]
    if role_id in submitted_list:
        return True, False, "This role seems to have already submitted orders"

    # ======
    # Orders
    # ======

    variant_dict_json = json.dumps(variant_dict)

    # evaluate situation

    # situation: get ownerships
    ownership_dict: typing.Dict[str, int] = {}
    game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
    for _, center_num, role_num in game_ownerships:
        ownership_dict[str(center_num)] = role_num

    # situation: get units
    game_units = units.Unit.list_by_game_id(sql_executor, game_id)
    unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    fake_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
        if fake:
            fake_unit_dict[str(role_num)].append([type_num, zone_num])
        elif region_dislodged_from_num:
            dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
        else:
            unit_dict[str(role_num)].append([type_num, zone_num])

    # situation: get forbiddens
    forbidden_list = []
    game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
    for _, region_num in game_forbiddens:
        forbidden_list.append(region_num)

    situation_dict = {
        'ownerships': ownership_dict,
        'dislodged_ones': dislodged_unit_dict,
        'units': unit_dict,
        'fake_units': fake_unit_dict,
        'forbiddens': forbidden_list,
    }
    situation_dict_json = json.dumps(situation_dict)

    json_dict = {
        'variant': variant_dict_json,
        'advancement': game.current_advancement,
        'situation': situation_dict_json,
        'names': names,
        'role': role_id,
    }

    # post to disorderer
    host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
    port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
    url = f"{host}:{port}/disorder"
    req_result = SESSION.post(url, data=json_dict)

    if 'msg' in req_result.json():
        submission_report = req_result.json()['msg']
    else:
        submission_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

    # adjudication failed
    if req_result.status_code != 201:
        print(f"ERROR from server  : {req_result.text}")
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        return False, False, f"Failed to submit civil disorder {message} : {submission_report}"

    # ok so orders are made up ok

    orders_default = req_result.json()['orders_default']

    print(f"disorderer returns {orders_default=}", file=sys.stderr)

    # store orders

    # purge previous

    previous_orders = orders.Order.list_by_game_id_role_num(sql_executor, int(game_id), role_id)

    # purge
    for (_, role_num, _, zone_num, _, _) in previous_orders:
        order = orders.Order(int(game_id), role_num, 0, zone_num, 0, 0)
        order.delete_database(sql_executor)

    # insert new ones
    for the_order in orders_default:
        order = orders.Order(int(game_id), 0, 0, 0, 0, 0)
        order.load_json(the_order)
        order.update_database(sql_executor)

        # special case : build : create a fake unit
        # this was done before submitting
        # we tolerate that some extra fake unit may persist from previous submission

    # insert this submission
    submission = submissions.Submission(int(game_id), int(role_id))
    submission.update_database(sql_executor)

    # ======
    # Agreement
    # ======

    definitive_value = 1

    # update db here for agreement
    definitive = definitives.Definitive(int(game_id), int(role_id), definitive_value)
    definitive.update_database(sql_executor)  # noqa: F821

    # note : commit will be done by caller

    return True, True, "Civil disorder orders inserted"


def adjudicate(game_id: int, game: games.Game, variant_data: typing.Dict[str, typing.Any], names: str, sql_executor: database.SqlExecutor) -> typing.Tuple[bool, str]:
    """ this will perform game adjudication """

    # check game over
    if game.game_over():
        return False, "INFORMATION : game over !"

    variant_dict_json = json.dumps(variant_data)

    # evaluate situation

    # situation: get ownerships
    ownership_dict = {}
    game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
    for _, center_num, role_num in game_ownerships:
        ownership_dict[str(center_num)] = role_num

    # situation: get units
    game_units = units.Unit.list_by_game_id(sql_executor, game_id)
    unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    fake_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    for _, type_num, zone_num, role_num, region_dislodged_from_num, fake in game_units:
        if fake:
            fake_unit_dict[str(role_num)].append([type_num, zone_num])
        elif region_dislodged_from_num:
            dislodged_unit_dict[str(role_num)].append([type_num, zone_num, region_dislodged_from_num])
        else:
            unit_dict[str(role_num)].append([type_num, zone_num])

    # situation: get forbiddens
    forbidden_list = []
    game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
    for _, region_num in game_forbiddens:
        forbidden_list.append(region_num)

    situation_dict = {
        'ownerships': ownership_dict,
        'dislodged_ones': dislodged_unit_dict,
        'units': unit_dict,
        'fake_units': fake_unit_dict,
        'forbiddens': forbidden_list,
    }
    situation_dict_json = json.dumps(situation_dict)

    # evaluate orders
    orders_list = []
    orders_from_game = orders.Order.list_by_game_id(sql_executor, game_id)
    for _, role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num in orders_from_game:
        orders_list.append([role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num])
    orders_list_json = json.dumps(orders_list)

    json_dict = {
        'variant': variant_dict_json,
        'advancement': game.current_advancement,
        'situation': situation_dict_json,
        'orders': orders_list_json,
        'names': names,
    }

    # post to solver
    host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
    port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
    url = f"{host}:{port}/solve"
    req_result = SESSION.post(url, data=json_dict)

    if 'msg' in req_result.json():
        adjudication_report = req_result.json()['msg']
    else:
        adjudication_report = "\n".join([req_result.json()['stderr'], req_result.json()['stdout']])

    # adjudication failed
    if req_result.status_code != 201:
        print(f"ERROR from server  : {req_result.text}")
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        return False, f"ERROR : Failed to adjudicate {message} : {adjudication_report}"

    # adjudication successful : backup for transition archive

    # position for transition

    # get ownerships
    ownership_dict = {}
    game_ownerships = ownerships.Ownership.list_by_game_id(sql_executor, game_id)
    for _, center_num, role_num in game_ownerships:
        ownership_dict[str(center_num)] = role_num

    # get units
    unit_dict2: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    dislodged_unit_dict2: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    game_units = units.Unit.list_by_game_id(sql_executor, game_id)
    for _, type_num, zone_num, role_num, zone_dislodged_from_num, fake in game_units:
        if fake:
            pass  # this is confidential
        elif zone_dislodged_from_num:
            dislodged_unit_dict2[str(role_num)].append([type_num, zone_num, zone_dislodged_from_num])
        else:
            unit_dict2[str(role_num)].append([type_num, zone_num])

    # get forbiddens
    forbidden_list = []
    game_forbiddens = forbiddens.Forbidden.list_by_game_id(sql_executor, game_id)
    for _, region_num in game_forbiddens:
        forbidden_list.append(region_num)

    position_transition_dict = {
        'ownerships': ownership_dict,
        'dislodged_ones': dislodged_unit_dict2,
        'units': unit_dict2,
        'forbiddens': forbidden_list,
    }

    # orders for transition
    orders_transition_list = orders.Order.list_by_game_id(sql_executor, game_id)

    units_transition_list = units.Unit.list_by_game_id(sql_executor, game_id)
    fake_units_transition_list = [u for u in units_transition_list if u[5]]

    orders_transition_dict = {
        'orders': orders_transition_list,
        'fake_units': fake_units_transition_list,
    }

    # extract new position
    situation_result = req_result.json()['situation_result']
    the_ownerships = situation_result['ownerships']
    the_units = situation_result['units']
    the_dislodged_units = situation_result['dislodged_ones']
    the_forbiddens = situation_result['forbiddens']

    # extract actives
    the_active_roles = req_result.json()['active_roles']

    # store new position in database

    # purge

    # purge previous ownerships
    for (_, center_num, role_num) in ownerships.Ownership.list_by_game_id(sql_executor, int(game_id)):
        ownership = ownerships.Ownership(int(game_id), center_num, role_num)
        ownership.delete_database(sql_executor)

    # purge previous units
    for (_, type_num, role_num, zone_num, zone_dislodged_from_num, fake) in units.Unit.list_by_game_id(sql_executor, int(game_id)):
        unit = units.Unit(int(game_id), type_num, role_num, zone_num, zone_dislodged_from_num, fake)
        unit.delete_database(sql_executor)

    # purge previous forbiddens
    for (_, center_num) in forbiddens.Forbidden.list_by_game_id(sql_executor, int(game_id)):
        forbidden = forbiddens.Forbidden(int(game_id), center_num)
        forbidden.delete_database(sql_executor)

    # purge actives
    for (_, role_num) in actives.Active.list_by_game_id(sql_executor, int(game_id)):
        active = actives.Active(int(game_id), role_num)
        active.delete_database(sql_executor)

    # purge submissions
    for (_, role_num) in submissions.Submission.list_by_game_id(sql_executor, int(game_id)):
        submission = submissions.Submission(int(game_id), role_num)
        submission.delete_database(sql_executor)

    # clear agreements
    for (_, role_num, _) in definitives.Definitive.list_by_game_id(sql_executor, int(game_id)):
        definitive = definitives.Definitive(int(game_id), role_num, 0)
        definitive.delete_database(sql_executor)

    # insert

    # insert new ownerships
    for center_num, role in the_ownerships.items():
        ownership = ownerships.Ownership(int(game_id), int(center_num), role)
        ownership.update_database(sql_executor)

    # insert new units
    for role_num, the_unit_role in the_units.items():
        for type_num, zone_num in the_unit_role:
            unit = units.Unit(int(game_id), type_num, zone_num, int(role_num), 0, 0)
            unit.update_database(sql_executor)

    # insert new dislodged units
    for role_num, the_unit_role in the_dislodged_units.items():
        for type_num, zone_num, zone_dislodged_from_num in the_unit_role:
            unit = units.Unit(int(game_id), type_num, zone_num, int(role_num), zone_dislodged_from_num, 0)
            unit.update_database(sql_executor)

    # insert new forbiddens
    for region_num in the_forbiddens:
        forbidden = forbiddens.Forbidden(int(game_id), region_num)
        forbidden.update_database(sql_executor)

    # insert new actives
    for role_num in the_active_roles:
        active = actives.Active(int(game_id), int(role_num))
        active.update_database(sql_executor)

    # keep a copy of orders eligible for communication orders
    communication_eligibles = []
    for (_, _, order_type, zone_num, _, _) in orders.Order.list_by_game_id(sql_executor, game_id):
        if order_type in [4, 7]:
            communication_eligibles.append(zone_num)

    # remove orders
    for (_, rol_id, _, zone_num, _, _) in orders.Order.list_by_game_id(sql_executor, game_id):
        order = orders.Order(int(game_id), rol_id, 0, zone_num, 0, 0)
        order.delete_database(sql_executor)

    # extract new report
    orders_result = req_result.json()['orders_result']
    orders_result_simplified = orders_result

    # --------------------------
    # get communication orders

    # evaluate communication_orders (only the units with a hld of disperse order)
    communication_orders_list = []
    communication_orders_from_game = communication_orders.CommunicationOrder.list_by_game_id(sql_executor, game_id)
    for _, role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num in communication_orders_from_game:
        if active_unit_zone_num in communication_eligibles:
            communication_orders_list.append([role_num, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num])

    communication_orders_list_json = json.dumps(communication_orders_list)

    json_dict = {
        'variant': variant_dict_json,
        'advancement': game.current_advancement,
        'situation': situation_dict_json,
        'orders': communication_orders_list_json,
        'names': names,
    }

    # post to solver (for print)
    host = lowdata.SERVER_CONFIG['SOLVER']['HOST']
    port = lowdata.SERVER_CONFIG['SOLVER']['PORT']
    url = f"{host}:{port}/print"
    req_result = SESSION.post(url, data=json_dict)

    # print failed
    if req_result.status_code != 201:
        print(f"ERROR from server  : {req_result.text}")
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        return False, f"ERROR : Failed to print communication orders {message}"

    # extract printed orders
    communication_orders_content = req_result.json()['orders_content']
    communication_orders_content_tagged = '\n'.join([f"* {ll}" for ll in communication_orders_content.split('\n')])

    # remove communication orders
    for (_, rol_id, _, zone_num, _, _) in communication_orders.CommunicationOrder.list_by_game_id(sql_executor, game_id):
        communication_order = communication_orders.CommunicationOrder(int(game_id), rol_id, 0, zone_num, 0, 0)
        communication_order.delete_database(sql_executor)

    # --------------------------

    # make report
    report_txt = f"{orders_result_simplified}\n{communication_orders_content_tagged}"

    # date for report in database
    time_stamp = int(time.time())

    # put report in database
    report = reports.Report(int(game_id), time_stamp, report_txt)
    report.update_database(sql_executor)

    # put transition in database
    # important : need to be same as when getting situation
    position_transition_dict_json = json.dumps(position_transition_dict)
    orders_transition_dict_json = json.dumps(orders_transition_dict)
    transition = transitions.Transition(int(game_id), game.current_advancement, time_stamp, position_transition_dict_json, orders_transition_dict_json, report_txt)
    transition.update_database(sql_executor)

    # update season
    game.advance()
    game.update_database(sql_executor)

    return True, f"Adjudication performed for game {game.name} season {game.current_advancement}!"


def fake_post(game_id: int, role_id: int, definitive_value: int, names: str, sql_executor: database.SqlExecutor) -> typing.Tuple[bool, bool, bool, int, bool, str]:
    """
    posts an agreement in a game (or a disagreement)
    returns
      * a status (True if no error)
      * a late indicator (True if incident created)
      * an unsafe indicator (True player is unsafe - not protected against delay)
      * a missing code 0 unknown 1 orders 2 agreements 3 only your agreement
      * an adj_status adjudication indicator (True is adjudication was done)
      * a debug message (more detailed information )
    """

    status = True
    late = False
    unsafe = False
    missing = 0
    adjudicated = False
    debug_message = ""

    # what was before ?
    definitive_before = 0
    definitive_before_list = definitives.Definitive.list_by_game_id_role_num(sql_executor, game_id, role_id)
    if definitive_before_list:
        definitive_before_element = definitive_before_list[0]
        definitive_before = definitive_before_element[2]

    # find the game
    game = games.Game.find_by_identifier(sql_executor, game_id)
    if game is None:
        status = False
        debug_message = "ERROR : Could not find the game"
        return status, late, unsafe, missing, adjudicated, debug_message

    # are we after deadline ?
    after_deadline = game.past_deadline()

    # commute value if after deadline
    if after_deadline:
        if definitive_value == 2:
            definitive_value = 1

    # update db here for agreement
    definitive = definitives.Definitive(int(game_id), role_id, definitive_value)
    definitive.update_database(sql_executor)  # noqa: F821

    # no agreement : this is the end
    if definitive_value == 0:
        unsafe = True
        debug_message = "Player does not agree to adjudicate"
        return status, late, unsafe, missing, adjudicated, debug_message

    # if incident created
    late = False

    if after_deadline:

        # do we have a transition disagree -> agree (means actual submission of orders)
        if definitive_before == 0:

            # there cannot be delays for archive games
            if not game.archive:

                # here we are : insert this incident

                advancement = game.current_advancement
                player_id = game.get_role(sql_executor, int(role_id))
                if player_id is None:
                    status = False
                    debug_message = "ERROR : Could not find the player identifier"
                    return status, late, unsafe, missing, adjudicated, debug_message

                duration = game.hours_after_deadline()
                incident = incidents.Incident(int(game_id), int(role_id), advancement, player_id, duration)
                incident.update_database(sql_executor)  # noqa: F821

                late = True

    # needed list : those who need to submit orders
    actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
    needed_list = [o[1] for o in actives_list]

    # submitted_list : those who submitted orders
    submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
    submitted_list = [o[1] for o in submissions_list]

    # agreed_now_list : those who agreed to adjudicate now
    definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
    agreed_now_list = [o[1] for o in definitives_list if o[2] == 1]

    if not game.archive:

        # check all submitted
        for role in needed_list:
            if role not in submitted_list:
                missing = 1
                debug_message = "Still some orders are missing"
                return status, late, unsafe, missing, adjudicated, debug_message

        # check all others agreed
        for role in needed_list:
            # ignore for role_id : dealt with later
            if role == role_id:
                continue
            if role not in agreed_now_list:
                missing = 2
                debug_message = "Still some agreements from others are missing"
                return status, late, unsafe, missing, adjudicated, debug_message

        # check we are not last with just agree but after
        if definitive_value == 2:
            # we must be before deadline (otherwise 2 would have been muted to 1)
            missing = 3
            debug_message = "Only your agreement is missing!"
            return status, late, unsafe, missing, adjudicated, debug_message

    # evaluate variant
    variant_name = game.variant
    variant_data = variants.Variant.get_by_name(variant_name)
    if variant_data is None:
        status = False
        debug_message = "ERROR : Could not find the variant"
        return status, late, unsafe, missing, adjudicated, debug_message

    # now we can do adjudication itself

    # first adjudication
    adjudicated, adj_message = adjudicate(game_id, game, variant_data, names, sql_executor)

    if not adjudicated:
        debug_message = f"Failed first adjudication {adj_message} !"
        return status, late, unsafe, missing, adjudicated, debug_message

    # get all messages
    debug_messages: typing.List[str] = []

    # keep list of messages
    debug_messages.append(adj_message)

    # all possible next adjudications
    while True:

        # civil disorder orders
        for role_id1 in variant_data['disorder']:
            print(f"calling agree.disorder for {role_id1=}", file=sys.stderr)
            status, _, message = disorder(game_id, role_id1, game, variant_data, names, sql_executor)  # noqa: F821
            print(f"{status=} result {message=}", file=sys.stderr)
            # error disordering : stop now (safer, but should not happen)
            if not status:
                debug_messages.append(f"Failed to set power {role_id1} in disorder : {message}")
                debug_message = "\n".join(debug_messages)
                return status, late, unsafe, missing, adjudicated, debug_message

        # needed list : those who need to submit orders
        actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
        needed_list = [o[1] for o in actives_list]

        # submitted_list : those who submitted orders
        submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
        submitted_list = [o[1] for o in submissions_list]

        # agreed_now_list : those who agreed to adjudicate now
        definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
        agreed_now_list = [o[1] for o in definitives_list if o[2] == 1]

        # can we proceed
        orders_needed = False
        for role in needed_list:
            if role not in submitted_list or role not in agreed_now_list:
                orders_needed = True
                break

        if orders_needed:
            debug_messages.append("Orders needed now!")
            break

        # one more adjudication
        adj_status, adj_message = adjudicate(game_id, game, variant_data, names, sql_executor)

        # keep list of messages
        debug_messages.append(adj_message)

        # error adjudicating : stop now (safer, but should not happen)
        if not adj_status:
            status = False
            debug_message = "\n".join(debug_messages)
            return status, late, unsafe, missing, adjudicated, debug_message

    # update deadline
    game.push_deadline()
    game.update_database(sql_executor)

    debug_messages.append("Deadline adjusted!")

    # note : commit will be done by caller

    debug_message = "\n".join(debug_messages)
    return status, late, unsafe, missing, adjudicated, debug_message


if __name__ == '__main__':
    assert False, "Do not run this script"
