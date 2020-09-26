#!/usr/bin/env python3

"""
an ihm based on tkinter
this module handles units
"""

import typing
import json
import itertools

import tkinter
import tkinter.font  # type: ignore

import data
import renderer

# For displaying dislodged units
DISLODGED_BACKGROUND_COLOR = 'White'

# For displaying dislodged units
DISLODGED_COLOR = 'Orange'
DISLODGED_UNIT_X_SHIFT = - 5
DISLODGED_UNIT_Y_SHIFT = - 5
DISLODGED_TEXT_X_SHIFT = 14
DISLODGED_TEXT_Y_SHIFT = 12
DISLODGED_BACKGROUND_X_SHIFT = 2
DISLODGED_BACKGROUND_Y_SHIFT = -22
DISLODGED_RADIUS = 30


class Point:
    """ Point for easier compatbility with old C software (do not use a record here) """
    def __init__(self) -> None:
        self.x = 0  # pylint: disable=invalid-name
        self.y = 0  # pylint: disable=invalid-name


def outline_color_from_tuple(color_tuple: typing.Tuple[int, int, int]) -> str:
    """ Color to use for contours """

    if sum(color_tuple) < (256 + 256 + 256) // 2:
        return 'Grey'
    return 'Black'


def put_army(canvas: typing.Any, x_pos: int, y_pos: int, color_tuple: typing.Tuple[int, int, int]) -> None:
    """ Displays an army """

    color_red, color_green, color_blue = color_tuple
    fill_color = "#%02x%02x%02x" % (color_red, color_green, color_blue)
    outline_color = outline_color_from_tuple(color_tuple)

    x, y = x_pos, y_pos  # pylint: disable=invalid-name

    # socle
    p1 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
    p1[0].x = x - 15
    p1[0].y = y + 6
    p1[1].x = x - 15
    p1[1].y = y + 9
    p1[2].x = x + 6
    p1[2].y = y + 9
    p1[3].x = x + 6
    p1[3].y = y + 6
    canvas.create_polygon(*(itertools.chain(*[[p.x, p.y] for p in p1])), fill=fill_color, outline=outline_color)

    # coin
    p2 = [Point() for _ in range(3)]  # pylint: disable=invalid-name
    p2[0].x = x - 9
    p2[0].y = y + 6
    p2[1].x = x - 4
    p2[1].y = y + 6
    p2[2].x = x - 7
    p2[2].y = y + 3
    canvas.create_polygon(*(itertools.chain(*[[p.x, p.y] for p in p2])), fill=fill_color, outline=outline_color)

    # canon
    p3 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
    p3[0].x = x - 2
    p3[0].y = y - 7
    p3[1].x = x + 4
    p3[1].y = y - 15
    p3[2].x = x + 5
    p3[2].y = y - 13
    p3[3].x = x
    p3[3].y = y - 7
    canvas.create_polygon(*(itertools.chain(*[[p.x, p.y] for p in p3])), fill=fill_color, outline=outline_color)

    # cercle autour roue exterieure
    # simplified
    canvas.create_oval(x - 6, y - 6, x + 5, y + 5, fill=fill_color, outline=outline_color)

    # roue interieure
    # simplified
    canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill=fill_color, outline=outline_color)

    # exterieur coin
    canvas.create_line(x - 7, y + 3, x - 9, y + 6, fill=fill_color)


def put_fleet(canvas: typing.Any, x_pos: int, y_pos: int, color_tuple: typing.Tuple[int, int, int]) -> None:
    """ Displays a fleet """

    color_red, color_green, color_blue = color_tuple
    fill_color = "#%02x%02x%02x" % (color_red, color_green, color_blue)
    outline_color = outline_color_from_tuple(color_tuple)

    x, y = x_pos, y_pos  # pylint: disable=invalid-name

    # gros oeuvre
    p1 = [Point() for _ in range(32)]  # pylint: disable=invalid-name
    p1[0].x = x - 15
    p1[0].y = y + 4
    p1[1].x = x + 16
    p1[1].y = y + 4
    p1[2].x = x + 15
    p1[2].y = y
    p1[3].x = x + 10
    p1[3].y = y
    p1[4].x = x + 10
    p1[4].y = y - 3
    p1[5].x = x + 7
    p1[5].y = y - 3
    p1[6].x = x + 7
    p1[6].y = y - 2
    p1[7].x = x + 4
    p1[7].y = y - 2
    p1[8].x = x + 4
    p1[8].y = y - 9
    p1[9].x = x + 3
    p1[9].y = y - 9
    p1[10].x = x + 3
    p1[10].y = y - 6
    p1[11].x = x - 1
    p1[11].y = y - 6
    p1[12].x = x - 1
    p1[12].y = y - 9
    p1[13].x = x - 2
    p1[13].y = y - 9
    p1[14].x = x - 2
    p1[14].y = y - 13
    p1[15].x = x - 3
    p1[15].y = y - 13
    p1[16].x = x - 3
    p1[16].y = y - 6
    p1[17].x = x - 6
    p1[17].y = y - 6
    p1[18].x = x - 6
    p1[18].y = y - 5
    p1[19].x = x - 3
    p1[19].y = y - 5
    p1[20].x = x - 3
    p1[20].y = y - 4
    p1[21].x = x - 4
    p1[21].y = y - 3
    p1[22].x = x - 4
    p1[22].y = y - 2
    p1[23].x = x - 5
    p1[23].y = y - 2
    p1[24].x = x - 5
    p1[24].y = y - 3
    p1[25].x = x - 9
    p1[25].y = y - 3
    p1[26].x = x - 9
    p1[26].y = y
    p1[27].x = x - 12
    p1[27].y = y
    p1[28].x = x - 12
    p1[28].y = y - 1
    p1[29].x = x - 13
    p1[29].y = y - 1
    p1[30].x = x - 13
    p1[30].y = y
    p1[31].x = x - 12
    p1[31].y = y
    canvas.create_polygon(*(itertools.chain(*[[p.x, p.y] for p in p1])), fill=fill_color, outline=outline_color)

    # hublots
    for i in range(5):
        canvas.create_oval(x - 8 + 5 * i, y + 1, x - 8 + 5 * i + 2, y + 2, outline=outline_color)


class Unit(renderer.Renderer):
    """ A unit """

    def __init__(self, canvas: typing.Any, type_unit: data.TypeUnitEnum, role: int, zone: int, dislodged_origin: typing.Optional[int]) -> None:

        self._canvas = canvas

        assert isinstance(type_unit, data.TypeUnitEnum)
        self._type_unit = type_unit

        assert isinstance(role, int)
        self._role = role

        assert isinstance(zone, int)
        self._zone = zone

        self._dislodged_origin = dislodged_origin  # None means a unit in moves season

    def render(self) -> None:

        role = self._role
        assert data.ROLE_DATA
        color_red = int(data.ROLE_DATA[str(role)]['red'])
        color_green = int(data.ROLE_DATA[str(role)]['green'])
        color_blue = int(data.ROLE_DATA[str(role)]['blue'])
        color_tuple = (color_red, color_green, color_blue)

        zone_num = self._zone
        assert data.ZONE_DATA
        x_pos = int(data.ZONE_DATA[str(zone_num)]['x_pos'])
        y_pos = int(data.ZONE_DATA[str(zone_num)]['y_pos'])

        if self._dislodged_origin is not None:

            # shift position a bit
            x_pos_used = x_pos + DISLODGED_UNIT_X_SHIFT
            y_pos_used = y_pos + DISLODGED_UNIT_Y_SHIFT

            # put unit
            if self._type_unit == data.TypeUnitEnum.ARMY_TYPE:
                put_army(self._canvas, x_pos_used, y_pos_used, color_tuple)
            elif self._type_unit == data.TypeUnitEnum.FLEET_TYPE:
                put_fleet(self._canvas, x_pos_used, y_pos_used, color_tuple)
            else:
                assert False, "What is this unit type ?"

            # text to insert
            origin_name = data.find_zone_name(self._dislodged_origin)

            # size of the text to display
            width_calculated = tkinter.font.Font(font='TkDefaultFont').measure(origin_name)
            height_calculated = tkinter.font.Font(font='TkDefaultFont').metrics('linespace')

            # display the text (+ a rectangle as background)
            self._canvas.create_rectangle(x_pos_used + DISLODGED_BACKGROUND_X_SHIFT, y_pos_used + DISLODGED_BACKGROUND_Y_SHIFT, x_pos_used + DISLODGED_BACKGROUND_X_SHIFT + width_calculated, y_pos_used + DISLODGED_BACKGROUND_Y_SHIFT + height_calculated, fill=DISLODGED_BACKGROUND_COLOR, width=0)
            self._canvas.create_text(x_pos_used + DISLODGED_TEXT_X_SHIFT, y_pos_used - DISLODGED_TEXT_Y_SHIFT, text=origin_name, fill=DISLODGED_COLOR)

            # circle around unit
            self._canvas.create_oval(x_pos_used - DISLODGED_RADIUS // 2, y_pos_used - DISLODGED_RADIUS // 2, x_pos_used + DISLODGED_RADIUS // 2, y_pos_used + DISLODGED_RADIUS // 2, fill=None, outline=DISLODGED_COLOR, width=2)

        else:

            if self._type_unit == data.TypeUnitEnum.ARMY_TYPE:
                put_army(self._canvas, x_pos, y_pos, color_tuple)
            elif self._type_unit == data.TypeUnitEnum.FLEET_TYPE:
                put_fleet(self._canvas, x_pos, y_pos, color_tuple)
            else:
                assert False, "What is this unit type ?"

    def load_json(self, json_dict: typing.Dict[str, typing.Any]) -> None:
        """ Load from dict """

        type_unit = data.TypeUnitEnum.decode(json_dict["type_unit"])
        assert type_unit is not None
        self.type_unit = type_unit
        self._role = json_dict["role"]
        self._zone = json_dict["zone"]
        self._dislodged_origin = json_dict["dislodged_origin"] if "dislodged_origin" in json_dict else None

    def save_json(self) -> typing.Dict[str, typing.Any]:
        """ Save to  dict """

        json_dict = {
            "type_unit": self.type_unit.value,
            "role": int(self._role),
            "zone": self._zone
        }
        if self._dislodged_origin is not None:
            json_dict.update({"dislodged_origin": self._dislodged_origin})
        return json_dict

    def may_move_there_by_convoy(self, zone_dest: int) -> bool:
        """ says if move is possible usiung a convoy"""

        region_zone_num = data.find_region_num(self.zone)
        assert data.VARIANT_DATA
        region_type = data.VARIANT_DATA['regions'][region_zone_num - 1]
        region_type_enum = data.TypeRegionEnum.decode(region_type)
        assert region_type_enum is not None

        region_zone_dest_num = data.find_region_num(zone_dest)
        region_dest_type = data.VARIANT_DATA['regions'][region_zone_dest_num - 1]
        region_dest_type_enum = data.TypeRegionEnum.decode(region_dest_type)
        assert region_dest_type_enum is not None

        if region_zone_num is region_zone_dest_num:
            return False

        if self._type_unit is not data.TypeUnitEnum.ARMY_TYPE:
            return False

        if not (region_type_enum is data.TypeRegionEnum.COAST_TYPE and region_dest_type_enum is data.TypeRegionEnum.COAST_TYPE):
            return False

        if data.is_special_coast(zone_dest):
            return False

        return True

    def may_move_there_direct(self, zone_dest: int) -> bool:
        """ says if move is possible not using convoy (direct) """

        unit_type_num = self._type_unit.value
        unit_zone = self._zone
        assert data.VARIANT_DATA
        return zone_dest in data.VARIANT_DATA['neighbouring'][unit_type_num - 1][str(unit_zone)]

    def may_support_there(self, zone_dest_num: int) -> bool:
        """ says if support is possible """

        region_zone_dest_num = data.find_region_num(zone_dest_num)

        # must access a zone of same region
        unit_type_num = self.type_unit.value
        unit_zone = self._zone
        assert data.VARIANT_DATA
        for zone_dest_access in data.VARIANT_DATA['neighbouring'][unit_type_num - 1][str(unit_zone)]:
            region_zone_dest_access = data.find_region_num(zone_dest_access)
            if region_zone_dest_access == region_zone_dest_num:
                return True

        return False

    def may_appear(self) -> bool:
        """ says if unit may appear there """

        # check this type of unit is compatible with this type of region

        region_zone_num = data.find_region_num(self.zone)
        assert data.VARIANT_DATA
        region_type = data.VARIANT_DATA['regions'][region_zone_num - 1]
        region_type_enum = data.TypeRegionEnum.decode(region_type)
        assert region_type_enum is not None

        if self._type_unit is data.TypeUnitEnum.ARMY_TYPE:

            # army on coast ok most of the time
            if region_type_enum is data.TypeRegionEnum.COAST_TYPE:
                # army may not appear on special coasts
                if data.is_special_coast(self.zone):
                    return False
                return True

            # army inland ok
            if region_type_enum is data.TypeRegionEnum.INLAND_TYPE:
                return True

        if self._type_unit is data.TypeUnitEnum.FLEET_TYPE:

            # fleet on coast ok most of the time
            if region_type_enum is data.TypeRegionEnum.COAST_TYPE:
                # fleet may appear on special coasts
                if data.is_special_coast(self.zone):
                    return True
                # fleet may not appear on coasts that have special coasts
                for region_num, _ in data.VARIANT_DATA['coastal_zones']:
                    if self.zone == region_num:
                        return False
                return True

            # fleet at sea  ok
            if region_type_enum is data.TypeRegionEnum.SEA_TYPE:
                return True

        return False

    def may_convoy(self) -> bool:
        """ says if convoy is possible """

        # Must be a fleet
        if self._type_unit is not data.TypeUnitEnum.FLEET_TYPE:
            return False

        region_zone_num = data.find_region_num(self.zone)
        assert data.VARIANT_DATA
        region_type = data.VARIANT_DATA['regions'][region_zone_num - 1]
        region_type_enum = data.TypeRegionEnum.decode(region_type)
        assert region_type_enum is not None

        # Must be at sea
        if region_type_enum is not data.TypeRegionEnum.SEA_TYPE:
            return False

        return True

    def may_be_convoyed(self) -> bool:
        """ says if convoy (passive) is possible """

        # Must be an army
        if self._type_unit is not data.TypeUnitEnum.ARMY_TYPE:
            return False

        region_zone_num = data.find_region_num(self.zone)
        assert data.VARIANT_DATA
        region_type = data.VARIANT_DATA['regions'][region_zone_num - 1]
        region_type_enum = data.TypeRegionEnum.decode(region_type)
        assert region_type_enum is not None

        # Must be in coast
        if region_type_enum is not data.TypeRegionEnum.COAST_TYPE:
            return False

        return True

    @property
    def zone(self) -> int:
        """ property """
        return self._zone

    @property
    def dislodged_origin(self) -> typing.Optional[int]:
        """ property """
        return self._dislodged_origin

    @property
    def type_unit(self) -> data.TypeUnitEnum:
        """ property """
        return self._type_unit

    @type_unit.setter
    def type_unit(self, type_unit: data.TypeUnitEnum) -> None:
        """ setter """
        self._type_unit = type_unit

    @property
    def role(self) -> int:
        """ property """
        return self._role

    @role.setter
    def role(self, role: int) -> None:
        """ setter """
        self._role = role

    def __str__(self) -> str:
        zone_name = data.find_zone_name(self._zone)
        return f"{self._type_unit} {zone_name}"


class BagUnits:
    """ A bag of units """

    def __init__(self, canvas: typing.Any) -> None:
        self._canvas = canvas
        self._content: typing.Dict[int, Unit] = dict()
        self._content_fake: typing.Dict[int, Unit] = dict()
        self._content_dislodged: typing.Dict[int, Unit] = dict()

    def reinit(self) -> None:
        """ reinit """
        self._content = dict()
        self._content_fake = dict()
        self._content_dislodged = dict()

    def add_unit(self, unit: Unit) -> None:
        """ Add unit """

        assert unit.dislodged_origin is None
        zone_num = unit.zone
        assert zone_num is not None
        region_num = data.find_region_num(zone_num)
        self._content[region_num] = unit

    def add_fake_unit(self, unit: Unit) -> None:
        """ Add fake unit """

        assert unit.dislodged_origin is None
        zone_num = unit.zone
        assert zone_num is not None
        region_num = data.find_region_num(zone_num)
        self._content_fake[region_num] = unit

    def add_dislodged_unit(self, dislodged_unit: Unit) -> None:
        """ Add dislodged unit """

        assert dislodged_unit.dislodged_origin is not None
        zone_num = dislodged_unit.zone
        assert zone_num is not None
        region_num = data.find_region_num(zone_num)
        self._content_dislodged[region_num] = dislodged_unit

    def remove_unit(self, unit: Unit) -> None:
        """ Remove unit """

        zone_num = unit.zone
        assert zone_num is not None
        region_num = data.find_region_num(zone_num)
        del self._content[region_num]

        # and we remove the order too
        self._canvas.bag_orders.remove_from_unit(unit)

    def refresh(self) -> None:
        """ From the orders here refresh the order text window """

        # units first
        for unit in self._content.values():
            unit.render()

        # dislodged after so they get in front
        for dislodged_unit in self._content_dislodged.values():
            dislodged_unit.render()

    def load_from_file(self, filename: str) -> None:
        """ load orders from file """

        with open(filename, 'r') as file_ptr2:
            json_data = json.load(file_ptr2)
            self._content = dict()
            for json_unit in json_data:
                unit = Unit(self._canvas, data.TypeUnitEnum.ARMY_TYPE, 0, 0, None)
                unit.load_json(json_unit)
                if unit.dislodged_origin is None:
                    self.add_unit(unit)
                else:
                    self.add_dislodged_unit(unit)

    def save_to_file(self, filehandle: typing.Any) -> None:
        """ save orders to file """

        json_data = list()
        for unit in self._content.values():
            json_data.append(unit.save_json())
        output = json.dumps(json_data, indent=4)
        with filehandle as file_ptr3:
            file_ptr3.write(output)

    def save_json(self) -> typing.List[typing.Dict[str, typing.Any]]:
        """ export as list of dict """
        json_data = list()
        for unit in self._content.values():
            json_data.append(unit.save_json())
        return json_data

    def save_dislodged_json(self) -> typing.List[typing.Dict[str, typing.Any]]:
        """ export as list of dict """
        json_data = list()
        for dislodged_unit in self._content_dislodged.values():
            json_data.append(dislodged_unit.save_json())
        return json_data

    def find_unit(self, zone_num: int) -> typing.Optional[Unit]:
        """ Find unit at zone """
        for unit in self._content.values():
            if unit.zone == zone_num:
                return unit
        return None

    def find_fake_unit(self, zone_num: int) -> typing.Optional[Unit]:
        """ Find fake unit at zone """
        for fake_unit in self._content_fake.values():
            if fake_unit.zone == zone_num:
                return fake_unit
        return None

    def find_unit_same_region(self, zone_num: int) -> typing.Optional[Unit]:
        """ Find unit at region """
        for unit in self._content.values():
            if data.find_region_num(unit.zone) == data.find_region_num(zone_num):
                return unit
        return None

    def find_dislodged_unit(self, zone_num: int) -> typing.Optional[Unit]:
        """ Find dislodged unit at zone """
        for unit in self._content_dislodged.values():
            if unit.zone == zone_num:
                return unit
        return None


if __name__ == "__main__":
    assert False, "Do not run this script"
