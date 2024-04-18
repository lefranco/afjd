""" unit_design """

from math import pi


class Point:
    """ Point """

    def __init__(self, x: int, y: int) -> None:  # pylint: disable=invalid-name
        self.x = x  # pylint: disable=invalid-name
        self.y = y  # pylint: disable=invalid-name

    def transpose(self):
        """ turns 45 degrees """
        return Point(- self.y, self.x)


def draw_poly(x_pos: int, y_pos: int, p_stuff, transpose: bool, fill: True, ctx):
    """ draw_poly """

    # transpose if necessary
    if transpose:
        p_stuff = [p.transpose() for p in p_stuff]

    # draw
    ctx.beginPath()
    for num, point in enumerate(p_stuff):
        if not num:
            ctx.moveTo(x_pos + point.x, y_pos + point.y)
        else:
            ctx.lineTo(x_pos + point.x, y_pos + point.y)
    if fill:
        ctx.fill()
    ctx.stroke()
    ctx.closePath()


def draw_circle(x_pos: int, y_pos: int, ray: int, ctx):
    """ draw_circle """

    ctx.beginPath()
    ctx.arc(x_pos, y_pos, ray, 0, 2 * pi, False)
    ctx.fill()
    ctx.stroke()
    ctx.closePath()


def stabbeur_army(x_pos: int, y_pos: int, transpose: bool, ctx):
    """ display an army the stabbeur way """

    # the ctx.strokeStyle and ctx.fillStyle should be defined beforehand

    # basement
    p_basement = [
        Point(-11, 5),
        Point(-11, 7),
        Point(5, 7),
        Point(5, 5)
    ]
    draw_poly(x_pos, y_pos, p_basement, transpose, True, ctx)

    # corner
    p_corner = [
        Point(-7, 5),
        Point(-3, 5),
        Point(-5, 2)
    ]
    draw_poly(x_pos, y_pos, p_corner, transpose, True, ctx)

    # cannon
    p_cannon = [
        Point(-2, -5),
        Point(2, -10),
        Point(3, -9),
        Point(0, -5)
    ]
    draw_poly(x_pos, y_pos, p_cannon, transpose, True, ctx)

    # circle around external wheel
    draw_circle(x_pos, y_pos, 5, ctx)

    # internal wheel
    draw_circle(x_pos, y_pos, 2, ctx)

    # external corner
    p_ext_corner = [
        Point(-5, 2),
        Point(-7, 5)
    ]
    draw_poly(x_pos, y_pos, p_ext_corner, transpose, False, ctx)


def stabbeur_fleet(x_pos: int, y_pos: int, transpose: bool, ctx):
    """ display a fleet the stabbeur way """

    # the ctx.strokeStyle and ctx.fillStyle should be defined beforehand

    # big work
    p_big_work = [
        Point(- 11, 3),
        Point(12, 3),
        Point(11, 0),
        Point(8, 0),
        Point(8, - 2),
        Point(5, - 2),
        Point(5, - 2),
        Point(3, - 2),
        Point(3, - 7),
        Point(2, - 7),
        Point(2, - 5),
        Point(- 1, - 5),
        Point(- 1, - 7),
        Point(- 2, - 7),
        Point(- 2, - 11),
        Point(- 2, - 11),
        Point(- 2, - 5),
        Point(- 5, - 5),
        Point(- 5, - 4),
        Point(- 2, - 4),
        Point(- 2, - 3),
        Point(- 3, - 2),
        Point(- 3, - 2),
        Point(- 4, - 2),
        Point(- 4, - 2),
        Point(- 7, - 2),
        Point(- 7, 0),
        Point(- 9, 0),
        Point(- 9, - 1),
        Point(- 11, - 1),
        Point(- 11, 0),
        Point(- 9, 0),
        Point(- 11, 4)
    ]
    draw_poly(x_pos, y_pos, p_big_work, transpose, True, ctx)

    # porthole
    p_porthole = [Point(- 6 + 4 * i + 1, 1) for i in range(4)]
    if transpose:
        p_porthole = [p.transpose() for p in p_porthole]
    for point in p_porthole:
        draw_circle(x_pos + point.x, y_pos + point.y, 1, ctx)
