""" unit_design """

# pylint: disable=multiple-statements

import math


class Point:
    """ Point for easier compatbility with old C software (do not use a record here) """
    def __init__(self) -> None:
        self.x = 0  # pylint: disable=invalid-name
        self.y = 0  # pylint: disable=invalid-name


def stabbeur_army(x: int, y: int, ctx):  # pylint: disable=invalid-name
    """ display an army the stabbeur way """

    # the ctx.strokeStyle and ctx.fillStyle should be defined

    # socle
    p1 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
    p1[0].x = x - 15; p1[0].y = y + 6
    p1[1].x = x - 15; p1[1].y = y + 9
    p1[2].x = x + 6; p1[2].y = y + 9
    p1[3].x = x + 6; p1[3].y = y + 6
    ctx.beginPath()
    for n, p in enumerate(p1):  # pylint: disable=invalid-name
        if not n:
            ctx.moveTo(p.x, p.y)
        else:
            ctx.lineTo(p.x, p.y)
    ctx.fill(); ctx.stroke(); ctx.closePath()

    # coin
    p2 = [Point() for _ in range(3)]  # pylint: disable=invalid-name
    p2[0].x = x - 9; p2[0].y = y + 6
    p2[1].x = x - 4; p2[1].y = y + 6
    p2[2].x = x - 7; p2[2].y = y + 3
    ctx.beginPath()
    for n, p in enumerate(p2):  # pylint: disable=invalid-name
        if not n:
            ctx.moveTo(p.x, p.y)
        else:
            ctx.lineTo(p.x, p.y)
    ctx.fill(); ctx.stroke(); ctx.closePath()

    # canon
    p3 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
    p3[0].x = x - 2; p3[0].y = y - 7
    p3[1].x = x + 4; p3[1].y = y - 15
    p3[2].x = x + 5; p3[2].y = y - 13
    p3[3].x = x; p3[3].y = y - 7
    ctx.beginPath()
    for n, p in enumerate(p3):  # pylint: disable=invalid-name
        if not n:
            ctx.moveTo(p.x, p.y)
        else:
            ctx.lineTo(p.x, p.y)
    ctx.fill(); ctx.stroke(); ctx.closePath()

    # cercle autour roue exterieure
    # simplified
    ctx.beginPath()
    ctx.arc(x, y, 6, 0, 2 * math.pi, False)
    ctx.fill(); ctx.stroke(); ctx.closePath()

    # roue interieure
    # simplified
    ctx.beginPath()
    ctx.arc(x, y, 2, 0, 2 * math.pi, False)
    ctx.fill(); ctx.stroke(); ctx.closePath()

    # exterieur coin
    p4 = [Point() for _ in range(2)]  # pylint: disable=invalid-name
    p4[0].x = x - 7; p4[0].y = y + 3
    p4[1].x = x - 9; p4[1].y = y + 6
    ctx.beginPath()
    for n, p in enumerate(p4):  # pylint: disable=invalid-name
        if not n:
            ctx.moveTo(p.x, p.y)
        else:
            ctx.lineTo(p.x, p.y)
    ctx.stroke(); ctx.closePath()  # no fill


def stabbeur_fleet(x: int, y: int, ctx):  # pylint: disable=invalid-name
    """ display a fleet the stabbeur way """

    # the ctx.strokeStyle and ctx.fillStyle should be defined

    # gros oeuvre
    p1 = [Point() for _ in range(33)]  # pylint: disable=invalid-name
    p1[0].x = x - 15; p1[0].y = y + 4
    p1[1].x = x + 16; p1[1].y = y + 4
    p1[2].x = x + 15; p1[2].y = y
    p1[3].x = x + 10; p1[3].y = y
    p1[4].x = x + 10; p1[4].y = y - 3
    p1[5].x = x + 7; p1[5].y = y - 3
    p1[6].x = x + 7; p1[6].y = y - 2
    p1[7].x = x + 4; p1[7].y = y - 2
    p1[8].x = x + 4; p1[8].y = y - 9
    p1[9].x = x + 3; p1[9].y = y - 9
    p1[10].x = x + 3; p1[10].y = y - 6
    p1[11].x = x - 1; p1[11].y = y - 6
    p1[12].x = x - 1; p1[12].y = y - 9
    p1[13].x = x - 2; p1[13].y = y - 9
    p1[14].x = x - 2; p1[14].y = y - 13
    p1[15].x = x - 3; p1[15].y = y - 13
    p1[16].x = x - 3; p1[16].y = y - 6
    p1[17].x = x - 6; p1[17].y = y - 6
    p1[18].x = x - 6; p1[18].y = y - 5
    p1[19].x = x - 3; p1[19].y = y - 5
    p1[20].x = x - 3; p1[20].y = y - 4
    p1[21].x = x - 4; p1[21].y = y - 3
    p1[22].x = x - 4; p1[22].y = y - 2
    p1[23].x = x - 5; p1[23].y = y - 2
    p1[24].x = x - 5; p1[24].y = y - 3
    p1[25].x = x - 9; p1[25].y = y - 3
    p1[26].x = x - 9; p1[26].y = y
    p1[27].x = x - 12; p1[27].y = y
    p1[28].x = x - 12; p1[28].y = y - 1
    p1[29].x = x - 13; p1[29].y = y - 1
    p1[30].x = x - 13; p1[30].y = y
    p1[31].x = x - 12; p1[31].y = y
    p1[32].x = x - 15; p1[32].y = y + 4
    ctx.beginPath()
    for n, p in enumerate(p1):  # pylint: disable=invalid-name
        if not n:
            ctx.moveTo(p.x, p.y)
        else:
            ctx.lineTo(p.x, p.y)
    ctx.fill(); ctx.stroke(); ctx.closePath()

    # hublots
    for i in range(5):
        ctx.beginPath()
        ctx.arc(x - 8 + 5 * i + 1, y + 1, 1, 0, 2 * math.pi, False)
        ctx.stroke(); ctx.closePath()  # no fill
