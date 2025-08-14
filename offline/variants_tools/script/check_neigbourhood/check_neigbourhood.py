#!/usr/bin/env python3


"""
Check neighbourhood (symetry)
"""

import typing
import collections
import json
import argparse


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--variant_file', required=True, help='variant file')
    args = parser.parse_args()

    with open(args.variant_file, "r", encoding='utf-8') as read_file:
        parameters_read = json.load(read_file)

    neighbouring = parameters_read['neighbouring']
    army_neighbouring = neighbouring[0]
    fleet_neighbouring = neighbouring[1]

    for neighbouring in army_neighbouring, fleet_neighbouring:
        for zone1, neighbours in neighbouring.items():
            for zone2 in neighbours:
                if str(zone2) not in neighbouring:
                    print(f"By {'army' if neighbouring == army_neighbouring else 'fleet'} {zone2} is in {zone1}' neighbours list but has no neighbour at all")
                    continue
                if int(zone1) not in neighbouring[str(zone2)]:
                    print(f"By {'army' if neighbouring == army_neighbouring else 'fleet'} {zone2} is in {zone1}' neighbours list but not the other way round")


if __name__ == '__main__':
    main()
