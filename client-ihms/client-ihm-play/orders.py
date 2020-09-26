#!/usr/bin/env python3

"""
an ihm based on tkinter
this module handles orders entered by user
"""

import typing
import enum
import json
import math

import tkinter

import data
import renderer
import units

# For displaying orders
PASSIVE_X_SHIFT = 5
PASSIVE_Y_SHIFT = 5
ACTION_COLOR = 'Black'
SUPPORTED_COLOR = 'Grey'
SUPPORT_COLOR = 'Red'
CONVOY_COLOR = 'Blue'
HOLD_RADIUS = 10

DISBAND_SIZE = 8

REMOVE_COLOR = 'Black'
REMOVE_SIZE = 8

CREATED_SIZE = 12
CREATED_COLOR = 'Black'


@enum.unique
class OrderEnum(enum.Enum):
    """ Button that was clicked """

    # move
    ATTACK_ORDER = enum.auto()
    OFFENSIVE_SUPPORT_ORDER = enum.auto()
    DEFENSIVE_SUPPORT_ORDER = enum.auto()
    HOLD_ORDER = enum.auto()
    CONVOY_ORDER = enum.auto()

    # retreat
    RETREAT_ORDER = enum.auto()
    DISBAND_ORDER = enum.auto()

    # adjustment
    BUILD_ORDER = enum.auto()
    REMOVE_ORDER = enum.auto()

    @staticmethod
    def decode(val: int) -> typing.Optional['OrderEnum']:
        """ from int to enum """
        for order in OrderEnum:
            if order.value == val:
                return order
        return None


@enum.unique
class OrderPhaseEnum(enum.Enum):
    """ The three phases so three different sets of possible orders  """

    MOVEMENT_PHASE = enum.auto()
    RETREAT_PHASE = enum.auto()
    ADJUSTMENT_PHASE = enum.auto()


class Order(renderer.Renderer):
    """ An order """
    def __init__(self, canvas: typing.Any) -> None:

        self._canvas = canvas
        self._order_type: typing.Optional[OrderEnum] = None
        self._active_unit: typing.Optional[units.Unit] = None
        self._passive_unit: typing.Optional[units.Unit] = None
        self._destination_zone: typing.Optional[int] = None

    def render(self) -> None:
        """ Put on canvas """

        assert self._active_unit is not None
        zone_from_num = self._active_unit.zone
        assert data.ZONE_DATA
        x_pos_from = int(data.ZONE_DATA[str(zone_from_num)]['x_pos'])
        y_pos_from = int(data.ZONE_DATA[str(zone_from_num)]['y_pos'])

        # Moves

        if self._order_type is OrderEnum.ATTACK_ORDER:

            assert self._destination_zone is not None
            zone_to_num = self._destination_zone
            x_pos_to = int(data.ZONE_DATA[str(zone_to_num)]['x_pos'])
            y_pos_to = int(data.ZONE_DATA[str(zone_to_num)]['y_pos'])
            self._canvas.create_line(x_pos_from, y_pos_from, x_pos_to, y_pos_to, fill=ACTION_COLOR, arrow=tkinter.LAST)

        if self._order_type is OrderEnum.OFFENSIVE_SUPPORT_ORDER:

            assert self._passive_unit is not None
            zone_passive_from_num = self._passive_unit.zone
            x_pos_passive_from = int(data.ZONE_DATA[str(zone_passive_from_num)]['x_pos'])
            y_pos_passive_from = int(data.ZONE_DATA[str(zone_passive_from_num)]['y_pos'])
            assert self._destination_zone is not None
            zone_to_num = self._destination_zone
            x_pos_to = int(data.ZONE_DATA[str(zone_to_num)]['x_pos']) + PASSIVE_X_SHIFT
            y_pos_to = int(data.ZONE_DATA[str(zone_to_num)]['y_pos']) + PASSIVE_Y_SHIFT
            self._canvas.create_line(x_pos_passive_from, y_pos_passive_from, x_pos_to, y_pos_to, fill=SUPPORTED_COLOR, arrow=tkinter.LAST)

            x_middle = (x_pos_passive_from + x_pos_to) // 2
            y_middle = (y_pos_passive_from + y_pos_to) // 2
            self._canvas.create_line(x_pos_from, y_pos_from, x_middle, y_middle, fill=SUPPORT_COLOR)

        if self._order_type is OrderEnum.DEFENSIVE_SUPPORT_ORDER:

            assert self._passive_unit is not None
            zone_passive_num = self._passive_unit.zone
            x_pos_passive = int(data.ZONE_DATA[str(zone_passive_num)]['x_pos']) + PASSIVE_X_SHIFT
            y_pos_passive = int(data.ZONE_DATA[str(zone_passive_num)]['y_pos']) + PASSIVE_Y_SHIFT

            distance = math.sqrt((x_pos_passive - x_pos_from)**2 + (y_pos_passive - y_pos_from)**2)
            if distance > HOLD_RADIUS:
                x_pos_passive_reach = x_pos_from + ((distance - HOLD_RADIUS) / distance) * (x_pos_passive - x_pos_from)
                y_pos_passive_reach = y_pos_from + ((distance - HOLD_RADIUS) / distance) * (y_pos_passive - y_pos_from)
                self._canvas.create_line(x_pos_from, y_pos_from, x_pos_passive_reach, y_pos_passive_reach, fill=SUPPORT_COLOR)

            self._canvas.create_oval(x_pos_passive - HOLD_RADIUS, y_pos_passive - HOLD_RADIUS, x_pos_passive + HOLD_RADIUS, y_pos_passive + HOLD_RADIUS, fill=None, outline=SUPPORTED_COLOR)

        if self._order_type is OrderEnum.HOLD_ORDER:
            self._canvas.create_oval(x_pos_from - HOLD_RADIUS, y_pos_from - HOLD_RADIUS, x_pos_from + HOLD_RADIUS, y_pos_from + HOLD_RADIUS, fill=None, outline=ACTION_COLOR)

        if self._order_type is OrderEnum.CONVOY_ORDER:

            assert self._passive_unit is not None
            zone_passive_from_num = self._passive_unit.zone
            x_pos_passive_from = int(data.ZONE_DATA[str(zone_passive_from_num)]['x_pos']) + PASSIVE_X_SHIFT
            y_pos_passive_from = int(data.ZONE_DATA[str(zone_passive_from_num)]['y_pos']) + PASSIVE_Y_SHIFT
            assert self._destination_zone is not None
            zone_to_num = self._destination_zone
            x_pos_to = int(data.ZONE_DATA[str(zone_to_num)]['x_pos']) + PASSIVE_X_SHIFT
            y_pos_to = int(data.ZONE_DATA[str(zone_to_num)]['y_pos']) + PASSIVE_Y_SHIFT
            self._canvas.create_line(x_pos_passive_from, y_pos_passive_from, x_pos_to, y_pos_to, fill=SUPPORTED_COLOR, arrow=tkinter.LAST)

            x_middle = (x_pos_passive_from + x_pos_to) // 2
            y_middle = (y_pos_passive_from + y_pos_to) // 2
            self._canvas.create_line(x_pos_from, y_pos_from, x_middle, y_middle, fill=CONVOY_COLOR)

        # Retreats

        if self._order_type is OrderEnum.RETREAT_ORDER:

            x_pos = x_pos_from + units.DISLODGED_UNIT_X_SHIFT
            y_pos = y_pos_from + units.DISLODGED_UNIT_Y_SHIFT

            assert self._destination_zone is not None
            zone_to_num = self._destination_zone
            x_pos_to = int(data.ZONE_DATA[str(zone_to_num)]['x_pos']) + units.DISLODGED_UNIT_X_SHIFT
            y_pos_to = int(data.ZONE_DATA[str(zone_to_num)]['y_pos']) + units.DISLODGED_UNIT_Y_SHIFT
            self._canvas.create_line(x_pos, y_pos, x_pos_to, y_pos_to, fill=ACTION_COLOR, arrow=tkinter.LAST)

        if self._order_type is OrderEnum.DISBAND_ORDER:
            x_pos = x_pos_from + units.DISLODGED_UNIT_X_SHIFT
            y_pos = y_pos_from + units.DISLODGED_UNIT_Y_SHIFT
            self._canvas.create_line(x_pos + DISBAND_SIZE, y_pos + DISBAND_SIZE, x_pos - DISBAND_SIZE, y_pos - DISBAND_SIZE, fill=REMOVE_COLOR, width=2)
            self._canvas.create_line(x_pos + DISBAND_SIZE, y_pos - DISBAND_SIZE, x_pos - DISBAND_SIZE, y_pos + DISBAND_SIZE, fill=REMOVE_COLOR, width=2)

        # Adjustments

        if self._order_type is OrderEnum.BUILD_ORDER:
            self._active_unit.render()
            self._canvas.create_rectangle(x_pos_from - CREATED_SIZE, y_pos_from - CREATED_SIZE, x_pos_from + CREATED_SIZE, y_pos_from + CREATED_SIZE, fill=None, outline=CREATED_COLOR, width=2)

        if self._order_type is OrderEnum.REMOVE_ORDER:
            self._canvas.create_line(x_pos_from + REMOVE_SIZE, y_pos_from + REMOVE_SIZE, x_pos_from - REMOVE_SIZE, y_pos_from - REMOVE_SIZE, fill=REMOVE_COLOR, width=2)
            self._canvas.create_line(x_pos_from + REMOVE_SIZE, y_pos_from - REMOVE_SIZE, x_pos_from - REMOVE_SIZE, y_pos_from + REMOVE_SIZE, fill=REMOVE_COLOR, width=2)

    def load_json(self, json_dict: typing.Dict[str, typing.Any]) -> None:
        """ Load from dict """

        if "order_type" in json_dict:
            self._order_type = OrderEnum.decode(json_dict["order_type"])
        if "active_unit" in json_dict:
            unit = units.Unit(self._canvas, data.TypeUnitEnum.ARMY_TYPE, 1, 1, None)
            unit.load_json(json_dict["active_unit"])
            self._active_unit = unit
        if "passive_unit" in json_dict:
            unit = units.Unit(self._canvas, data.TypeUnitEnum.ARMY_TYPE, 1, 1, None)
            unit.load_json(json_dict["passive_unit"])
            self._passive_unit = unit
        if "destination_zone" in json_dict:
            self._destination_zone = json_dict["destination_zone"]

    def save_json(self) -> typing.Dict[str, typing.Any]:
        """ Save to  dict """

        json_dict = dict()
        if self._order_type is not None:
            json_dict.update({"order_type": self._order_type.value})
        if self._active_unit is not None:
            json_dict.update({"active_unit": self._active_unit.save_json()})
        if self._passive_unit is not None:
            json_dict.update({"passive_unit": self._passive_unit.save_json()})
        if self._destination_zone is not None:
            json_dict.update({"destination_zone": self._destination_zone})
        return json_dict

    @property
    def order_type(self) -> typing.Optional[OrderEnum]:
        """ property """
        return self._order_type

    @order_type.setter
    def order_type(self, order_type: OrderEnum) -> None:
        """ setter """
        self._order_type = order_type

    @property
    def active_unit(self) -> typing.Optional[units.Unit]:
        """ property """
        return self._active_unit

    @active_unit.setter
    def active_unit(self, active_unit: units.Unit) -> None:
        """ setter """
        self._active_unit = active_unit

    @property
    def passive_unit(self) -> typing.Optional[units.Unit]:
        """ property """
        return self._passive_unit

    @passive_unit.setter
    def passive_unit(self, passive_unit: units.Unit) -> None:
        """ setter """
        self._passive_unit = passive_unit

    @property
    def destination_zone(self) -> typing.Optional[int]:
        """ property """
        return self._destination_zone

    @destination_zone.setter
    def destination_zone(self, destination_zone: int) -> None:
        """ setter """
        self._destination_zone = destination_zone

    def __str__(self) -> str:

        # Move
        if self._order_type is OrderEnum.ATTACK_ORDER:
            assert self._destination_zone is not None
            zone_dest = data.find_zone_name(self._destination_zone)
            return f"{self._active_unit} - {zone_dest}"
        if self._order_type is OrderEnum.OFFENSIVE_SUPPORT_ORDER:
            assert self._destination_zone is not None
            zone_dest = data.find_zone_name(self._destination_zone)
            return f"{self._active_unit} S {self._passive_unit} - {zone_dest}"
        if self._order_type is OrderEnum.DEFENSIVE_SUPPORT_ORDER:
            return f"{self._active_unit} S {self._passive_unit}"
        if self._order_type is OrderEnum.HOLD_ORDER:
            return f"{self._active_unit} H"
        if self._order_type is OrderEnum.CONVOY_ORDER:
            assert self._destination_zone is not None
            zone_dest = data.find_zone_name(self._destination_zone)
            return f"{self._active_unit} C {self._passive_unit} - {zone_dest}"

        # Retreat
        if self._order_type is OrderEnum.RETREAT_ORDER:
            assert self._destination_zone is not None
            zone_dest = data.find_zone_name(self._destination_zone)
            return f"{self._active_unit} R {zone_dest}"
        if self._order_type is OrderEnum.DISBAND_ORDER:
            return f"{self._active_unit} A"

        # Adjustment
        if self._order_type is OrderEnum.BUILD_ORDER:
            return f"+ {self.active_unit}"
        if self._order_type is OrderEnum.REMOVE_ORDER:
            return f"- {self.active_unit}"

        assert False, "What is this phase/ order type ?"
        return ""


class BagOrders:
    """ A bag of orders """

    def __init__(self, canvas: typing.Any) -> None:
        self._canvas = canvas
        self._content: typing.Dict[int, Order] = dict()
        self._scrolled_text: typing.Optional[typing.Any] = None

    def reinit(self) -> None:
        """ empy bag of orders """
        self._content = dict()
        self._canvas.application.button_simulate.config(state=tkinter.DISABLED)
        self._canvas.application.button_reinit.config(state=tkinter.DISABLED)

    def add_update_order(self, order: Order) -> None:
        """ Add order or update if already there """

        assert order.active_unit is not None
        zone_num = order.active_unit.zone
        assert zone_num is not None
        region_num = data.find_region_num(zone_num)
        self._content[region_num] = order

        self._canvas.application.button_simulate.config(state=tkinter.ACTIVE)
        self._canvas.application.button_reinit.config(state=tkinter.ACTIVE)

    def remove_order(self, order: Order) -> None:
        """ Remove order """

        assert order.active_unit is not None
        zone_num = order.active_unit.zone
        assert zone_num is not None
        region_num = data.find_region_num(zone_num)
        del self._content[region_num]

    def remove_from_unit(self, unit: units.Unit) -> None:
        """ Remove ordrer given to a unit """

        order_to_remove: typing.Optional[Order] = None
        for order in self._content.values():
            if order.active_unit == unit:
                order_to_remove = order
                break

        if order_to_remove is not None:
            self.remove_order(order_to_remove)

    def refresh(self) -> None:
        """ From the orders here refresh the canvas"""

        # put as graphics
        for order in self._content.values():
            order.render()

        # put as text
        self._canvas.application.text_orders.configure(state=tkinter.NORMAL)
        self._canvas.application.text_orders.delete('1.0', tkinter.END)
        for order in self._content.values():
            self._canvas.application.text_orders.insert(tkinter.END, f"{order}\n")
        self._canvas.application.text_orders.see(tkinter.END)
        self._canvas.application.text_orders.configure(state=tkinter.DISABLED)

    def load_from_file(self, filename: str) -> None:
        """ load orders from file """

        with open(filename, 'r') as file_ptr2:
            json_data = json.load(file_ptr2)
            self._content = dict()
            for json_order in json_data:
                order = Order(self._canvas)
                order.load_json(json_order)
                self.add_update_order(order)

    def save_to_file(self, filehandle: typing.Any) -> None:
        """ save orders to file """

        json_data = list()
        for order in self._content.values():
            json_data.append(order.save_json())
        output = json.dumps(json_data, indent=4)
        with filehandle as file_ptr3:
            file_ptr3.write(output)

    def save_json(self) -> typing.List[typing.Dict[str, typing.Any]]:
        """ export as list of dict """
        json_data = list()
        for order in self._content.values():
            json_data.append(order.save_json())
        return json_data


if __name__ == "__main__":
    assert False, "Do not run this script"
