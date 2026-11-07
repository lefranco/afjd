#!/usr/bin/env python3


"""Check colors used in displaying
"""

import argparse
import colorsys
import itertools
import json
import math
import os
import random
import sys
import typing

# pylint: disable=invalid-name

# uncomment line below in windows
# sys.stdout.reconfigure(encoding='utf-8')

MAXINT = 1000000
TRANSPARENCY_OWNER = 0.80

TOLERANCE_HUE = 10
MIN_DIFFERENCE_LUM = 20

# parameter 'threshold_separation' :
# dE < 1 : Imperceptible to the naked eye
# dE < 5 : Very close, barely distinguishable
# dE < 10 : Distinguishable but close
# else OK, clearly distinct


def alpha_compose(background: tuple[int, int, int], item: tuple[int, int, int]) -> tuple[int, int, int]:
    """Compose item over background using alpha transparency."""
    res: tuple[int, int, int] = tuple(round(TRANSPARENCY_OWNER * item[i] + (1 - TRANSPARENCY_OWNER) * background[i]) for i in range(3))  # type: ignore[assignment]
    return res


def rgb_to_luminance(r: int, g: int, b: int) -> float:
    """Relative luminance approximation, 0-100%."""
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0 * 100.0


def rgb_to_hsv(r_i: int, g_i: int, b_i: int) -> tuple[float, float, float]:
    """Converts RGB (0-255) to HSV (H en degrees 0-360, S and V in %)"""
    r, g, b = r_i / 255.0, g_i / 255.0, b_i / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)  # beware : colorsys returns H,L,S
    return h * 360.0, s * 100.0, v * 100.0


def rgb_to_lab(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Converts RGB (0-255) to space CIELAB, using XYZ."""

    def linearize(c: float) -> float:
        c = c / 255.0
        return math.pow(((c + 0.055) / 1.055), 2.4) if c > 0.04045 else c / 12.92

    r_lin, g_lin, b_lin = linearize(r), linearize(g), linearize(b)

    # RGB lineair -> XYZ (matrice sRGB standard, illuminating D65)
    x = r_lin * 0.4124 + g_lin * 0.3576 + b_lin * 0.1805
    y = r_lin * 0.2126 + g_lin * 0.7152 + b_lin * 0.0722
    z = r_lin * 0.0193 + g_lin * 0.1192 + b_lin * 0.9505

    x, y, z = x / 0.95047, y / 1.00000, z / 1.08883

    def f(t: float) -> float:
        return math.pow(t, (1. / 3.)) if t > 0.008856 else (7.787 * t) + (16. / 116.)

    fx, fy, fz = f(x), f(y), f(z)
    L = (116 * fy) - 16
    a = 500 * (fx - fy)
    b_lab = 200 * (fy - fz)

    return L, a, b_lab


def delta_e_cie2000(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> float:
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

    T = (1 - 0.17 * math.cos(math.radians(hp_avg - 30)) + 0.24 * math.cos(math.radians(2 * hp_avg)) + 0.32 * math.cos(math.radians(3 * hp_avg + 6)) - 0.20 * math.cos(math.radians(4 * hp_avg - 63)))

    d_ro = 30 * math.exp(-(((hp_avg - 275) / 25) ** 2))
    RC = 2 * math.sqrt(Cp_avg**7 / (Cp_avg**7 + 25**7))
    SL = 1 + ((0.015 * (Lp_avg - 50)**2) / math.sqrt(20 + (Lp_avg - 50)**2))
    SC = 1 + 0.045 * Cp_avg
    SH = 1 + 0.015 * Cp_avg * T
    RT = -math.sin(math.radians(2 * d_ro)) * RC

    dE = math.sqrt((dLp / SL) ** 2 + (dCp / SC) ** 2 + (dHp / SH) ** 2 + RT * (dCp / SC) * (dHp / SH))
    return dE


def closeness(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    """The ultimate comparer between two RGB... so simple !"""
    lab1 = rgb_to_lab(*rgb1)
    lab2 = rgb_to_lab(*rgb2)
    dE = delta_e_cie2000(lab1, lab2)
    return dE


def check_couple_unit_filler(name: str, unit: tuple[int, int, int], fill: tuple[int, int, int], silent: bool) -> float:
    """Checks that the fill has a similar hue and sufficient lightness difference from the unit."""
    r1, g1, b1 = unit
    h1, s1, v1 = rgb_to_hsv(*unit)
    r2, g2, b2 = fill
    h2, s2, v2 = rgb_to_hsv(*fill)
    hue_difference = min(abs(h1 - h2), 360. - abs(h1 - h2))  # handles wrap-around 0°/360°

    lum1 = rgb_to_luminance(*unit)
    lum2 = rgb_to_luminance(*fill)
    gap_lum = min(abs(lum1 - lum2), 100. - abs(lum1 - lum2))  # handles wrap-around 0/100

    ok_hue = hue_difference <= TOLERANCE_HUE
    ok_lum = gap_lum >= MIN_DIFFERENCE_LUM

    if not silent:
        print(f"\t+++ Consistency unit/fill within faction {name} +++")
        print(f"\t\tUnit : H={h1:.2f}° S={s1:.2f}% V={v1:.2f}% LUM={lum1:.2f} (from rendered unit r={r1} g={g1} b={b1}")
        print(f"\t\tFiller  : H={h2:.2f}° S={s2:.2f}% V={v2:.2f}% LUM={lum2:.2f} (from rendered fill r={r2} g={g2} b={b2})")
        print(f"\t\tHue difference = {hue_difference:.2f}°  {'OK' if ok_hue else f'⚠️ TOO DIFFERENT should be <= {TOLERANCE_HUE:.2f}'}")
        print(f"\t\tLum difference = {gap_lum:.2f} pts  {'OK' if ok_lum else f'⚠️ TOO SMALL should be >= {MIN_DIFFERENCE_LUM:.2f}'}")
        print()

    # the bigger the better
    return hue_difference


def check_pairs_factions(factions: dict[str, dict[str, tuple[tuple[int, int, int], str]]], threshold_separation: int) -> None:
    """Compares all factions by unit color to detect potential confusion."""
    worst = float(MAXINT)
    worst_data = (float(MAXINT), "", "")
    first_key = next(iter(factions))
    for check in factions[first_key]:

        print(f"\t++++  Check conflicts between factions for [{check.replace('_', ' ')}] color ++++")
        print()

        conflicts = []
        for n1, n2 in itertools.combinations(factions, 2):
            rgb1 = factions[n1][check][0]
            rgb2 = factions[n2][check][0]
            gap = closeness(rgb1, rgb2)
            if check != "fill_on_earth":
                worst = min(worst, gap)
            if gap < threshold_separation:
                conflicts.append((n1, n2, gap))

        if not conflicts:
            print("\t\tNo conflict detected, all factions are separated enough!")
            print()
            continue

        for n1, n2, gap in sorted(conflicts, key=lambda x: x[2]):
            icon = factions[first_key][check][1]
            mess = f"\t\t {icon} {n1} vs {n2} : gap of {gap:.1f} dE (should be >= {threshold_separation} dE)"
            if icon == '⛔️':
                if gap < worst_data[0]:
                    worst_data = (gap, check, mess)
            print(mess)
        print()

    if worst_data[0] != MAXINT:
        print(f"Worst gap is {worst_data[0]:.4f} dE when checking '{worst_data[1].replace('_', ' ')}' for:")
        print(worst_data[2])
    print()
    print(f"Worst unit separation is {worst:.2f}")
    print()


def display_factions_hue_recap(factions: dict[str, dict[str, tuple[tuple[int, int, int], str]]]) -> None:
    """Recap on hue circle"""
    worst = float(MAXINT)
    target = 0.9 * (360. / len(factions))

    hue_table = {name: rgb_to_hsv(*colors["unit_on_fill_on_earth"][0])[0] for name, colors in factions.items()}
    stat = dict(sorted(hue_table.items(), key=lambda i: i[1]))
    prev_h = list(stat.values())[-1] - 360.
    for n, h in stat.items():
        delta = h - prev_h
        print(f"\t{h:0.2f} {n} {delta=:0.2f}", end='')
        if delta < target:
            print(f" ⚠️ (<{target=})", end='')
        worst = min(worst, delta)
        print()
        prev_h = h

    print()
    print(f"Worst hue value separation is {worst:.2f}")
    print()


def sort_factions_on_hue(factions: dict[str, dict[str, tuple[tuple[int, int, int], str]]]) -> list[str]:
    """sort_factions_on_hue"""
    hue_table = {name: rgb_to_hsv(*colors["unit_on_fill_on_earth"][0])[0] for name, colors in factions.items()}
    stat = dict(sorted(hue_table.items(), key=lambda i: i[1]))
    return list(stat.keys())


def climb_heuristic(factions: dict[str, dict[str, tuple[tuple[int, int, int], str]]]) -> tuple[float, float, list[str]]:
    """Heuristic for climbing"""

    # ----------
    # closest gap must be as big as possible
    # ----------
    pair_heuris = float(MAXINT)
    for n1, n2 in itertools.combinations(factions, 2):
        for check in ("unit_on_sea", "unit_on_earth", "unit_on_fill_on_earth"):
            rgb1 = factions[n1][check][0]
            rgb2 = factions[n2][check][0]
            gap = closeness(rgb1, rgb2)
            pair_heuris = min(gap, pair_heuris)

    # ----------
    # hue_faction_consistency_heuris must be as small as possible
    # lum_faction_diff_heuris must be as big as possible
    # ----------
    hue_faction_consistency_heuris = 0.
    for name, colors in factions.items():
        hue_faction_consistency = check_couple_unit_filler(name, colors["unit_on_fill_on_earth"][0], colors["fill_on_earth"][0], silent=True)
        hue_faction_consistency_heuris = max(hue_faction_consistency_heuris, hue_faction_consistency)

    # also this one
    sorted_factions = sort_factions_on_hue(factions)

    return pair_heuris, hue_faction_consistency_heuris, sorted_factions


def check_colors(sea_background_param: str, earth_background_param: str, threshold_separation: int, json_parameters_data: dict[str, typing.Any], silent: bool) -> tuple[float, float, list[str]]:
    """check_colors"""
    # ----------
    # sea background
    # ----------
    try:
        hex_val = sea_background_param.lstrip('#')
        if len(sea_background_param) != 7 or len(hex_val) != 6:
            raise ValueError
        sea_background_tuple: tuple[int, int, int] = tuple(int(hex_val[i: i + 2], 16) for i in (0, 2, 4))  # type: ignore[assignment]
    except ValueError:
        print("Incorrect background format for sea! Expected #RRGGBB")
        sys.exit(1)
    if not silent:
        print(f"Using sea background as r={sea_background_tuple[0]} g={sea_background_tuple[1]} b={sea_background_tuple[2]}")

    # ----------
    # earth background
    # ----------
    try:
        hex_val = earth_background_param.lstrip('#')
        if len(earth_background_param) != 7 or len(hex_val) != 6:
            raise ValueError
        earth_background_tuple: tuple[int, int, int] = tuple(int(hex_val[i: i + 2], 16) for i in (0, 2, 4))  # type: ignore[assignment]
    except ValueError:
        print("Incorrect background format for earth! Expected #RRGGBB")
        sys.exit(1)
    if not silent:
        print(f"Using earth background as r={earth_background_tuple[0]} g={earth_background_tuple[1]} b={earth_background_tuple[2]}")

    if not silent:
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
            "fill_on_earth": (fill_on_earth_color_tuple_rendered, '⚠️'),
            "unit_on_sea": (unit_on_sea_color_tuple_rendered, '⛔️'),
            "unit_on_earth": (unit_on_earth_color_tuple_rendered, '⛔️'),
            "unit_on_fill_on_earth": (unit_on_fill_on_earth_color_tuple_rendered, '⛔️'),
        }

    # check every pair unit/background individually
    if not silent:
        print("---- Check consistency unit/fill within factions ----")
        print()
        for name, colors in factions.items():
            check_couple_unit_filler(name, colors["unit_on_fill_on_earth"][0], colors["fill_on_earth"][0], silent=False)

    # check conflicts between factions (hue too close)
    if not silent:
        print("---- Check factions separation ----")
        print()
        check_pairs_factions(factions, threshold_separation)

    # display factions recap hues
    if not silent:
        print("---- Display factions recap on hues ----")
        print()
        display_factions_hue_recap(factions)

    # for climb
    return climb_heuristic(factions)


FAILED_COUNTER_LIMIT = 20000
MAX_ABS_CHANGE = 15
NUM_CHANGED = 2

START_PAIR_HEURIS_MIN = 15
MAX_START_ATTEMPTS = 150000


def hill_climber(restart: bool, fill_step: bool, sea_background: str, earth_background: str, threshold_separation: int, json_parameters_data: dict[str, typing.Any]) -> None:
    """hill_climber"""
    sorted_start_factions: list[str] = []
    pair_heuris: float | None = None
    hue_faction_consistency_heuris: float | None = None

    try:

        if restart:

            print("Restarting ! Hoho !")

            # memorize start faction order by hue
            _, _, sorted_start_factions = check_colors(sea_background, earth_background, threshold_separation, json_parameters_data, silent=True)

            # we restart everything so make a random initial situation
            restart_attempts = 0
            while True:
                for role in [r for r in json_parameters_data['roles'] if int(r)]:
                    for rgb in ('red', 'green', 'blue'):
                        json_parameters_data['roles'][role][rgb][0] = random.choice(range(256))
                        json_parameters_data['roles'][role][rgb][1] = random.choice(range(256))

                pair_heuris, hue_faction_consistency_heuris, _ = check_colors(sea_background, earth_background, threshold_separation, json_parameters_data, silent=True)

                # need at least some quality
                if pair_heuris > START_PAIR_HEURIS_MIN:
                    break

                # and give up if too long
                restart_attempts += 1
                assert restart_attempts < MAX_START_ATTEMPTS, "Damn it, could not restart!"

        failed_changes_counter = 0
        pair_heuris = None

        # fill_step : we change fill values instead of unit values
        if fill_step:
            unit_or_fill = 1
            print("Playing with fill color...")
        else:
            unit_or_fill = 0
            print("Playing with unit color...")

        while True:

            # if never done : get initial values
            if pair_heuris is None:
                pair_heuris, hue_faction_consistency_heuris, _ = check_colors(sea_background, earth_background, threshold_separation, json_parameters_data, silent=True)
                # show for user
                print(f"I{pair_heuris=:05.2f} {hue_faction_consistency_heuris=:06.2f}", file=sys.stderr)

            # determine two random change
            role_table: dict[int, str] = {}
            rgb_table: dict[int, str] = {}
            delta_table: dict[int, int] = {}
            for num in range(NUM_CHANGED):
                role_table[num] = random.choice([r for r in json_parameters_data['roles'] if int(r) and r not in role_table.values()])
                rgb_table[num] = random.choice(['red', 'green', 'blue'])
                delta_sign = random.choice([-1, +1])
                delta_abs = random.choice(range(1, MAX_ABS_CHANGE + 1))
                delta_table[num] = delta_sign * delta_abs
                json_parameters_data['roles'][role_table[num]][rgb_table[num]][unit_or_fill] += delta_table[num]

            # check random change is correct, if not reject
            rejected = False
            for num in range(NUM_CHANGED):
                if not 0 <= json_parameters_data['roles'][role_table[num]][rgb_table[num]][unit_or_fill] <= 255:
                    rejected = True
                    break
            if rejected:
                for num in range(NUM_CHANGED):
                    json_parameters_data['roles'][role_table[num]][rgb_table[num]][unit_or_fill] -= delta_table[num]
                continue

            # evaluate with change
            new_pair_heuris, new_hue_faction_consistency_heuris, _ = check_colors(sea_background, earth_background, threshold_separation, json_parameters_data, silent=True)

            # calculate if rejected
            # need to improve pair or hue (hue ignored for the moment)
            regression = new_pair_heuris < pair_heuris
            improvement = new_pair_heuris > pair_heuris

            if fill_step:
                assert new_hue_faction_consistency_heuris is not None
                # need to improve consistency without breaking the rest
                regression |= new_hue_faction_consistency_heuris > hue_faction_consistency_heuris
                # regression |= new_lum_faction_diff_heuris < lum_faction_diff_heuris
                improvement |= new_hue_faction_consistency_heuris < hue_faction_consistency_heuris
                # improvement |= new_lum_faction_diff_heuris > lum_faction_diff_heuris

            # reject if regression no improvement
            if regression or not improvement:
                for num in range(NUM_CHANGED):
                    json_parameters_data['roles'][role_table[num]][rgb_table[num]][unit_or_fill] -= delta_table[num]
                failed_changes_counter += 1
                if failed_changes_counter > FAILED_COUNTER_LIMIT:
                    print()
                    print("LOCKED !", file=sys.stderr)
                    raise KeyboardInterrupt
                continue

            # officialize change
            pair_heuris = new_pair_heuris
            hue_faction_consistency_heuris = new_hue_faction_consistency_heuris

            # show for user
            print(f"^{pair_heuris=:05.2f} {hue_faction_consistency_heuris=:06.2f}", end='\r', file=sys.stderr)

            failed_changes_counter = 0

    except KeyboardInterrupt:

        print(file=sys.stderr)
        _, _, sorted_factions = check_colors(sea_background, earth_background, threshold_separation, json_parameters_data, silent=True)

        # reinstall order of factions per hue
        if restart:
            role_copy = json_parameters_data['roles'].copy()
            role2strrank = {v['name']: k for k, v in json_parameters_data['roles'].items()}
            for name1, name2 in zip(sorted_start_factions, sorted_factions):
                json_parameters_data['roles'][role2strrank[name1]] = role_copy[role2strrank[name2]]
                json_parameters_data['roles'][role2strrank[name1]]['name'] = name1
                #  print(f"{name2} -> {name1}")

        # output optimized situation
        parameters_file_opt = f"optimized_{pair_heuris:05.2f}_{hue_faction_consistency_heuris:06.2f}__json".replace('.', '').replace('__', '.')
        with open(parameters_file_opt, "w", encoding='utf-8') as write_file:
            try:
                json.dump(json_parameters_data, write_file, ensure_ascii=False, indent=4)
            except Exception as exception:  # pylint: disable=broad-except
                print(f"Failed to save {parameters_file_opt} : {exception}")
                sys.exit(-1)
        print(f"Written file {parameters_file_opt}")
        sys.exit(0)


def main() -> None:
    """Main"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    parser.add_argument('-e', '--earth_background', required=True, help='Provide a background color for earth from map file')
    parser.add_argument('-s', '--sea_background', help='Provide a background color for sea from map file')
    parser.add_argument('-t', '--threshold_separation', type=int, default=20, help='Provide a threshold for accepted separation between colors')
    parser.add_argument('-c', '--climb', action='store_true', help='Try to improve colors with a hill climb algo')
    parser.add_argument('-r', '--restart', action='store_true', help='Restart from scratch when hill climbing')
    parser.add_argument('-f', '--fill_step', action='store_true', help='Optimize fill values instead of unit value when hill climbing')
    args = parser.parse_args()

    # load files at start
    parameters_file = args.parameters_file
    earth_background = args.earth_background
    if not args.sea_background:
        print("Taking for sea same background as for earth...")
        sea_background = earth_background
    else:
        sea_background = args.sea_background
    threshold_separation = args.threshold_separation

    # complain if no parameter file
    if not os.path.exists(parameters_file):
        print(f"File '{parameters_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    # load parameters from json data file
    with open(parameters_file, encoding='utf-8') as read_file:
        try:
            json_parameters_data = json.load(read_file)
        except Exception as exception:  # pylint: disable=broad-except
            print(f"Failed to load {parameters_file} : {exception}")
            sys.exit(-1)

    if args.climb:
        hill_climber(args.restart, args.fill_step, sea_background, earth_background, threshold_separation, json_parameters_data)
        sys.exit(0)

    _ = check_colors(sea_background, earth_background, threshold_separation, json_parameters_data, silent=False)


if __name__ == "__main__":
    main()
