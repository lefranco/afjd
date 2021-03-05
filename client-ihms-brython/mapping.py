""" mapping """

# pylint: disable=pointless-statement, expression-not-assigned


import enum
import typing
import abc
import math

# pylint: disable=pointless-statement, expression-not-assigned, multiple-statements
# noqa: E702


def draw_arrow(x_start: int, y_start: int, x_dest: int, y_dest: int, ctx: typing.Any) -> None:
    """ low level draw an arrow """

    # the ctx.strokeStyle and ctx.fillStyle should be defined

    # first draw the arrow line
    ctx.beginPath()
    ctx.moveTo(x_start, y_start)
    ctx.lineTo(x_dest, y_dest)
    ctx.closePath(); ctx.stroke()

    # first draw the arrow head
    ctx.save()

    ctx.translate(x_dest, y_dest)
    angle = - math.atan2(x_start - x_dest, y_start - y_dest)
    ctx.rotate(angle)
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(-3, 6)
    ctx.lineTo(3, 6)
    ctx.closePath(); ctx.fill()

    ctx.restore()


class Renderable:
    """ Renderable """

    @abc.abstractmethod
    def render(self, ctx: typing.Any) -> None:
        """ render = display """


@enum.unique
class RegionTypeEnum(enum.Enum):
    """ RegionTypeEnum """

    LAND_REGION = enum.auto()
    COAST_REGION = enum.auto()
    SEA_REGION = enum.auto()

    @staticmethod
    def from_code(code: int) -> typing.Optional['RegionTypeEnum']:
        """ from_code """
        for region_type in RegionTypeEnum:
            if region_type.value == code:
                return region_type
        return None


@enum.unique
class UnitTypeEnum(enum.Enum):
    """ UnitTypeEnum """

    ARMY_UNIT = enum.auto()
    FLEET_UNIT = enum.auto()

    @staticmethod
    def from_code(code: int) -> typing.Optional['UnitTypeEnum']:
        """ from_code """
        for unit_type in UnitTypeEnum:
            if unit_type.value == code:
                return unit_type
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
        for season in SeasonEnum:
            if season.value == code:
                return season
        return None

    def __str__(self) -> str:
        return f"{self.name}"


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
        for order_type in OrderTypeEnum:
            if order_type.value == code:
                return order_type
        return None

    def __str__(self) -> str:
        return f"{self.name}"


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

        # the type of the region land, coast or sea
        self._region_type = region_type

        # if the region has a center
        self._center: typing.Optional[Center] = None

        # the zone (for localisation)
        self._zone: typing.Optional[Zone] = None

        # the unit occupying the region (for identifying units)
        self._occupant: typing.Optional['Unit'] = None

    @property
    def center(self) -> typing.Optional[Center]:
        """ property """
        return self._center

    @center.setter
    def center(self, center: Center) -> None:
        """ setter """
        self._center = center

    @property
    def zone(self) -> typing.Optional['Zone']:
        """ property """
        return self._zone

    @zone.setter
    def zone(self, zone: 'Zone') -> None:
        """ setter """
        self._zone = zone


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
    def coast_type(self) -> typing.Optional[CoastType]:
        """ property """
        return self._coast_type

    @property
    def region(self) -> Region:
        """ property """
        return self._region

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
        """ outline_colour """
        the_sum = self.red + self.green + self.blue
        if the_sum < (3 * 255) // 10:
            return ColourRecord(red=255 // 2, green=255 // 2, blue=255 // 2)
        return ColourRecord(red=0, green=0, blue=0)

    def str_value(self) -> str:
        """ str_value """
        return f"rgb({self.red}, {self.green}, {self.blue})"


class PositionRecord(typing.NamedTuple):
    """ A position """
    x_pos: int
    y_pos: int


class Variant(Renderable):
    """ A variant """

    def __init__(self, raw_variant_content: typing.Dict[str, typing.Any], raw_parameters_content: typing.Dict[str, typing.Any]) -> None:

        # =================
        # from variant file
        # =================

        # load the variant from dict
        self._raw_variant_content = raw_variant_content

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

        # load the zones

        # first the standard zones
        self._zones: typing.Dict[int, Zone] = dict()
        for num, region in enumerate(self._regions.values()):
            number = num + 1
            zone = Zone(region, None)
            region.zone = zone
            self._zones[number] = zone

        # need an offset
        offset = max(self._zones.keys())

        # then the special coast zones
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

        # load the parameters content
        self._raw_parameters_content = raw_parameters_content

        self._name_table: typing.Dict[typing.Any, str] = dict()
        self._colour_table: typing.Dict[typing.Any, ColourRecord] = dict()
        self._position_table: typing.Dict[typing.Any, PositionRecord] = dict()
        self._legend_position_table: typing.Dict[typing.Any, PositionRecord] = dict()

        # load the map size
        data_dict = self._raw_parameters_content['map']
        width = data_dict['width']
        height = data_dict['height']
        map_size = PositionRecord(x_pos=width, y_pos=height)
        self._map_size = map_size

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
            green = data_dict['green']
            blue = data_dict['blue']
            colour = ColourRecord(red=red, green=green, blue=blue)
            self._colour_table[role] = colour

        # load coasts types names
        assert len(self._raw_parameters_content['coasts']) == len(self._coast_types)
        for coast_type_num_str, data_dict in self._raw_parameters_content['coasts'].items():
            coast_type_num = int(coast_type_num_str)
            coast_type = self._coast_types[coast_type_num]
            self._name_table[coast_type] = data_dict['name']

        # load the zones names and localisations
        assert len(self._raw_parameters_content['zones']) == len(self._zones)
        for zone_num_str, data_dict in self._raw_parameters_content['zones'].items():
            zone_num = int(zone_num_str)
            zone = self._zones[zone_num]

            # special zones have a special name
            if zone.coast_type:
                coast_type = zone.coast_type
                name = self._name_table[coast_type]
            else:
                name = data_dict['name']

            self._name_table[zone] = name
            x_pos = data_dict['x_legend_pos']
            y_pos = data_dict['y_legend_pos']
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

    def render(self, ctx: typing.Any) -> None:
        """ render the legends only """
        for zone in self._zones.values():
            position = self._legend_position_table[zone]
            x_pos = position.x_pos
            y_pos = position.y_pos
            legend = self._name_table[zone]
            ctx.fillText(legend, x_pos, y_pos)

    @property
    def map_size(self) -> PositionRecord:
        """ property """
        return self._map_size

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
    def zones(self) -> typing.Dict[int, Zone]:
        """ property """
        return self._zones

    @property
    def roles(self) -> typing.Dict[int, Role]:
        """ property """
        return self._roles


class Point:
    """ Point for easier compatbility with old C software (do not use a record here) """
    def __init__(self) -> None:
        self.x = 0  # pylint: disable=invalid-name
        self.y = 0  # pylint: disable=invalid-name

    def __str__(self) -> str:
        return f"x={self.x} y={self.y}"


class Unit(Renderable):  # pylint: disable=abstract-method
    """ A unit """

    def __init__(self, position: 'Position', role: Role, zone: Zone, dislodged_origin: typing.Optional[Region]) -> None:
        self._position = position
        self._role = role
        self._zone = zone
        self._dislodged_origin: typing.Optional[Region] = dislodged_origin

    def render_as_dislodged(self, x_pos: int, y_pos: int, ctx: typing.Any) -> None:
        """ render additional stuff when dislodged """

        assert self._dislodged_origin is not None

        # because we know names of zones but not of regions
        zone_dislodger = self._dislodged_origin.zone
        dislodger_legend = self._position.variant.name_table[zone_dislodger]

        # dislodger
        dislodger_colour = ColourRecord(255, 127, 0)  # orange-ish
        ctx.fillStyle = dislodger_colour.str_value()
        ctx.fillText(dislodger_legend, x_pos + 12, y_pos - 9)

        # circle
        ctx.beginPath()
        circle_colour = ColourRecord(255, 127, 0)  # orange-ish
        ctx.strokeStyle = circle_colour.str_value()
        ctx.arc(x_pos, y_pos, 12, 0, 2 * math.pi, False)
        ctx.closePath(); ctx.stroke()  # no fill

    @property
    def zone(self) -> Zone:
        """ property """
        return self._zone


class Army(Unit):
    """ An army """

    # use init from parent class

    def render(self, ctx: typing.Any) -> None:
        """put me on screen """

        fill_color = self._position.variant.colour_table[self._role]
        ctx.fillStyle = fill_color.str_value()

        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        position = self._position.variant.position_table[self._zone]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        # shift for dislodged units
        if self._dislodged_origin is not None:
            x -= 5  # pylint: disable=invalid-name
            y -= 5  # pylint: disable=invalid-name

        # socle
        p1 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
        p1[0].x = x - 15; p1[0].y = y + 6
        p1[1].x = x - 15; p1[1].y = y + 9
        p1[2].x = x + 6; p1[2].y = y + 9
        p1[3].x = x + 6; p1[3].y = y + 6
        ctx.beginPath()
        for n, p in enumerate(p1):  # pylint: disable=invalid-name
            if not n:
                ctx.moveTo(p.x, p.y)
            else:
                ctx.lineTo(p.x, p.y)
        ctx.closePath(); ctx.fill(); ctx.stroke()

        # coin
        p2 = [Point() for _ in range(3)]  # pylint: disable=invalid-name
        p2[0].x = x - 9; p2[0].y = y + 6
        p2[1].x = x - 4; p2[1].y = y + 6
        p2[2].x = x - 7; p2[2].y = y + 3
        ctx.beginPath()
        for n, p in enumerate(p2):  # pylint: disable=invalid-name
            if not n:
                ctx.moveTo(p.x, p.y)
            else:
                ctx.lineTo(p.x, p.y)
        ctx.closePath(); ctx.fill(); ctx.stroke()

        # canon
        p3 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
        p3[0].x = x - 2; p3[0].y = y - 7
        p3[1].x = x + 4; p3[1].y = y - 15
        p3[2].x = x + 5; p3[2].y = y - 13
        p3[3].x = x; p3[3].y = y - 7
        ctx.beginPath()
        for n, p in enumerate(p3):  # pylint: disable=invalid-name
            if not n:
                ctx.moveTo(p.x, p.y)
            else:
                ctx.lineTo(p.x, p.y)
        ctx.closePath(); ctx.fill(); ctx.stroke()

        # cercle autour roue exterieure
        # simplified
        ctx.beginPath()
        ctx.arc(x, y, 6, 0, 2 * math.pi, False)
        ctx.closePath(); ctx.fill(); ctx.stroke()

        # roue interieure
        # simplified
        ctx.beginPath()
        ctx.arc(x, y, 2, 0, 2 * math.pi, False)
        ctx.closePath(); ctx.fill(); ctx.stroke()

        # exterieur coin
        p4 = [Point() for _ in range(2)]  # pylint: disable=invalid-name
        p4[0].x = x - 7; p4[0].y = y + 3
        p4[1].x = x - 9; p4[1].y = y + 6
        ctx.beginPath()
        for n, p in enumerate(p4):  # pylint: disable=invalid-name
            if not n:
                ctx.moveTo(p.x, p.y)
            else:
                ctx.lineTo(p.x, p.y)
        ctx.closePath(); ctx.stroke()  # no fill

        # more stuff if dislodged
        if self._dislodged_origin is not None:
            self.render_as_dislodged(x, y, ctx)


class Fleet(Unit):
    """ An fleet """

    # use init from parent class

    def render(self, ctx: typing.Any) -> None:
        """put me on screen """

        fill_color = self._position.variant.colour_table[self._role]
        ctx.fillStyle = fill_color.str_value()

        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        position = self._position.variant.position_table[self._zone]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        # shift for dislodged units
        if self._dislodged_origin is not None:
            x -= 5  # pylint: disable=invalid-name
            y -= 5  # pylint: disable=invalid-name

        # gros oeuvre
        p1 = [Point() for _ in range(32)]  # pylint: disable=invalid-name
        p1[0].x = x - 15; p1[0].y = y + 4
        p1[1].x = x + 16; p1[1].y = y + 4
        p1[2].x = x + 15; p1[2].y = y
        p1[3].x = x + 10; p1[3].y = y
        p1[4].x = x + 10; p1[4].y = y - 3
        p1[5].x = x + 7; p1[5].y = y - 3
        p1[6].x = x + 7; p1[6].y = y - 2
        p1[7].x = x + 4; p1[7].y = y - 2
        p1[8].x = x + 4; p1[8].y = y - 9
        p1[9].x = x + 3; p1[9].y = y - 9
        p1[10].x = x + 3; p1[10].y = y - 6
        p1[11].x = x - 1; p1[11].y = y - 6
        p1[12].x = x - 1; p1[12].y = y - 9
        p1[13].x = x - 2; p1[13].y = y - 9
        p1[14].x = x - 2; p1[14].y = y - 13
        p1[15].x = x - 3; p1[15].y = y - 13
        p1[16].x = x - 3; p1[16].y = y - 6
        p1[17].x = x - 6; p1[17].y = y - 6
        p1[18].x = x - 6; p1[18].y = y - 5
        p1[19].x = x - 3; p1[19].y = y - 5
        p1[20].x = x - 3; p1[20].y = y - 4
        p1[21].x = x - 4; p1[21].y = y - 3
        p1[22].x = x - 4; p1[22].y = y - 2
        p1[23].x = x - 5; p1[23].y = y - 2
        p1[24].x = x - 5; p1[24].y = y - 3
        p1[25].x = x - 9; p1[25].y = y - 3
        p1[26].x = x - 9; p1[26].y = y
        p1[27].x = x - 12; p1[27].y = y
        p1[28].x = x - 12; p1[28].y = y - 1
        p1[29].x = x - 13; p1[29].y = y - 1
        p1[30].x = x - 13; p1[30].y = y
        p1[31].x = x - 12; p1[31].y = y
        ctx.beginPath()
        for n, p in enumerate(p1):  # pylint: disable=invalid-name
            if not n:
                ctx.moveTo(p.x, p.y)
            else:
                ctx.lineTo(p.x, p.y)
        ctx.closePath(); ctx.fill(); ctx.stroke()

        # hublots
        for i in range(5):
            ctx.beginPath()
            ctx.arc(x - 8 + 5 * i + 1, y + 1, 1, 0, 2 * math.pi, False)
            ctx.closePath(); ctx.stroke()  # no fill

        # more stuff if dislodged
        if self._dislodged_origin is not None:
            self.render_as_dislodged(x, y, ctx)


class Ownership(Renderable):
    """ OwnerShip """

    def __init__(self, position: 'Position', role: Role, center: Center) -> None:
        self._position = position
        self._role = role
        self._center = center

    def render(self, ctx: typing.Any) -> None:
        """put me on screen """

        fill_color = self._position.variant.colour_table[self._role]
        ctx.fillStyle = fill_color.str_value()

        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        position = self._position.variant.position_table[self._center]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        ctx.beginPath()
        ctx.fillRect(x - 4, y - 4, 8, 8)
        ctx.strokeRect(x - 4, y - 4, 8, 8)
        ctx.closePath(); ctx.fill(); ctx.stroke()


class Forbidden(Renderable):
    """ Forbidden """

    def __init__(self, position: 'Position', region: Region) -> None:
        self._position = position
        self._region = region

    def render(self, ctx: typing.Any) -> None:
        """put me on screen """

        outline_colour = ColourRecord(red=255, green=0, blue=0)
        ctx.strokeStyle = outline_colour.str_value()

        region = self._region
        zone = region.zone
        position = self._position.variant.position_table[zone]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        ctx.beginPath()
        ctx.moveTo(x + 6, y + 6)
        ctx.lineTo(x - 6, y - 6)
        ctx.moveTo(x + 6, y - 6)
        ctx.lineTo(x - 6, y + 6)
        ctx.closePath(); ctx.stroke()


class Position(Renderable):
    """ A position that can be displayed """

    def __init__(self, server_dict: typing.Dict[str, typing.Any], variant: Variant) -> None:

        self._variant = variant

        # ownerships
        ownerships = server_dict['ownerships']
        self._ownerships: typing.List[Ownership] = list()
        for center_num_str, role_num in ownerships.items():
            center_num = int(center_num_str)
            center = variant._centers[center_num]
            role = variant._roles[role_num]
            ownership = Ownership(self, role, center)
            self._ownerships.append(ownership)

        # dict that says which unit is on a region
        self._occupant: typing.Dict[Region, Unit] = dict()

        # units
        units = server_dict['units']
        self._units: typing.List[Unit] = list()
        for role_num_str, role_units in units.items():
            role_num = int(role_num_str)
            role = variant._roles[role_num]
            for type_unit_code, zone_number in role_units:
                type_unit = UnitTypeEnum.from_code(type_unit_code)
                zone = variant._zones[zone_number]
                if type_unit is UnitTypeEnum.ARMY_UNIT:
                    unit = Army(self, role, zone, None)
                if type_unit is UnitTypeEnum.FLEET_UNIT:
                    unit = Fleet(self, role, zone, None)  # type: ignore
                self._units.append(unit)
                region = zone.region
                self._occupant[region] = unit

        # forbiddens
        forbiddens = server_dict['forbiddens']
        self._forbiddens: typing.List[Forbidden] = list()
        for region_num in forbiddens:
            region = variant._regions[region_num]
            forbidden = Forbidden(self, region)
            self._forbiddens.append(forbidden)

        # dislodged_units
        dislodged_ones = server_dict['dislodged_ones']
        self._dislodged_units: typing.List[Unit] = list()
        for role_num_str, role_units in dislodged_ones.items():
            role_num = int(role_num_str)
            role = variant._roles[role_num]
            for type_unit_code, zone_number, dislodger_region_number in role_units:
                type_unit = UnitTypeEnum.from_code(type_unit_code)
                zone = variant._zones[zone_number]
                dislodger_region = variant._regions[dislodger_region_number]
                if type_unit is UnitTypeEnum.ARMY_UNIT:
                    dislodged_unit = Army(self, role, zone, dislodger_region)
                if type_unit is UnitTypeEnum.FLEET_UNIT:
                    dislodged_unit = Fleet(self, role, zone, dislodger_region)  # type: ignore
                self._dislodged_units.append(dislodged_unit)
                # the dislodger occupying the region is forgotten
                region = zone.region
                self._occupant[region] = unit

    def render(self, ctx: typing.Any) -> None:
        """put me on screen """

        # ownerships
        for ownership in self._ownerships:
            ownership.render(ctx)

        # units
        for unit in self._units:
            unit.render(ctx)

        # forbiddens
        for forbidden in self._forbiddens:
            forbidden.render(ctx)

        # dislodged_units
        for dislodged_unit in self._dislodged_units:
            dislodged_unit.render(ctx)

    @property
    def variant(self) -> Variant:
        """ property """
        return self._variant


class Order(Renderable):
    """ Order """

    def __init__(self, position: 'Position', order_type: OrderTypeEnum, active_unit: Unit, passive_unit: typing.Optional[Unit], destination_zone: typing.Optional[Zone]) -> None:
        self._position = position
        self._order_type = order_type
        self._active_unit = active_unit
        self._passive_unit = passive_unit
        self._destination_zone = destination_zone

    def render(self, ctx: typing.Any) -> None:
        """put me on screen """

        # -- moves --

        if self._order_type is OrderTypeEnum.ATTACK_ORDER:

            assert self._destination_zone is not None

            # red color : attack
            stroke_color = ColourRecord(red=255, green=0, blue=0)
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            # an arrow (move)
            from_point = self._position.variant.position_table[self._active_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            ctx.beginPath()
            draw_arrow(from_point.x_pos, from_point.y_pos, dest_point.x_pos, dest_point.y_pos, ctx)
            ctx.closePath(); ctx.stroke()

        if self._order_type is OrderTypeEnum.OFF_SUPPORT_ORDER:

            assert self._passive_unit is not None
            assert self._destination_zone is not None

            # red color : support to attack
            stroke_color = ColourRecord(red=255, green=0, blue=0)
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            # a dashed arrow (passive move)
            from_point = self._position.variant.position_table[self._passive_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            ctx.setLineDash([4, 2]); ctx.beginPath()
            draw_arrow(from_point.x_pos, from_point.y_pos, dest_point.x_pos, dest_point.y_pos, ctx)
            ctx.closePath(); ctx.stroke(); ctx.setLineDash([])

            # a line (support)
            from_point2 = self._position.variant.position_table[self._active_unit.zone]
            dest_point2 = PositionRecord((from_point.x_pos + dest_point.x_pos) // 2, (from_point.y_pos + dest_point.y_pos) // 2)
            ctx.beginPath()
            ctx.moveTo(from_point2.x_pos, from_point2.y_pos)
            ctx.lineTo(dest_point2.x_pos, dest_point2.y_pos, ctx)
            ctx.closePath(); ctx.stroke()

        if self._order_type is OrderTypeEnum.DEF_SUPPORT_ORDER:

            assert self._passive_unit is not None

            # green for peaceful defensive support
            stroke_color = ColourRecord(red=0, green=255, blue=0)
            ctx.strokeStyle = stroke_color.str_value()

            # put a dashed circle (stand) over unit
            center_point = self._position.variant.position_table[self._passive_unit.zone]
            ctx.setLineDash([4, 2])
            ctx.beginPath()
            ctx.arc(center_point.x_pos, center_point.y_pos, 12, 0, 2 * math.pi, False)
            ctx.closePath(); ctx.stroke(); ctx.setLineDash([])

            # put a line (support)
            from_point = self._position.variant.position_table[self._active_unit.zone]
            dest_point = self._position.variant.position_table[self._passive_unit.zone]
            ctx.beginPath()
            ctx.moveTo(from_point.x_pos, from_point.y_pos)
            ctx.lineTo(dest_point.x_pos, dest_point.y_pos)
            ctx.closePath(); ctx.stroke()

        if self._order_type is OrderTypeEnum.HOLD_ORDER:

            # green for peaceful hold
            stroke_color = ColourRecord(red=0, green=255, blue=0)
            ctx.strokeStyle = stroke_color.str_value()

            center_point = self._position.variant.position_table[self._active_unit.zone]

            # put a circle (stand) around unit
            ctx.beginPath()
            ctx.arc(center_point.x_pos, center_point.y_pos, 12, 0, 2 * math.pi, False)
            ctx.closePath(); ctx.stroke()

        if self._order_type is OrderTypeEnum.CONVOY_ORDER:

            assert self._passive_unit is not None
            assert self._destination_zone is not None

            # blue for convoy
            stroke_color = ColourRecord(red=0, green=0, blue=255)
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            # a dashed arrow (passive move)
            from_point = self._position.variant.position_table[self._passive_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            ctx.setLineDash([4, 2]); ctx.beginPath()
            draw_arrow(from_point.x_pos, from_point.y_pos, dest_point.x_pos, dest_point.y_pos, ctx)
            ctx.closePath(); ctx.stroke(); ctx.setLineDash([])

            # put a line (convoy)
            from_point2 = self._position.variant.position_table[self._active_unit.zone]
            dest_point2 = PositionRecord((from_point.x_pos + dest_point.x_pos) // 2, (from_point.y_pos + dest_point.y_pos) // 2)
            ctx.beginPath()
            ctx.moveTo(from_point2.x_pos, from_point2.y_pos)
            ctx.lineTo(dest_point2.x_pos, dest_point2.y_pos)
            ctx.closePath(); ctx.stroke()

        # -- retreats --

        if self._order_type is OrderTypeEnum.RETREAT_ORDER:

            assert self._destination_zone is not None

            # orange for retreat
            stroke_color = ColourRecord(255, 127, 0)  # orange-ish
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            # put an arrow (move/retreat)
            from_point = self._position.variant.position_table[self._active_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            ctx.beginPath()
            draw_arrow(from_point.x_pos, from_point.y_pos, dest_point.x_pos, dest_point.y_pos, ctx)
            ctx.closePath(); ctx.stroke()

        if self._order_type is OrderTypeEnum.DISBAND_ORDER:

            # orange for retreat
            stroke_color = ColourRecord(255, 127, 0)  # orange-ish
            ctx.strokeStyle = stroke_color.str_value()

            # put a cross over unit
            cross_center_point = self._position.variant.position_table[self._active_unit.zone]
            ctx.beginPath()
            ctx.moveTo(cross_center_point.x_pos + 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos - 8, cross_center_point.y_pos + 8)
            ctx.moveTo(cross_center_point.x_pos - 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos + 8, cross_center_point.y_pos + 8)
            ctx.closePath(); ctx.stroke()

        # -- builds --

        if self._order_type is OrderTypeEnum.BUILD_ORDER:

            # put fake unit
            self._active_unit.render(ctx)

            # grey for builds
            stroke_color = ColourRecord(127, 127, 127)
            ctx.strokeStyle = stroke_color.str_value()

            # put a square around unit
            cross_center_point = self._position.variant.position_table[self._active_unit.zone]
            ctx.beginPath()
            ctx.rect(cross_center_point.x_pos - 8, cross_center_point.y_pos - 8, 16, 16)
            ctx.closePath(); ctx.stroke()

        if self._order_type is OrderTypeEnum.REMOVE_ORDER:

            # grey for builds
            stroke_color = ColourRecord(127, 127, 127)
            ctx.strokeStyle = stroke_color.str_value()

            # put a cross over unit
            cross_center_point = self._position.variant.position_table[self._active_unit.zone]
            ctx.beginPath()
            ctx.moveTo(cross_center_point.x_pos + 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos - 8, cross_center_point.y_pos + 8)
            ctx.moveTo(cross_center_point.x_pos - 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos + 8, cross_center_point.y_pos + 8)
            ctx.closePath(); ctx.stroke()


class Orders(Renderable):
    """ A set of orders that can be displayed / requires position """

    def __init__(self, server_dict: typing.Dict[str, typing.Any], position: Position) -> None:

        self._position = position

        # fake units - they must go first
        fake_units = server_dict['fake_units']
        self._fake_units: typing.List[Unit] = list()
        for _, unit_type_num, zone_num, role_num, _, _ in fake_units:
            unit_type = UnitTypeEnum.from_code(unit_type_num)
            zone = self._position.variant.zones[zone_num]
            role = self._position.variant.roles[role_num]
            if unit_type is UnitTypeEnum.ARMY_UNIT:
                fake_unit = Army(self._position, role, zone, None)
            if unit_type is UnitTypeEnum.FLEET_UNIT:
                fake_unit = Fleet(self._position, role, zone, None)  # type: ignore
            self._fake_units.append(fake_unit)

        # orders
        orders = server_dict['orders']
        self._orders: typing.List[Order] = list()
        for _, _, order_type_num, active_unit_num, passive_unit_num, destination_zone_num in orders:

            order_type = OrderTypeEnum.from_code(order_type_num)
            assert order_type is not None

            zone_active_unit = self._position.variant.zones[active_unit_num]
            region_active_unit = zone_active_unit.region
            active_unit = self._position._occupant[region_active_unit]

            passive_unit = None
            if passive_unit_num != 0:
                zone_passive_unit = self._position.variant.zones[passive_unit_num]
                region_passive_unit = zone_passive_unit.region
                passive_unit = self._position._occupant[region_passive_unit]

            destination_zone = None
            if destination_zone_num != 0:
                destination_zone = self._position.variant.zones[destination_zone_num]

            order = Order(self._position, order_type, active_unit, passive_unit, destination_zone)
            self._orders.append(order)

    def render(self, ctx: typing.Any) -> None:
        """put me on screen """

        # orders
        for order in self._orders:
            order.render(ctx)
