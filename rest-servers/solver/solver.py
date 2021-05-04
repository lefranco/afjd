#!/usr/bin/env python3

"""
File : solver.py

Calls the engine
"""

import typing
import tempfile
import os
import shutil
import subprocess
import collections


import flask_restful  # type: ignore

SEASON_NAME_TABLE = ["PRINTEMPS", "ETE", "AUTOMNE", "HIVER", "BILAN"]


def build_variant_file(variant: typing.Dict[str, typing.Any], names: typing.Dict[str, typing.Any]) -> typing.List[str]:
    """ This will build the diplo.dat file """

    result: typing.List[str] = list()

    result.append("; -------")
    result.append("; ANNEEZERO")
    result.append("; -------")
    year_zero = variant['year_zero']
    result.append(f"ANNEEZERO {year_zero}")

    result.append("; -------")
    result.append("; PAYS")
    result.append("; -------")
    number_roles = int(variant['roles']['number'])
    assert len(names['roles']) == number_roles + 1
    for role_num in range(1, number_roles + 1):
        name, adjective, letter = names['roles'][str(role_num)]
        result.append(f"PAYS {name} x{letter} {adjective}")

    result.append("; -------")
    result.append("; REGIONS")
    result.append("; -------")
    region_names = [r for r in names['zones'].values() if r]
    assert len(region_names) == len(variant['regions'])
    result.append("; cotes")
    for num_region, region in enumerate(region_names):
        if variant['regions'][num_region] == 1:
            result.append(f"REGION {region}")
    result.append("; terre")
    for num_region, region in enumerate(region_names):
        if variant['regions'][num_region] == 2:
            result.append(f"REGION {region}")
    result.append("; mer")
    for num_region, region in enumerate(region_names):
        if variant['regions'][num_region] == 3:
            result.append(f"REGION {region}")

    result.append("; -------")
    result.append("; CENTRES")
    result.append("; -------")
    for center_num in variant['centers']:
        region_name = region_names[center_num - 1]
        result.append(f"CENTRE {region_name}")

    result.append("; -------")
    result.append("; centres de depart")
    result.append("; -------")
    for role_num, centers in enumerate(variant['start_centers']):
        for start_center_num in centers:
            # role
            role, _, _ = names['roles'][str(role_num + 1)]
            # center
            center_num = variant['centers'][start_center_num - 1]
            region_name = region_names[center_num - 1]
            result.append(f"CENTREDEPART {role} {region_name}")
        result.append("")

    result.append("; -------")
    result.append("; ZONES")
    result.append("; -------")
    for num_region, region in enumerate(region_names):
        if variant['regions'][num_region] == 1:
            result.append(f"ZONE COTE {region}")
    for num_region, coast_type_num in variant['coastal_zones']:
        region = region_names[num_region - 1]
        coast = names['coasts'][str(coast_type_num)]
        result.append(f"ZONE COTE {region} {coast}")
    for num_region, region in enumerate(region_names):
        if variant['regions'][num_region] == 2:
            result.append(f"ZONE TERRE {region}")
    for num_region, region in enumerate(region_names):
        if variant['regions'][num_region] == 3:
            result.append(f"ZONE MER {region}")

    assert len(names['zones']) == len(variant['regions']) + len(variant['coastal_zones'])
    zone_names = [r for r in names['zones'].values() if r]
    zone_names += [f"{names['zones'][str(r)]}{names['coasts'][str(c)]}" for r, c in variant['coastal_zones']]

    result.append("; -------")
    result.append("; voisinage par les armees")
    result.append("; -------")
    for zone_from, zones_to in variant['neighbouring'][0].items():
        for zone_to in zones_to:
            zone_from_name = zone_names[int(zone_from) - 1]
            zone_to_name = zone_names[zone_to - 1]
            result.append(f"ARMEEVOISIN {zone_from_name} {zone_to_name}")
    result.append("; -------")
    result.append("; voisinage par les flottes")
    result.append("; -------")
    for zone_from, zones_to in variant['neighbouring'][1].items():
        for zone_to in zones_to:
            zone_from_name = zone_names[int(zone_from) - 1]
            zone_to_name = zone_names[zone_to - 1]
            result.append(f"FLOTTEVOISIN {zone_from_name} {zone_to_name}")

    result.append("; -------")
    result.append("; ELOIGNEMENTS")
    result.append("; -------")
    for unit_type, distances_role in enumerate(variant['distancing']):
        unit_name = "A" if unit_type == 0 else "F"
        for role_num, distances in enumerate(distances_role):
            role_name, _, _ = names['roles'][str(role_num + 1)]
            for zone_num, distance in distances.items():
                zone_name = zone_names[int(zone_num) - 1]
                result.append(f"ELOIGNEMENT {unit_name} {role_name} {zone_name} {distance}")

    result.append("")
    return result


def build_situation_file(advancement: int, situation: typing.Dict[str, typing.Any], variant: typing.Dict[str, typing.Any], names: typing.Dict[str, typing.Any]) -> typing.List[str]:
    """ This will build the situ.dat file """

    result: typing.List[str] = list()

    year_zero = variant['year_zero']
    season = advancement % len(SEASON_NAME_TABLE)
    season_name = SEASON_NAME_TABLE[season]
    year = year_zero + 1 + advancement // len(SEASON_NAME_TABLE)
    result.append(f"SAISON {season_name} {year}")
    result.append(f"SAISONMODIF HIVER {year_zero}")  # not used actually

    region_names = [r for r in names['zones'].values() if r]
    zone_names = [r for r in names['zones'].values() if r]
    zone_names += [f"{names['zones'][str(r)]}{names['coasts'][str(c)]}" for r, c in variant['coastal_zones']]

    # build a table zone name -> region name
    region_table = dict()
    for zone in names['zones'].values():
        if zone:
            region_table[zone] = zone
    for region, coast in variant['coastal_zones']:
        region_table[f"{names['zones'][str(region)]}{names['coasts'][str(coast)]}"] = f"{names['zones'][str(region)]}"

    result.append("")
    result.append("; LES POSSESSIONS")
    result.append("")

    for center_num, role_num in situation['ownerships'].items():
        role_name, _, _ = names['roles'][str(role_num)]
        center_num = variant['centers'][int(center_num) - 1]
        region_name = region_names[center_num - 1]
        result.append(f"POSSESSION {role_name} {region_name}")

    result.append("")
    result.append("; LES UNITES")
    result.append("")

    # normal units
    result.append("; non delogees")
    executioner_table = dict()
    for role_num, units in situation['units'].items():
        role_name, _, _ = names['roles'][str(role_num)]

        for unit_type, zone_num in units:

            unit_name = "A" if unit_type == 1 else "F"
            zone_name = zone_names[int(zone_num) - 1]

            # put line
            result.append(f"UNITE {unit_name} {role_name} {zone_name}")

            # keep a note for building retreat declaration
            region = region_table[zone_name]
            executioner_table[region] = (unit_name, role_name, zone_name)

    # dislodged units
    result.append("; delogees")
    for role_num, dislodged_units in situation['dislodged_ones'].items():
        role_name, _, _ = names['roles'][str(role_num)]

        for unit_type, zone_num, _ in dislodged_units:

            unit_name = "A" if unit_type == 1 else "F"
            zone_name = zone_names[int(zone_num) - 1]

            # put line
            result.append(f"UNITE {unit_name} {role_name} {zone_name}")

    result.append("")
    result.append("; LES DELOGEES")
    result.append("")

    for role_num, dislodged_units in situation['dislodged_ones'].items():
        role_name, _, _ = names['roles'][str(role_num)]

        for unit_type, zone_num, zone_from_num in dislodged_units:

            unit_name = "A" if unit_type == 1 else "F"
            zone_name = zone_names[int(zone_num) - 1]

            # executioner occupant of region not dislodged
            region = region_table[zone_name]
            unit_from_name, role_from_name, zone_from_name = executioner_table[region]

            origin_zone_from_name = zone_names[int(zone_from_num) - 1]

            # put line
            result.append(f"DELOGEE {unit_name} {role_name} {zone_name} BOURREAU {unit_from_name} {role_from_name} {zone_from_name} ORIGINE {origin_zone_from_name}")

    result.append("")
    result.append("; LES INTERDITS")
    result.append("")

    for region_num in situation['forbiddens']:
        region_name = region_names[region_num - 1]
        result.append(f"INTERDIT {region_name}")

    result.append("")

    return result


def build_orders_file(orders: typing.List[typing.List[int]], situation: typing.Dict[str, typing.Any], variant: typing.Dict[str, typing.Any], names: typing.Dict[str, typing.Any]) -> typing.List[str]:
    """ This will build the orders.txt file """

    result: typing.List[str] = list()

    zone_names = [r for r in names['zones'].values() if r]
    zone_names += [f"{names['zones'][str(r)]}{names['coasts'][str(c)]}" for r, c in variant['coastal_zones']]

    unit_type_table = dict()
    for _, units in situation['units'].items():
        for unit_type, zone_num in units:
            unit_name = "A" if unit_type == 1 else "F"
            unit_type_table[zone_num] = unit_name

    dislodged_unit_type_table = dict()
    for _, dislodged_units in situation['dislodged_ones'].items():
        for unit_type, zone_num, _ in dislodged_units:
            unit_name = "A" if unit_type == 1 else "F"
            dislodged_unit_type_table[zone_num] = unit_name

    fake_unit_type_table = dict()
    for _, fake_units in situation['fake_units'].items():
        for unit_type, zone_num in fake_units:
            fake_unit_name = "A" if unit_type == 1 else "F"
            fake_unit_type_table[zone_num] = fake_unit_name

    previous_role_name = None
    for order in orders:
        if len(order) != 5:
            flask_restful.abort(400, msg="ERROR - need 5 elements in order")
        role_num, type_order, active_zone_num, passive_zone_num, dest_zone_num = order
        if 'roles' not in names:
            flask_restful.abort(400, msg="ERROR - 'roles' missing in names[]")
        if str(role_num) not in names['roles']:
            flask_restful.abort(400, msg=f"ERROR - {role_num} missing in names['roles']")
        role_name, _, _ = names['roles'][str(role_num)]
        if role_name != previous_role_name:
            result.append(role_name)
            previous_role_name = role_name

        if type_order in [8]:  # build
            if active_zone_num not in fake_unit_type_table:
                flask_restful.abort(400, msg="ERROR - active_zone_num (build) is wrong")
            active_type = fake_unit_type_table[active_zone_num]
        elif type_order in [6, 7]:  # retreat
            if active_zone_num not in dislodged_unit_type_table:
                flask_restful.abort(400, msg="ERROR - active_zone_num (retreat) is wrong")
            active_type = dislodged_unit_type_table[active_zone_num]
        else:  # not build nor retreat
            if active_zone_num not in unit_type_table:
                flask_restful.abort(400, msg="ERROR - active_zone_num (not build nor retreat) is wrong")
            active_type = unit_type_table[active_zone_num]

        if not int(active_zone_num) - 1 < len(zone_names):
            flask_restful.abort(400, msg="ERROR - active_zone_num is wrong")
        active_zone = zone_names[int(active_zone_num) - 1]

        if passive_zone_num:
            if not int(passive_zone_num) - 1 < len(zone_names):
                flask_restful.abort(400, msg="ERROR - passive_zone_num is wrong")
            passive_zone = zone_names[int(passive_zone_num) - 1]
        else:
            passive_zone = None

        if dest_zone_num:
            if not int(dest_zone_num) - 1 < len(zone_names):
                flask_restful.abort(400, msg="ERROR - dest_zone_num is wrong")
            dest_zone = zone_names[int(dest_zone_num) - 1]
        else:
            dest_zone = None

        if type_order == 1:  # move
            result.append(f"{active_type} {active_zone} - {dest_zone}")
        elif type_order == 2:  # offensive support
            result.append(f"{active_type} {active_zone} S {passive_zone} - {dest_zone}")
        elif type_order == 3:  # defensive support
            result.append(f"{active_type} {active_zone} S {passive_zone}")
        elif type_order == 4:  # hold
            result.append(f"{active_type} {active_zone} H")
        elif type_order == 5:  # convoy
            result.append(f"{active_type} {active_zone} C {passive_zone} - {dest_zone}")
        elif type_order == 6:  # retreat
            result.append(f"{active_type} {active_zone} R {dest_zone}")
        elif type_order == 7:  # disband
            result.append(f"{active_type} {active_zone} A")
        elif type_order == 8:  # build
            result.append(f"+ {active_type} {active_zone}")
        elif type_order == 9:  # remove
            result.append(f"- {active_type} {active_zone}")
        else:
            flask_restful.abort(400, msg="ERROR - type_order is wrong")

    result.append("")
    return result


def read_situation(situation_result_content: typing.List[str], variant: typing.Dict[str, typing.Any], names: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """ This will read the situ_result.dat file """

    region_names = [r.upper() for r in names['zones'].values() if r]
    zone_names = [r.upper() for r in names['zones'].values() if r]
    zone_names += [f"{names['zones'][str(r)]}{names['coasts'][str(c)]}".upper() for r, c in variant['coastal_zones']]
    role_names = [v[0].upper() for k, v in names['roles'].items() if int(k)]
    center_table = variant['centers']
    type_names = ["A", "F"]

    ownership_dict: typing.Dict[str, typing.Any] = dict()
    unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    dislodged_unit_dict: typing.Dict[str, typing.List[typing.List[int]]] = collections.defaultdict(list)
    forbidden_list: typing.List[int] = list()

    for line in situation_result_content:

        # remove endline
        line = line.strip()

        # ignore empty lines
        if not line:
            continue

        # ignore comments
        if line.startswith(";"):
            continue

        # split in list
        tokens = line.split(" ")

        if tokens[0] == "POSSESSION":
            role_num = role_names.index(tokens[1].upper()) + 1
            region_num = region_names.index(tokens[2].upper()) + 1
            center_num = center_table.index(region_num) + 1
            ownership_dict[str(center_num)] = role_num

        if tokens[0] == "UNITE":
            type_num = type_names.index(tokens[1].upper()) + 1
            role_num = role_names.index(tokens[2].upper()) + 1
            zone_num = zone_names.index(tokens[3].upper()) + 1
            unit_dict[str(role_num)].append([type_num, zone_num])

        if tokens[0] == "INTERDIT":
            region_num = region_names.index(tokens[1].upper()) + 1
            forbidden_list.append(region_num)

        if tokens[0] == "DELOGEE":
            type_num = type_names.index(tokens[1].upper()) + 1
            role_num = role_names.index(tokens[2].upper()) + 1
            zone_num = zone_names.index(tokens[3].upper()) + 1
            assert tokens[4].upper() == "BOURREAU"
            _ = type_names.index(tokens[5].upper()) + 1
            _ = role_names.index(tokens[6].upper()) + 1
            _ = zone_names.index(tokens[7].upper()) + 1
            assert tokens[8].upper() == "ORIGINE"
            zone_dislodged_from_num = zone_names.index(tokens[9].upper()) + 1
            dislodged_unit_dict[str(role_num)].append([type_num, zone_num, zone_dislodged_from_num])

    # important : we remove units that are dislodged
    for role_num_str, dislodged_units in dislodged_unit_dict.items():
        for type_num, zone_num, _ in dislodged_units:
            unit_dict[role_num_str].remove([type_num, zone_num])

    return {
        'ownerships': ownership_dict,
        'dislodged_ones': dislodged_unit_dict,
        'units': unit_dict,
        'forbiddens': forbidden_list,
    }


def read_orders(orders_result_content: typing.List[str], variant: typing.Dict[str, typing.Any], names: typing.Dict[str, typing.Any], role_num: int) -> typing.List[typing.Dict[str, typing.Any]]:
    """ This will read the orders_result.txt file """

    region_names = [r.upper() for r in names['zones'].values() if r]
    zone_names = [r.upper() for r in names['zones'].values() if r]
    zone_names += [f"{names['zones'][str(r)]}{names['coasts'][str(c)]}".upper() for r, c in variant['coastal_zones']]
    role_names = [v[0].upper() for k, v in names['roles'].items() if int(k)]
    center_table = variant['centers']
    type_names = ["A", "F"]

    orders_list: typing.List[int] = list()

    for line in orders_result_content:

        # remove endline
        line = line.strip()

        # ignore empty lines
        if not line:
            continue

        # ignore comments
        if line.startswith(";"):
            continue

        # split in list
        tokens = line.split(" ")

        if tokens[0] == "-":
            zone_num = zone_names.index(tokens[2].upper()) + 1
            order_type = 9
        else:
            zone_num = zone_names.index(tokens[1].upper()) + 1
            if tokens[2] == "H":
                order_type = 4
            if tokens[2] == "A":
                order_type = 7

        order = {
            'active_unit': {
                'role' : role_num,
                'zone' : zone_num
            },
            'order_type' : order_type,
        }

        orders_list.append(order)

    return orders_list


def read_actives(active_roles_content: typing.List[str], names: typing.Dict[str, typing.Any]) -> typing.List[int]:
    """ This will read the situ_result.dat file """

    active_list: typing.List[int] = list()

    role_names = [v[0].upper() for k, v in names['roles'].items() if int(k)]

    for line in active_roles_content:

        # remove endline
        line = line.strip()

        # ignore empty lines
        if not line:
            continue

        # ignore comments
        if line.startswith(";"):
            continue

        # split in list
        tokens = line.split(" ")

        # extract active countries/roles
        for token in tokens:
            role_num = role_names.index(token.upper()) + 1
            active_list.append(role_num)

    return active_list


def solve(variant: typing.Dict[str, typing.Any], advancement: int, situation: typing.Dict[str, typing.Any], orders: typing.List[typing.List[int]], role: typing.Optional[int], names: typing.Dict[str, typing.Any]) -> typing.Tuple[int, str, str, typing.Optional[typing.Dict[str, typing.Any]], typing.Optional[str], typing.Optional[typing.List[int]]]:
    """ returns errorcode, stderr, stdout, sit-result(dict), ord-result(text), actives-roles(text/list?) """

    diplo_dat_content = build_variant_file(variant, names)
    situation_content = build_situation_file(advancement, situation, variant, names)
    orders_content = build_orders_file(orders, situation, variant, names)

    with tempfile.TemporaryDirectory() as tmpdirname:

        # make DIPLOCOM
        os.mkdir(f"{tmpdirname}/DIPLOCOM")

        # copy message file
        shutil.copyfile("./messages/DIPLO.fr.TXT", f"{tmpdirname}/DIPLOCOM/DIPLO.fr.TXT")

        # make DEFAULT
        os.mkdir(f"{tmpdirname}/DIPLOCOM/DEFAULT")

        # copy DATA
        with open(f"{tmpdirname}/DIPLOCOM/DEFAULT/DIPLO.DAT", "w") as outfile:
            outfile.write("\n".join(diplo_dat_content))

        # copy situation
        with open(f"{tmpdirname}/situation.dat", "w") as outfile:
            outfile.write("\n".join(situation_content))

        # copy orders
        with open(f"{tmpdirname}/orders.txt", "w") as outfile:
            outfile.write("\n".join(orders_content))

        # affect env variable
        os.putenv("DIPLOCOM", f"{tmpdirname}/DIPLOCOM")

        # parameters used to cal the C language written solver
        call_list = [
            "./engine/solveur",
            "-i", f"{tmpdirname}/situation.dat",
            "-o", f"{tmpdirname}/orders.txt",
            "-f", f"{tmpdirname}/situation_result.dat",
            "-a", f"{tmpdirname}/orders_result.txt",
            "-A", f"{tmpdirname}/active_roles.txt"
        ]

        # in case we are checking partial orders
        if role is not None:
            _, _, initial_role = names['roles'][str(role)]
            call_list += [
                f"-x{initial_role}",
            ]

        # run solver
        result = subprocess.run(
            call_list,
            check=False,
            capture_output=True)

        if result.returncode != 0:
            return result.returncode, result.stderr.decode(), result.stdout.decode(), None, None, None

        # copy back situation
        with open(f"{tmpdirname}/situation_result.dat", "r") as infile:
            situation_result_content = infile.readlines()
        situation_result = read_situation(situation_result_content, variant, names)

        # copy back orders
        with open(f"{tmpdirname}/orders_result.txt", "r") as infile:
            orders_result_content = infile.readlines()
            orders_result = ''.join(orders_result_content)

        # copy back actives
        with open(f"{tmpdirname}/active_roles.txt", "r") as infile:
            active_roles_content = infile.readlines()
        active_roles_list = read_actives(active_roles_content, names)

        return result.returncode, result.stderr.decode(), result.stdout.decode(), situation_result, orders_result, active_roles_list


def disorder(variant: typing.Dict[str, typing.Any], advancement: int, situation: typing.Dict[str, typing.Any], role: int, names: typing.Dict[str, typing.Any]) -> typing.Tuple[int, str, str, typing.Optional[str]]:
    """ returns errorcode, stderr, stdout, ord-result(text) """

    diplo_dat_content = build_variant_file(variant, names)
    situation_content = build_situation_file(advancement, situation, variant, names)

    with tempfile.TemporaryDirectory() as tmpdirname:

        # make DIPLOCOM
        os.mkdir(f"{tmpdirname}/DIPLOCOM")

        # copy message file
        shutil.copyfile("./messages/DIPLO.fr.TXT", f"{tmpdirname}/DIPLOCOM/DIPLO.fr.TXT")

        # make DEFAULT
        os.mkdir(f"{tmpdirname}/DIPLOCOM/DEFAULT")

        # copy DATA
        with open(f"{tmpdirname}/DIPLOCOM/DEFAULT/DIPLO.DAT", "w") as outfile:
            outfile.write("\n".join(diplo_dat_content))

        # copy situation
        with open(f"{tmpdirname}/situation.dat", "w") as outfile:
            outfile.write("\n".join(situation_content))

        # affect env variable
        os.putenv("DIPLOCOM", f"{tmpdirname}/DIPLOCOM")

        _, _, initial_role = names['roles'][str(role)]

        # parameters used to cal the C language written solver
        call_list = [
            "./engine/solveur",
            "-i", f"{tmpdirname}/situation.dat",
            f"-P{initial_role}", f"{tmpdirname}/orders_result.txt",
        ]

        # run solver
        result = subprocess.run(
            call_list,
            check=False,
            capture_output=True)

        if result.returncode != 0:
            return result.returncode, result.stderr.decode(), result.stdout.decode(), None

        # copy back orders
        with open(f"{tmpdirname}/orders_result.txt", "r") as infile:
            orders_result_content = infile.readlines()
            orders_result = ''.join(orders_result_content)

        orders_list = read_orders(orders_result_content, variant, names, role)

        return result.returncode, result.stderr.decode(), result.stdout.decode(), orders_list


if __name__ == '__main__':
    assert False, "Do not run this script"
