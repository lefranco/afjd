""" xxx """

import json
import enum
import typing
import itertools


@enum.unique
class RegionTypeEnum(enum.Enum):
    """ RegionTypeEnum """

    LAND_REGION = enum.auto()
    COAST_REGION = enum.auto()
    SEA_REGION = enum.auto()

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

        # the region in which is the center
        self._region = region

        # the owner at start of the game
        self._owner_start: typing.Optional['Role'] = None

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

        # the type of the regio: land, coast or sea
        self._region_type = region_type

        # if the region has a center
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

        # most of the time zone = region
        self._region = region

        # for the special zones that have a specific coast
        self._coast_type = coast_type

        # other zones one may access by fleet and army
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

    def __init__(self) -> None:

        # start centers the role have
        self._start_centers: typing.List[Center] = list()

    @property
    def start_centers(self) -> typing.List[Center]:
        """ property """
        return self._start_centers

    @start_centers.setter
    def start_centers(self, start_centers: typing.List[Center]) -> None:
        """ setter """
        self._start_centers = start_centers

class ColourRecord(typing.NamedTuple):
    """ A colour """
    red: int
    green: int
    blue: int

    def outline_colour(self) -> 'ColourRecord':
        if self.red + self.green + self.blue < (256 + 256 + 256) // 2:
            return ColourRecord(red=256//2, green=256//2, blue=256//2)
        return ColourRecord(red=0, green=0, blue=0)

    def str_value(self) -> str:
        return f"rgb({self.red}, {self.green}, {self.blue})"

class PositionRecord(typing.NamedTuple):
    """ A position """
    x_pos: int
    y_pos: int

class Variant:
    """ A variant """

    def __init__(self, variant_file_name: str, parameters_file_name: str) -> None:

        # =================
        # from variant file
        # =================

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
            role = Role()
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

        # =================
        # from parameters file
        # =================

        # load the parameters file
        with open(parameters_file_name, "r") as read_file:
            self._raw_parameters_content = json.load(read_file)

        self._name_table: typing.Dict[typing.Any, str] = dict()
        self._colour_table: typing.Dict[typing.Any, ColourRecord] = dict()
        self._position_table: typing.Dict[typing.Any, PositionRecord] = dict()
        self._legend_position_table: typing.Dict[typing.Any, PositionRecord] = dict()

        # load the regions type names
        assert len(self._raw_parameters_content['regions']) == len(RegionTypeEnum)
        for region_type_code_str, data_dict in self._raw_parameters_content['regions'].items():
            region_type_code = int(region_type_code_str)
            region_type = RegionTypeEnum.from_code(region_type_code)
            assert region_type is not None
            name = data_dict['name']
            self._name_table[region_type] = name

        # load the units type names
        assert len(self._raw_parameters_content['units']) == len(UnitTypeEnum)
        for unit_type_code_str, data_dict in self._raw_parameters_content['units'].items():
            unit_type_code = int(unit_type_code_str)
            unit_type = UnitTypeEnum.from_code(unit_type_code)
            assert unit_type is not None
            name = data_dict['name']
            self._name_table[unit_type] = name

        # load the roles names and colours
        assert len(self._raw_parameters_content['roles']) == len(self._roles) + 1
        for role_num_str, data_dict in self._raw_parameters_content['roles'].items():
            role_num = int(role_num_str)
            if role_num == 0:  # gm
                continue
            role = self._roles[role_num]
            name = data_dict['name']
            self._name_table[role] = name
            red = data_dict['red']
            assert isinstance(red, int)
            green = data_dict['green']
            blue = data_dict['blue']
            colour = ColourRecord(red=red, green=green, blue=blue)
            self._colour_table[role] = colour

        # load the zones names and localisations
        assert len(self._raw_parameters_content['zones']) == len(self._zones)
        for zone_num_str, data_dict in self._raw_parameters_content['zones'].items():
            zone_num = int(zone_num_str)
            zone = self._zones[zone_num]
            name = data_dict['name']
            self._name_table[zone] = name
            x_pos = data_dict['x_name']  # TODO : rename into x_legend_pos
            y_pos = data_dict['y_name']  # TODO : rename into y_legend_pos
            legend_position = PositionRecord(x_pos=x_pos, y_pos=y_pos)
            self._legend_position_table[zone] = legend_position
            x_pos = data_dict['x_pos']
            y_pos = data_dict['y_pos']
            unit_position = PositionRecord(x_pos=x_pos, y_pos=y_pos)
            self._position_table[zone] = unit_position

        # load the centers localisations
        assert len(self._raw_parameters_content['centers']) == len(self._centers)
        for center_num_str, data_dict in self._raw_parameters_content['centers'].items():
            center_num = int(center_num_str)
            center = self._centers[center_num]
            x_pos = data_dict['x_pos']
            y_pos = data_dict['y_pos']
            center_position = PositionRecord(x_pos=x_pos, y_pos=y_pos)
            self._position_table[center] = center_position

        # load coasts types names
        assert len(self._raw_parameters_content['coasts']) == len(self._coast_types)
        for coast_type_num_str, data_dict in self._raw_parameters_content['coasts'].items():
            coast_type_num = int(coast_type_num_str)
            coast_type = self._coast_types[coast_type_num]
            self._name_table[coast_type] = name

        # load seasons names
        assert len(self._raw_parameters_content['seasons']) == len(SeasonEnum)
        for season_num_str, data_dict in self._raw_parameters_content['seasons'].items():
            season_num = int(season_num_str)
            season = SeasonEnum.from_code(season_num)
            assert season is not None
            self._name_table[season] = name

        # load orders types names
        assert len(self._raw_parameters_content['orders']) == len(OrderTypeEnum)
        for order_type_num_str, data_dict in self._raw_parameters_content['orders'].items():
            order_type_num = int(order_type_num_str)
            order_type = OrderTypeEnum.from_code(order_type_num)
            assert order_type is not None
            self._name_table[order_type] = name

    @property
    def name_table(self) -> typing.Dict[typing.Any, str]:
        """ property """
        return self._name_table

    @property
    def colour_table(self) -> typing.Dict[typing.Any, ColourRecord]:
        """ property """
        return self._colour_table

    @property
    def position_table(self) -> typing.Dict[typing.Any, PositionRecord]:
        """ property """
        return self._position_table

    @property
    def legend_position_table(self) -> typing.Dict[typing.Any, PositionRecord]:
        """ property """
        return self._legend_position_table


    def __str__(self) -> str:
        return "TODO"


class Point:
    """ Point for easier compatbility with old C software (do not use a record here) """
    def __init__(self) -> None:
        self.x = 0  # pylint: disable=invalid-name
        self.y = 0  # pylint: disable=invalid-name

class Unit:
    """ A unit """

    def __init__(self, variant: Variant, role: Role, zone: Zone) -> None:
        self._variant = variant
        self._role = role
        self._zone = zone


class Army(Unit):

    # no init : use init from parent class


    def render(self, ctx: typing.Any) -> None:
        """put me on screen """

        fill_color = self._variant.colour_table[self._role]
        outline_colour = fill_color.outline_colour()

        position = self._variant.position_table[self._zone]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        # socle
        p1 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
        p1[0].x = x - 15; p1[0].y = y + 6
        p1[1].x = x - 15; p1[1].y = y + 9
        p1[2].x = x + 6; p1[2].y = y + 9
        p1[3].x = x + 6; p1[3].y = y + 6
        canvas.create_polygon(*(itertools.chain(*[[p.x, p.y] for p in p1])), fill=fill_color.str_value(), outline=outline_colour.str_value())

        # coin
        p2 = [Point() for _ in range(3)]  # pylint: disable=invalid-name
        p2[0].x = x - 9; p2[0].y = y + 6
        p2[1].x = x - 4; p2[1].y = y + 6
        p2[2].x = x - 7; p2[2].y = y + 3
        canvas.create_polygon(*(itertools.chain(*[[p.x, p.y] for p in p2])), fill=fill_color.str_value(), outline=outline_colour.str_value())

        # canon
        p3 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
        p3[0].x = x - 2; p3[0].y = y - 7
        p3[1].x = x + 4; p3[1].y = y - 15
        p3[2].x = x + 5; p3[2].y = y - 13
        p3[3].x = x;  p3[3].y = y - 7
        canvas.create_polygon(*(itertools.chain(*[[p.x, p.y] for p in p3])), fill=fill_color.str_value(), outline=outline_colour.str_value())

        # cercle autour roue exterieure
        # simplified
        canvas.create_oval(x - 6, y - 6, x + 5, y + 5, fill=fill_color.str_value(), outline=outline_colour.str_value())

        # roue interieure
        # simplified
        canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill=fill_color.str_value(), outline=outline_colour.str_value())

        # exterieur coin
        canvas.create_line(x - 7, y + 3, x - 9, y + 6, fill=fill_color.str_value())



