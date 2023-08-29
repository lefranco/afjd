#!/usr/bin/env python3


""" geometry """

import math
import enum
import typing


class DirectionEnum(enum.Enum):
    """ DirectionEnum """

    NORTH_EAST = 1
    NORTH_WEST = 2
    SOUTH_WEST = 3
    SOUTH_EAST = 4


def perpendicular(direction: DirectionEnum) -> DirectionEnum:
    """ perpendicular """
    if direction is DirectionEnum.NORTH_EAST:
        return DirectionEnum.NORTH_WEST
    if direction is DirectionEnum.NORTH_WEST:
        return DirectionEnum.SOUTH_WEST
    if direction is DirectionEnum.SOUTH_WEST:
        return DirectionEnum.SOUTH_EAST
    # if direction is DirectionEnum.SOUTH_EAST:
    return DirectionEnum.NORTH_EAST


def xy_shift(direction: DirectionEnum, amplitude: int) -> typing.Tuple[int, int]:
    """ x_shift """
    if direction is DirectionEnum.NORTH_EAST:
        return amplitude, -amplitude
    if direction is DirectionEnum.NORTH_WEST:
        return - amplitude, - amplitude
    if direction is DirectionEnum.SOUTH_WEST:
        return - amplitude, amplitude
    #  if direction is DirectionEnum.SOUTH_EAST:
    return amplitude, amplitude


class PositionRecord:
    """ A position """

    def __init__(self, x_pos: int, y_pos: int) -> None:
        self.x_pos = x_pos
        self.y_pos = y_pos

    def distance(self, other: 'PositionRecord') -> float:
        """ euclidian distance """
        return math.sqrt((other.x_pos - self.x_pos) ** 2 + (other.y_pos - self.y_pos) ** 2)

    def shift(self, direction: DirectionEnum, amplitude: int) -> 'PositionRecord':
        """ shift """
        x_shift, y_shift = xy_shift(direction, amplitude)
        return PositionRecord(x_pos=self.x_pos + x_shift, y_pos=self.y_pos + y_shift)

    def __str__(self) -> str:
        return f"({self.x_pos},{self.y_pos})"


def get_direction(p_from: PositionRecord, p_to: PositionRecord) -> DirectionEnum:
    """ two points give a vector and we get the direction """

    if p_to.y_pos < p_from.y_pos:
        if p_to.x_pos < p_from.x_pos:
            return DirectionEnum.NORTH_WEST
        return DirectionEnum.NORTH_EAST
    if p_to.x_pos < p_from.x_pos:
        return DirectionEnum.SOUTH_WEST
    return DirectionEnum.SOUTH_EAST


class Polygon:
    """ A polygon """

    def __init__(self, points: typing.List[PositionRecord]) -> None:

        # points
        self.points = points

        # shifted
        self.shifted_points = [points[-1]] + points[:-1]

        # bounding box
        self.x_min = min(p.x_pos for p in points)
        self.x_max = max(p.x_pos for p in points)
        self.y_min = min(p.y_pos for p in points)
        self.y_max = max(p.y_pos for p in points)

    def is_inside_me(self, point: PositionRecord) -> bool:
        """
            Adapted from this C code :

            int pnpoly(int nvert, float *vertx, float *verty, float testx, float testy)
            {
                int i, j, c = 0;
              for (i = 0, j = nvert-1; i < nvert; j = i++) {
                  if ( ((verty[i]>testy) != (verty[j]>testy)) &&
                     (testx < (vertx[j]-vertx[i]) * (testy-verty[i]) / (verty[j]-verty[i]) + vertx[i]) )
                c = !c;
              }
                return c;
            }

            from https://wrfranklin.org/Research/Short_Notes/pnpoly.html
        """

        # check bounding box (optimization)
        if not (self.x_min < point.x_pos <= self.x_max and self.y_min < point.y_pos <= self.y_max):
            return False

        inside = False

        for vj_point, vi_point in zip(self.shifted_points, self.points):
            if (vi_point.y_pos > point.y_pos) != (vj_point.y_pos > point.y_pos) and \
               point.x_pos < (vj_point.x_pos - vi_point.x_pos) * (point.y_pos - vi_point.y_pos) / (vj_point.y_pos - vi_point.y_pos) + vi_point.x_pos:

                inside = not inside

        return inside

    def __str__(self) -> str:
        return ','.join([str(p) for p in self.points])
