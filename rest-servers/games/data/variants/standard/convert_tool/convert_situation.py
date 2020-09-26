#!/usr/bin/env python3

""" converter """

import typing
import json
import sys
import collections


UNIT_TYPE_TABLE = ['A', 'F']

ROLE_TABLE = ['ENGLAND', 'FRANCE', 'GERMANY', 'ITALY', 'AUSTRIA', 'RUSSIA', 'TURKEY']

CENTER_TABLE = [ 'ANK', 'BEL', 'BER', 'BRE', 'BUD', 'BUL', 'CON', 'DEN', 'EDI', 'GRE', 'HOL', 'KIE', 'LON', 'LVP', 'MAR', 'MOS', 'MUN', 'NAP', 'NWY',
                 'PAR', 'POR', 'ROM', 'RUM', 'SER', 'SEV', 'SMY', 'SPA', 'STP', 'SWE', 'TRI', 'TUN', 'VEN', 'VIE', 'WAR' ]

REGION_TABLE = ['ADR','AEG','ALB','ANK', 'APU', 'ARM','BAL','BAR','BEL','BER','BLA','BOH','BOT','BRE','BUD','BUL','BUR','CLY','CON','DEN','EAS','EDI',
                'ENG','FIN','GAL','GAS','GOL','GRE','HEL','HOL','ION','IRI','KIE','LON','LVN','LVP','MAR','MID','MOS','MUN','NAF','NAP','NAT','NRG',
                'NTH','NWY','PAR','PIC','PIE','POR','PRU','ROM','RUH','RUM','SER','SEV','SIL','SKA','SMY','SPA','STP','SWE','SYR','TRI','TUN','TUS',
                'TYN','TYR','UKR','VEN','VIE','WAL','WAR','WES','YOR']

ZONE_TABLE = REGION_TABLE + ["BULEC", "BULSC", "SPANC", "SPASC", "STPNC", "STPSC"]

SEASON_TABLE= ['PRINTEMPS', 'ETE', 'AUTOMNE', 'HIVER', 'BILAN']

def main():

    input_file = 'SITPRI01.DAT'
    with open(input_file, 'r') as file_ptr:

        situation  = dict()
        situation['ownerships'] = dict()
        situation['units'] = collections.defaultdict(list)

        for line in file_ptr.readlines():

            line = line.strip()
            if not line:
                continue
            if line.startswith(';'):
                continue
            tab = line.split(' ')

            name = tab[0]
            name = tab[0].upper()

            if name == 'SAISON':

                assert len(tab) == 3

                season = tab[1].upper()
                assert season in SEASON_TABLE, f"Unknown season {season}"
                season_num = SEASON_TABLE.index(season)

                year = int(tab[2])
                assert 1901 <= year <= 1999, f"Bad year {year}"

                advancement = (year - 1901) * 5 + season_num + 1
                situation['advancement'] = advancement

            elif name == 'SAISONMODIF':

                assert len(tab) == 3

                season_changed = tab[1].upper()
                assert season_changed in SEASON_TABLE, f"Unknown season {season_changed}"
                season_changed_num = SEASON_TABLE.index(season_changed)

                year_changed = int(tab[2])
                assert 1900 <= year_changed <= 1999, f"Bad year {year_changed}"

                last_change = (year_changed - 1901) * 5 + season_changed_num + 1
                situation['last_change'] = last_change

            elif name == 'POSSESSION':

                assert len(tab) == 3

                role = tab[1].upper()
                assert role in ROLE_TABLE, f"Unknown role {role}"
                role_num = ROLE_TABLE.index(role) + 1

                center = tab[2].upper()
                assert center in CENTER_TABLE, f"Unknown center {center}"
                center_num = CENTER_TABLE.index(center) + 1

                situation['ownerships'][center_num] = role_num

            elif name == 'UNITE':

                assert len(tab) == 4

                unit_type = tab[1].upper()
                assert unit_type in UNIT_TYPE_TABLE, f"Unknown unit type {unit_type}"
                unit_type_num = UNIT_TYPE_TABLE.index(unit_type) + 1

                role = tab[2].upper()
                assert role in ROLE_TABLE, f"Unknown role {role}"
                role_num = ROLE_TABLE.index(role) + 1

                zone = tab[3].upper()
                assert zone in ZONE_TABLE, f"Unknown zone {zone}"
                zone_num = ZONE_TABLE.index(zone) + 1

                situation['units'][role_num].append((unit_type_num, zone_num))

            else:
                assert False, f"What is this ? {name}"

    json_data = dict()
    json_data["situation"] = situation

    output_file = "result.json"
    output = json.dumps(json_data, indent=4)
    with open(output_file, 'w') as file_ptr:
        file_ptr.write(output)



if __name__ == "__main__":
    main()
