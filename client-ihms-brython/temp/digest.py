""" xxx """

import json
import enum
import typing
import collections


@enum.unique
class RegionTypeEnum(enum.Enum):
    """ RegionTypeEnum """

    LAND_REGION = enum.auto()
    COAST_REGION = enum.auto()
    SEA_REGION = enum.auto()

    name_table: typing.Dict['RegionTypeEnum', str] = dict()

    @staticmethod
    def from_code(code: int) -> typing.Optional['RegionTypeEnum']:
        """ from_code """
        if code == 1:
            return RegionTypeEnum.COAST_REGION
        if code == 2:
            return RegionTypeEnum.LAND_REGION
        if code == 3:
            return RegionTypeEnum.SEA_REGION
        return None


@enum.unique
class UnitTypeEnum(enum.Enum):
    """ UnitTypeEnum """

    ARMY_UNIT = enum.auto()
    FLOAT_UNIT = enum.auto()

    @staticmethod
    def from_code(code: int) -> typing.Optional['UnitTypeEnum']:
        """ from_code """
        if code == 1:
            return UnitTypeEnum.ARMY_UNIT
        if code == 2:
            return UnitTypeEnum.FLOAT_UNIT
        return None


@enum.unique
class SeasonEnum(enum.Enum):
    """ SeasonEnum """

    SPRING_SEASON = enum.auto()
    SUMMER_SEASON = enum.auto()
    AUTUMN_SEASON = enum.auto()
    WINTER_SEASON = enum.auto()
    ADJUST_SEASON = enum.auto()

    @staticmethod
    def from_code(code: int) -> typing.Optional['SeasonEnum']:
        """ from_code """
        if code == 1:
            return SeasonEnum.SPRING_SEASON
        if code == 2:
            return SeasonEnum.SUMMER_SEASON
        if code == 3:
            return SeasonEnum.AUTUMN_SEASON
        if code == 4:
            return SeasonEnum.WINTER_SEASON
        if code == 5:
            return SeasonEnum.ADJUST_SEASON
        return None


@enum.unique
class OrderTypeEnum(enum.Enum):
    """ OrderTypeEnum """

    ATTACK_ORDER = enum.auto()
    OFF_SUPPORT_ORDER = enum.auto()
    DEF_SUPPORT_ORDER = enum.auto()
    HOLD_ORDER = enum.auto()
    CONVOY_ORDER = enum.auto()
    RETREAT_ORDER = enum.auto()
    DISBAND_ORDER = enum.auto()
    BUILD_ORDER = enum.auto()
    REMOVE_ORDER = enum.auto()

    @staticmethod
    def from_code(code: int) -> typing.Optional['OrderTypeEnum']:
        """ from_code """
        if code == 1:
            return OrderTypeEnum.ATTACK_ORDER
        if code == 2:
            return OrderTypeEnum.OFF_SUPPORT_ORDER
        if code == 3:
            return OrderTypeEnum.DEF_SUPPORT_ORDER
        if code == 4:
            return OrderTypeEnum.HOLD_ORDER
        if code == 5:
            return OrderTypeEnum.CONVOY_ORDER
        if code == 6:
            return OrderTypeEnum.RETREAT_ORDER
        if code == 7:
            return OrderTypeEnum.DISBAND_ORDER
        if code == 8:
            return OrderTypeEnum.BUILD_ORDER
        if code == 9:
            return OrderTypeEnum.REMOVE_ORDER
        return None


class Center:
    """ A Center """

    def __init__(self, region: 'Region') -> None:
        self._region = region
        self._owner_start: typing.Optional['Role'] = None

    def is_start_center(self) -> bool:
        """ is_start_center """
        return self.owner_start is not None

    @property
    def owner_start(self) -> typing.Optional['Role']:
        """ property """
        return self._owner_start

    @owner_start.setter
    def owner_start(self, owner_start: 'Role') -> None:
        """ setter """
        self._owner_starts = owner_start


class CoastType:
    """ A CoastType """

    def __init__(self, code: int) -> None:
        self._code = code


class Region:
    """ A region """

    def __init__(self, region_type: RegionTypeEnum) -> None:
        self._type = region_type
        self._center: typing.Optional[Center] = None

    @property
    def center(self) -> typing.Optional[Center]:
        """ property """
        return self._center

    @center.setter
    def center(self, center: Center) -> None:
        """ setter """
        self._center = center


class Zone:
    """ A zone """

    def __init__(self, region: Region, coast_type: typing.Optional[CoastType]) -> None:
        self._region = region
        self._coast_type = coast_type
        self._neighbours: typing.Dict[UnitTypeEnum, typing.List['Zone']] = {u: list() for u in UnitTypeEnum}

    @property
    def neighbours(self) -> typing.Dict[UnitTypeEnum, typing.List['Zone']]:
        """ property """
        return self._neighbours

    @neighbours.setter
    def neighbours(self, neighbours: typing.Dict[UnitTypeEnum, typing.List['Zone']]) -> None:
        """ setter """
        self._neighbours = neighbours


class Role:
    """ a Role """

    def __init__(self, number: int) -> None:
        self._number = number
        self._start_centers: typing.List[Center] = list()
        self._start_units: typing.List[Unit] = list()
        self._distances: typing.Dict[Zone, int] = collections.defaultdict(int)

    @property
    def start_centers(self) -> typing.List[Center]:
        """ property """
        return self._start_centers

    @start_centers.setter
    def start_centers(self, start_centers: typing.List[Center]) -> None:
        """ setter """
        self._start_centers = start_centers

    @property
    def start_units(self) -> typing.List['Unit']:
        """ property """
        return self._start_units

    @start_units.setter
    def start_units(self, start_units: typing.List['Unit']) -> None:
        """ setter """
        self._start_units = start_units


class Unit:
    """ A unit """

    def __init__(self, unit_type: UnitTypeEnum, owner: Role, zone: Zone) -> None:
        self._unit_type = unit_type
        self._owner = owner
        self._zone = zone


class Variant:
    """ A variant """

    def __init__(self, variant_file_name: str, parameters_file_name: str) -> None:

        # load the variant file
        with open(variant_file_name, "r") as read_file:
            self._raw_variant_content = json.load(read_file)

        # load the regions
        self._regions: typing.Dict[int, Region] = dict()
        for num, code in enumerate(self._raw_variant_content['regions']):
            number = num + 1
            region_type = RegionTypeEnum.from_code(code)
            assert region_type is not None
            region = Region(region_type)
            self._regions[number] = region

        # load the centers
        self._centers: typing.Dict[int, Center] = dict()
        for num, num_region in enumerate(self._raw_variant_content['centers']):
            number = num + 1
            region = self._regions[num_region]
            center = Center(region)
            region.center = center
            self._centers[number] = center

        # load the roles
        self._roles: typing.Dict[int, Role] = dict()
        for num in range(self._raw_variant_content['roles']['number']):
            number = num + 1
            role = Role(number)
            self._roles[number] = role

        assert len(self._raw_variant_content['start_centers']) == len(self._roles)

        # load start centers
        self._start_centers: typing.Dict[int, Center] = dict()
        for num, role_start_centers in enumerate(self._raw_variant_content['start_centers']):
            number = num + 1
            role = self._roles[number]
            for num_center in role_start_centers:
                start_center = self._centers[num_center]
                role.start_centers.append(start_center)
                start_center.owner_start = role

        # load the coast types
        self._coast_types: typing.Dict[int, CoastType] = dict()
        for num in range(self._raw_variant_content['type_coasts']['number']):
            number = num + 1
            coast_type = CoastType(number)
            self._coast_types[number] = coast_type

        # load the coast zones

        # first the standard zones
        self._zones: typing.Dict[int, Zone] = dict()
        for num, region in enumerate(self._regions.values()):
            number = num + 1
            zone = Zone(region, None)
            self._zones[number] = zone

        # need an offset
        offset = max(self._zones.keys())

        # the the special coast zones
        for num, (region_num, coast_type_num) in enumerate(self._raw_variant_content['coastal_zones']):
            number = num + 1
            region = self._regions[region_num]
            coast_type = self._coast_types[coast_type_num]
            zone = Zone(region, coast_type)
            self._zones[offset + number] = zone

        # load the start units
        for num, role_start_units in enumerate(self._raw_variant_content['start_units']):
            number = num + 1
            role = self._roles[number]
            for unit_type_code_str, role_start_units2 in role_start_units.items():
                unit_type_code = int(unit_type_code_str)
                unit_type = UnitTypeEnum.from_code(unit_type_code)
                assert unit_type is not None
                for zone_num in role_start_units2:
                    zone = self._zones[zone_num]
                    start_unit = Unit(unit_type, role, zone)
                    role.start_units.append(start_unit)

        # load the year zero
        self._year_zero = self._raw_variant_content['year_zero']

        # load the neighbouring
        for num, neighbourings in enumerate(self._raw_variant_content['neighbouring']):
            number = num + 1
            unit_type = UnitTypeEnum.from_code(number)
            assert unit_type is not None
            for from_zone_num_str, zone_neighbours_list in neighbourings.items():
                from_zone_num = int(from_zone_num_str)
                from_zone = self._zones[from_zone_num]
                for to_zone_num in zone_neighbours_list:
                    to_zone = self._zones[to_zone_num]
                    from_zone.neighbours[unit_type].append(to_zone)

        # load the distancing
        # not needed

        # load the parameters file
        with open(parameters_file_name, "r") as read_file:
            self._raw_parameters_content = json.load(read_file)

        self._name_table: typing.Dict[typing.Any, str] = dict()
        self._colour_table: typing.Dict[typing.Any, typing.Tuple[int, int, int]] = dict()
        self._coordinates_table: typing.Dict[typing.Any, typing.Tuple[int, int]] = dict()
        self._legend_coordinates_table: typing.Dict[typing.Any, typing.Tuple[int, int]] = dict()

        # load the regions type names
        for code_str, data_dict in self._raw_parameters_content['regions'].items():
            code = int(code_str)
            name = data_dict['name']
            region_type = RegionTypeEnum.from_code(code)
            assert region_type is not None
            self._name_table[region_type] = name

        # load the units type names
        for code_str, data_dict in self._raw_parameters_content['units'].items():
            code = int(code_str)
            name = data_dict['name']
            unit_type = UnitTypeEnum.from_code(code)
            assert unit_type is not None
            self._name_table[unit_type] = name

        # load the roles names and colours
        for role_num_str, data_dict in self._raw_parameters_content['roles'].items():
            role_num = int(role_num_str)
            if role_num == 0:  # gm
                continue
            role = self._roles[role_num]
            name = data_dict['name']
            red = data_dict['red']
            green = data_dict['green']
            blue = data_dict['blue']
            colour = (red, green, blue)
            self._name_table[role] = name
            self._colour_table[role] = colour

        # load the zones names and localisations
        for zone_num_str, data_dict in self._raw_parameters_content['zones'].items():
            zone_num = int(zone_num_str)
            zone = self._zones[zone_num]
            name = data_dict['name']
            x_legend_pos = data_dict['x_name']  # TODO : rename into x_legend_pos
            y_legend_pos = data_dict['y_name']  # TODO : rename into y_legend_pos
            x_pos = data_dict['x_pos']
            y_pos = data_dict['y_pos']
            self._name_table[zone] = name
            self._legend_coordinates_table[zone] = (x_legend_pos, y_legend_pos)
            self._coordinates_table[zone] = (x_pos, y_pos)

        # load the centers localisations
        for center_num_str, data_dict in self._raw_parameters_content['centers'].items():
            center_num = int(center_num_str)
            center = self._centers[center_num]
            x_pos = data_dict['x_pos']
            y_pos = data_dict['y_pos']
            self._coordinates_table[center] = (x_pos, y_pos)

        # load coasts types names
        for coast_type_num_str, data_dict in self._raw_parameters_content['coasts'].items():
            coast_type_num = int(coast_type_num_str)
            coast_type = self._coast_types[coast_type_num]
            self._name_table[coast_type] = name

        # load seasons names
        for season_num_str, data_dict in self._raw_parameters_content['seasons'].items():
            season_num = int(season_num_str)
            season = SeasonEnum.from_code(season_num)
            assert season is not None
            self._name_table[season] = name

        # load seasons names
        for order_type_num_str, data_dict in self._raw_parameters_content['orders'].items():
            order_type_num = int(order_type_num_str)
            order_type = OrderTypeEnum.from_code(order_type_num)
            assert order_type is not None
            self._name_table[order_type] = name

    def __str__(self) -> str:
        return "TODO"


def main() -> None:
    """ main """

    variant = Variant("./standard.json", "./parameters.json")
    print(variant)


if __name__ == '__main__':
    main()
    #  assert False, "Do not run this script"
