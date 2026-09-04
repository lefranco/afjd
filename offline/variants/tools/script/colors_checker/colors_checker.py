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
import colorsys


TRANSPARENCY_OWNER = 0.70

TOLERANCE_HUE = 10
MIN_DIFFERENCE_LUM = 25
THRESHOLD_SEPARATION = 25


def alpha_compose(background, item):
    """Compose item over background using alpha transparency."""
    return tuple(round(TRANSPARENCY_OWNER * item[i] + (1-TRANSPARENCY_OWNER) * background[i]) for i in range(3))


def rgb_to_hls(r, g, b):
    """Converts RGB (0-255) to HLS (H en degrees 0-360, L and S in %)"""

    r, g, b = r / 255.0, g / 255.0, b / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)  # beware : colorsys returns H,L,S
    return h * 360.0, l * 100.0, s * 100.0


def check_couple_unit_background(name: str, unit, fill) -> None:
    """Checks that the fill has a similar hue and sufficient lightness difference from the unit."""

    r1, g1, b1 = unit
    h1, l1, s1 = rgb_to_hls(*unit)
    r2, g2, b2 = fill
    h2, l2, s2 = rgb_to_hls(*fill)

    hue_difference = min(abs(h1 - h2), 360 - abs(h1 - h2))  # handles wrap-around 0°/360°
    gap_lum = l2 - l1

    ok_hue = hue_difference <= TOLERANCE_HUE
    ok_lum = gap_lum >= MIN_DIFFERENCE_LUM

    print(f"--- {name} ---")
    print(f"  Unit : H={h1:.2f}° L={l1:.2f}% S={s1:.2f}%  (from rendered unit r={r1} g={g1} b={b1}")
    print(f"  Filler  : H={h2:.2f}° L={l2:.2f}% S={s2:.2f}% (from rendered fill r={r2} g={g2} b={b2})")
    print(f"  Hue difference = {hue_difference:.2f}°  {'OK' if ok_hue else f'⚠️ TOO DIFFERENT should be <= {TOLERANCE_HUE:.2f}'}")
    print(f"  Lightness difference = {gap_lum:.2f} pts  {'OK' if ok_lum else f'⚠️ TOO SMALL should be >= {MIN_DIFFERENCE_LUM:.2f}'}")
    print()


def check_pairs_factions(factions) -> None:
    """Compares all factions by unit color to detect potential confusion."""

    for type_ in ("unit", "fill"):

        print(f"=== CHECK CONFLICTS BETWEEN FACTIONS ({type_} color) ===\n")

        conflicts = []
        for n1, n2 in itertools.combinations(factions, 2):
            h1, _, _ = rgb_to_hls(*factions[n1][type_])
            h2, _, _ = rgb_to_hls(*factions[n2][type_])
            gap = min(abs(h1 - h2), 360 - abs(h1 - h2))
            if gap < THRESHOLD_SEPARATION:
                conflicts.append((n1, n2, gap))

        if not conflicts:
            print(f"  No conflict detected, all factions are separated enough for {type_}")
            return

        for n1, n2, gap in sorted(conflicts, key=lambda x: x[2]):
            print(f"  ⚠️  {n1} vs {n2} : gap of {gap:.1f}° (should be >= {THRESHOLD_SEPARATION}°)")
        print()


def check_colors(background_param: str, json_parameters_data: typing.Dict[str, typing.Any]) -> None:
    """ check_colors """

    # ----------
    # background
    # ----------
    try:
        hex_val = background_param.lstrip('#')
        if len(background_param) != 7 or len(hex_val) != 6:
            raise ValueError
        background_tuple = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        print("Incorrect background format! Expected #RRGGBB")
        sys.exit(1)

    # ----------
    # parameters
    # ----------

    # load colors
    factions = {}
    for role, role_data in json_parameters_data['roles'].items():
        if int(role) == 0:
            continue

        role_name = role_data['name']
        unit_color_tuple = (role_data['red'][0], role_data['green'][0], role_data['blue'][0])
        if any(not 0 <= c <= 255 for c in unit_color_tuple):
            print(f"Incorrect rgb for {role_name}!")
            sys.exit(1)
        unit_color_tuple_rendered = alpha_compose(background_tuple, unit_color_tuple)

        fill_color_tuple = (role_data['red'][1], role_data['green'][1], role_data['blue'][1])
        if any(not 0 <= c <= 255 for c in fill_color_tuple):
            print(f"Incorrect rgb for {role_name}!")
            sys.exit(1)
        fill_color_tuple_rendered = alpha_compose(background_tuple, fill_color_tuple)

        factions[role_name] = {"unit": unit_color_tuple_rendered, "fill": fill_color_tuple_rendered}

    # check every pair unit/background individually
    for name, colors in factions.items():
        check_couple_unit_background(name, colors["unit"], colors["fill"])

    # check conflicts between factions (hue too close)
    check_pairs_factions(factions)


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    parser.add_argument('-b', '--background', required=True, help='Provide a background color from map file')
    args = parser.parse_args()

    #  load files at start
    parameters_file = args.parameters_file
    background = args.background

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

    check_colors(background, json_parameters_data)


if __name__ == "__main__":
    main()
