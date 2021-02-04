#!/usr/bin/env python3

"""
an ihm based on tkinter
this module handles forbidden regions (forbidden to retreat into becaus of conflicts during previous phase
"""


import typing

import data
import renderer

FORBIDDEN_COLOR = 'Red'


class Forbidden(renderer.Renderer):
    """ A blocked region """

    def __init__(self, canvas: typing.Any, region_num: int) -> None:
        self._canvas = canvas

        assert isinstance(region_num, int)
        self._region_num = region_num

    def render(self) -> None:
        """ Put on canvas """

        region_num = self._region_num
        assert data.ZONE_DATA
        x_pos = int(data.ZONE_DATA[str(region_num)]['x_pos'])
        y_pos = int(data.ZONE_DATA[str(region_num)]['y_pos'])

        self._canvas.create_line(x_pos + 6, y_pos + 6, x_pos - 6, y_pos - 6, fill=FORBIDDEN_COLOR, width=2)
        self._canvas.create_line(x_pos + 6, y_pos - 6, x_pos - 6, y_pos + 6, fill=FORBIDDEN_COLOR, width=2)

    @property
    def region_num(self) -> int:
        """ property """
        return self._region_num

    def __str__(self) -> str:
        #  DEBUG
        return f"region_num={self._region_num}"


class BagForbiddens:
    """ A bag of forbiddens """

    def __init__(self, canvas: typing.Any) -> None:
        self._canvas = canvas
        self._content: typing.List[Forbidden] = list()

    def reinit(self) -> None:
        """ reinit """
        self._content = list()

    def add_forbidden(self, forbidden: Forbidden) -> None:
        """ add forbidden """
        self._content.append(forbidden)

    def remove_forbidden(self, forbidden: Forbidden) -> None:
        """ remove forbidden """
        self._content.remove(forbidden)

    def refresh(self) -> None:
        """ From the orders here refresh the order text window """

        for forbidden in self._content:
            forbidden.render()

    def save_json(self) -> typing.List[int]:
        """ export as list of dict """
        json_data = list()
        for forbidden in self._content:
            json_data.append(forbidden.region_num)
        return json_data


if __name__ == "__main__":
    assert False, "Do not run this script"
