#!/usr/bin/env python3


"""
File : make.py

"""

import typing
import collections
import json
import argparse


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_file', required=True, help='variant file')
    parser.add_argument('-o', '--output_file', required=True, help='region visibility file')
    args = parser.parse_args()

    with open(args.input_file, "r", encoding='utf-8') as read_file:
        parameters_read = json.load(read_file)

    regions = parameters_read['regions']
    regions_list = list(range(1, len(regions) + 1))

    neighbouring = parameters_read['neighbouring']
    army_neighbouring = neighbouring[0]
    fleet_neighbouring = neighbouring[1]

    # we build a zone2region dict

    zone2region = {r: r for r in regions_list}

    coastal_zones = parameters_read['coastal_zones']
    zone2region.update({len(regions_list) + i + 1: c[0] for i, c in enumerate(coastal_zones)})

    # we build a visibility dict

    visibility: typing.Dict[int, typing.Set[int]] = collections.defaultdict(set)

    for neighbouring in army_neighbouring, fleet_neighbouring:
        for zone1, neighbours in neighbouring.items():
            region1 = zone2region[int(zone1)]
            for zone2 in neighbours:
                region2 = zone2region[int(zone2)]
                visibility[region1].add(region2)

    # little check : symetry
    for region1, regions_set in visibility.items():
        assert all(region1 in visibility[r] for r in regions_set), "Symetry issue in visibility table"

    # polish the visibility table before jsonifying it
    visibility_table = {str(k): sorted(list(v)) for k, v in sorted(visibility.items())}

    # need the center -> region table
    centers = parameters_read['centers']
    center2region = {str(i + 1): r for i, r in enumerate(centers)}

    # store things
    data_json = {
        'center2region': center2region,
        'zone2region': zone2region,
        'visibility_table': visibility_table,
    }

    output = json.dumps(data_json, indent=4)
    with open(args.output_file, "w", encoding='utf-8') as write_file:
        write_file.write(output)


if __name__ == '__main__':
    main()
