""" geometry """

import enum
import math


@enum.unique
class DirectionEnum(enum.Enum):
    """ DirectionEnum """

    NORTH_EAST = enum.auto()
    NORTH_WEST = enum.auto()
    SOUTH_WEST = enum.auto()
    SOUTH_EAST = enum.auto()

    def perpendicular(self) -> 'DirectionEnum':
        """ perpendicular """
        if self is DirectionEnum.NORTH_EAST:
            return DirectionEnum.NORTH_WEST
        if self is DirectionEnum.NORTH_WEST:
            return DirectionEnum.SOUTH_WEST
        if self is DirectionEnum.SOUTH_WEST:
            return DirectionEnum.SOUTH_EAST
        # if self is DirectionEnum.SOUTH_EAST:
        return DirectionEnum.NORTH_EAST

    def xy_shift(self):
        """ x_shift """
        if self is DirectionEnum.NORTH_EAST:
            return 3, -3
        if self is DirectionEnum.NORTH_WEST:
            return - 3, - 3
        if self is DirectionEnum.SOUTH_WEST:
            return - 3, 3
        #  if self is DirectionEnum.SOUTH_EAST:
        return 3, 3

class PositionRecord:
    """ A position """

    def __init__(self, x_pos, y_pos) -> None:
        self.x_pos = x_pos
        self.y_pos = y_pos

    def distance(self, other: 'PositionRecord') -> float:
        """ euclidian distance """
        return math.sqrt((other.x_pos - self.x_pos) ** 2 + (other.y_pos - self.y_pos) ** 2)

    def shift(self, direction: DirectionEnum) -> 'PositionRecord':
        """ shift """
        x_shift, y_shift = direction.xy_shift()
        return PositionRecord(x_pos=self.x_pos + x_shift, y_pos=self.y_pos + y_shift)


def get_direction(p_from: PositionRecord, p_to: PositionRecord) -> DirectionEnum:
    """ two points give a vector and we get the direction """

    if p_to.y_pos < p_from.y_pos:
        if p_to.x_pos < p_from.x_pos:
            return DirectionEnum.NORTH_WEST
        return DirectionEnum.NORTH_EAST
    if p_to.x_pos < p_from.x_pos:
        return DirectionEnum.SOUTH_WEST
    return DirectionEnum.SOUTH_EAST
