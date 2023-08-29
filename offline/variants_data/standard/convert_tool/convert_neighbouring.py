#!/usr/bin/env python3

""" converter """

import typing
import json
import sys
import collections

UNIT_TYPE_TABLE = ['A', 'F']


REGION_TABLE = ['ADR','AEG','ALB','ANK', 'APU', 'ARM','BAL','BAR','BEL','BER','BLA','BOH','BOT','BRE','BUD','BUL','BUR','CLY','CON','DEN','EAS','EDI',
                'ENG','FIN','GAL','GAS','GOL','GRE','HEL','HOL','ION','IRI','KIE','LON','LVN','LVP','MAR','MID','MOS','MUN','NAF','NAP','NAT','NRG',
                'NTH','NWY','PAR','PIC','PIE','POR','PRU','ROM','RUH','RUM','SER','SEV','SIL','SKA','SMY','SPA','STP','SWE','SYR','TRI','TUN','TUS',
                'TYN','TYR','UKR','VEN','VIE','WAL','WAR','WES','YOR']

ZONE_TABLE = REGION_TABLE + ["BULEC", "BULSC", "SPANC", "SPASC", "STPNC", "STPSC"]

def main():

    input_file = 'voisinage.DAT'
    with open(input_file, 'r') as file_ptr:

        neighbouring = list()
        for _ in UNIT_TYPE_TABLE:
            neighbouring.append(collections.defaultdict(list))

        for line in file_ptr.readlines():

            line = line.strip()
            if not line:
                continue
            if line.startswith(';'):
                continue
            tab = line.split(' ')
            assert len(tab) == 3

            name = tab[0].upper()
            assert name in [ 'ARMEEVOISIN', 'FLOTTEVOISIN']
            num0 = ['ARMEEVOISIN', 'FLOTTEVOISIN'].index(name)

            zone1 = tab[1].upper()
            assert zone1 in ZONE_TABLE, f"Unknown zone {zone1}"
            zone_num1 = ZONE_TABLE.index(zone1) + 1

            zone2 = tab[2].upper()
            assert zone2 in ZONE_TABLE, f"Unknown zone {zone2}"
            zone_num2 = ZONE_TABLE.index(zone2) + 1

            neighbouring[num0][zone_num1].append(zone_num2)


    json_data = dict()
    json_data["neighbouring"] = neighbouring

    output_file = "result.json"
    output = json.dumps(json_data, indent=4, ensure_ascii=False)
    with open(output_file, 'w') as file_ptr:
        file_ptr.write(output)



if __name__ == "__main__":
    main()
