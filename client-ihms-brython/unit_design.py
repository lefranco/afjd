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
        Point(-15, 6),
        Point(-15, 9),
        Point(6, 9),
        Point(6, 6)
    ]
    draw_poly(x_pos, y_pos, p_basement, transpose, True, ctx)

    # corner
    p_corner = [
        Point(-9, 6),
        Point(-4, 6),
        Point(-7, 3)
    ]
    draw_poly(x_pos, y_pos, p_corner, transpose, True, ctx)

    # cannon
    p_cannon = [
        Point(-2, -7),
        Point(3, -14),
        Point(4, -12),
        Point(0, -7)
    ]
    draw_poly(x_pos, y_pos, p_cannon, transpose, True, ctx)

    # circle around external wheel
    draw_circle(x_pos, y_pos, 6, ctx)

    # internal wheel
    draw_circle(x_pos, y_pos, 2, ctx)

    # external corner
    p_ext_corner = [
        Point(-7, 3),
        Point(-9, 6)
    ]
    draw_poly(x_pos, y_pos, p_ext_corner, transpose, False, ctx)


def stabbeur_fleet(x_pos: int, y_pos: int, transpose: bool, ctx):
    """ display a fleet the stabbeur way """

    # the ctx.strokeStyle and ctx.fillStyle should be defined beforehand

    # big work
    p_big_work = [
        Point(- 15, 4),
        Point(16, 4),
        Point(15, 0),
        Point(10, 0),
        Point(10, - 3),
        Point(7, - 3),
        Point(7, - 2),
        Point(4, - 2),
        Point(4, - 9),
        Point(3, - 9),
        Point(3, - 6),
        Point(- 1, - 6),
        Point(- 1, - 9),
        Point(- 2, - 9),
        Point(- 2, - 13),
        Point(- 3, - 13),
        Point(- 3, - 6),
        Point(- 6, - 6),
        Point(- 6, - 5),
        Point(- 3, - 5),
        Point(- 3, - 4),
        Point(- 4, - 3),
        Point(- 4, - 2),
        Point(- 5, - 2),
        Point(- 5, - 3),
        Point(- 9, - 3),
        Point(- 9, 0),
        Point(- 12, 0),
        Point(- 12, - 1),
        Point(- 13, - 1),
        Point(- 13, 0),
        Point(- 12, 0),
        Point(- 15, 4)
    ]
    draw_poly(x_pos, y_pos, p_big_work, transpose, True, ctx)

    # porthole
    p_porthole = [Point(- 8 + 5 * i + 1, 1) for i in range(5)]
    if transpose:
        p_porthole = [p.transpose() for p in p_porthole]
    for point in p_porthole:
        draw_circle(x_pos + point.x, y_pos + point.y, 1, ctx)
