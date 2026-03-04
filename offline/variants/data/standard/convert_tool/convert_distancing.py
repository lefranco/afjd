#!/usr/bin/env python3

""" converter """

import typing
import json
import sys
import collections


UNIT_TYPE_TABLE = ['A', 'F']

ROLE_TABLE = ['ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'AUSTRIA', 'RUSSIA', 'TURKEY']

REGION_TABLE = ['ADR','AEG','ALB','ANK', 'APU', 'ARM','BAL','BAR','BEL','BER','BLA','BOH','BOT','BRE','BUD','BUL','BUR','CLY','CON','DEN','EAS','EDI',
                'ENG','FIN','GAL','GAS','GOL','GRE','HEL','HOL','ION','IRI','KIE','LON','LVN','LVP','MAR','MID','MOS','MUN','NAF','NAP','NAT','NRG',
                'NTH','NWY','PAR','PIC','PIE','POR','PRU','ROM','RUH','RUM','SER','SEV','SIL','SKA','SMY','SPA','STP','SWE','SYR','TRI','TUN','TUS',
                'TYN','TYR','UKR','VEN','VIE','WAL','WAR','WES','YOR']

ZONE_TABLE = REGION_TABLE + ["BULEC", "BULSC", "SPANC", "SPASC", "STPNC", "STPSC"]

def main():

    input_file = 'eloignement.DAT'
    with open(input_file, 'r') as file_ptr:

        distancing = list()
        for _ in UNIT_TYPE_TABLE:
            role_list = list()
            for _ in ROLE_TABLE:
                role_list.append(collections.defaultdict(list))
            distancing.append(role_list)

        for line in file_ptr.readlines():

            line = line.strip()
            if not line:
                continue
            if line.startswith(';'):
                continue
            tab = line.split(' ')
            assert len(tab) == 5

            name = tab[0].upper()
            assert name == 'ELOIGNEMENT'

            unit_type = tab[1].upper()
            assert unit_type in UNIT_TYPE_TABLE, f"Unknown unit type {unit_type}"
            unit_type_num = UNIT_TYPE_TABLE.index(unit_type)

            role = tab[2].upper()
            assert role in ROLE_TABLE, f"Unknown role {role}"
            role_num = ROLE_TABLE.index(role)

            zone = tab[3].upper()
            assert zone in ZONE_TABLE, f"Unknown zone {zone}"
            zone_num = ZONE_TABLE.index(zone) + 1

            distance = int(tab[4])

            distancing[unit_type_num][role_num][zone_num] = distance


    json_data = dict()
    json_data["distancing"] = distancing

    output_file = "result.json"
    output = json.dumps(json_data, indent=4, ensure_ascii=False)
    with open(output_file, 'w') as file_ptr:
        file_ptr.write(output)



if __name__ == "__main__":
    main()
