""" mapping """

import typing


class RegionTypeEnum:
    """ RegionTypeEnum """

    COAST_REGION = 1
    LAND_REGION = 2
    SEA_REGION = 3

    @staticmethod
    def inventory() -> typing.Tuple[int, ...]:
        """ inventory """
        return (RegionTypeEnum.COAST_REGION, RegionTypeEnum.LAND_REGION, RegionTypeEnum.SEA_REGION)

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

    @property
    def region(self) -> 'Region':
        """ property """
        return self._region

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
    def variant(self) -> 'Variant':
        """ property """
        return self._variant


class Role:
    """ a Role """

    def __init__(self, identifier: int) -> None:

        self._identifier = identifier

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier


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
        for num, role_start_units in enumerate(raw_variant_content['start_units']):
            number = num + 1
            role = self._roles[number]
            for unit_type_code_str, role_start_units2 in role_start_units.items():
                unit_type_code = int(unit_type_code_str)
                unit_type = UnitTypeEnum.from_code(unit_type_code)
                assert unit_type is not None
                for zone_num in role_start_units2:
                    zone = self._zones[zone_num]

        # =================
        # from parameters file
        # =================

        self._region_name_table: typing.Dict[RegionTypeEnum, str] = {}
        self._unit_name_table: typing.Dict[UnitTypeEnum, str] = {}
        self._role_name_table: typing.Dict[Role, str] = {}
        self._coast_name_table: typing.Dict[CoastType, str] = {}
        self._zone_name_table: typing.Dict[Zone, str] = {}
        self._season_name_table: typing.Dict[SeasonEnum, str] = {}
        self._order_name_table: typing.Dict[OrderTypeEnum, str] = {}

        self._role_add_table = {}

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

            self._role_add_table[role] = (data_dict['adjective_name'], data_dict['letter_name'])

        # load coasts types names
        assert len(raw_parameters_content['coasts']) == len(self._coast_types)
        for coast_type_num_str, data_dict in raw_parameters_content['coasts'].items():
            coast_type_num = int(coast_type_num_str)
            coast_type = self._coast_types[coast_type_num]
            self._coast_name_table[coast_type] = data_dict['name']

        # load the zones names and localisations (units and legends)
        assert len(raw_parameters_content['zones']) == len(self._zones)
        for zone_num_str, data_dict in raw_parameters_content['zones'].items():
            zone_num = int(zone_num_str)
            zone = self._zones[zone_num]

            # special zones have a special name
            if zone.coast_type:
                assert zone.region.zone is not None
                region_name = self._zone_name_table[zone.region.zone]
                coast_name = self._coast_name_table[zone.coast_type]
                name = f"{region_name}{coast_name}"
            else:
                name = data_dict['name']

            self._zone_name_table[zone] = name

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

    def number_centers(self) -> int:
        """ number_centers """
        return len(self._centers)

    @property
    def role_name_table(self) -> typing.Dict[Role, str]:
        """ property """
        return self._role_name_table

    @property
    def roles(self) -> typing.Dict[int, Role]:
        """ property """
        return self._roles

    @property
    def extra_requirement_solo(self) -> bool:
        """ property """
        return self._extra_requirement_solo
