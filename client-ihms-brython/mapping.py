""" mapping """

# pylint: disable=pointless-statement, expression-not-assigned, multiple-statements, wrong-import-order, wrong-import-position


from abc import abstractmethod
from math import atan2, sqrt, pi, inf

import geometry
import center_design
import unit_design

# proximity necessary for a center or a unit (to come before the zone)
# otherwise the zones have no chance since units are first
MAX_PROXIMITY_ITEM_UNIT = 10

# for filling zones coloring
TRANSPARENCY_OWNER = 0.70

# for filling zones fog
TRANSPARENCY_FOG = 0.60

# for shortening arrow
EPSILON_SHORTER_ARROW = 3


def shorten_arrow(x_start: int, y_start: int, x_dest: int, y_dest: int):
    """ shorten the segment a little bit (returns new x_dest, y_dest) """

    delta_x = x_dest - x_start
    delta_y = y_dest - y_start
    dist = sqrt(delta_x**2 + delta_y**2)
    if dist < 2 * EPSILON_SHORTER_ARROW:
        return x_dest, y_dest

    new_dist = dist - EPSILON_SHORTER_ARROW
    ratio = new_dist / dist
    new_x_dest = x_start + ratio * delta_x
    new_y_dest = y_start + ratio * delta_y
    return new_x_dest, new_y_dest


def draw_arrow(x_start: int, y_start: int, x_dest: int, y_dest: int, ctx) -> None:
    """ low level draw an arrow """

    # the ctx.strokeStyle and ctx.fillStyle should be defined
    # the ctx.lineWidth should be defined

    # first draw the arrow line

    ctx.beginPath()
    ctx.moveTo(x_start, y_start)
    ctx.lineTo(x_dest, y_dest)
    ctx.stroke(); ctx.closePath()

    # keep this
    angle = - atan2(x_start - x_dest, y_start - y_dest)

    # second draw the arrow head
    ctx.save()

    ctx.translate(x_dest, y_dest)
    ctx.rotate(angle)
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(-4, 7)
    ctx.lineTo(4, 7)
    ctx.fill(); ctx.closePath()

    ctx.restore()

    # third draw the arrow AT 2/3

    x_two_thirds = (x_start + 2 * x_dest) / 3
    y_two_thirds = (y_start + 2 * y_dest) / 3

    ctx.save()

    ctx.translate(x_two_thirds, y_two_thirds)
    ctx.rotate(angle)
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(-3, 6)
    ctx.moveTo(0, 0)
    ctx.lineTo(3, 6)
    ctx.stroke(); ctx.closePath()

    ctx.restore()


def fill_zone(ctx, zone_area, fill_colour, transparency):
    """ fill_zone """

    # ctx.lineWidth not used

    # fill coulour
    ctx.fillStyle = fill_colour.str_value()  # filling zone

    # change transparency
    prev_global_alpha = ctx.globalAlpha
    ctx.globalAlpha = transparency

    ctx.beginPath()
    for n, p in enumerate(zone_area.points):  # pylint: disable=invalid-name
        if not n:
            ctx.moveTo(p.x_pos, p.y_pos)
        else:
            ctx.lineTo(p.x_pos, p.y_pos)
    ctx.fill(); ctx.closePath()

    # restore transparency
    ctx.globalAlpha = prev_global_alpha


class Renderable:
    """ Renderable """

    @abstractmethod
    def render(self, ctx) -> None:
        """ render = display """


class Highliteable:
    """ Highliteable """

    @abstractmethod
    def highlite(self, ctx, active) -> None:
        """ active means mouse is over object, not active means it is not """

    @abstractmethod
    def description(self) -> str:
        """ text to display when mouses passes over """


class RegionTypeEnum:
    """ RegionTypeEnum """

    COAST_REGION = 1
    LAND_REGION = 2
    SEA_REGION = 3

    @staticmethod
    def inventory():
        """ inventory """
        return (RegionTypeEnum.COAST_REGION, RegionTypeEnum.LAND_REGION, RegionTypeEnum.SEA_REGION)

    @staticmethod
    def from_code(code: int):
        """ from_code """
        return code


class UnitTypeEnum:
    """ UnitTypeEnum """

    ARMY_UNIT = 1
    FLEET_UNIT = 2

    @staticmethod
    def inventory():
        """ inventory """
        return (UnitTypeEnum.ARMY_UNIT, UnitTypeEnum.FLEET_UNIT)

    @staticmethod
    def to_code(unit):
        """ to_code """
        return unit

    @staticmethod
    def from_code(code: int):
        """ from_code """
        return code


class SeasonEnum:
    """ SeasonEnum """

    SPRING_SEASON = 1
    SUMMER_SEASON = 2
    AUTUMN_SEASON = 3
    WINTER_SEASON = 4
    ADJUST_SEASON = 5

    @staticmethod
    def inventory():
        """ inventory """
        return (SeasonEnum.SPRING_SEASON, SeasonEnum.SUMMER_SEASON, SeasonEnum.AUTUMN_SEASON, SeasonEnum.WINTER_SEASON, SeasonEnum.ADJUST_SEASON)

    @staticmethod
    def from_code(code: int):
        """ from_code """
        return code


class OrderTypeEnum:
    """ OrderTypeEnum """

    ATTACK_ORDER = 1
    OFF_SUPPORT_ORDER = 2
    DEF_SUPPORT_ORDER = 3
    HOLD_ORDER = 4
    CONVOY_ORDER = 5
    RETREAT_ORDER = 6
    DISBAND_ORDER = 7
    BUILD_ORDER = 8
    REMOVE_ORDER = 9

    @staticmethod
    def inventory():
        """ inventory """
        return (OrderTypeEnum.ATTACK_ORDER, OrderTypeEnum.OFF_SUPPORT_ORDER, OrderTypeEnum.DEF_SUPPORT_ORDER, OrderTypeEnum.HOLD_ORDER, OrderTypeEnum.CONVOY_ORDER, OrderTypeEnum.RETREAT_ORDER, OrderTypeEnum.DISBAND_ORDER, OrderTypeEnum.BUILD_ORDER, OrderTypeEnum.REMOVE_ORDER)

    @staticmethod
    def to_code(order):
        """ to_code """
        return order

    @staticmethod
    def from_code(code: int):
        """ from_code """
        return code

    @staticmethod
    def shortcut(char: str):
        """ shortcut """
        if char == 'a':
            return OrderTypeEnum.ATTACK_ORDER
        if char == 'o':
            return OrderTypeEnum.OFF_SUPPORT_ORDER
        if char == 'd':
            return OrderTypeEnum.DEF_SUPPORT_ORDER
        if char == 't':
            return OrderTypeEnum.HOLD_ORDER
        if char == 'c':
            return OrderTypeEnum.CONVOY_ORDER
        return None

    @staticmethod
    def compatible(order_type, advancement_season: SeasonEnum) -> bool:
        """ type order compatible with season """
        if advancement_season in [SeasonEnum.SPRING_SEASON, SeasonEnum.AUTUMN_SEASON]:
            return order_type in [OrderTypeEnum.ATTACK_ORDER, OrderTypeEnum.OFF_SUPPORT_ORDER, OrderTypeEnum.DEF_SUPPORT_ORDER, OrderTypeEnum.HOLD_ORDER, OrderTypeEnum.CONVOY_ORDER]
        if advancement_season in [SeasonEnum.SUMMER_SEASON, SeasonEnum.WINTER_SEASON]:
            return order_type in [OrderTypeEnum.RETREAT_ORDER, OrderTypeEnum.DISBAND_ORDER]
        if advancement_season is SeasonEnum.ADJUST_SEASON:
            return order_type in [OrderTypeEnum.BUILD_ORDER, OrderTypeEnum.REMOVE_ORDER]
        return False


class Center(Highliteable, Renderable):
    """ A Center """

    def __init__(self, identifier: int, region: 'Region') -> None:

        self._identifier = identifier

        # the region in which is the center
        self._region = region

        # the owner at start of the game
        self._owner_start = None

    def actual_draw(self, ctx):
        """ actual_draw """

        ctx.lineWidth = 1

        position = self._region.zone.variant.position_table[self]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        # show a center (just the circle)
        ctx.beginPath()
        ctx.arc(x, y, center_design.CENTER_RAY, 0, 2 * pi, False)
        ctx.stroke(); ctx.closePath()

    def render_start(self, ctx):
        """ render_start """

        if not self._owner_start:
            return

        ctx.lineWidth = 1

        fill_color = CENTER_FILL_COLOUR
        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()
        ctx.fillStyle = fill_color.str_value()  # for a center

        position = self._region.zone.variant.position_table[self]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        ctx.beginPath()
        ctx.arc(x, y, center_design.CENTER_RAY + 2, 0, 2 * pi, False)
        ctx.stroke(); ctx.closePath()

    def render(self, ctx):
        """ put me on screen """

        fill_color = CENTER_FILL_COLOUR
        ctx.fillStyle = fill_color.str_value()  # for a center

        position = self._region.zone.variant.position_table[self]
        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        # show a center (just the disk)
        ctx.beginPath()
        ctx.arc(x, y, center_design.CENTER_RAY, 0, 2 * pi, False)
        ctx.fill(); ctx.stroke(); ctx.closePath()

        outline_colour = OUTLINE_COLOUR
        ctx.strokeStyle = outline_colour.str_value()  # for an ownership

        self.actual_draw(ctx)

    def highlite(self, ctx, active) -> None:
        """ highlite (if active otherwise not) """

        outline_colour = OUTLINE_COLOUR
        # alteration (highlite)
        if active:
            outline_colour = OUTLINE_COLOUR_HIGHLITED
        ctx.strokeStyle = outline_colour.str_value()  # for an ownership

        self.actual_draw(ctx)

    def description(self):
        """ description for helping """

        variant = self._region.zone.variant

        # zone
        zone = self.region.zone
        zone_full_name = variant.full_zone_name_table[zone]

        return f"Un centre neutre positionné dans la région {zone_full_name}."

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

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier


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
    def region_type(self) -> RegionTypeEnum:
        """ property """
        return self._region_type

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


class Zone(Highliteable, Renderable):
    """ A zone """

    def __init__(self, identifier: int, region: Region, coast_type, parent_zone, variant) -> None:

        self._identifier = identifier

        # most of the time zone = region
        self._region = region

        # for the special zones that have a specific coast
        self._coast_type = coast_type
        self._parent_zone = parent_zone

        # other zones one may access by fleet and army
        self._neighbours = {u: [] for u in UnitTypeEnum.inventory()}

        # variant
        self._variant = variant

    def actual_draw(self, ctx, outline_colour):
        """ actual_draw """

        # if bigger, leaves a trace of where mouse has been (larger boundaries)
        ctx.lineWidth = 1

        path = self._variant.path_table[self]
        ctx.beginPath()
        first_point = path.points[0]
        ctx.moveTo(first_point.x_pos, first_point.y_pos)
        for point in path.points[1:]:
            ctx.lineTo(point.x_pos, point.y_pos)
        ctx.lineTo(first_point.x_pos, first_point.y_pos)

        stroke_color = outline_colour
        ctx.strokeStyle = stroke_color.str_value()
        ctx.stroke(); ctx.closePath()

    def render(self, ctx):
        """ put me on screen """
        outline_colour = OUTLINE_COLOUR
        self.actual_draw(ctx, outline_colour)

    def render_geographical(self, ctx, role):
        """ put me on screen - fill me because geographically belong to role """

        # Filling the zone because it geographically belongs to a role (priority rank = 3)

        path = self._variant.path_table[self]
        background_fill_color = self._variant.background_colour_table[role]
        fill_zone(ctx, path, background_fill_color, TRANSPARENCY_OWNER)

    def render_foggy(self, ctx):
        """ put me on screen - fill me because foggy """

        # Filling the zone because foggy here

        path = self._variant.path_table[self]
        fill_zone(ctx, path, FOG_COLOUR, TRANSPARENCY_FOG)

    def render_legend(self, ctx):
        """ render_legend """

        legend_colour = LEGEND_COLOUR
        ctx.fillStyle = legend_colour.str_value()  # for a text

        # legend position and unit position are calculated from area ith polylabel
        position = self._variant.legend_position_table[self]
        x_pos = position.x_pos
        y_pos = position.y_pos

        # legend content (just for the length)
        if self._coast_type:
            legend = self._variant.coast_name_table[self._coast_type]
        else:
            legend = self._variant.zone_name_table[self]

        # put on screen
        text_width = ctx.measureText(legend).width
        ctx.font = LEGEND_FONT
        ctx.fillText(legend, x_pos - text_width / 2, y_pos)

    def highlite(self, ctx, active) -> None:
        """ highlite (if active otherwise not) """

        if active:
            outline_colour = OUTLINE_COLOUR_HIGHLITED
        else:
            if self._coast_type:
                outline_colour = SPECIAL_COAST_OUTLINE_COLOUR
            else:
                outline_colour = OUTLINE_COLOUR

        # alteration (highlite)
        self.actual_draw(ctx, outline_colour)

    def description(self):
        """ description for helping """

        variant = self._variant

        # zone
        # zone
        zone_full_name = variant.full_zone_name_table[self]
        zone_name = variant.zone_name_table[self]

        # region type name
        region_type_name = variant.region_name_table[self._region.region_type]

        neighbours_army_desc = f"par {self._variant.unit_name_table[UnitTypeEnum.ARMY_UNIT]} : [{' '.join([variant.zone_name_table[z] for z in self.neighbours[UnitTypeEnum.ARMY_UNIT]])}]" if self.neighbours[UnitTypeEnum.ARMY_UNIT] else ""

        neighbours_fleet_desc = f"par {self._variant.unit_name_table[UnitTypeEnum.FLEET_UNIT]} : [{' '.join([variant.zone_name_table[z] for z in self.neighbours[UnitTypeEnum.FLEET_UNIT]])}]" if self.neighbours[UnitTypeEnum.FLEET_UNIT] else ""

        return f"La zone {zone_full_name} ({zone_name}) - {region_type_name} - dont les voisins sont {neighbours_army_desc} {neighbours_fleet_desc}."

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

    @property
    def variant(self) -> 'Variant':
        """ property """
        return self._variant

    @property
    def parent_zone(self) -> 'Zone':
        """ property """
        return self._parent_zone

    def __str__(self) -> str:
        variant = self._variant
        zone_full_name = variant.full_zone_name_table[self]
        return f"La zone {zone_full_name}"


class Role:
    """ a Role """

    def __init__(self, identifier) -> None:

        self._identifier = identifier

        # start centers the role have
        self._start_centers = []

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

    def highlite_colour(self) -> 'ColourRecord':
        """ highlite_colour """
        return ColourRecord(self.red // 1.2, self.green // 1.2, self.blue // 1.2)

    def str_value(self) -> str:
        """ str_value """
        return f"rgb({self.red}, {self.green}, {self.blue})"


# position
DISLODGED_TEXT_BACKGROUND_COLOUR = ColourRecord(255, 255, 255)  # white
DISLODGED_TEXT_COLOUR = ColourRecord(0, 0, 0)  # black
DISLODGED_COLOUR = ColourRecord(255, 140, 0)  # dark orange
DISLODGED_SHIFT_X = -9
DISLODGED_SHIFT_Y = -7


def dislodged_font() -> str:
    """ legend_font """

    font_style = 'normal'
    font_variant = 'normal'
    font_weight = 'lighter'
    font_size = 'xx-small'
    font_family = 'Arial'
    return f"{font_style} {font_variant} {font_weight} {font_size} {font_family}"  # default is 10 sans serif


DISLODGED_FONT = dislodged_font()

# orders
ATTACK_COLOUR = ColourRecord(red=255, green=25, blue=25)  # red
ATTACK_FAILED_COLOUR = ColourRecord(red=25, green=25, blue=25)  # black (not used)
SUPPORT_COLOUR = ColourRecord(red=25, green=190, blue=25)  # green a bit dark
CONVOY_COLOUR = ColourRecord(red=25, green=25, blue=255)  # blue
RETREAT_COLOUR = ColourRecord(red=255, green=127, blue=0)  # orange
ADJUSTMENT_COLOUR = ColourRecord(red=0, green=0, blue=0)  # black

# legend & additional
LEGEND_COLOUR = ColourRecord(red=0, green=0, blue=0)  # black
AUTHORS_COLOUR = ColourRecord(red=0, green=0, blue=0)  # black
ADDITIONAL_COLOUR = ColourRecord(red=255, green=0, blue=0)  # red

# outline
SPECIAL_COAST_OUTLINE_COLOUR = ColourRecord(red=50, green=50, blue=50)  # black-ish
OUTLINE_COLOUR = ColourRecord(red=25, green=25, blue=25)  # black-ish
OUTLINE_COLOUR_HIGHLITED = ColourRecord(red=255, green=0, blue=0)  # red

# show
SHOW_COLOUR = ColourRecord(red=255, green=25, blue=25)  # red


def legend_font() -> str:
    """ legend_font """

    font_style = 'normal'
    font_variant = 'normal'
    font_weight = 'normal'
    font_size = 'xx-small'
    font_family = 'Arial'
    return f"{font_style} {font_variant} {font_weight} {font_size} {font_family}"  # default is 10 sans serif


LEGEND_FONT = legend_font()


def map_text_font() -> str:
    """ map_text_font """

    font_style = 'oblique'
    font_variant = 'normal'
    font_weight = 'lighter'
    font_size = 'x-small'
    font_family = 'Arial'
    return f"{font_style} {font_variant} {font_weight} {font_size} {font_family}"


def map_additional_text_font() -> str:
    """ map_text_font """

    font_style = 'normal'
    font_variant = 'normal'
    font_weight = 'lighter'
    font_size = 'small'
    font_family = 'Arial'
    return f"{font_style} {font_variant} {font_weight} {font_size} {font_family}"


MAP_TEXT_FONT = map_text_font()
VARIANT_AUTHOR_X_POS = 10
VARIANT_AUTHOR_Y_POS = 12

MAP_ADDITIONAL_TEXT_FONT = map_additional_text_font()
ADDITIONAL_X_POS = 10
ADDITIONAL_Y_POS = 10
TEXT_HEIGHT_PIXEL = 16


# center
CENTER_FILL_COLOUR = ColourRecord(red=200, green=200, blue=200)  # light grey

# fog
FOG_COLOUR = ColourRecord(red=100, green=100, blue=100)  # dark grey

ASCII_CONVERSION_TABLE = {
    "àâ": 'a',
    "éèê": 'e',
    "î": 'i',
    "ô": 'o',
    "ù": 'u',
    "ç": 'c',
}


class Variant(Renderable):
    """ A variant """

    def __init__(self, name: str, raw_variant_content, raw_parameters_content) -> None:

        self._name = name

        # =================
        # from variant file
        # =================

        # load the authors
        self._variant_author = raw_variant_content['author']

        # load the additional_text
        self._additional_text = raw_parameters_content['additional_text']

        # build everywhere
        self._build_everywhere = raw_variant_content['build_everywhere']

        # start build
        self._start_build = raw_variant_content['start_build']

        # extra_requirement_solo
        self._extra_requirement_solo = raw_variant_content['extra_requirement_solo']

        # load the regions
        self._regions = {}
        for num, code in enumerate(raw_variant_content['regions']):
            number = num + 1
            region_type = RegionTypeEnum.from_code(code)
            assert region_type is not None
            region = Region(number, region_type)
            self._regions[number] = region

        # load the centers
        self._centers = {}
        for num, num_region in enumerate(raw_variant_content['centers']):
            number = num + 1
            region = self._regions[num_region]
            center = Center(number, region)
            region.center = center
            self._centers[number] = center

        # load the roles (starts at zero)
        self._roles = {}
        for num in range(raw_variant_content['roles']['number']):
            number = num + 1
            role = Role(number)
            self._roles[number] = role

        assert len(raw_variant_content['start_centers']) == len(self._roles)

        # load start centers
        for num, role_start_centers in enumerate(raw_variant_content['start_centers']):
            number = num + 1
            role = self._roles[number]
            for number_center in role_start_centers:
                start_center = self._centers[number_center]
                start_center.owner_start = role
                role.start_centers.append(start_center)

        # load the coast types
        self._coast_types = {}
        for num in range(raw_variant_content['type_coasts']['number']):
            number = num + 1
            coast_type = CoastType(number)
            self._coast_types[number] = coast_type

        # load the zones

        # first the standard zones
        self._zones = {}
        for num, region in enumerate(self._regions.values()):
            number = num + 1
            zone = Zone(number, region, None, None, self)
            region.zone = zone
            self._zones[number] = zone

        # need an offset
        offset = max(self._zones.keys())

        # then the special coast zones
        for num, (region_num, coast_type_num) in enumerate(raw_variant_content['coastal_zones']):
            number = num + 1
            region = self._regions[region_num]
            coast_type = self._coast_types[coast_type_num]
            coast_num = region_num
            parent_zone = self._zones[coast_num]
            zone = Zone(offset + number, region, coast_type, parent_zone, self)
            self._zones[offset + number] = zone

        # load the start units
        self._start_units = {}
        for num, role_start_units in enumerate(raw_variant_content['start_units']):
            number = num + 1
            role = self._roles[number]
            self._start_units[role] = []
            for unit_type_code_str, role_start_units2 in role_start_units.items():
                unit_type_code = int(unit_type_code_str)
                unit_type = UnitTypeEnum.from_code(unit_type_code)
                assert unit_type is not None
                for zone_num in role_start_units2:
                    zone = self._zones[zone_num]
                    self._start_units[role].append((unit_type, zone))

        # load the year zero and increment
        self._year_zero = int(raw_variant_content['year_zero'])
        self._increment = int(raw_variant_content['increment'])

        # load the neighbouring
        for num, neighbourings in enumerate(raw_variant_content['neighbouring']):
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

        self._region_name_table = {}
        self._unit_name_table = {}
        self._role_name_table = {}
        self._coast_name_table = {}
        self._coast_full_name_table = {}
        self._zone_name_table = {}
        self._full_zone_name_table = {}
        self._season_name_table = {}
        self._order_name_table = {}

        self._item_colour_table = {}
        self._background_colour_table = {}
        self._position_table = {}
        self._legend_position_table = {}
        self._role_add_table = {}
        self._path_table = {}
        self._geographic_owner_table = {}

        # load the map size
        data_dict = raw_parameters_content['map']
        width = data_dict['width']
        height = data_dict['height']
        map_size = geometry.PositionRecord(x_pos=width, y_pos=height)
        self._map_size = map_size

        # load the regions type names
        assert len(raw_parameters_content['regions']) == len(RegionTypeEnum.inventory())
        for region_type_code_str, data_dict in raw_parameters_content['regions'].items():
            region_type_code = int(region_type_code_str)
            region_type = RegionTypeEnum.from_code(region_type_code)
            assert region_type is not None
            name = data_dict['name']
            self._region_name_table[region_type] = name

        # load the units type names
        assert len(raw_parameters_content['units']) == len(UnitTypeEnum.inventory())
        for unit_type_code_str, data_dict in raw_parameters_content['units'].items():
            unit_type_code = int(unit_type_code_str)
            unit_type = UnitTypeEnum.from_code(unit_type_code)
            assert unit_type is not None
            name = data_dict['name']
            self._unit_name_table[unit_type] = name

        # add GM role
        role = Role(0)
        self._roles[0] = role

        # load the roles names and colours
        assert len(raw_parameters_content['roles']) == len(self._roles)

        for role_num_str, data_dict in raw_parameters_content['roles'].items():

            role_num = int(role_num_str)
            role = self._roles[role_num]
            name = data_dict['name']
            self._role_name_table[role] = name

            red_item, red_background = data_dict['red']
            green_item, green_background = data_dict['green']
            blue_item, blue_background = data_dict['blue']

            item_colour = ColourRecord(red=red_item, green=green_item, blue=blue_item)
            self._item_colour_table[role] = item_colour

            background_colour = ColourRecord(red=red_background, green=green_background, blue=blue_background)
            self._background_colour_table[role] = background_colour

            self._role_add_table[role] = (data_dict['adjective_name'], data_dict['letter_name'])

        # load coasts types names
        assert len(raw_parameters_content['coasts']) == len(self._coast_types)
        for coast_type_num_str, data_dict in raw_parameters_content['coasts'].items():
            coast_type_num = int(coast_type_num_str)
            coast_type = self._coast_types[coast_type_num]
            self._coast_name_table[coast_type] = data_dict['name']
            self._coast_full_name_table[coast_type] = data_dict['full_name']

        # load the zones names and localisations (units and legends)
        assert len(raw_parameters_content['zones']) == len(self._zones)
        for zone_num_str, data_dict in raw_parameters_content['zones'].items():
            zone_num = int(zone_num_str)
            zone = self._zones[zone_num]

            # special zones have a special name
            if zone.coast_type:

                # name
                region_name = self._zone_name_table[zone.region.zone]
                coast_name = self._coast_name_table[zone.coast_type]
                name = f"{region_name}{coast_name}"

                # full name
                region_full_name = self._full_zone_name_table[zone.region.zone]
                coast_full_name = self._coast_full_name_table[zone.coast_type]
                full_name = f"{region_full_name} {coast_full_name}"

            else:
                # much simpler !
                name = data_dict['name']
                full_name = data_dict['full_name']

            self._zone_name_table[zone] = name
            self._full_zone_name_table[zone] = full_name

            # unit position
            x_pos = data_dict['x_pos']
            y_pos = data_dict['y_pos']
            unit_position = geometry.PositionRecord(x_pos=x_pos, y_pos=y_pos)
            self._position_table[zone] = unit_position

            # legend position
            x_legend_pos = data_dict['x_legend_pos']
            y_legend_pos = data_dict['y_legend_pos']
            legend_position = geometry.PositionRecord(x_pos=x_legend_pos, y_pos=y_legend_pos)
            self._legend_position_table[zone] = legend_position

            #  geographic_owner_table
            if 'display' in data_dict:
                num_owner = data_dict['display']
                owner = self._roles[num_owner]
                self._geographic_owner_table[zone] = owner

        # zone areas (polygons)
        assert len(raw_parameters_content['zone_areas']) == len(self._zones)
        for zone_num_str, data_dict in raw_parameters_content['zone_areas'].items():
            zone_num = int(zone_num_str)
            zone = self._zones[zone_num]
            # get area
            area = data_dict['area']
            self._path_table[zone] = geometry.Polygon([geometry.PositionRecord(*t) for t in area])

        # load the centers localisations
        assert len(raw_parameters_content['centers']) == len(self._centers)
        for center_num_str, data_dict in raw_parameters_content['centers'].items():
            center_num = int(center_num_str)
            center = self._centers[center_num]
            x_pos = data_dict['x_pos']
            y_pos = data_dict['y_pos']
            center_position = geometry.PositionRecord(x_pos=x_pos, y_pos=y_pos)
            self._position_table[center] = center_position

        # load seasons names
        assert len(raw_parameters_content['seasons']) == len(SeasonEnum.inventory())
        for season_num_str, data_dict in raw_parameters_content['seasons'].items():
            season_num = int(season_num_str)
            season = SeasonEnum.from_code(season_num)
            assert season is not None
            self._season_name_table[season] = data_dict['name']

        # load orders types names
        assert len(raw_parameters_content['orders']) == len(OrderTypeEnum.inventory())
        for order_type_num_str, data_dict in raw_parameters_content['orders'].items():
            order_type_num = int(order_type_num_str)
            order_type = OrderTypeEnum.from_code(order_type_num)
            assert order_type is not None
            self._order_name_table[order_type] = data_dict['name']

    def closest_center(self, designated_pos: geometry.PositionRecord):
        """ closest_center  """

        closest_center = None
        distance_closest = inf

        for center in self._centers.values():
            center_pos = self.position_table[center]
            distance = designated_pos.distance(center_pos)
            if distance < distance_closest:
                closest_center = center
                distance_closest = distance

        return closest_center

    def closest_zone(self, designated_pos: geometry.PositionRecord, unit_type: OrderTypeEnum):
        """ closest_zone """

        closest_zone = None
        distance_closest = inf

        # sort them by distance
        zones_sorted = sorted(self.zones.values(), key=lambda z: designated_pos.distance(self.position_table[z]))

        # yields the closest one which point is in (because can be in two zones : specific coasts)
        inside_ones = 0
        for zone in zones_sorted:
            # army cannot go on special coasts
            if zone.parent_zone and unit_type is UnitTypeEnum.ARMY_UNIT:
                continue
            zone_path = self.path_table[zone]
            if zone_path.is_inside_me(designated_pos):
                inside_ones += 1
                zone_pos = self.position_table[zone]
                distance = designated_pos.distance(zone_pos)
                if distance < distance_closest:
                    closest_zone = zone
                    distance_closest = distance
                if inside_ones >= 2:
                    break

        # by default
        if not closest_zone:
            closest_zone = zones_sorted[0]

        return closest_zone

    def render(self, ctx) -> None:
        """ put me on screen """

        # distinguish start centers
        for center in self._centers.values():
            center.render_start(ctx)

        # put legends actually
        for zone in self._zones.values():
            zone.render_legend(ctx)

        ctx.font = MAP_TEXT_FONT

        info_colour = AUTHORS_COLOUR
        ctx.fillStyle = info_colour.str_value()  # for a text

        # put the authors
        ctx.fillText(f"{self._variant_author}", VARIANT_AUTHOR_X_POS, VARIANT_AUTHOR_Y_POS)

        info_colour = ADDITIONAL_COLOUR
        ctx.fillStyle = info_colour.str_value()  # for a text

        # put the additional
        ctx.font = MAP_ADDITIONAL_TEXT_FONT
        x_pos = ADDITIONAL_X_POS
        num_lines = len(self._additional_text.split('\n'))
        start_y_pos = self._map_size.y_pos - TEXT_HEIGHT_PIXEL * (num_lines - 1)
        for num, chunk in enumerate(self._additional_text.split('\n')):
            y_pos = start_y_pos + TEXT_HEIGHT_PIXEL * num - ADDITIONAL_Y_POS
            ctx.fillText(chunk, x_pos, y_pos)

    def extract_names(self):
        """ extract the names we are using to pass them to adjudicator """

        def make_ascii(word):

            def replacement(letter):
                for candidates, target in ASCII_CONVERSION_TABLE.items():
                    if letter in candidates:
                        return target
                assert letter.isascii(), f"Please tell me how to simplify '{letter}'"
                return letter

            return ''.join(map(replacement, word))

        def extract_role_data(role):
            """ extract_role_data """
            additional = self._role_add_table[role]
            return [self._role_name_table[role], make_ascii(additional[0]), additional[1]]

        def extract_zone_data(zone):
            """ extract_zone_data """
            if zone.coast_type:
                return ''
            return self._zone_name_table[zone]

        role_names = {k: extract_role_data(v) for k, v in self._roles.items()}
        zone_names = {k: extract_zone_data(v) for k, v in self._zones.items()}
        coast_names = {k: self._coast_name_table[v] for k, v in self._coast_types.items()}

        return {'roles': role_names, 'zones': zone_names, 'coasts': coast_names}

    def role_adjective(self, role: Role):
        """ role_adjective """
        role_info = self._role_add_table[role]
        return role_info[0]

    def number_centers(self):
        """ number_centers """
        return len(self._centers)

    @property
    def name(self) -> str:
        """ property """
        return self._name

    @property
    def map_size(self) -> geometry.PositionRecord:
        """ property """
        return self._map_size

    @property
    def region_name_table(self):
        """ property """
        return self._region_name_table

    @property
    def unit_name_table(self):
        """ property """
        return self._unit_name_table

    @property
    def role_name_table(self):
        """ property """
        return self._role_name_table

    @property
    def coast_name_table(self):
        """ property """
        return self._coast_name_table

    @property
    def zone_name_table(self):
        """ property """
        return self._zone_name_table

    @property
    def full_zone_name_table(self):
        """ property """
        return self._full_zone_name_table

    @property
    def season_name_table(self):
        """ property """
        return self._season_name_table

    @property
    def order_name_table(self):
        """ property """
        return self._order_name_table

    @property
    def item_colour_table(self):
        """ property """
        return self._item_colour_table

    @property
    def background_colour_table(self):
        """ property """
        return self._background_colour_table

    @property
    def geographic_owner_table(self):
        """ property """
        return self._geographic_owner_table

    @property
    def position_table(self):
        """ property """
        return self._position_table

    @property
    def path_table(self):
        """ property """
        return self._path_table

    @property
    def legend_position_table(self):
        """ property """
        return self._legend_position_table

    @property
    def centers(self):
        """ property """
        return self._centers

    @property
    def zones(self):
        """ property """
        return self._zones

    @property
    def roles(self):
        """ property """
        return self._roles

    @property
    def start_units(self):
        """ property """
        return self._start_units

    @property
    def year_zero(self) -> int:
        """ property """
        return self._year_zero

    @property
    def increment(self) -> int:
        """ property """
        return self._increment

    @property
    def build_everywhere(self) -> bool:
        """ property """
        return self._build_everywhere

    @property
    def start_build(self) -> bool:
        """ property """
        return self._start_build

    @property
    def extra_requirement_solo(self) -> bool:
        """ property """
        return self._extra_requirement_solo


# imagined units
BLUR_COLOR = 'Black'
BLUR_VALUE = 20


class Unit(Highliteable, Renderable):
    """ A unit """

    def __init__(self, position: 'Position', role: Role, zone: Zone, dislodged_origin, imagined) -> None:
        self._position = position
        self._role = role
        self._zone = zone
        self._dislodged_origin = dislodged_origin
        self._imagined = imagined

    def is_dislodged(self):
        """ dislodged """
        return self._dislodged_origin is not None

    def actual_draw(self, ctx):
        """ actual_draw """

        if self._zone:
            position = self._position.variant.position_table[self._zone]
        else:
            position = DUMMY_POSITION

        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name

        # shift for dislodged units
        transpose = False
        if self.is_dislodged():
            x += DISLODGED_SHIFT_X  # pylint: disable=invalid-name
            y += DISLODGED_SHIFT_Y  # pylint: disable=invalid-name
            transpose = True
        # actual display of unit
        if isinstance(self, Army):
            unit_design.stabbeur_army(x, y, transpose, ctx)
        if isinstance(self, Fleet):
            unit_design.stabbeur_fleet(x, y, transpose, ctx)

        # more stuff if dislodged
        if self.is_dislodged():
            self.render_as_dislodged(x, y, ctx)

    def render(self, ctx) -> None:
        """ put me on screen """

        # Filling the zone because occupied by a unit (priority rank = 2)

        # must be somewhere (not a fake unit in sandbox)
        if self._zone:

            # must not be dislodged
            if not self.is_dislodged():

                # must not be on a center
                if not self._zone.region.center:

                    # special coasts : we get the big one
                    zone = self._zone.parent_zone if self._zone.parent_zone else self._zone

                    # must not be at sea
                    if zone.region.region_type is not RegionTypeEnum.SEA_REGION:
                        path = self._position.variant.path_table[zone]
                        background_fill_color = self._position.variant.background_colour_table[self._role]
                        fill_zone(ctx, path, background_fill_color, TRANSPARENCY_OWNER)
                        self._zone.render_legend(ctx)

        fill_color = self._position.variant.item_colour_table[self._role]

        if self._imagined:
            prev_shadow_color = ctx.shadowColor
            ctx.shadowColor = BLUR_COLOR
            prev_shadow_blur = ctx.shadowBlur
            ctx.shadowBlur = BLUR_VALUE

        ctx.fillStyle = fill_color.str_value()  # for unit
        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        self.actual_draw(ctx)

        if self._imagined:
            ctx.shadowColor = prev_shadow_color
            ctx.shadowBlur = prev_shadow_blur

    def render_as_dislodged(self, x_pos: int, y_pos: int, ctx) -> None:
        """ render additional stuff when dislodged """

        assert self._dislodged_origin is not None

        # because we know names of zones but not of regions
        zone_dislodger = self._dislodged_origin.zone
        dislodger_legend = self._position.variant.zone_name_table[zone_dislodger]

        # dislodger

        dislodger_back_colour = DISLODGED_TEXT_BACKGROUND_COLOUR
        ctx.fillStyle = dislodger_back_colour.str_value()  # for background
        ctx.rect(x_pos + 12, y_pos - 17, len(dislodger_legend) * 6, 10)
        ctx.fill()

        dislodger_frame_colour = DISLODGED_COLOUR
        ctx.strokeStyle = dislodger_frame_colour.str_value()
        ctx.lineWidth = 1.5
        ctx.beginPath()
        ctx.rect(x_pos + 12, y_pos - 17, len(dislodger_legend) * 6.5, 10)
        ctx.stroke(); ctx.closePath()

        dislodger_colour = DISLODGED_TEXT_COLOUR
        ctx.fillStyle = dislodger_colour.str_value()  # for text
        ctx.font = DISLODGED_FONT
        ctx.fillText(dislodger_legend, x_pos + 13, y_pos - 9)

    def highlite(self, ctx, active) -> None:
        """ highlite (if active otherwise not) """

        fill_color = self._position.variant.item_colour_table[self._role]
        # alteration (highlite)
        if active:
            fill_color = fill_color.highlite_colour()
        ctx.fillStyle = fill_color.str_value()  # for unit

        outline_colour = fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        self.actual_draw(ctx)

    def description(self):
        """ description for helping """

        variant = self._position.variant

        # unit type
        type_name = ""
        if isinstance(self, Army):
            type_name = variant.unit_name_table[UnitTypeEnum.ARMY_UNIT].lower()
        if isinstance(self, Fleet):
            type_name = variant.unit_name_table[UnitTypeEnum.FLEET_UNIT].lower()

        imagined_info = ' imaginée' if self._imagined else ''

        # role
        adjective = variant.role_adjective(self._role)

        # zone
        zone = self._zone

        if not zone:
            return f"Une {type_name}{imagined_info} appartenant au joueur {adjective}."

        zone_full_name = variant.full_zone_name_table[zone]

        # dislodger - actually not used since called on standard units
        dislodged_info = ""
        if self._dislodged_origin is not None:
            zone_dislodger = self._dislodged_origin.zone
            dislodger_legend = self._position.variant.zone_name_table[zone_dislodger]
            dislodged_info = f" - delogée par une unité venue de la région {dislodger_legend}"

        return f"Une {type_name}{imagined_info} appartenant au joueur {adjective} positionnée dans la région {zone_full_name}{dislodged_info}."

    def type_unit(self):
        """ type_unit """

        type_unit = None
        if isinstance(self, Fleet):
            type_unit = UnitTypeEnum.FLEET_UNIT
        if isinstance(self, Army):
            type_unit = UnitTypeEnum.ARMY_UNIT
        return UnitTypeEnum.to_code(type_unit)

    def save_json(self):
        """ Save to  dict """

        json_dict = {
            "type_unit": self.type_unit(),
            "role": self._role.identifier,
            "zone": self._zone.identifier
        }
        if self._dislodged_origin is not None:
            json_dict.update({"dislodged_origin": self._dislodged_origin.identifier})
        return json_dict

    def export_json(self):
        """ For trainer """
        return [self.type_unit(), self._zone.identifier]

    @property
    def zone(self) -> Zone:
        """ property """
        return self._zone

    @property
    def role(self) -> Role:
        """ property """
        return self._role

    @property
    def dislodged_origin(self) -> Region:
        """ property """
        return self._dislodged_origin

    @property
    def imagined(self) -> bool:
        """ property """
        return self._imagined

    def __str__(self) -> str:
        variant = self._position.variant
        zone = self._zone
        name = variant.zone_name_table[zone]
        type_name = ""
        if isinstance(self, Army):
            type_name = variant.unit_name_table[UnitTypeEnum.ARMY_UNIT]
        if isinstance(self, Fleet):
            type_name = variant.unit_name_table[UnitTypeEnum.FLEET_UNIT]
        type_name_initial = type_name[0]
        return f"{type_name_initial} {name} {'(i)' if self._imagined else ''}"


# position for units in reserve table
DUMMY_POSITION = geometry.PositionRecord(x_pos=15, y_pos=15)


class Army(Unit):
    """ An army """

    # use init from parent class
    # use render from parent class


class Fleet(Unit):
    """ An fleet """

    # use init from parent class
    # use render from parent class


class Ownership(Highliteable, Renderable):
    """ OwnerShip """

    def __init__(self, position: 'Position', role: Role, center: Center) -> None:
        self._position = position
        self._role = role
        self._center = center

    def actual_draw(self, ctx) -> None:
        """ render"""

        if self._center:
            position = self._position.variant.position_table[self._center]
        else:
            position = DUMMY_POSITION

        x, y = position.x_pos, position.y_pos  # pylint: disable=invalid-name
        center_design.stabbeur_center(x, y, ctx)

    def render(self, ctx) -> None:
        """ put me on screen """

        # Filling the zone because center is owned (priority rank = 1)

        if self._center:
            zone = self._center.region.zone
            path = self._position.variant.path_table[zone]
            background_fill_color = self._position.variant.background_colour_table[self._role]
            fill_zone(ctx, path, background_fill_color, TRANSPARENCY_OWNER)

        item_fill_color = self._position.variant.item_colour_table[self._role]
        ctx.fillStyle = item_fill_color.str_value()  # for an ownership

        outline_colour = item_fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        self.actual_draw(ctx)

    def highlite(self, ctx, active) -> None:
        """ highlite (if active otherwise not) """

        item_fill_color = self._position.variant.item_colour_table[self._role]
        # alteration (highlite)
        if active:
            item_fill_color = item_fill_color.highlite_colour()
        ctx.fillStyle = item_fill_color.str_value()  # for an ownership

        outline_colour = item_fill_color.outline_colour()
        ctx.strokeStyle = outline_colour.str_value()

        self.actual_draw(ctx)

    def description(self):
        """ description for helping """

        variant = self._position.variant

        # role
        adjective = variant.role_adjective(self._role)

        # zone
        if not self._center:
            return f"Un centre appartenant au joueur {adjective}."

        zone = self._center.region.zone
        zone_full_name = variant.full_zone_name_table[zone]

        return f"Un centre appartenant au joueur {adjective} positionné dans la région {zone_full_name}."

    def save_json(self):
        """ Save to  dict """

        json_dict = {
            "role": self._role.identifier,
            "center_num": self._center.identifier
        }
        return json_dict

    def export_json(self):
        """ For trainer """
        return str(self._center.identifier), self._role.identifier

    @property
    def role(self) -> Role:
        """ property """
        return self._role

    @property
    def center(self) -> Center:
        """ property """
        return self._center


FORBIDDEN_COLOR = ColourRecord(red=255, green=0, blue=0)


class Forbidden(Highliteable, Renderable):
    """ Forbidden """

    def __init__(self, position: 'Position', region: Region) -> None:
        self._position = position
        self._region = region

    def actual_draw(self, ctx) -> None:
        """ actual_draw """

        ctx.lineWidth = 2  # Need to really see it
        # ctx.fillStyle is not used

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

    def render(self, ctx) -> None:
        """ put me on screen """

        outline_colour = FORBIDDEN_COLOR
        ctx.strokeStyle = outline_colour.str_value()

        self.actual_draw(ctx)

    def highlite(self, ctx, active) -> None:
        """ highlite (if active otherwise not) """

        outline_colour = FORBIDDEN_COLOR
        if active:
            outline_colour = outline_colour.highlite_colour()
        ctx.strokeStyle = outline_colour.str_value()

        self.actual_draw(ctx)

    def description(self):
        """ description for helping """

        variant = self._position.variant

        # role

        # zone
        zone = self._region.zone
        zone_full_name = variant.full_zone_name_table[zone]

        return f"Une région bloquée suite à conflit en {zone_full_name}."

    @property
    def region(self) -> Region:
        """ property """
        return self._region


class Position(Renderable):
    """ A position that can be displayed """

    def __init__(self, server_dict, variant: Variant) -> None:

        self._variant = variant

        # dict that says which ownership owns a center
        self._owner_table = {}

        # ownerships
        ownerships = server_dict['ownerships']
        self._ownerships = []
        for center_num_str, role_num in ownerships.items():
            center_num = int(center_num_str)
            center = variant._centers[center_num]
            role = variant._roles[role_num]
            ownership = Ownership(self, role, center)
            self._ownerships.append(ownership)
            self._owner_table[center] = ownership

        # dict that says which unit is on a region
        self._occupant_table = {}

        # units
        units = server_dict['units']

        self._units = []
        for role_num_str, role_units in units.items():
            role_num = int(role_num_str)
            role = variant._roles[role_num]
            for type_unit_code, zone_number in role_units:
                type_unit = UnitTypeEnum.from_code(type_unit_code)
                zone = variant._zones[zone_number]
                if type_unit is UnitTypeEnum.ARMY_UNIT:
                    unit = Army(self, role, zone, None, False)
                if type_unit is UnitTypeEnum.FLEET_UNIT:
                    unit = Fleet(self, role, zone, None, False)  # type: ignore
                self._units.append(unit)
                region = zone.region
                self._occupant_table[region] = unit

        # For historical reasons this may happen
        if 'imagined_units' not in server_dict:
            server_dict['imagined_units'] = {}

        # imagined units
        imagined_units = server_dict['imagined_units']

        for role_num_str, role_units in imagined_units.items():
            role_num = int(role_num_str)
            role = variant._roles[role_num]
            for type_unit_code, zone_number in role_units:
                type_unit = UnitTypeEnum.from_code(type_unit_code)
                zone = variant._zones[zone_number]
                if type_unit is UnitTypeEnum.ARMY_UNIT:
                    unit = Army(self, role, zone, None, True)
                if type_unit is UnitTypeEnum.FLEET_UNIT:
                    unit = Fleet(self, role, zone, None, True)  # type: ignore
                self._units.append(unit)
                region = zone.region
                self._occupant_table[region] = unit

        # forbiddens
        forbiddens = server_dict['forbiddens']
        self._forbiddens = []
        for region_num in forbiddens:
            region = variant._regions[region_num]
            forbidden = Forbidden(self, region)
            self._forbiddens.append(forbidden)

        real_occupants_table = self._occupant_table.copy()

        # dislodged_units
        dislodged_ones = server_dict['dislodged_ones']
        self._dislodged_units = []
        for role_num_str, role_units in dislodged_ones.items():
            role_num = int(role_num_str)
            role = variant._roles[role_num]
            for type_unit_code, zone_number, dislodger_zone_number in role_units:
                type_unit = UnitTypeEnum.from_code(type_unit_code)
                zone = variant._zones[zone_number]
                dislodger_zone = variant._zones[dislodger_zone_number]
                dislodger_region = dislodger_zone.region
                if type_unit is UnitTypeEnum.ARMY_UNIT:
                    dislodged_unit = Army(self, role, zone, dislodger_region, False)
                if type_unit is UnitTypeEnum.FLEET_UNIT:
                    dislodged_unit = Fleet(self, role, zone, dislodger_region, False)  # type: ignore
                self._dislodged_units.append(dislodged_unit)
                # the dislodger occupying the region is forgotten
                region = zone.region
                self._occupant_table[region] = dislodged_unit

        # dislodging_table
        self._dislodging_table = {}
        for dislodged_unit in self._dislodged_units:
            region = dislodged_unit.zone.region
            dislodging_unit = real_occupants_table[region]
            self._dislodging_table[dislodging_unit] = dislodged_unit

        # seen regions
        self._seen_regions = []
        if 'seen_regions' in server_dict:
            self._seen_regions = server_dict['seen_regions']

    def erase_centers(self) -> None:
        """ erase all centers """
        self._ownerships = []
        self._owner_table = []

    def erase_units(self) -> None:
        """ erase all units """
        self._units = []
        self._occupant_table = {}

    def render(self, ctx) -> None:
        """ put me on screen """

        # put zones and geographical regions
        for zone in self._variant.zones.values():

            # put boundaries
            zone.render(ctx)

            # must geographically belong to a role
            if zone not in self._variant.geographic_owner_table:
                continue

            # must not be owned
            if zone.region.center in self._owner_table:
                continue

            # must not be occupied
            if zone.region in self._occupant_table:
                continue

            role = self._variant.geographic_owner_table[zone]
            zone.render_geographical(ctx, role)

        # put ownerships
        for ownership in self._ownerships:
            ownership.render(ctx)

        # put units
        for unit in self._units:
            unit.render(ctx)

        # put forbiddens
        for forbidden in self._forbiddens:
            forbidden.render(ctx)

        # put dislodged_units
        for dislodged_unit in self._dislodged_units:
            dislodged_unit.render(ctx)

        # put centers (only neutral ones)
        neutral_centers = set(self._variant.centers.values()) - {o.center for o in self._ownerships}
        for center in neutral_centers:
            center.render(ctx)

        # put foggy regions
        if self._seen_regions:
            for zone in self._variant.zones.values():
                if zone.region.identifier not in self._seen_regions:
                    zone.render_foggy(ctx)

    def save_json1(self):
        """ export units as list of dict """
        return [u.save_json() for u in self._units]

    def save_json2(self):
        """ export ownerships as list of dict """
        return [o.save_json() for o in self._ownerships]

    def save_json3(self):
        """ export dislodged_units as list of dict """
        return [du.save_json() for du in self._dislodged_units]

    def save_json4(self):
        """ export forbidden as list of int """
        return [f.region.identifier for f in self._forbiddens]

    def closest_ownership(self, designated_pos: geometry.PositionRecord):
        """ closest_ownership  """

        closest_ownership = None
        distance_closest = inf

        for ownership in self._ownerships:
            center = ownership.center
            center_pos = self._variant.position_table[center]
            distance = designated_pos.distance(center_pos)
            if distance < distance_closest:
                closest_ownership = ownership
                distance_closest = distance

        return closest_ownership

    def closest_unit(self, designated_pos: geometry.PositionRecord, dislodged):
        """ closest_unit (pass dislodged = None for all dislodged and not dislodged)  """

        closest_unit = None
        distance_closest = inf

        # what list do we use ?
        if dislodged is None:
            search_list = self._units + self._dislodged_units
        else:
            if dislodged:
                search_list = self._dislodged_units
            else:
                search_list = self._units

        for unit in search_list:
            zone = unit.zone
            unit_pos = self._variant.position_table[zone]
            if unit.is_dislodged():
                unit_pos = geometry.PositionRecord(x_pos=unit_pos.x_pos + DISLODGED_SHIFT_X, y_pos=unit_pos.y_pos + DISLODGED_SHIFT_Y)
            distance = designated_pos.distance(unit_pos)
            if distance < distance_closest:
                closest_unit = unit
                distance_closest = distance

        return closest_unit

    def closest_object(self, designated_pos: geometry.PositionRecord):
        """ closest_object : unit, center, region  """

        closest_object = None
        distance_closest = inf

        # what list do we use ?
        search_list = self._units + self._dislodged_units

        # search in the units (must be close enough)

        for unit in search_list:
            zone = unit.zone
            unit_pos = self._variant.position_table[zone]
            if unit.is_dislodged():
                unit_pos = geometry.PositionRecord(x_pos=unit_pos.x_pos + DISLODGED_SHIFT_X, y_pos=unit_pos.y_pos + DISLODGED_SHIFT_Y)
            distance = designated_pos.distance(unit_pos)
            if distance >= MAX_PROXIMITY_ITEM_UNIT:
                continue
            if distance < distance_closest:
                closest_object = unit
                distance_closest = distance

        # search in the ownerships (must be close enough)

        for ownership in self._ownerships:
            center = ownership.center
            center_pos = self._variant.position_table[center]
            distance = designated_pos.distance(center_pos)
            if distance >= MAX_PROXIMITY_ITEM_UNIT:
                continue
            if distance < distance_closest:
                closest_object = ownership
                distance_closest = distance

        # search in the centers (must be after ownerships otherwise the latter have no chance)

        for center in self._variant.centers.values():
            center_pos = self._variant.position_table[center]
            distance = designated_pos.distance(center_pos)
            if distance >= MAX_PROXIMITY_ITEM_UNIT:
                continue
            if distance < distance_closest:
                closest_object = center
                distance_closest = distance

        for forbidden in self._forbiddens:
            zone = forbidden.region.zone
            region_pos = self._variant.position_table[zone]
            distance = designated_pos.distance(region_pos)
            if distance >= MAX_PROXIMITY_ITEM_UNIT:
                continue
            if distance < distance_closest:
                closest_object = forbidden
                distance_closest = distance

        # search the zones
        # important : it must come last
        # because hot spot is same between units and zones so otherwise units have no chance of being selected

        # sort zones by distance
        zones_sorted = sorted(self._variant.zones.values(), key=lambda z: designated_pos.distance(self._variant.position_table[z]))

        # yields the closest one which point is in (because can be in two zones : specific coasts)
        inside_ones = 0
        for zone in zones_sorted:
            zone_path = self._variant.path_table[zone]
            if zone_path.is_inside_me(designated_pos):
                inside_ones += 1
                zone_pos = self._variant.position_table[zone]
                distance = designated_pos.distance(zone_pos)
                if distance < distance_closest:
                    closest_object = zone
                    distance_closest = distance
                if inside_ones >= 2:
                    break

        return closest_object

    def role_retreats(self, role: Role):
        """ informations about retreats for the role """

        informations = []

        for dislodged_unit in self._dislodged_units:

            if dislodged_unit.role != role:
                continue

            if isinstance(dislodged_unit, Fleet):
                type_name = self._variant.unit_name_table[UnitTypeEnum.FLEET_UNIT].lower()
                where_to = ' / '.join([f"{self._variant.full_zone_name_table[z]} ({self._variant.zone_name_table[z]})" for z in dislodged_unit.zone.neighbours[UnitTypeEnum.FLEET_UNIT] if z.region not in self._occupant_table and z.region not in [f.region for f in self._forbiddens] and z.region != dislodged_unit.dislodged_origin])
            if isinstance(dislodged_unit, Army):
                type_name = self._variant.unit_name_table[UnitTypeEnum.ARMY_UNIT].lower()
                where_to = ' / '.join([f"{self._variant.full_zone_name_table[z]} ({self._variant.zone_name_table[z]})" for z in dislodged_unit.zone.neighbours[UnitTypeEnum.ARMY_UNIT] if z.region not in self._occupant_table and z.region not in [f.region for f in self._forbiddens] and z.region != dislodged_unit.dislodged_origin])

            information = f"Votre {type_name} en {self._variant.full_zone_name_table[dislodged_unit.zone]} ({self._variant.zone_name_table[dislodged_unit.zone]}) peut retraiter en : {where_to}"
            informations.append(information)

        return informations

    def role_builds(self, role: Role):
        """ how many builds allowed (positive or negative) for the role """

        nb_ownerships = len([o for o in self._ownerships if o.role == role])
        nb_units = len([u for u in self._units if u.role == role])
        if self.variant.build_everywhere:
            nb_free_centers = len([c for c in self.variant.centers.values() if c in self._owner_table and self._owner_table[c].role == role and c.region not in self._occupant_table])
        else:
            nb_free_centers = len([c for c in role.start_centers if c in self._owner_table and self._owner_table[c].role == role and c.region not in self._occupant_table])

        nb_builds = min(nb_ownerships - nb_units, nb_free_centers)
        return nb_builds, nb_ownerships, nb_units, nb_free_centers

    def role_ratings(self):
        """ a rating of roles """
        raw_dict = {self._variant.role_name_table[self._variant.roles[i]]: len([o for o in self._ownerships if o.role == self._variant.roles[i]]) for i in self._variant.roles if i != 0}
        return {r: raw_dict[r] for r in sorted(raw_dict.keys(), key=lambda r: (-raw_dict[r], r))}

    def role_units(self):
        """ a units number of roles """
        raw_dict = {self._variant.role_name_table[self._variant.roles[i]]: len([u for u in self._units + self._dislodged_units if u.role == self._variant.roles[i]]) for i in self._variant.roles if i != 0}
        return raw_dict

    def role_colours(self):
        """ a rating of roles """
        return {self._variant.role_name_table[r]: self._variant.item_colour_table[r] for r in self._variant.roles.values()}

    def add_unit(self, unit: Unit):
        """ add_unit (sandbox and rectification)"""
        self._units.append(unit)
        region = unit.zone.region
        self._occupant_table[region] = unit

    def remove_unit(self, unit: Unit):
        """ remove_unit (sandbox and rectification)"""
        region = unit.zone.region
        # test because a dislodging unit is not in the table
        if region in self._occupant_table:
            del self._occupant_table[region]
        if unit.is_dislodged():
            self._dislodged_units.remove(unit)
        else:
            self._units.remove(unit)

    def add_ownership(self, ownership: Ownership):
        """ add_ownership (rectification)"""
        self._ownerships.append(ownership)
        center = ownership.center
        self._owner_table[center] = ownership

    def remove_ownership(self, ownership: Ownership):
        """ remove_ownership (rectification)"""
        center = ownership.center
        del self._owner_table[center]
        self._ownerships.remove(ownership)

    def empty(self) -> bool:
        """ empty """
        return not self._units

    def export_json(self):
        """ For trainer """
        return {
            'ownerships': dict([o.export_json() for o in self._ownerships]),
            'dislodged_ones': [],  # not handled
            'units': {str(r.identifier): [u.export_json() for u in self._units if u.role == r] for r in {u.role for u in self._units}},
            'forbiddens': []  # not handled
        }

    @property
    def variant(self) -> Variant:
        """ property """
        return self._variant

    @property
    def occupant_table(self):
        """ property """
        return self._occupant_table

    @property
    def owner_table(self):
        """ property """
        return self._owner_table

    @property
    def units(self):
        """ property """
        return self._units

    @property
    def dislodging_table(self):
        """ property """
        return self._dislodging_table


DASH_PATTERN = [5, 5]


class Order(Renderable):
    """ Order """

    def __init__(self, position: 'Position', order_type: OrderTypeEnum, active_unit: Unit, passive_unit, destination_zone, communication) -> None:
        self._position = position
        self._order_type = order_type
        self._active_unit = active_unit
        self._passive_unit = passive_unit
        self._destination_zone = destination_zone
        self._communication = communication

    def render(self, ctx) -> None:
        """ put me on screen """

        # -- moves --

        if self._order_type is OrderTypeEnum.ATTACK_ORDER:

            assert self._destination_zone is not None

            # red color : attack
            stroke_color = ATTACK_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            ctx.lineWidth = 1  # Enough for just attack

            # an arrow (move)
            from_point = self._position.variant.position_table[self._active_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            dest_point_closer_x, dest_point_closer_y = shorten_arrow(from_point.x_pos, from_point.y_pos, dest_point.x_pos, dest_point.y_pos)
            draw_arrow(from_point.x_pos, from_point.y_pos, dest_point_closer_x, dest_point_closer_y, ctx)

        if self._order_type is OrderTypeEnum.OFF_SUPPORT_ORDER:

            assert self._passive_unit is not None
            assert self._destination_zone is not None

            # red for support to attack
            stroke_color = ATTACK_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            ctx.lineWidth = 1.5  # a bit more for dashed
            ctx.setLineDash(DASH_PATTERN)

            # a dashed arrow (passive move)
            from_point = self._position.variant.position_table[self._passive_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            direction = geometry.get_direction(from_point, dest_point)

            # we do not shift
            from_point_shifted = from_point
            dest_point_shifted = dest_point

            dest_point_shifted_closer_x, dest_point_shifted_closer_y = shorten_arrow(from_point_shifted.x_pos, from_point_shifted.y_pos, dest_point_shifted.x_pos, dest_point_shifted.y_pos)
            draw_arrow(from_point_shifted.x_pos, from_point_shifted.y_pos, dest_point_shifted_closer_x, dest_point_shifted_closer_y, ctx)

            # put back
            ctx.lineWidth = 1  # enough for line
            ctx.setLineDash([])

            # a line (support)
            from_point2 = self._position.variant.position_table[self._active_unit.zone]
            dest_point2 = geometry.PositionRecord(round((from_point_shifted.x_pos + 2 * dest_point_shifted.x_pos) / 3), round((from_point_shifted.y_pos + 2 * dest_point_shifted.y_pos) / 3))
            ctx.beginPath()
            ctx.moveTo(from_point2.x_pos, from_point2.y_pos)
            ctx.lineTo(dest_point2.x_pos, dest_point2.y_pos)
            ctx.stroke(); ctx.closePath()

        if self._order_type is OrderTypeEnum.DEF_SUPPORT_ORDER:

            assert self._passive_unit is not None

            # green for peaceful defensive support
            stroke_color = SUPPORT_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            # ctx.fillStyle is not used

            ctx.lineWidth = 1.5   # a bit more for dashed
            ctx.setLineDash(DASH_PATTERN)

            # prepare the line
            from_point = self._position.variant.position_table[self._active_unit.zone]
            dest_point = self._position.variant.position_table[self._passive_unit.zone]
            direction = geometry.get_direction(from_point, dest_point)
            next_direction = geometry.perpendicular(direction)
            dest_point_shifted = dest_point.shift(next_direction, 3)

            # put a dashed circle (stand) over unit
            center_point = self._position.variant.position_table[self._passive_unit.zone]
            center_point_shifted = center_point.shift(next_direction, 3)
            ctx.beginPath()
            ctx.arc(center_point_shifted.x_pos, center_point_shifted.y_pos, 12, 0, 2 * pi, False)
            ctx.stroke(); ctx.closePath()

            # put back
            ctx.lineWidth = 1  # enough for line
            ctx.setLineDash([])

            # put the prepared line (support)

            ctx.beginPath()
            ctx.moveTo(from_point.x_pos, from_point.y_pos)
            ctx.lineTo(dest_point_shifted.x_pos, dest_point_shifted.y_pos)
            ctx.stroke(); ctx.closePath()

        if self._order_type is OrderTypeEnum.HOLD_ORDER:

            # green for peaceful hold
            stroke_color = SUPPORT_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            # ctx.fillStyle is not used

            ctx.lineWidth = 1.5  # a bit more for dashed
            ctx.setLineDash(DASH_PATTERN)

            center_point = self._position.variant.position_table[self._active_unit.zone]

            # put a circle (stand) around unit
            ctx.beginPath()
            ctx.arc(center_point.x_pos, center_point.y_pos, 12, 0, 2 * pi, False)
            ctx.stroke(); ctx.closePath()

            # put back
            ctx.setLineDash([])

        if self._order_type is OrderTypeEnum.CONVOY_ORDER:

            assert self._passive_unit is not None
            assert self._destination_zone is not None

            # blue for convoy
            stroke_color = CONVOY_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            ctx.lineWidth = 1.5  # a bit more for dashed
            ctx.setLineDash(DASH_PATTERN)

            # a dashed arrow (passive move)
            from_point = self._position.variant.position_table[self._passive_unit.zone]
            dest_point = self._position.variant.position_table[self._destination_zone]
            direction = geometry.get_direction(from_point, dest_point)
            next_direction = geometry.perpendicular(direction)
            from_point_shifted = from_point.shift(next_direction, 3)  # was 6
            dest_point_shifted = dest_point.shift(next_direction, 3)  # was 6
            dest_point_shifted_closer_x, dest_point_shifted_closer_y = shorten_arrow(from_point_shifted.x_pos, from_point_shifted.y_pos, dest_point_shifted.x_pos, dest_point_shifted.y_pos)
            draw_arrow(from_point_shifted.x_pos, from_point_shifted.y_pos, dest_point_shifted_closer_x, dest_point_shifted_closer_y, ctx)

            # put back
            ctx.lineWidth = 1  # enough for line
            ctx.setLineDash([])

            # put a line (convoy)
            from_point2 = self._position.variant.position_table[self._active_unit.zone]
            dest_point2 = geometry.PositionRecord(round((from_point_shifted.x_pos + 2 * dest_point_shifted.x_pos) / 3), round((from_point_shifted.y_pos + 2 * dest_point_shifted.y_pos) / 3))
            ctx.beginPath()
            ctx.moveTo(from_point2.x_pos, from_point2.y_pos)
            ctx.lineTo(dest_point2.x_pos, dest_point2.y_pos)
            ctx.stroke(); ctx.closePath()

        # -- retreats --

        if self._order_type is OrderTypeEnum.RETREAT_ORDER:

            assert self._destination_zone is not None

            # orange for retreat
            stroke_color = RETREAT_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.lineWidth = 1.5  # Retreats : not that many so can be thicker
            ctx.fillStyle = stroke_color.str_value()  # for draw_arrow

            # put an arrow (move/retreat)
            unit_position = self._position.variant.position_table[self._active_unit.zone]
            from_point = geometry.PositionRecord(x_pos=unit_position.x_pos + DISLODGED_SHIFT_X, y_pos=unit_position.y_pos + DISLODGED_SHIFT_Y)
            dest_point = self._position.variant.position_table[self._destination_zone]
            dest_point_closer_x, dest_point_closer_y = shorten_arrow(from_point.x_pos + DISLODGED_SHIFT_X, from_point.y_pos + DISLODGED_SHIFT_Y, dest_point.x_pos, dest_point.y_pos)
            draw_arrow(from_point.x_pos, from_point.y_pos, dest_point_closer_x, dest_point_closer_y, ctx)
            # -- end

        if self._order_type is OrderTypeEnum.DISBAND_ORDER:

            # orange for retreat
            stroke_color = RETREAT_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.lineWidth = 1.5
            # ctx.fillStyle is not used

            # put a cross over unit
            unit_position = self._position.variant.position_table[self._active_unit.zone]
            cross_center_point = geometry.PositionRecord(x_pos=unit_position.x_pos + DISLODGED_SHIFT_X, y_pos=unit_position.y_pos + DISLODGED_SHIFT_Y)
            ctx.beginPath()
            ctx.moveTo(cross_center_point.x_pos + 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos - 8, cross_center_point.y_pos + 8)
            ctx.moveTo(cross_center_point.x_pos - 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos + 8, cross_center_point.y_pos + 8)
            ctx.stroke(); ctx.closePath()

        # -- builds --

        if self._order_type is OrderTypeEnum.BUILD_ORDER:

            # put fake unit
            self._active_unit.render(ctx)

            # grey for builds
            stroke_color = ADJUSTMENT_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.lineWidth = 1.5
            # ctx.fillStyle is not used

            # put a square around unit
            square_center_point = self._position.variant.position_table[self._active_unit.zone]
            ctx.beginPath()
            ctx.rect(square_center_point.x_pos - 8, square_center_point.y_pos - 8, 16, 16)
            ctx.stroke(); ctx.closePath()

        if self._order_type is OrderTypeEnum.REMOVE_ORDER:

            # grey for builds
            stroke_color = ADJUSTMENT_COLOUR if not self._communication else COMMUNICATION_ORDER_COLOR
            ctx.strokeStyle = stroke_color.str_value()
            ctx.lineWidth = 1.5
            # ctx.fillStyle is not used

            # put a cross over unit
            cross_center_point = self._position.variant.position_table[self._active_unit.zone]
            ctx.beginPath()
            ctx.moveTo(cross_center_point.x_pos + 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos - 8, cross_center_point.y_pos + 8)
            ctx.moveTo(cross_center_point.x_pos - 8, cross_center_point.y_pos - 8)
            ctx.lineTo(cross_center_point.x_pos + 8, cross_center_point.y_pos + 8)
            ctx.stroke(); ctx.closePath()

    def save_json(self):
        """ Save to  dict """

        json_dict = {}
        if self._order_type is not None:
            json_dict.update({"order_type": UnitTypeEnum.to_code(self._order_type)})
        if self._active_unit is not None:
            json_dict.update({"active_unit": self._active_unit.save_json()})
        if self._passive_unit is not None:
            json_dict.update({"passive_unit": self._passive_unit.save_json()})
        if self._destination_zone is not None:
            json_dict.update({"destination_zone": self._destination_zone.identifier})
        return json_dict

    def export_json(self):
        """ For trainer """
        return [0, 0, UnitTypeEnum.to_code(self._order_type), self._active_unit.zone.identifier, self._passive_unit.zone.identifier if self._passive_unit else 0, self._destination_zone.identifier if self._destination_zone else 0]

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
            dest_zone_name = variant.zone_name_table[self._destination_zone]
            return f"{self._active_unit} - {dest_zone_name}"
        if self._order_type is OrderTypeEnum.OFF_SUPPORT_ORDER:
            dest_zone_name = variant.zone_name_table[self._destination_zone]
            foreign = variant.role_adjective(self._passive_unit.role) if self._passive_unit.role != self._active_unit.role else ""
            return f"{self._active_unit} S {foreign} {self._passive_unit} - {dest_zone_name}"
        if self._order_type is OrderTypeEnum.DEF_SUPPORT_ORDER:
            foreign = variant.role_adjective(self._passive_unit.role) if self._passive_unit.role != self._active_unit.role else ""
            return f"{self._active_unit} S {foreign} {self._passive_unit}"
        if self._order_type is OrderTypeEnum.HOLD_ORDER:
            return f"{self._active_unit} H"
        if self._order_type is OrderTypeEnum.CONVOY_ORDER:
            dest_zone_name = variant.zone_name_table[self._destination_zone]
            foreign = variant.role_adjective(self._passive_unit.role) if self._passive_unit.role != self._active_unit.role else ""
            return f"{self._active_unit} C {foreign} {self._passive_unit} - {dest_zone_name}"
        if self._order_type is OrderTypeEnum.RETREAT_ORDER:
            dest_zone_name = variant.zone_name_table[self._destination_zone]
            return f"{self._active_unit} R {dest_zone_name}"
        if self._order_type is OrderTypeEnum.DISBAND_ORDER:
            return f"{self._active_unit} D"
        if self._order_type is OrderTypeEnum.BUILD_ORDER:
            return f"+ {self._active_unit}"
        if self._order_type is OrderTypeEnum.REMOVE_ORDER:
            return f"- {self._active_unit}"
        return ""


# comm witness

# rectangle
COMMUNICATION_ORDER_PATH = geometry.Polygon([geometry.PositionRecord(*t) for t in [(10, 30), (40, 30), (40, 45), (10, 45), (10, 30)]])


# magenta (like text)
COMMUNICATION_ORDER_COLOR = ColourRecord(red=255, green=0, blue=255)


class Orders(Renderable):
    """ A set of orders that can be displayed / requires position """

    def __init__(self, server_dict, position: Position, communication_orders_list) -> None:

        self._position = position

        # these fake units are local here - they belong to orders, not the position
        self._fake_units = {}

        # fake units - they must go first
        #  (they serve for our handling of ihm)
        fake_units = server_dict['fake_units']
        for _, unit_type_num, zone_num, role_num, _, _ in fake_units:
            unit_type = UnitTypeEnum.from_code(unit_type_num)
            zone = self._position.variant.zones[zone_num]
            role = self._position.variant.roles[role_num]
            if unit_type is UnitTypeEnum.ARMY_UNIT:
                fake_unit = Army(self._position, role, zone, None, False)
            if unit_type is UnitTypeEnum.FLEET_UNIT:
                fake_unit = Fleet(self._position, role, zone, None, False)  # type: ignore
            self._fake_units[zone_num] = fake_unit

        # orders
        self._orders = []
        self._communication_orders = []
        # communication order do not have the game id as first item
        communication_orders_list = [[0] + o for o in communication_orders_list]
        for source, dest in ((server_dict['orders'], self._orders), (communication_orders_list, self._communication_orders)):
            for _, _, order_type_num, active_unit_zone_num, passive_unit_zone_num, destination_zone_num in source:

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

                order = Order(self._position, order_type, active_unit, passive_unit, destination_zone, source == communication_orders_list)
                dest.append(order)

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

    def all_ordered(self, role_id: int) -> bool:
        """ is_ordered """

        for unit in self._position.units:

            # must be of role if given
            if role_id not in (0, unit.role.identifier):
                continue

            # must have order
            if not self.is_ordered(unit):
                return False

        return True

    def closest_unit_or_built_unit(self, designated_pos: geometry.PositionRecord):
        """ closest_unit_or_built_unit """

        closest_unit = None
        distance_closest = inf

        # search units from position (make a copy)
        search_list = list(self._position.units)

        # add units from build orders
        search_list += list(self._fake_units.values())

        for unit in search_list:
            zone = unit.zone
            unit_pos = self._position.variant.position_table[zone]
            distance = designated_pos.distance(unit_pos)
            # if two units at same position we prefer the built one
            # this only occurs when user built on an existing unit
            if distance < distance_closest or (distance == distance_closest and unit in self._fake_units.values()):
                closest_unit = unit
                distance_closest = distance

        return closest_unit

    def erase_orders(self) -> None:
        """ erase all orders """

        self._orders = []
        self._fake_units = {}

    def rest_hold(self, role_id) -> None:
        """ set the unordered units orders to hold """

        # should be in season for move orders - not checked here

        for unit in self._position.units:

            # must not hgave an order
            if self.is_ordered(unit):
                continue

            # must be of role if role is given
            if role_id not in (0, unit.role.identifier):
                continue

            # receive order
            order = Order(self._position, OrderTypeEnum.HOLD_ORDER, unit, None, None, False)
            self.insert_order(order)

    def render(self, ctx) -> None:
        """ put me on screen """

        # orders
        for order in self._orders:
            order.render(ctx)

        if self._communication_orders:
            # The little rectangle
            fill_zone(ctx, COMMUNICATION_ORDER_PATH, COMMUNICATION_ORDER_COLOR, 1)

        # communication orders
        for order in self._communication_orders:
            order.render(ctx)

    def save_json(self):
        """ export as list of dict """
        # Note : we do not export fake units
        json_data = []
        for order in self._orders:
            json_data.append(order.save_json())
        return json_data

    def number(self):
        """" how many (builds) """
        return len(self._orders)

    def text_version(self) -> str:
        """" nice to read """

        text = ""
        roles_present = {o.active_unit.role for o in self._orders}
        for role in sorted(roles_present, key=lambda r: r.identifier):
            role_name = self._position.variant.role_name_table[role]
            text += role_name
            text += "\n"
            orders_role = '\n'.join([str(o) for o in self._orders if o.active_unit.role == role])
            text += orders_role
            text += "\n"
            text += "\n"
        return text

    def export_json(self):
        """ For trainer """
        return {
            'fake_units': [],  # not handled
            'orders': [o.export_json() for o in self._orders]
        }

    @property
    def orders(self):
        """ property """
        return self._orders

    def __str__(self) -> str:
        return '\n'.join([str(o) for o in self._orders])
