#!/usr/bin/env python3


"""
Check colors used in displaying
"""

import argparse
import typing
import os
import sys
import json
import itertools
import math
import colorsys


TRANSPARENCY_OWNER = 0.70

TOLERANCE_HUE = 10
MIN_DIFFERENCE_LUM = 20

# parameter 'threshold_separation' : 
# dE < 1 : Imperceptible to the naked eye
# dE < 5 : Very close, barely distinguishable
# dE < 10 : Distinguishable but close
# else OK, clearly distinct


def alpha_compose(background, item):
    """Compose item over background using alpha transparency."""
    return tuple(round(TRANSPARENCY_OWNER * item[i] + (1-TRANSPARENCY_OWNER) * background[i]) for i in range(3))


def rgb_to_luminance(r, g, b):
    """Relative luminance approximation, 0-100%."""
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0 * 100.0


def rgb_to_hsv(r, g, b):
    """Converts RGB (0-255) to HSV (H en degrees 0-360, S and V in %)"""

    r, g, b = r / 255.0, g / 255.0, b / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)  # beware : colorsys returns H,L,S
    return h * 360.0, s * 100.0, v * 100.0


def rgb_to_lab(r, g, b):
    """Converts RGB (0-255) to space CIELAB, using XYZ."""

    def linearize(c):
        c = c / 255.0
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

    r_lin, g_lin, b_lin = linearize(r), linearize(g), linearize(b)

    # RGB lineair -> XYZ (matrice sRGB standard, illuminating D65)
    x = r_lin * 0.4124 + g_lin * 0.3576 + b_lin * 0.1805
    y = r_lin * 0.2126 + g_lin * 0.7152 + b_lin * 0.0722
    z = r_lin * 0.0193 + g_lin * 0.1192 + b_lin * 0.9505

    x, y, z = x / 0.95047, y / 1.00000, z / 1.08883

    def f(t):
        return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16 / 116)

    fx, fy, fz = f(x), f(y), f(z)
    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b_lab = 200 * (fy - fz)

    return L, a, b_lab


def delta_e_cie2000(lab1, lab2):
    """Calculates Delta E 2000 of two colors Lab."""

    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_avg = (C1 + C2) / 2

    G = 0.5 * (1 - math.sqrt(C_avg**7 / (C_avg**7 + 25**7)))
    a1p = a1 * (1 + G)
    a2p = a2 * (1 + G)

    C1p = math.sqrt(a1p**2 + b1**2)
    C2p = math.sqrt(a2p**2 + b2**2)

    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360

    dLp = L2 - L1
    dCp = C2p - C1p

    dhp = h2p - h1p
    if C1p * C2p == 0:
        dhp = 0
    elif abs(dhp) > 180:
        dhp -= 360 * (1 if dhp > 0 else -1)
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)

    Lp_avg = (L1 + L2) / 2
    Cp_avg = (C1p + C2p) / 2

    if C1p * C2p == 0:
        hp_avg = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hp_avg = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hp_avg = (h1p + h2p + 360) / 2
    else:
        hp_avg = (h1p + h2p - 360) / 2

    T = (1 - 0.17 * math.cos(math.radians(hp_avg - 30))
           + 0.24 * math.cos(math.radians(2 * hp_avg))
           + 0.32 * math.cos(math.radians(3 * hp_avg + 6))
           - 0.20 * math.cos(math.radians(4 * hp_avg - 63)))

    d_ro = 30 * math.exp(-(((hp_avg - 275) / 25) ** 2))
    RC = 2 * math.sqrt(Cp_avg**7 / (Cp_avg**7 + 25**7))
    SL = 1 + ((0.015 * (Lp_avg - 50)**2) / math.sqrt(20 + (Lp_avg - 50)**2))
    SC = 1 + 0.045 * Cp_avg
    SH = 1 + 0.015 * Cp_avg * T
    RT = -math.sin(math.radians(2 * d_ro)) * RC

    dE = math.sqrt(
        (dLp / SL) ** 2 +
        (dCp / SC) ** 2 +
        (dHp / SH) ** 2 +
        RT * (dCp / SC) * (dHp / SH)
    )
    return dE


def closeness(rgb1, rgb2):
    """The ultimate comparer between two RGB... so simple !"""

    lab1 = rgb_to_lab(*rgb1)
    lab2 = rgb_to_lab(*rgb2)
    dE = delta_e_cie2000(lab1, lab2)
    return dE
    

def check_couple_unit_filler(name: str, unit, fill) -> None:
    """Checks that the fill has a similar hue and sufficient lightness difference from the unit."""

    r1, g1, b1 = unit
    h1, s1, v1 = rgb_to_hsv(*unit)
    r2, g2, b2 = fill
    h2, s2, v2 = rgb_to_hsv(*fill)

    hue_difference = min(abs(h1 - h2), 360 - abs(h1 - h2))  # handles wrap-around 0°/360°
    lum1 = rgb_to_luminance(*unit)
    lum2 = rgb_to_luminance(*fill)
    gap_lum = lum2 - lum1

    ok_hue = hue_difference <= TOLERANCE_HUE
    ok_lum = gap_lum >= MIN_DIFFERENCE_LUM

    print(f"\t+++ Consistency unit/fill within faction {name} +++")
    print(f"\t\tUnit : H={h1:.2f}° S={s1:.2f}% V={v1:.2f}% LUM={lum1:.2f} (from rendered unit r={r1} g={g1} b={b1}")
    print(f"\t\tFiller  : H={h2:.2f}° S={s2:.2f}% V={v2:.2f}% LUM={lum2:.2f} (from rendered fill r={r2} g={g2} b={b2})")
    print(f"\t\tHue difference = {hue_difference:.2f}°  {'OK' if ok_hue else f'⚠️ TOO DIFFERENT should be <= {TOLERANCE_HUE:.2f}'}")
    print(f"\t\tLum difference = {gap_lum:.2f} pts  {'OK' if ok_lum else f'⚠️ TOO SMALL should be >= {MIN_DIFFERENCE_LUM:.2f}'}")
    print()


def check_pairs_factions(factions, threshold_separation) -> None:
    """Compares all factions by unit color to detect potential confusion."""

    worst_worst_gap = worst_gap = 1000
    first_key = next(iter(factions))
    for check in factions[first_key]:

        print(f"\t++++  Check conflicts between factions for [{check.replace('_', ' ')}] color ++++")
        print()

        conflicts = []
        for n1, n2 in itertools.combinations(factions, 2):
            rgb1 = factions[n1][check]
            rgb2 = factions[n2][check]
            gap = closeness(rgb1, rgb2)
            if gap < threshold_separation:
                conflicts.append((n1, n2, gap))
                worst_gap = min(worst_gap, gap)
                worst_worst_gap = min(worst_worst_gap, worst_gap)

        if not conflicts:
            print(f"\t\tNo conflict detected, all factions are separated enough!")
            print()
            continue

        for n1, n2, gap in sorted(conflicts, key=lambda x: x[2]):
            print(f"\t\t ⚠️  {n1} vs {n2} : gap of {gap:.1f} dE (should be >= {threshold_separation} dE)")
        print()

        print(f"\tWorst gap is {worst_gap:.4f} dE...")
        print()

    print(f"Worstworst gap is {worst_worst_gap:.4f} dE...")
    print()

def check_colors(sea_background_param: str, earth_background_param: str, threshold_separation: int, json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ check_colors """

    # ----------
    # sea background
    # ----------
    try:
        hex_val = sea_background_param.lstrip('#')
        if len(sea_background_param) != 7 or len(hex_val) != 6:
            raise ValueError
        sea_background_tuple = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        print("Incorrect background format for sea! Expected #RRGGBB")
        sys.exit(1)
    print(f"Using sea background as r={sea_background_tuple[0]} g={sea_background_tuple[1]} b={sea_background_tuple[2]}")

    # ----------
    # earth background
    # ----------
    try:
        hex_val = earth_background_param.lstrip('#')
        if len(earth_background_param) != 7 or len(hex_val) != 6:
            raise ValueError
        earth_background_tuple = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        print("Incorrect background format for earth! Expected #RRGGBB")
        sys.exit(1)
    print(f"Using earth background as r={earth_background_tuple[0]} g={earth_background_tuple[1]} b={earth_background_tuple[2]}")

    print()

    # ----------
    # parameters
    # ----------

    factions = {}
    for role, role_data in json_parameters_data['roles'].items():
        if int(role) == 0:
            continue

        # load colors
        role_name = role_data['name']
        unit_color_tuple = (role_data['red'][0], role_data['green'][0], role_data['blue'][0])
        if any(not 0 <= c <= 255 for c in unit_color_tuple):
            print(f"Incorrect rgb for {role_name}!")
            sys.exit(1)

        fill_color_tuple = (role_data['red'][1], role_data['green'][1], role_data['blue'][1])
        if any(not 0 <= c <= 255 for c in fill_color_tuple):
            print(f"Incorrect rgb for {role_name}!")
            sys.exit(1)

        unit_on_sea_color_tuple_rendered = alpha_compose(sea_background_tuple, unit_color_tuple)
        unit_on_earth_color_tuple_rendered = alpha_compose(earth_background_tuple, unit_color_tuple)
        fill_on_earth_color_tuple_rendered = alpha_compose(earth_background_tuple, fill_color_tuple)
        unit_on_fill_on_earth_color_tuple_rendered = alpha_compose(fill_on_earth_color_tuple_rendered, unit_color_tuple)

        factions[role_name] = {
            "unit_on_sea": unit_on_sea_color_tuple_rendered, 
            "unit_on_earth": unit_on_earth_color_tuple_rendered,
            "fill_on_earth": fill_on_earth_color_tuple_rendered, 
            "unit_on_fill_on_earth": unit_on_fill_on_earth_color_tuple_rendered
        }

    # check every pair unit/background individually
    print(f"---- Check consistency unit/fill within factions ----")
    print()
    for name, colors in factions.items():
        check_couple_unit_filler(name, colors["unit_on_fill_on_earth"], colors["fill_on_earth"])

    # check conflicts between factions (hue too close)
    print(f"---- Check factions separation ----")
    print()
    check_pairs_factions(factions, threshold_separation)


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    parser.add_argument('-s', '--sea_background', required=True, help='Provide a background color for sea from map file')
    parser.add_argument('-e', '--earth_background', required=True, help='Provide a background color for earth from map file')
    parser.add_argument('-t', '--threshold_separation', type=int, default=20, help='Provide a threshold for accepted separatoin between colors')
    args = parser.parse_args()

    #  load files at start
    parameters_file = args.parameters_file
    sea_background = args.sea_background
    earth_background = args.earth_background
    threshold_separation = args.threshold_separation

    if not os.path.exists(parameters_file):
        print(f"File '{parameters_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    # load parameters from json data file
    with open(parameters_file, "r", encoding='utf-8') as read_file:
        try:
            json_parameters_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {parameters_file} : {exception}")
            sys.exit(-1)

    earth_background = args.earth_background
    check_colors(sea_background, earth_background, threshold_separation, json_parameters_data)


if __name__ == "__main__":
    main()
