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

    def xy_shift(self, amplitude: int):
        """ x_shift """
        if self is DirectionEnum.NORTH_EAST:
            return amplitude, -amplitude
        if self is DirectionEnum.NORTH_WEST:
            return - amplitude, - amplitude
        if self is DirectionEnum.SOUTH_WEST:
            return - amplitude, amplitude
        #  if self is DirectionEnum.SOUTH_EAST:
        return amplitude, amplitude


class PositionRecord:
    """ A position """

    def __init__(self, x_pos, y_pos) -> None:
        self.x_pos = x_pos
        self.y_pos = y_pos

    def distance(self, other: 'PositionRecord') -> float:
        """ euclidian distance """
        return math.sqrt((other.x_pos - self.x_pos) ** 2 + (other.y_pos - self.y_pos) ** 2)

    def shift(self, direction: DirectionEnum, amplitude: int) -> 'PositionRecord':
        """ shift """
        x_shift, y_shift = direction.xy_shift(amplitude)
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


class LineRecord:
    """ A LineRecord """

    def __init__(self, point1: PositionRecord, point2: PositionRecord) -> None:
        self.point1 = point1
        self.point2 = point2

    def on_me(self, point: PositionRecord) -> bool:
        """ on_me """

        # Check whether point is on the line or not
        return point.x_pos <= max(self.point1.x_pos, self.point2.x_pos) and point.x_pos <= min(self.point1.x_pos, self.point2.x_pos) and (point.y_pos <= max(self.point1.y_pos, self.point2.y_pos) and point.y_pos <= min(self.point1.y_pos, self.point2.y_pos))


def relative_direction(point_a: PositionRecord, point_b: PositionRecord, point_c: PositionRecord) -> int:
    """ direction """

    val = (point_b.y_pos - point_a.y_pos) * (point_c.x_pos - point_b.x_pos) - (point_b.x_pos - point_a.x_pos) * (point_c.y_pos - point_b.y_pos)

    if val == 0:  # Colinear
        return 0

    if val < 0:  # Anti-clockwise direction
        return 2

    # Clockwise direction
    return 1


def is_intersect(line1: LineRecord, line2: LineRecord) -> bool:
    """ is_intersect """

    # Four direction for two lines and points of other line
    dir1 = relative_direction(line1.point1, line1.point2, line2.point1)
    dir2 = relative_direction(line1.point1, line1.point2, line2.point2)
    dir3 = relative_direction(line2.point1, line2.point2, line1.point1)
    dir4 = relative_direction(line2.point1, line2.point2, line1.point2)

    # When intersecting
    if dir1 != dir2 and dir3 != dir4:
        return True

    # When p2 of line2 are on the line1
    if dir1 == 0 and line1.on_me(line2.point1):
        return True

    # When p1 of line2 are on the line1
    if dir2 == 0 and line1.on_me(line2.point2):
        return True

    # When p2 of line1 are on the line2
    if dir3 == 0 and line2.on_me(line1.point1):
        return True

    # When p1 of line1 are on the line2
    if dir4 == 0 and line2.on_me(line1.point2):
        return True

    return False


FAR_AWAY = 9999


class Polygon:
    """ A polygon """

    def __init__(self, points) -> None:
        self.points = points

    def is_inside_me(self, point: PositionRecord) -> bool:
        """ is_inside_me """

        size = len(self.points)
        if size < 3:
            return False

        # Create a point at infinity, y is same as point
        exline = LineRecord(point, PositionRecord(FAR_AWAY, point.y_pos))
        count = 0
        i = 0
        while True:

            # Forming a line from two consecutive points of poly
            side = LineRecord(self.points[i], self.points[(i + 1) % size])
            if is_intersect(side, exline):

                # If side is intersects exline
                if relative_direction(side.point1, point, side.point2) == 0:
                    return side.on_me(point)

                count += 1

            i = (i + 1) % size

            if i == 0:
                break

        # When count is odd
        return bool(count % 2)

    def __str__(self) -> str:
        return ','.join([str(p) for p in self.points])
