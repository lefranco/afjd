#!/usr/bin/env python3

"""
an ihm based on tkinter
this is a low level module that reads all data from configration files
"""

import typing
import configparser
import enum
import collections

MAP_FILE = ''

VARIANT_NAME = ''


class ConfigFile:
    """    Just reads an ini file   """

    def __init__(self, filename: str) -> None:
        self._config = configparser.ConfigParser(inline_comment_prefixes='#',    # do not accept ';'
                                                 empty_lines_in_values=False,    # as it says
                                                 interpolation=None)             # do not use variables

        assert self._config.read(filename, encoding='utf-8'), f"Missing ini file named {filename}"

    def section(self, section_name: str) -> configparser.SectionProxy:
        """ Accesses a section of a config file  """
        assert self._config.has_section(section_name), "Missing section in ini file"
        return self._config[section_name]

    def section_list(self) -> typing.List[str]:
        """ Accesses the list of sections of a config file  """
        return self._config.sections()


SERVER_CONFIG: typing.Dict[str, typing.Dict[str, typing.Any]] = collections.defaultdict(dict)


def load_servers_config() -> None:
    """ read servers config """

    global SERVER_CONFIG

    servers_config = ConfigFile('./config/servers.ini')
    for server in servers_config.section_list():
        server_data = servers_config.section(server)
        SERVER_CONFIG[server]['HOST'] = server_data['HOST']
        SERVER_CONFIG[server]['PORT'] = int(server_data['PORT'])


def set_variant_name(variant_name: str) -> None:
    """ set variant """
    global VARIANT_NAME
    VARIANT_NAME = variant_name


DESIGN_NAME = ''


def set_design_name(design_name: str) -> None:
    """ set design """
    global DESIGN_NAME
    DESIGN_NAME = design_name


# data related to variant (loaded from outside)
VARIANT_DATA: typing.Dict[str, typing.Any] = dict()


def set_map_file() -> None:
    """ set map file from locally """

    assert VARIANT_NAME
    assert DESIGN_NAME

    global MAP_FILE
    MAP_FILE = f'./local_design/{VARIANT_NAME}/{DESIGN_NAME}/map.png'


def read_config(file_name: str) -> typing.Dict[str, typing.Any]:
    """ Quick read of configuration """

    config = configparser.ConfigParser()
    config.read(file_name)
    config_data = dict()

    for section in config.sections():
        config_data[section] = dict(config[section])
    return config_data


# data related to design
UNIT_DATA: typing.Dict[str, typing.Any] = dict()
ROLE_DATA: typing.Dict[str, typing.Any] = dict()
ZONE_DATA: typing.Dict[str, typing.Any] = dict()
CENTER_DATA: typing.Dict[str, typing.Any] = dict()
COAST_DATA: typing.Dict[str, typing.Any] = dict()
SEASON_DATA: typing.Dict[str, typing.Any] = dict()
ORDERS_DATA: typing.Dict[str, typing.Any] = dict()


def load_design_data() -> None:
    """ load standard data from locally """

    assert VARIANT_NAME
    assert DESIGN_NAME

    # local naming of diplomacy concepts

    global UNIT_DATA
    UNIT_DATA = read_config(f'./local_design/{VARIANT_NAME}/{DESIGN_NAME}/units.ini')

    global ROLE_DATA
    ROLE_DATA = read_config(f'./local_design/{VARIANT_NAME}/{DESIGN_NAME}/roles.ini')

    global ZONE_DATA
    ZONE_DATA = read_config(f'./local_design/{VARIANT_NAME}/{DESIGN_NAME}/zones.ini')

    global CENTER_DATA
    CENTER_DATA = read_config(f'./local_design/{VARIANT_NAME}/{DESIGN_NAME}/centers.ini')

    global COAST_DATA
    COAST_DATA = read_config(f'./local_design/{VARIANT_NAME}/{DESIGN_NAME}/coasts.ini')

    global SEASON_DATA
    SEASON_DATA = read_config(f'./local_design/{VARIANT_NAME}/{DESIGN_NAME}/seasons.ini')

    global ORDERS_DATA
    ORDERS_DATA = read_config(f'./local_design/{VARIANT_NAME}/{DESIGN_NAME}/orders.ini')


@enum.unique
class TypeUnitEnum(enum.Enum):
    """ The two possible types of units  """

    ARMY_TYPE = enum.auto()
    FLEET_TYPE = enum.auto()

    def swap(self) -> 'TypeUnitEnum':
        """ swap between army and fleet """
        if self is TypeUnitEnum.ARMY_TYPE:
            return TypeUnitEnum.FLEET_TYPE
        if self is TypeUnitEnum.FLEET_TYPE:
            return TypeUnitEnum.ARMY_TYPE
        assert False, "Cannot swap"
        return TypeUnitEnum.ARMY_TYPE

    def __str__(self) -> str:
        type_unit_num = self.value
        return str(UNIT_DATA[str(type_unit_num)]['name'][:1])

    @staticmethod
    def decode(val: int) -> typing.Optional['TypeUnitEnum']:
        """ from int to enum """
        for type_unit in TypeUnitEnum:
            if type_unit.value == val:
                return type_unit
        return None


@enum.unique
class TypeRegionEnum(enum.Enum):
    """ The three possible types of region   """

    COAST_TYPE = enum.auto()
    INLAND_TYPE = enum.auto()
    SEA_TYPE = enum.auto()

    @staticmethod
    def decode(val: int) -> typing.Optional['TypeRegionEnum']:
        """ from int to enum """
        for type_region in TypeRegionEnum:
            if type_region.value == val:
                return type_region
        return None


def is_special_coast(zone_num: int) -> bool:
    """ to detect special coast like stp, spa and bul """

    return zone_num > len(VARIANT_DATA['regions'])


def find_center_num(region_num: int) -> typing.Optional[int]:
    """ to get center of region """

    for center_num, region_num_found in enumerate(VARIANT_DATA['centers']):
        if region_num_found == region_num:
            return center_num + 1
    return None


def find_region_num(zone_num: int) -> int:
    """ to get region of zone (usually same except for specific coasts) """

    if not is_special_coast(zone_num):
        return zone_num

    coast_zone_num = zone_num - len(VARIANT_DATA['regions']) - 1
    region_num, _ = VARIANT_DATA['coastal_zones'][coast_zone_num]
    return int(region_num)


def find_zone_name(zone_num: int) -> str:
    """ converts zone number to text """

    if not is_special_coast(zone_num):
        return f"{ZONE_DATA[str(zone_num)]['name']}"

    coast_zone_num = zone_num - len(VARIANT_DATA['regions']) - 1
    region_num, coast_num = VARIANT_DATA['coastal_zones'][coast_zone_num]
    region_name = ZONE_DATA[str(region_num)]['name']
    coast_name = COAST_DATA[str(coast_num)]['name']
    return f"{region_name} {coast_name}"


def find_region_center(center_num: int) -> int:
    """ from id of center returns id of region """

    region_num = int(VARIANT_DATA['centers'][center_num - 1])
    return region_num


def find_region_name(region_num: int) -> str:
    """ converts region number to text """

    region_name = ZONE_DATA[str(region_num)]['name']
    return f"{region_name}"


def may_build_there(zone_num: int) -> typing.Optional[int]:
    """ says if build is possible returns role (None if not possible) """

    region_zone_num = find_region_num(zone_num)
    for role in range(VARIANT_DATA['roles']['number']):
        for start_center in VARIANT_DATA['start_centers'][role]:
            region_num = VARIANT_DATA['centers'][start_center - 1]
            if region_num == region_zone_num:
                return role + 1
    return None


def extract_names() -> typing.Dict[str, typing.Dict[int, typing.Any]]:
    """ extract the names we are using to pass them to adjudicator """

    role_names = {int(r): (str(ROLE_DATA[r]['name']), str(ROLE_DATA[r]['adjective_name']), str(ROLE_DATA[r]['letter_name'])) for r in ROLE_DATA}
    zone_names = {int(z): str(ZONE_DATA[z]['name']) for z in ZONE_DATA}
    coast_names = {int(c): str(COAST_DATA[c]['name']) for c in COAST_DATA}

    return {'roles': role_names, 'zones': zone_names, 'coasts': coast_names}


if __name__ == "__main__":
    assert False, "Do not run this script"
