#!/usr/bin/env python3

"""
an ihm based on tkinter
this module handles ownerships of centers by playing roles
"""


import typing
import json

import data
import renderer

CENTER_SIZE = 4


class CenterOwnership(renderer.Renderer):
    """ An ownership (a relation between a center and a role) """

    def __init__(self, canvas: typing.Any, role: int, center_num: int) -> None:

        self._canvas = canvas

        assert isinstance(role, int)
        self._role = role

        assert isinstance(center_num, int)
        self._center_num = center_num

    def render(self) -> None:
        """ Put on canvas """

        role = self._role
        assert data.ROLE_DATA
        color_red = int(data.ROLE_DATA[str(role)]['red'])
        color_green = int(data.ROLE_DATA[str(role)]['green'])
        color_blue = int(data.ROLE_DATA[str(role)]['blue'])
        color_tuple = (color_red, color_green, color_blue)

        center_num = self._center_num
        assert data.CENTER_DATA
        x_pos = int(data.CENTER_DATA[str(center_num)]['x_pos'])
        y_pos = int(data.CENTER_DATA[str(center_num)]['y_pos'])

        color_red, color_green, color_blue = color_tuple
        fill_color = "#%02x%02x%02x" % (color_red, color_green, color_blue)
        self._canvas.create_rectangle(x_pos - CENTER_SIZE, y_pos - CENTER_SIZE, x_pos + CENTER_SIZE, y_pos + CENTER_SIZE, fill=fill_color)

    def load_json(self, json_dict: typing.Dict[str, typing.Any]) -> None:
        """ Load from dict """

        self._role = json_dict["role"]
        self._center_num = json_dict["center_num"]

    def save_json(self) -> typing.Dict[str, typing.Any]:
        """ Save to  dict """

        json_dict = {
            "role": int(self._role),
            "center_num": self._center_num
        }
        return json_dict

    @property
    def center_num(self) -> int:
        """ property """
        return self._center_num

    @property
    def role(self) -> int:
        """ property """
        return self._role

    @role.setter
    def role(self, role: int) -> None:
        """ setter """
        self._role = role

    def __str__(self) -> str:
        center_num = self._center_num
        region_num = data.find_region_center(center_num)
        region_name = data.find_region_name(region_num)
        return f"{region_name}"


class BagCenters:
    """ A bag of centers """

    def __init__(self, canvas: typing.Any) -> None:
        self._canvas = canvas
        self._content: typing.Dict[int, CenterOwnership] = dict()

    def reinit(self) -> None:
        """ reinit """
        self._content = dict()

    def add_center(self, center_ownership: CenterOwnership) -> None:
        """ Add center """
        center_num = center_ownership.center_num
        region_num = data.find_region_center(center_num)
        self._content[region_num] = center_ownership

    def remove_center(self, center_ownership: CenterOwnership) -> None:
        """ Remove center """
        center_num = center_ownership.center_num
        region_num = data.find_region_center(center_num)
        del self._content[region_num]

    def refresh(self) -> None:
        """ From the centers here refresh the canvas"""

        for center_ownership in self._content.values():
            center_ownership.render()

    def load_from_file(self, filename: str) -> None:
        """ load orders from file """

        with open(filename, 'r') as file_ptr2:
            json_data = json.load(file_ptr2)
            self._content = dict()
            for json_center in json_data:
                center_ownership = CenterOwnership(self._canvas, 0, 0)
                center_ownership.load_json(json_center)
                self.add_center(center_ownership)

    def save_to_file(self, filehandle: typing.Any) -> None:
        """ save orders to file """

        json_data = list()
        for center_ownership in self._content.values():
            json_data.append(center_ownership.save_json())
        output = json.dumps(json_data, indent=4)
        with filehandle as file_ptr3:
            file_ptr3.write(output)

    def save_json(self) -> typing.List[typing.Dict[str, typing.Any]]:
        """ export as list of dict """
        json_data = list()
        for center_ownership in self._content.values():
            json_data.append(center_ownership.save_json())
        return json_data

    def find_center(self, zone_num: int) -> typing.Optional[CenterOwnership]:
        """ Find center at zone """

        for center_ownership in self._content.values():
            center_num = center_ownership.center_num
            region_num = data.find_region_center(center_num)
            if region_num == data.find_region_num(zone_num):
                return center_ownership
        return None
