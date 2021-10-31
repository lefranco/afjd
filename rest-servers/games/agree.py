#!/usr/bin/env python3


"""
File : agree.py

Handles the agreement to solve
"""
import typing
import collections
import json
import datetime
import time

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
import lowdata


SESSION = requests.Session()


def adjudicate(game_id: int, names: str, sql_executor: database.SqlExecutor) -> typing.Tuple[bool, str]:
    """ this will perform game adjudication """

    # find the game
    game = games.Game.find_by_identifier(sql_executor, game_id)
    if game is None:
        return False, "ERROR : Could not find the game"

    # evaluate variant
    variant_name = game.variant
    variant_dict = variants.Variant.get_by_name(variant_name)
    if variant_dict is None:
        return False, "ERROR : Could not find the variant"

    variant_dict_json = json.dumps(variant_dict)

    # evaluate situation

    # situation: get ownerships
    ownership_dict = dict()
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
    forbidden_list = list()
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
    orders_list = list()
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
    ownership_dict = dict()
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
    forbidden_list = list()
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
        definitive = definitives.Definitive(int(game_id), role_num, False)
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
    communication_eligibles = list()
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
    communication_orders_list = list()
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

    # date for report in database (actually unused)
    time_stamp = int(time.time())

    # make report
    date_now = datetime.datetime.now()
    date_desc = date_now.strftime('%Y-%m-%d %H:%M:%S')
    report_txt = f"{date_desc}:\n{orders_result_simplified}\n{communication_orders_content_tagged}"

    # put report in database
    report = reports.Report(int(game_id), time_stamp, report_txt)
    report.update_database(sql_executor)

    # put transition in database
    # important : need to be same as when getting situation
    position_transition_dict_json = json.dumps(position_transition_dict)
    orders_transition_dict_json = json.dumps(orders_transition_dict)
    transition = transitions.Transition(int(game_id), game.current_advancement, position_transition_dict_json, orders_transition_dict_json, report_txt)
    transition.update_database(sql_executor)

    # update season
    game.advance()
    game.update_database(sql_executor)

    # update deadline
    game.push_deadline()
    game.update_database(sql_executor)

    return True, "Adjudication performed !"


def post(game_id: int, role_id: int, definitive_value: bool, names: str, sql_executor: database.SqlExecutor) -> typing.Tuple[bool, bool, str]:
    """
    posts an agreement in a game (or a disagreement)
    returns
      * a status (True if no error)
      * an adjudication indicator (True is adjudication ready)
      * a message (explaining the error)
    """

    # update db here
    if role_id == 0:
        definitive = definitives.Definitive(int(game_id), role_id, definitive_value)
        definitive.update_database(sql_executor)  # noqa: F821
    else:
        definitive = definitives.Definitive(int(game_id), role_id, definitive_value)
        definitive.update_database(sql_executor)  # noqa: F821

    if not definitive_value:
        return True, False, "Player does not agree to adjudicate"

    # needed list : those who need to submit orders
    actives_list = actives.Active.list_by_game_id(sql_executor, game_id)
    needed_list = [o[1] for o in actives_list]

    # submissions_list : those who submitted orders
    submissions_list = submissions.Submission.list_by_game_id(sql_executor, game_id)
    submitted_list = [o[1] for o in submissions_list]

    # definitives_list : those who agreed to adjudicate
    definitives_list = definitives.Definitive.list_by_game_id(sql_executor, game_id)
    agreed_list = [o[1] for o in definitives_list]

    # find the game
    game = games.Game.find_by_identifier(sql_executor, game_id)
    if game is None:
        return False, False, "ERROR : Could not find the game"

    if not game.archive:

        # check all submitted
        for role in needed_list:
            if role not in submitted_list:
                return True, False, "Still some orders are missing"

        # check all agreed
        for role in needed_list:
            # ignore for role_id : it may not be in database yet
            if role == role_id:
                continue
            if role not in agreed_list:
                return True, False, "Still some agreements are missing"

    # now we can do adjudication itself

    # get all messages
    adj_messages: typing.List[str] = list()

    # first adjudication
    adj_first_status, adj_message = adjudicate(game_id, names, sql_executor)

    # keep list of messages
    adj_messages.append(adj_message)

    # all possible next adjudications
    while True:

        # one adjudication
        adj_status, adj_message = adjudicate(game_id, names, sql_executor)

        # failed : done
        if not adj_status:
            break

        # keep list of messages
        adj_messages.append(adj_message)

    # note : commit will be done by caller

    return True, adj_first_status, "\n".join(adj_messages)


if __name__ == '__main__':
    assert False, "Do not run this script"
