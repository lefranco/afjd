""" mapping """

# pylint: disable=pointless-statement, expression-not-assigned


import enum
import abc
import math

# pylint: disable=pointless-statement, expression-not-assigned, multiple-statements
# noqa: E702

import geometry

def shorten_arrow(x_start: int, y_start: int, x_dest: int, y_dest: int):
    """ shorten the segment a little bit (returns new x_dest, y_dest) """
    epsilon = 5

    delta_x = x_dest - x_start
    delta_y = y_dest - y_start
    dist = math.sqrt(delta_x**2 +delta_y**2)
    if dist < 2 * epsilon:
        return x_dest, y_dest
    new_dist = dist - epsilon
    ratio = new_dist / dist
    new_x_dest = x_start + ratio * delta_x
    new_y_dest = y_start + ratio * delta_y
    return new_x_dest, new_y_dest

def draw_arrow(x_start: int, y_start: int, x_dest: int, y_dest: int, ctx) -> None:
    """ low level draw an arrow """

    # the ctx.strokeStyle and ctx.fillStyle should be defined

    # first draw the arrow line

    ctx.beginPath()
    ctx.moveTo(x_start, y_start)
    ctx.lineTo(x_dest, y_dest)
    ctx.stroke(); ctx.closePath()

    # second draw the arrow head
    ctx.save()

    ctx.translate(x_dest, y_dest)
    angle = - math.atan2(x_start - x_dest, y_start - y_dest)
    ctx.rotate(angle)
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(-3, 6)
    ctx.lineTo(3, 6)
    ctx.fill(); ctx.closePath()

    ctx.restore()


class Renderable:
    """ Renderable """

    @abc.abstractmethod
    def render(self, ctx) -> None:
        """ render = display """


@enum.unique
class RegionTypeEnum(enum.Enum):
    """ RegionTypeEnum """

    LAND_REGION = enum.auto()
    COAST_REGION = enum.auto()
    SEA_REGION = enum.auto()

    @staticmethod
    def from_code(code: int):
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
    def from_code(code: int):
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
    def from_code(code: int):
        """ from_code """
        for season in SeasonEnum:
            if season.value == code:
                return season
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
    def from_code(code: int):
        """ from_code """
        for order_type in OrderTypeEnum:
            if order_type.value == code:
                return order_type
        return None

    def compatible(self, advancement_season: SeasonEnum) -> bool:
        """ type order compatble with season """
        if advancement_season in [SeasonEnum.SPRING_SEASON, SeasonEnum.AUTUMN_SEASON]:
            return self in [OrderTypeEnum.ATTACK_ORDER, OrderTypeEnum.OFF_SUPPORT_ORDER, OrderTypeEnum.DEF_SUPPORT_ORDER, OrderTypeEnum.HOLD_ORDER, OrderTypeEnum.CONVOY_ORDER]
        if advancement_season in [SeasonEnum.SUMMER_SEASON, SeasonEnum.WINTER_SEASON]:
            return self in [OrderTypeEnum.RETREAT_ORDER, OrderTypeEnum.DISBAND_ORDER]
        if advancement_season is SeasonEnum.ADJUST_SEASON:
            return self in [OrderTypeEnum.BUILD_ORDER, OrderTypeEnum.REMOVE_ORDER]
        return False


class Center:
    """ A Center """

    def __init__(self, region: 'Region') -> None:

        # the region in which is the center
        self._region = region

        # the owner at start of the game
        self._owner_start = None

    @property
    def region(self) -> 'Region':
        """ property """
        return self._region

    @property
    def owner_start(self):
        """ property """
        return self._owner_start

    @owner_start.setter
    def owner_start(self, owner_start: 'Role') -> None:
        """ setter """
        self._owner_start = owner_start


class CoastType:
    """ A CoastType """

    def __init__(self, code: int) -> None:
        self._code = code


class Region:
    """ A region """

    def __init__(self, identifier: int, region_type: RegionTypeEnum) -> None:

        self._identifier = identifier

        # the type of the region land, coast or sea
        self._region_type = region_type

        # if the region has a center
        self._center = None

        # the zone (for localisation)
        self._zone = None

        # the unit occupying the region (for identifying units)
        self._occupant = None

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def center(self):
        """ property """
        return self._center

    @center.setter
    def center(self, center: Center) -> None:
        """ setter """
        self._center = center

    @property
    def zone(self):
        """ property """
        return self._zone

    @zone.setter
    def zone(self, zone: 'Zone') -> None:
        """ setter """
        self._zone = zone


class Zone:
    """ A zone """

    def __init__(self, identifier: int, region: Region, coast_type) -> None:

        self._identifier = identifier

        # most of the time zone = region
        self._region = region

        # for the special zones that have a specific coast
        self._coast_type = coast_type

        # other zones one may access by fleet and army
        self._neighbours = {u: list() for u in UnitTypeEnum}

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def coast_type(self):
        """ property """
        return self._coast_type

    @property
    def region(self) -> Region:
        """ property """
        return self._region

    @property
    def neighbours(self):
        """ property """
        return self._neighbours

    @neighbours.setter
    def neighbours(self, neighbours) -> None:
        """ setter """
        self._neighbours = neighbours


class Role:
    """ a Role """

    def __init__(self, identifier) -> None:

        self._identifier = identifier

        # start centers the role have
        self._start_centers = list()

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def start_centers(self):
        """ property """
        return self._start_centers

    @start_centers.setter
    def start_centers(self, start_centers) -> None:
        """ setter """
        self._start_centers = start_centers


class ColourRecord:
    """ A colour """

    def __init__(self, red, green, blue) -> None:
        self.red = red
        self.green = green
        self.blue = blue

    def outline_colour(self) -> 'ColourRecord':
        """ outline_colour """
        the_sum = self.red + self.green + self.blue
        if the_sum < (3 * 255) // 10:
            return ColourRecord(red=255 // 2, green=255 // 2, blue=255 // 2)
        return ColourRecord(red=0, green=0, blue=0)

    def str_value(self) -> str:
        """ str_value """
        return f"rgb({self.red}, {self.green}, {self.blue})"


# position
DISLODGED_TEXT_BACKGROUND_COLOUR = ColourRecord(255, 255, 255)  # white
DISLODGED_COLOUR = ColourRecord(255, 127, 0)  # orange
DISLODGED_SHIFT = -5

# orders
ATTACK_COLOUR = ColourRecord(red=255, green=25, blue=25)  # red
SUPPORT_COLOUR = ColourRecord(red=25, green=255, blue=25)  # green
CONVOY_COLOUR = ColourRecord(red=25, green=25, blue=255)  # blue
RETREAT_COLOUR = ColourRecord(red=0, green=0, blue=0)  # black
ADJUSTMENT_COLOUR = ColourRecord(red=0, green=0, blue=0)  # black

# legend
LEGEND_COLOUR = ColourRecord(red=0, green=0, blue=0)  # black

# center
CENTER_COLOUR = ColourRecord(red=225, green=225, blue=225)  # light grey


class Variant(Renderable):
    """ A variant """

    def __init__(self, raw_variant_content, raw_parameters_content) -> None:

        # =================
        # from variant file
        # =================

        # load the variant from dict
        self._raw_variant_content = raw_variant_content

        # load the regions
        self._regions = dict()
        for num, code in enumerate(self._raw_variant_content['regions']):
            number = num + 1
            region_type = RegionTypeEnum.from_code(code)
            assert region_type is not None
            region = Region(number, region_type)
            self._regions[number] = region

        # load the centers
        self._centers = dict()
        for num, num_region in enumerate(self._raw_variant_content['centers']):
            number = num + 1
            region = self._regions[num_region]
            center = Center(region)
            region.center = center
            self._centers[number] = center

        # load the roles (starts at zero)
        self._roles = dict()
        for num in range(self._raw_variant_content['roles']['number']):
            number = num + 1
            role = Role(number)
            self._roles[number] = role

        assert len(self._raw_variant_content['start_centers']) == len(self._roles)

        # load start centers
        self._start_centers = dict()
        for num, role_start_centers in enumerate(self._raw_variant_content['start_centers']):
            number = num + 1
            role = self._roles[number]
            for number_center in role_start_centers:
                start_center = self._centers[number_center]
                start_center.owner_start = role
                role.start_centers.append(start_center)

        # load the coast types
        self._coast_types = dict()
        for num in range(self._raw_variant_content['type_coasts']['number']):
            number = num + 1
            coast_type = CoastType(number)
            self._coast_types[number] = coast_type

        # load the zones

        # first the standard zones
        self._zones = dict()
        for num, region in enumerate(self._regions.values()):
            number = num + 1
            zone = Zone(number, region, None)
            region.zone = zone
            self._zones[number] = zone

        # need an offset
        offset = max(self._zones.keys())

        # then the special coast zones
        for num, (region_num, coast_type_num) in enumerate(self._raw_variant_content['coastal_zones']):
            number = num + 1
            region = self._regions[region_num]
            coast_type = self._coast_types[coast_type_num]
            zone = Zone(offset + number, region, coast_type)
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
        self._year_zero = int(self._raw_variant_content['year_zero'])

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

        self._name_table = dict()
        self._colour_table = dict()
        self._position_table = dict()
        self._legend_position_table = dict()
        self._role_add_table = dict()

        # load the map size
        data_dict = self._raw_parameters_content['map']
        width = data_dict['width']
        height = data_dict['height']
        map_size = geometry.PositionRecord(x_pos=width, y_pos=height)
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

        # add GM role
        role = Role(0)
        self._roles[0] = role

        # load the roles names and colours
        assert len(self._raw_parameters_content['roles']) == len(self._roles)
        for role_num_str, data_dict in self._raw_parameters_content['roles'].items():
            role_num = int(role_num_str)
            role = self._roles[role_num]
            name = data_dict['name']
            self._name_table[role] = name
            red = data_dict['red']
            green = data_dict['green']
            blue = data_dict['blue']
            colour = ColourRecord(red=red, green=green, blue=blue)
            self._colour_table[role] = colour
            self._role_add_table[role] = (data_dict['adjective_name'], data_dict['letter_name'])

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
                region_name = self._name_table[zone.region.zone]
                coast_name = self._name_table[zone.coast_type]
                name = f"{region_name}{coast_name}"
            else:
                name = data_dict['name']

            self._name_table[zone] = name
            x_pos = data_dict['x_legend_pos']
            y_pos = data_dict['y_legend_pos']
            legend_position = geometry.PositionRecord(x_pos=x_pos, y_pos=y_pos)
            self._legend_position_table[zone] = legend_position
            x_pos = data_dict['x_pos']
            y_pos = data_dict['y_pos']
            unit_position = geometry.PositionRecord(x_pos=x_pos, y_pos=y_pos)
            self._position_table[zone] = unit_position

        # load the centers localisations
        assert len(self._raw_parameters_content['centers']) == len(self._centers)
        for center_num_str, data_dict in self._raw_parameters_content['centers'].items():
            center_num = int(center_num_str)
            center = self._centers[center_num]
            x_pos = data_dict['x_pos']
            y_pos = data_dict['y_pos']
            center_position = geometry.PositionRecord(x_pos=x_pos, y_pos=y_pos)
            self._position_table[center] = center_position

        # load seasons names
        assert len(self._raw_parameters_content['seasons']) == len(SeasonEnum)
        for season_num_str, data_dict in self._raw_parameters_content['seasons'].items():
            season_num = int(season_num_str)
            season = SeasonEnum.from_code(season_num)
            assert season is not None
            self._name_table[season] = data_dict['name']

        # load orders types names
        assert len(self._raw_parameters_content['orders']) == len(OrderTypeEnum)
        for order_type_num_str, data_dict in self._raw_parameters_content['orders'].items():
            order_type_num = int(order_type_num_str)
            order_type = OrderTypeEnum.from_code(order_type_num)
            assert order_type is not None
            self._name_table[order_type] = data_dict['name']

    def closest_zone(self, designated_pos: geometry.PositionRecord):
        """ closest_zone """

        closest_zone = None
        distance_closest = None
        for zone in self._zones.values():
            zone_pos = self.position_table[zone]
            distance = designated_pos.distance(zone_pos)
            if distance_closest is None or distance < distance_closest:
                closest_zone = zone
                distance_closest = distance

        return closest_zone

    def render(self, ctx) -> None:
        """ render the legends only """

        # colour
        legend_colour = LEGEND_COLOUR
        ctx.fillStyle = legend_colour.str_value()

        # put legends
        for zone in self._zones.values():
            position = self._legend_position_table[zone]
            x_pos = position.x_pos
            y_pos = position.y_pos
            if zone.coast_type:
                legend = self._name_table[zone.coast_type]
            else:
                legend = self._name_table[zone]
            ctx.fillText(legend, x_pos, y_pos)

        # put centers

        fill_color = CENTER_COLOUR
        ctx.fillStyle = fill_color.str_value()

        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        for center in self._centers.values():

            position = self._position_table[center]
            x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

            ctx.beginPath()
            ctx.arc(x, y, 4, 0, 2 * math.pi, False)
            ctx.fill(); ctx.stroke(); ctx.closePath()

    def extract_names(self):
        """ extract the names we are using to pass them to adjudicator """

        def extract_role_data(role):
            """ extract_role_data """
            additional = self._role_add_table[role]
            return [self._name_table[role], additional[0], additional[1]]

        def extract_zone_data(zone):
            """ extract_zone_data """
            if zone.coast_type:
                return ''
            return self._name_table[zone]

        role_names = {k: extract_role_data(v) for k, v in self._roles.items()}
        zone_names = {k: extract_zone_data(v) for k, v in self._zones.items()}
        coast_names = {k: self._name_table[v] for k, v in self._coast_types.items()}

        return {'roles': role_names, 'zones': zone_names, 'coasts': coast_names}

    @property
    def map_size(self) -> geometry.PositionRecord:
        """ property """
        return self._map_size

    @property
    def name_table(self):
        """ property """
        return self._name_table

    @property
    def colour_table(self):
        """ property """
        return self._colour_table

    @property
    def position_table(self):
        """ property """
        return self._position_table

    @property
    def zones(self):
        """ property """
        return self._zones

    @property
    def roles(self):
        """ property """
        return self._roles

    @property
    def year_zero(self) -> int:
        """ property """
        return self._year_zero


class Point:
    """ Point for easier compatbility with old C software (do not use a record here) """
    def __init__(self) -> None:
        self.x = 0  # pylint: disable=invalid-name
        self.y = 0  # pylint: disable=invalid-name


class Unit(Renderable):  # pylint: disable=abstract-method
    """ A unit """

    def __init__(self, position: 'Position', role: Role, zone: Zone, dislodged_origin) -> None:
        self._position = position
        self._role = role
        self._zone = zone
        self._dislodged_origin = dislodged_origin

    def render_as_dislodged(self, x_pos: int, y_pos: int, ctx) -> None:
        """ render additional stuff when dislodged """

        assert self._dislodged_origin is not None

        # because we know names of zones but not of regions
        zone_dislodger = self._dislodged_origin.zone
        dislodger_legend = self._position.variant.name_table[zone_dislodger]

        # dislodger

        dislodger_back_colour = DISLODGED_TEXT_BACKGROUND_COLOUR
        ctx.fillStyle = dislodger_back_colour.str_value()
        ctx.rect(x_pos + 10, y_pos - 17, 20, 10)
        ctx.fill()

        dislodger_colour = DISLODGED_COLOUR
        ctx.fillStyle = dislodger_colour.str_value()
        ctx.fillText(dislodger_legend, x_pos + 12, y_pos - 9)

        ctx.lineWidth = 2

        # circle
        ctx.beginPath()
        circle_colour = DISLODGED_COLOUR
        ctx.strokeStyle = circle_colour.str_value()
        ctx.arc(x_pos, y_pos, 12, 0, 2 * math.pi, False)
        ctx.stroke(); ctx.closePath()  # no fill

        # put back
        ctx.lineWidth = 1

    def save_json(self):
        """ Save to  dict """

        if isinstance(self, Fleet):
            type_unit = UnitTypeEnum.FLEET_UNIT
        if isinstance(self, Army):
            type_unit = UnitTypeEnum.ARMY_UNIT

        json_dict = {
            "type_unit": type_unit.value,
            "role": self._role.identifier,
            "zone": self._zone.identifier
        }
        if self._dislodged_origin is not None:
            json_dict.update({"dislodged_origin": self._dislodged_origin.identifier})
        return json_dict

    @property
    def zone(self) -> Zone:
        """ property """
        return self._zone

    @property
    def role(self) -> Role:
        """ property """
        return self._role

    def __str__(self) -> str:
        variant = self._position.variant
        zone = self._zone
        name = variant.name_table[zone]
        if isinstance(self, Army):
            type_name = variant.name_table[UnitTypeEnum.ARMY_UNIT]
        if isinstance(self, Fleet):
            type_name = variant.name_table[UnitTypeEnum.FLEET_UNIT]
        type_name_initial = type_name[0]
        return f"{type_name_initial} {name}"


class Army(Unit):
    """ An army """

    # use init from parent class

    def render(self, ctx) -> None:
        """put me on screen """

        fill_color = self._position.variant.colour_table[self._role]
        ctx.fillStyle = fill_color.str_value()

        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        position = self._position.variant.position_table[self._zone]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        # shift for dislodged units
        if self._dislodged_origin is not None:
            x += DISLODGED_SHIFT  # pylint: disable=invalid-name
            y += DISLODGED_SHIFT  # pylint: disable=invalid-name

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
        ctx.fill(); ctx.stroke(); ctx.closePath()

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
        ctx.fill(); ctx.stroke(); ctx.closePath()

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
        ctx.fill(); ctx.stroke(); ctx.closePath()

        # cercle autour roue exterieure
        # simplified
        ctx.beginPath()
        ctx.arc(x, y, 6, 0, 2 * math.pi, False)
        ctx.fill(); ctx.stroke(); ctx.closePath()

        # roue interieure
        # simplified
        ctx.beginPath()
        ctx.arc(x, y, 2, 0, 2 * math.pi, False)
        ctx.fill(); ctx.stroke(); ctx.closePath()

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
        ctx.stroke(); ctx.closePath()  # no fill

        # more stuff if dislodged
        if self._dislodged_origin is not None:
            self.render_as_dislodged(x, y, ctx)


class Fleet(Unit):
    """ An fleet """

    # use init from parent class

    def render(self, ctx) -> None:
        """put me on screen """

        fill_color = self._position.variant.colour_table[self._role]
        ctx.fillStyle = fill_color.str_value()

        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        position = self._position.variant.position_table[self._zone]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        # shift for dislodged units
        if self._dislodged_origin is not None:
            x += DISLODGED_SHIFT  # pylint: disable=invalid-name
            y += DISLODGED_SHIFT  # pylint: disable=invalid-name

        # gros oeuvre
        p1 = [Point() for _ in range(33)]  # pylint: disable=invalid-name
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
        p1[32].x = x - 15; p1[32].y = y + 4
        ctx.beginPath()
        for n, p in enumerate(p1):  # pylint: disable=invalid-name
            if not n:
                ctx.moveTo(p.x, p.y)
            else:
                ctx.lineTo(p.x, p.y)
        ctx.fill(); ctx.stroke(); ctx.closePath()

        # hublots
        for i in range(5):
            ctx.beginPath()
            ctx.arc(x - 8 + 5 * i + 1, y + 1, 1, 0, 2 * math.pi, False)
            ctx.stroke(); ctx.closePath()  # no fill

        # more stuff if dislodged
        if self._dislodged_origin is not None:
            self.render_as_dislodged(x, y, ctx)


class Ownership(Renderable):
    """ OwnerShip """

    def __init__(self, position: 'Position', role: Role, center: Center) -> None:
        self._position = position
        self._role = role
        self._center = center

    @property
    def role(self) -> Role:
        """ property """
        return self._role

    def render(self, ctx) -> None:
        """put me on screen """

        fill_color = self._position.variant.colour_table[self._role]
        ctx.fillStyle = fill_color.str_value()

        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        position = self._position.variant.position_table[self._center]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        ctx.beginPath()
        ctx.arc(x, y, 4, 0, 2 * math.pi, False)
        ctx.fill(); ctx.stroke(); ctx.closePath()


class Forbidden(Renderable):
    """ Forbidden """

    def __init__(self, position: 'Position', region: Region) -> None:
        self._position = position
        self._region = region

    def render(self, ctx) -> None:
        """put me on screen """

        outline_colour = ColourRecord(red=255, green=0, blue=0)
        ctx.strokeStyle = outline_colour.str_value()
        ctx.lineWidth = 2

        region = self._region
        zone = region.zone
        position = self._position.variant.position_table[zone]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        ctx.beginPath()
        ctx.moveTo(x + 6, y + 6)
        ctx.lineTo(x - 6, y - 6)
        ctx.moveTo(x + 6, y - 6)
        ctx.lineTo(x - 6, y + 6)
        ctx.stroke(); ctx.closePath()
        ctx.lineWidth = 1


class Position(Renderable):
    """ A position that can be displayed """

    def __init__(self, server_dict, variant: Variant) -> None:

        self._variant = variant

        # ownerships
        ownerships = server_dict['ownerships']
        self._ownerships = list()
        for center_num_str, role_num in ownerships.items():
            center_num = int(center_num_str)
            center = variant._centers[center_num]
            role = variant._roles[role_num]
            ownership = Ownership(self, role, center)
            self._ownerships.append(ownership)

        # dict that says which unit is on a region
        self._occupant_table = dict()

        # units
        units = server_dict['units']
        self._units = list()
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
                self._occupant_table[region] = unit

        # forbiddens
        forbiddens = server_dict['forbiddens']
        self._forbiddens = list()
        for region_num in forbiddens:
            region = variant._regions[region_num]
            forbidden = Forbidden(self, region)
            self._forbiddens.append(forbidden)

        # dislodged_units
        dislodged_ones = server_dict['dislodged_ones']
        self._dislodged_units = list()
        for role_num_str, role_units in dislodged_ones.items():
            role_num = int(role_num_str)
            role = variant._roles[role_num]
            for type_unit_code, zone_number, dislodger_zone_number in role_units:
                type_unit = UnitTypeEnum.from_code(type_unit_code)
                zone = variant._zones[zone_number]
                dislodger_zone = variant._zones[dislodger_zone_number]
                dislodger_region = dislodger_zone.region
                if type_unit is UnitTypeEnum.ARMY_UNIT:
                    dislodged_unit = Army(self, role, zone, dislodger_region)
                if type_unit is UnitTypeEnum.FLEET_UNIT:
                    dislodged_unit = Fleet(self, role, zone, dislodger_region)  # type: ignore
                self._dislodged_units.append(dislodged_unit)
                # the dislodger occupying the region is forgotten
                region = zone.region
                self._occupant_table[region] = dislodged_unit

    def render(self, ctx) -> None:
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

    def closest_unit(self, designated_pos: geometry.PositionRecord, dislodged: bool):
        """ closest_unit """

        closest_unit = None
        distance_closest = None
        search_list = self._dislodged_units if dislodged else self._units
        for unit in search_list:
            zone = unit.zone
            unit_pos = self._variant.position_table[zone]
            distance = designated_pos.distance(unit_pos)
            if distance_closest is None or distance < distance_closest:
                closest_unit = unit
                distance_closest = distance

        return closest_unit

    def has_dislodged(self) -> bool:
        """ has_dislodged """
        return bool(self._dislodged_units)

    def units_list(self):
        """ units_list """
        return self._units

    def role_ratings(self):
        """ a rating of roles """
        raw_dict = {self._variant.name_table[r]: len([o for o in self._ownerships if o.role == r]) for r in {o.role for o in self._ownerships}}
        return {r: raw_dict[r] for r in sorted(raw_dict.keys(), key=lambda r: raw_dict[r], reverse=True)}

    def role_colours(self):
        """ a rating of roles """
        return {self._variant.name_table[r]: self._variant.colour_table[r] for r in {o.role for o in self._ownerships}}

    @property
    def variant(self) -> Variant:
        """ property """
        return self._variant

    @property
    def occupant_table(self):
        """ property """
        return self._occupant_table


DASH_PATTERN = [4, 4]


class Order(Renderable):
    """ Order """

    def __init__(self, position: 'Position', order_type: OrderTypeEnum, active_unit: Unit, passive_unit, destination_zone) -> None:
        self._position = position
        self._order_type = order_type
        self._active_unit = active_unit
        self._passive_unit = passive_unit
        self._destination_zone = destination_zone

    def render(self, ctx) -> None:
        """put me on screen """

        # -- moves --

        if self._order_type is OrderTypeEnum.ATTACK_ORDER:

            assert self._destination_zone is not None

            # red color : attack
            stroke_color = ATTACK_COLOUR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            ctx.lineWidth = 2

            # an arrow (move)
            from_point = self._position.variant.position_table[self._active_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            dest_point_closer_x, dest_point_closer_y = shorten_arrow(from_point.x_pos, from_point.y_pos, dest_point.x_pos, dest_point.y_pos)
            draw_arrow(from_point.x_pos, from_point.y_pos, dest_point_closer_x, dest_point_closer_y, ctx)

            # put back
            ctx.lineWidth = 1

        if self._order_type is OrderTypeEnum.OFF_SUPPORT_ORDER:

            assert self._passive_unit is not None
            assert self._destination_zone is not None

            # red for support to attack
            stroke_color = ATTACK_COLOUR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            ctx.lineWidth = 2
            ctx.setLineDash(DASH_PATTERN)

            # a dashed arrow (passive move)
            from_point = self._position.variant.position_table[self._passive_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            direction = geometry.get_direction(from_point, dest_point)
            next_direction = direction.perpendicular()
            from_point_shifted = from_point.shift(next_direction)
            dest_point_shifted = dest_point.shift(next_direction)
            dest_point_shifted_closer_x, dest_point_shifted_closer_y = shorten_arrow(from_point_shifted.x_pos, from_point_shifted.y_pos, dest_point_shifted.x_pos, dest_point_shifted.y_pos)
            draw_arrow(from_point_shifted.x_pos, from_point_shifted.y_pos, dest_point_shifted_closer_x, dest_point_shifted_closer_y, ctx)

            # put back
            ctx.lineWidth = 1
            ctx.setLineDash([])

            # a line (support)
            from_point2 = self._position.variant.position_table[self._active_unit.zone]
            dest_point2 = geometry.PositionRecord((from_point_shifted.x_pos + dest_point_shifted.x_pos) // 2, (from_point_shifted.y_pos + dest_point_shifted.y_pos) // 2)
            ctx.beginPath()
            ctx.moveTo(from_point2.x_pos, from_point2.y_pos)
            ctx.lineTo(dest_point2.x_pos, dest_point2.y_pos)
            ctx.stroke(); ctx.closePath()

        if self._order_type is OrderTypeEnum.DEF_SUPPORT_ORDER:

            assert self._passive_unit is not None

            # green for peaceful defensive support
            stroke_color = SUPPORT_COLOUR
            ctx.strokeStyle = stroke_color.str_value()

            ctx.lineWidth = 2
            ctx.setLineDash(DASH_PATTERN)

            # prepare the line
            from_point = self._position.variant.position_table[self._active_unit.zone]
            dest_point = self._position.variant.position_table[self._passive_unit.zone]
            direction = geometry.get_direction(from_point, dest_point)
            next_direction = direction.perpendicular()
            dest_point_shifted = dest_point.shift(next_direction)

            # put a dashed circle (stand) over unit
            center_point = self._position.variant.position_table[self._passive_unit.zone]
            center_point_shifted = center_point.shift(next_direction)
            ctx.beginPath()
            ctx.arc(center_point_shifted.x_pos, center_point_shifted.y_pos, 12, 0, 2 * math.pi, False)
            ctx.stroke(); ctx.closePath()

            # put back
            ctx.lineWidth = 1
            ctx.setLineDash([])

            # put the prepared line (support)

            ctx.beginPath()
            ctx.moveTo(from_point.x_pos, from_point.y_pos)
            ctx.lineTo(dest_point_shifted.x_pos, dest_point_shifted.y_pos)
            ctx.stroke(); ctx.closePath()

        if self._order_type is OrderTypeEnum.HOLD_ORDER:

            # green for peaceful hold
            stroke_color = SUPPORT_COLOUR
            ctx.strokeStyle = stroke_color.str_value()

            ctx.lineWidth = 3
            ctx.setLineDash(DASH_PATTERN)

            center_point = self._position.variant.position_table[self._active_unit.zone]

            # put a circle (stand) around unit
            ctx.beginPath()
            ctx.arc(center_point.x_pos, center_point.y_pos, 12, 0, 2 * math.pi, False)
            ctx.stroke(); ctx.closePath()

            # put back
            ctx.lineWidth = 1
            ctx.setLineDash([])

        if self._order_type is OrderTypeEnum.CONVOY_ORDER:

            assert self._passive_unit is not None
            assert self._destination_zone is not None

            # blue for convoy
            stroke_color = CONVOY_COLOUR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            ctx.lineWidth = 2
            ctx.setLineDash(DASH_PATTERN)

            # a dashed arrow (passive move)
            from_point = self._position.variant.position_table[self._passive_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            direction = geometry.get_direction(from_point, dest_point)
            next_direction = direction.perpendicular()
            from_point_shifted = from_point.shift(next_direction)
            dest_point_shifted = dest_point.shift(next_direction)
            dest_point_shifted_closer_x, dest_point_shifted_closer_y = shorten_arrow(from_point_shifted.x_pos, from_point_shifted.y_pos, dest_point_shifted.x_pos, dest_point_shifted.y_pos)
            draw_arrow(from_point_shifted.x_pos, from_point_shifted.y_pos, dest_point_shifted_closer_x, dest_point_shifted_closer_y, ctx)

            # put back
            ctx.lineWidth = 1
            ctx.setLineDash([])

            # put a line (convoy)
            from_point2 = self._position.variant.position_table[self._active_unit.zone]
            dest_point2 = geometry.PositionRecord((from_point_shifted.x_pos + dest_point_shifted.x_pos) // 2, (from_point_shifted.y_pos + dest_point_shifted.y_pos) // 2)
            ctx.beginPath()
            ctx.moveTo(from_point2.x_pos, from_point2.y_pos)
            ctx.lineTo(dest_point2.x_pos, dest_point2.y_pos)
            ctx.stroke(); ctx.closePath()

        # -- retreats --

        if self._order_type is OrderTypeEnum.RETREAT_ORDER:

            assert self._destination_zone is not None

            # orange for retreat
            stroke_color = RETREAT_COLOUR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            ctx.lineWidth = 2

            # put an arrow (move/retreat)
            unit_position = self._position.variant.position_table[self._active_unit.zone]
            from_point = geometry.PositionRecord(x_pos=unit_position.x_pos + DISLODGED_SHIFT, y_pos=unit_position.y_pos + DISLODGED_SHIFT)
            dest_point = self._position.variant.position_table[self._destination_zone]
            draw_arrow(from_point.x_pos + DISLODGED_SHIFT, from_point.y_pos + DISLODGED_SHIFT, dest_point.x_pos, dest_point.y_pos, ctx)

            # put back
            ctx.lineWidth = 1

        if self._order_type is OrderTypeEnum.DISBAND_ORDER:

            # orange for retreat
            stroke_color = RETREAT_COLOUR
            ctx.strokeStyle = stroke_color.str_value()

            ctx.lineWidth = 2

            # put a cross over unit
            unit_position = self._position.variant.position_table[self._active_unit.zone]
            cross_center_point = geometry.PositionRecord(x_pos=unit_position.x_pos + DISLODGED_SHIFT, y_pos=unit_position.y_pos + DISLODGED_SHIFT)
            ctx.beginPath()
            ctx.moveTo(cross_center_point.x_pos + 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos - 8, cross_center_point.y_pos + 8)
            ctx.moveTo(cross_center_point.x_pos - 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos + 8, cross_center_point.y_pos + 8)
            ctx.stroke(); ctx.closePath()

            # put back
            ctx.lineWidth = 1

        # -- builds --

        if self._order_type is OrderTypeEnum.BUILD_ORDER:

            # put fake unit
            self._active_unit.render(ctx)

            # grey for builds
            stroke_color = ADJUSTMENT_COLOUR
            ctx.strokeStyle = stroke_color.str_value()

            ctx.lineWidth = 2

            # put a square around unit
            square_center_point = self._position.variant.position_table[self._active_unit.zone]
            ctx.beginPath()
            ctx.rect(square_center_point.x_pos - 8, square_center_point.y_pos - 8, 16, 16)
            ctx.stroke(); ctx.closePath()

            # put back
            ctx.lineWidth = 1

        if self._order_type is OrderTypeEnum.REMOVE_ORDER:

            # grey for builds
            stroke_color = ADJUSTMENT_COLOUR
            ctx.strokeStyle = stroke_color.str_value()

            ctx.lineWidth = 2

            # put a cross over unit
            cross_center_point = self._position.variant.position_table[self._active_unit.zone]
            ctx.beginPath()
            ctx.moveTo(cross_center_point.x_pos + 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos - 8, cross_center_point.y_pos + 8)
            ctx.moveTo(cross_center_point.x_pos - 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos + 8, cross_center_point.y_pos + 8)
            ctx.stroke(); ctx.closePath()

            # put back
            ctx.lineWidth = 1

    def save_json(self):
        """ Save to  dict """

        json_dict = dict()
        if self._order_type is not None:
            json_dict.update({"order_type": self._order_type.value})
        if self._active_unit is not None:
            json_dict.update({"active_unit": self._active_unit.save_json()})
        if self._passive_unit is not None:
            json_dict.update({"passive_unit": self._passive_unit.save_json()})
        if self._destination_zone is not None:
            json_dict.update({"destination_zone": self._destination_zone.identifier})
        return json_dict

    @property
    def active_unit(self) -> Unit:
        """ property """
        return self._active_unit

    @property
    def order_type(self) -> OrderTypeEnum:
        """ property """
        return self._order_type

    def __str__(self) -> str:

        variant = self._position.variant

        if self._order_type is OrderTypeEnum.ATTACK_ORDER:
            dest_zone_name = variant.name_table[self._destination_zone]
            return f"{self._active_unit} - {dest_zone_name}"
        if self._order_type is OrderTypeEnum.OFF_SUPPORT_ORDER:
            dest_zone_name = variant.name_table[self._destination_zone]
            return f"{self._active_unit} S {self._passive_unit} - {dest_zone_name}"
        if self._order_type is OrderTypeEnum.DEF_SUPPORT_ORDER:
            return f"{self._active_unit} S {self._passive_unit}"
        if self._order_type is OrderTypeEnum.HOLD_ORDER:
            return f"{self._active_unit} H"
        if self._order_type is OrderTypeEnum.CONVOY_ORDER:
            dest_zone_name = variant.name_table[self._destination_zone]
            return f"{self._active_unit} C {self._passive_unit} - {dest_zone_name}"
        if self._order_type is OrderTypeEnum.RETREAT_ORDER:
            dest_zone_name = variant.name_table[self._destination_zone]
            return f"{self._active_unit} R {dest_zone_name}"
        if self._order_type is OrderTypeEnum.DISBAND_ORDER:
            return f"{self._active_unit} A"
        if self._order_type is OrderTypeEnum.BUILD_ORDER:
            return f"+ {self._active_unit}"
        if self._order_type is OrderTypeEnum.REMOVE_ORDER:
            return f"- {self._active_unit}"
        return ""


class Orders(Renderable):
    """ A set of orders that can be displayed / requires position """

    def __init__(self, server_dict, position: Position) -> None:

        self._position = position

        # these fake units are local here - they belong to orders, not the position
        self._fake_units = dict()

        # fake units - they must go first
        #  (they serve for our handling of ihm)
        fake_units = server_dict['fake_units']
        for _, unit_type_num, zone_num, role_num, _, _ in fake_units:
            unit_type = UnitTypeEnum.from_code(unit_type_num)
            zone = self._position.variant.zones[zone_num]
            role = self._position.variant.roles[role_num]
            if unit_type is UnitTypeEnum.ARMY_UNIT:
                fake_unit = Army(self._position, role, zone, None)
            if unit_type is UnitTypeEnum.FLEET_UNIT:
                fake_unit = Fleet(self._position, role, zone, None)  # type: ignore
            self._fake_units[zone_num] = fake_unit

        # orders
        orders = server_dict['orders']
        self._orders = list()
        for _, _, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num in orders:

            order_type = OrderTypeEnum.from_code(order_type_num)
            assert order_type is not None

            if order_type is OrderTypeEnum.BUILD_ORDER:
                active_unit = self._fake_units[active_unit_zone_num]
            else:
                zone_active_unit = self._position.variant.zones[active_unit_zone_num]
                region_active_unit = zone_active_unit.region
                active_unit = self._position.occupant_table[region_active_unit]

            passive_unit = None
            if passive_unit_zone_num != 0:
                zone_passive_unit = self._position.variant.zones[passive_unit_zone_num]
                region_passive_unit = zone_passive_unit.region
                passive_unit = self._position.occupant_table[region_passive_unit]

            destination_zone = None
            if destination_zone_num != 0:
                destination_zone = self._position.variant.zones[destination_zone_num]

            order = Order(self._position, order_type, active_unit, passive_unit, destination_zone)
            self._orders.append(order)

    def insert_order(self, order: Order) -> None:
        """ insert_order """

        # go to region so a build in stp cancels a build in stp sc
        found = [o for o in self._orders if o.active_unit.zone.region == order.active_unit.zone.region]
        if found:
            prev_order = found.pop()
            self._orders.remove(prev_order)
        self._orders.append(order)

        # build : add fake unit (they serve for our handling of ihm)
        if order.order_type is OrderTypeEnum.BUILD_ORDER:
            active_unit = order.active_unit
            active_unit_zone_num = active_unit.zone.identifier
            self._fake_units[active_unit_zone_num] = active_unit

    def remove_order(self, unit: Unit) -> None:
        """ remove_order """

        found = [o for o in self._orders if o.active_unit == unit]
        assert found, "No unit to remove"
        prev_order = found.pop()
        self._orders.remove(prev_order)

        # build : remove fake unit (they serve for our handling of ihm)
        if prev_order.order_type is OrderTypeEnum.BUILD_ORDER:
            active_unit = prev_order.active_unit
            active_unit_zone_num = active_unit.zone.identifier
            del self._fake_units[active_unit_zone_num]

    def empty(self) -> bool:
        """ empty """
        return not self._orders

    def is_ordered(self, unit: Unit) -> bool:
        """ is_ordered """
        for order in self._orders:
            if order.active_unit == unit:
                return True
        return False

    def closest_unit(self, designated_pos: geometry.PositionRecord):
        """ closest_unit """

        closest_unit = None
        distance_closest = None
        search_list = self._fake_units.values()
        for unit in search_list:
            zone = unit.zone
            unit_pos = self._position.variant.position_table[zone]
            distance = designated_pos.distance(unit_pos)
            if distance_closest is None or distance < distance_closest:
                closest_unit = unit
                distance_closest = distance

        return closest_unit

    def erase_orders(self) -> None:
        """ erase all orders """

        self._orders = list()
        self._fake_units = dict()

    def rest_hold(self, role_id) -> None:
        """ set the unordered units orders to hold """

        # should be in season for move orders - not checked here

        units_in_position = set(self._position.units_list())

        # if within a role restrict to that role
        if role_id is not None:
            units_in_position = {u for u in units_in_position if u.role.identifier == role_id}

        ordered_units = {o.active_unit for o in self._orders}
        unordered_units = units_in_position - ordered_units
        for unordered_unit in unordered_units:
            order = Order(self._position, OrderTypeEnum.HOLD_ORDER, unordered_unit, None, None)
            self.insert_order(order)

    def render(self, ctx) -> None:
        """ put me on screen """

        # orders
        for order in self._orders:
            order.render(ctx)

    def save_json(self):
        """ export as list of dict """
        # Note : we do not export fake units
        json_data = list()
        for order in self._orders:
            json_data.append(order.save_json())
        return json_data

    def __str__(self) -> str:
        return '\n'.join([str(o) for o in self._orders])
