""" mapping """

import typing


class RegionTypeEnum:
    """ RegionTypeEnum """

    COAST_REGION = 1
    LAND_REGION = 2
    SEA_REGION = 3
    ISLAND_REGION = 4

    @staticmethod
    def inventory() -> typing.Tuple[int, ...]:
        """ inventory """
        return (RegionTypeEnum.COAST_REGION, RegionTypeEnum.LAND_REGION, RegionTypeEnum.SEA_REGION, RegionTypeEnum.ISLAND_REGION)

    @staticmethod
    def from_code(code: int) -> 'RegionTypeEnum':
        """ from_code """
        return code  # type: ignore


class UnitTypeEnum:
    """ UnitTypeEnum """

    ARMY_UNIT = 1
    FLEET_UNIT = 2

    @staticmethod
    def inventory() -> typing.Tuple[int, ...]:
        """ inventory """
        return (UnitTypeEnum.ARMY_UNIT, UnitTypeEnum.FLEET_UNIT)

    @staticmethod
    def to_code(unit: int) -> int:
        """ to_code """
        return unit

    @staticmethod
    def from_code(code: int) -> 'UnitTypeEnum':
        """ from_code """
        return code  # type: ignore


class SeasonEnum:
    """ SeasonEnum """

    SPRING_SEASON = 1
    SUMMER_SEASON = 2
    AUTUMN_SEASON = 3
    WINTER_SEASON = 4
    ADJUST_SEASON = 5

    @staticmethod
    def inventory() -> typing.Tuple[int, ...]:
        """ inventory """
        return (SeasonEnum.SPRING_SEASON, SeasonEnum.SUMMER_SEASON, SeasonEnum.AUTUMN_SEASON, SeasonEnum.WINTER_SEASON, SeasonEnum.ADJUST_SEASON)

    @staticmethod
    def from_code(code: int) -> 'SeasonEnum':
        """ from_code """
        return code  # type: ignore


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
    def inventory() -> typing.Tuple[int, ...]:
        """ inventory """
        return (OrderTypeEnum.ATTACK_ORDER, OrderTypeEnum.OFF_SUPPORT_ORDER, OrderTypeEnum.DEF_SUPPORT_ORDER, OrderTypeEnum.HOLD_ORDER, OrderTypeEnum.CONVOY_ORDER, OrderTypeEnum.RETREAT_ORDER, OrderTypeEnum.DISBAND_ORDER, OrderTypeEnum.BUILD_ORDER, OrderTypeEnum.REMOVE_ORDER)

    @staticmethod
    def to_code(order: int) -> int:
        """ to_code """
        return order

    @staticmethod
    def from_code(code: int) -> 'OrderTypeEnum':
        """ from_code """
        return code  # type: ignore


class Center:
    """ A Center """

    def __init__(self, identifier: int, region: 'Region') -> None:

        self._identifier = identifier

        # the region in which is the center
        self._region = region

        # the owner at start of the game
        self._owner_start: typing.Optional['Role'] = None

        # free = no build
        self._free = False

    @property
    def region(self) -> 'Region':
        """ property """
        return self._region

    @property
    def owner_start(self) -> typing.Optional['Role']:
        """ property """
        return self._owner_start

    @owner_start.setter
    def owner_start(self, owner_start: 'Role') -> None:
        """ setter """
        self._owner_start = owner_start

    @property
    def free(self) -> bool:
        """ property """
        return self._free

    @free.setter
    def free(self, free: bool) -> None:
        """ setter """
        self._free = free

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
        self._center: typing.Optional[Center] = None

        # the zone (for localisation)
        self._zone: typing.Optional[Zone] = None

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

    def __init__(self, identifier: int, region: Region, coast_type: typing.Optional[CoastType], parent_zone: typing.Optional['Zone'], variant: 'Variant') -> None:

        self._identifier = identifier

        # most of the time zone = region
        self._region = region

        # for the special zones that have a specific coast
        self._coast_type = coast_type
        self._parent_zone = parent_zone

        # other zones one may access by fleet and army
        self._neighbours: typing.Dict[int, typing.List[Zone]] = {u: [] for u in UnitTypeEnum.inventory()}

        # variant
        self._variant = variant

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def coast_type(self) -> typing.Optional[CoastType]:
        """ property """
        return self._coast_type

    @property
    def region(self) -> Region:
        """ property """
        return self._region

    @property
    def neighbours(self) -> typing.Dict[int, typing.List['Zone']]:
        """ property """
        return self._neighbours

    @neighbours.setter
    def neighbours(self, neighbours: typing.Dict[int, typing.List['Zone']]) -> None:
        """ setter """
        self._neighbours = neighbours

    @property
    def variant(self) -> 'Variant':
        """ property """
        return self._variant

    @property
    def parent_zone(self) -> typing.Optional['Zone']:
        """ property """
        return self._parent_zone

    def __str__(self) -> str:
        variant = self._variant
        zone_full_name = variant.full_zone_name_table[self]
        return f"La zone {zone_full_name}"


class Role:
    """ a Role """

    def __init__(self, identifier: int) -> None:

        self._identifier = identifier

        # start centers the role have
        self._start_centers: typing.List[Center] = []

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def start_centers(self) -> typing.List[Center]:
        """ property """
        return self._start_centers

    @start_centers.setter
    def start_centers(self, start_centers: typing.List[Center]) -> None:
        """ setter """
        self._start_centers = start_centers


class EmergencyCenter:
    """Emergency center for v1900 only"""
    def __init__(self, role: Role, region: Region) -> None:
        self._role = role
        self._region = region

    @property
    def role(self) -> Role:
        """ property """
        return self._role

    @property
    def region(self) -> Region:
        """ property """
        return self._region


ASCII_CONVERSION_TABLE = {
    "àâ": 'a',
    "éèê": 'e',
    "î": 'i',
    "ô": 'o',
    "ù": 'u',
    "ç": 'c',
}


class Variant:
    """ A variant """

    def __init__(self, name: str, raw_variant_content: typing.Dict[str, typing.Any], raw_parameters_content: typing.Dict[str, typing.Any]) -> None:

        self._name = name

        # =================
        # from variant file
        # =================

        # build everywhere
        self._build_everywhere = bool(raw_variant_content['build_everywhere'])

        # start build
        self._start_build = bool(raw_variant_content['start_build'])

        # extra_requirement_solo
        self._extra_requirement_solo = int(raw_variant_content['extra_requirement_solo'])

        # load the regions
        self._regions = {}
        self._regions_types = set()
        for num, code in enumerate(raw_variant_content['regions']):
            number = num + 1
            region_type = RegionTypeEnum.from_code(code)
            self._regions_types.add(region_type)
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

        # load free centers
        self._free_centers = []
        for number_center in raw_variant_content['free_centers']:
            free_center = self._centers[number_center]
            free_center.free = True
            self._free_centers.append(free_center)

        # load emergency centers
        self._emergency_centers = []
        for num_role, num_region in raw_variant_content['emergency_centers']:
            role = self._roles[num_role]
            region = self._regions[num_region]
            emergency_center = EmergencyCenter(role, region)
            self._emergency_centers.append(emergency_center)

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
        self._start_units: typing.Dict[Role, typing.List[typing.Tuple[UnitTypeEnum, Zone]]] = {}
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
        # not needed

        # load the distancing
        # not needed

        # =================
        # from parameters file
        # =================

        self._region_name_table: typing.Dict[RegionTypeEnum, str] = {}
        self._unit_name_table: typing.Dict[UnitTypeEnum, str] = {}
        self._role_name_table: typing.Dict[Role, str] = {}
        self._coast_name_table: typing.Dict[CoastType, str] = {}
        self._coast_full_name_table: typing.Dict[CoastType, str] = {}
        self._zone_name_table: typing.Dict[Zone, str] = {}
        self._full_zone_name_table: typing.Dict[Zone, str] = {}
        self._season_name_table: typing.Dict[SeasonEnum, str] = {}
        self._order_name_table: typing.Dict[OrderTypeEnum, str] = {}

        self._role_add_table: typing.Dict[Role, typing.Tuple[str, str]] = {}

        # load the regions type names (islands may not be present)
        assert len(raw_parameters_content['regions']) == len(self._regions_types)
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
                assert zone.region.zone is not None
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

    def extract_names(self) -> typing.Dict[str, typing.Any]:
        """ extract the names we are using to pass them to adjudicator """

        def make_ascii(word: str) -> str:

            def replacement(letter: str) -> str:
                for candidates, target in ASCII_CONVERSION_TABLE.items():
                    if letter in candidates:
                        return target
                assert letter.isascii(), f"Please tell me how to simplify '{letter}'"
                return letter

            return ''.join(map(replacement, word))

        def extract_role_data(role: Role) -> typing.List[str]:
            """ extract_role_data """
            additional = self._role_add_table[role]
            return [self._role_name_table[role], make_ascii(additional[0]), additional[1]]

        def extract_zone_data(zone: Zone) -> str:
            """ extract_zone_data """
            if zone.coast_type:
                return ''
            return self._zone_name_table[zone]

        role_names = {k: extract_role_data(v) for k, v in self._roles.items()}
        zone_names = {k: extract_zone_data(v) for k, v in self._zones.items()}
        coast_names = {k: self._coast_name_table[v] for k, v in self._coast_types.items()}

        return {'roles': role_names, 'zones': zone_names, 'coasts': coast_names}

    def role_adjective(self, role: Role) -> str:
        """ role_adjective """
        role_adj, _ = self._role_add_table[role]
        return role_adj

    def number_centers(self) -> int:
        """ number_centers """
        return len(self._centers)

    @property
    def name(self) -> str:
        """ property """
        return self._name

    @property
    def region_name_table(self) -> typing.Dict[RegionTypeEnum, str]:
        """ property """
        return self._region_name_table

    @property
    def unit_name_table(self) -> typing.Dict[UnitTypeEnum, str]:
        """ property """
        return self._unit_name_table

    @property
    def role_name_table(self) -> typing.Dict[Role, str]:
        """ property """
        return self._role_name_table

    @property
    def coast_name_table(self) -> typing.Dict[CoastType, str]:
        """ property """
        return self._coast_name_table

    @property
    def zone_name_table(self) -> typing.Dict[Zone, str]:
        """ property """
        return self._zone_name_table

    @property
    def full_zone_name_table(self) -> typing.Dict[Zone, str]:
        """ property """
        return self._full_zone_name_table

    @property
    def season_name_table(self) -> typing.Dict[SeasonEnum, str]:
        """ property """
        return self._season_name_table

    @property
    def order_name_table(self) -> typing.Dict[OrderTypeEnum, str]:
        """ property """
        return self._order_name_table

    @property
    def roles(self) -> typing.Dict[int, Role]:
        """ property """
        return self._roles

    @property
    def start_units(self) -> typing.Dict[Role, typing.List[typing.Tuple[UnitTypeEnum, Zone]]]:
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
    def extra_requirement_solo(self) -> int:
        """ property """
        return self._extra_requirement_solo

    @property
    def free_centers(self) -> typing.List[Center]:
        """ property """
        return self._free_centers

    @property
    def emergency_centers(self) -> typing.List[EmergencyCenter]:
        """ property """
        return self._emergency_centers
