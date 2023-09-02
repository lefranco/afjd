#!/usr/bin/env python3

"""
Graphic tool to adjust positions
"""

# pylint: disable=multiple-statements

import argparse
import typing
import os
import configparser
import sys
import json
import math
import itertools
import enum

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext


# Important : name of file with version information
VERSION_FILE_NAME = "./version.ini"

VERSION_SECTION = "version"

TITLE = "Adjust legend and units : \nclick to select legend or unit, right-click to select both, arrows to move selected, ctrl right to move faster, ctrl left to move slower, save to save to file"


class VersionRecord(typing.NamedTuple):
    """ All version related information  """

    name: str
    date: str
    hour: str

    major: int
    minor: int
    revision: int

    comment: str

    def short(self) -> str:
        """ short version of version """
        return f"Version {self.major}.{self.minor} rev {self.revision} ({self.name})"

    def __str__(self) -> str:
        return f"{self.name} version {self.major}.{self.minor} rev {self.revision}\nDated {self.date} {self.hour}\n\nComment : {self.comment}"


def load_version_information() -> VersionRecord:
    """ For testing """

    # Where is the file ?
    version_file = VERSION_FILE_NAME
    assert os.path.isfile(version_file), f"Please create file {version_file}"

    config = configparser.ConfigParser()
    config.read(version_file)

    section = VERSION_SECTION

    paragraph_name = section.upper()
    data = config[paragraph_name]

    name = data['name']
    date = data['date']
    hour = data['hour']

    major = int(data['major'])
    minor = int(data['minor'])
    revision = int(data['revision'])

    comment = data['comment']

    version_information = VersionRecord(name=name, date=date, hour=hour, major=major, minor=minor, revision=revision, comment=comment)
    return version_information


VERSION_INFORMATION = load_version_information()

FONT = ('Arial 7')
SHIFT_LEGEND_X = 0
SHIFT_LEGEND_Y = -6


class Point:
    """ Point for easier compatbility with old C software (do not use a record here) """
    def __init__(self) -> None:
        self.x = 0  # pylint: disable=invalid-name
        self.y = 0  # pylint: disable=invalid-name


def stabbeur_army(x: int, y: int, canvas: typing.Any, outline: str) -> typing.List[typing.Any]:  # pylint: disable=invalid-name
    """ display an army the stabbeur way """

    items = []

    # socle
    p1 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
    p1[0].x = x - 15; p1[0].y = y + 6
    p1[1].x = x - 15; p1[1].y = y + 9
    p1[2].x = x + 6; p1[2].y = y + 9
    p1[3].x = x + 6; p1[3].y = y + 6

    flat_points = itertools.chain.from_iterable(map(lambda p: (p.x, p.y), p1))
    polygon = canvas.create_polygon(*flat_points, outline=outline, fill='')
    items.append(polygon)

    # coin
    p2 = [Point() for _ in range(3)]  # pylint: disable=invalid-name
    p2[0].x = x - 9; p2[0].y = y + 6
    p2[1].x = x - 4; p2[1].y = y + 6
    p2[2].x = x - 7; p2[2].y = y + 3

    flat_points = itertools.chain.from_iterable(map(lambda p: (p.x, p.y), p2))
    polygon = canvas.create_polygon(*flat_points, outline=outline, fill='')
    items.append(polygon)

    # canon
    p3 = [Point() for _ in range(4)]  # pylint: disable=invalid-name
    p3[0].x = x - 2; p3[0].y = y - 7
    p3[1].x = x + 3; p3[1].y = y - 14
    p3[2].x = x + 4; p3[2].y = y - 12
    p3[3].x = x; p3[3].y = y - 7

    flat_points = itertools.chain.from_iterable(map(lambda p: (p.x, p.y), p3))
    polygon = canvas.create_polygon(*flat_points, outline=outline, fill='')
    items.append(polygon)

    # cercle autour roue exterieure
    # simplified
    radius = 6
    oval = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=outline)
    items.append(oval)

    # roue interieure
    # simplified
    radius = 2
    oval = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, outline=outline)
    items.append(oval)

    # exterieur coin
    p4 = [Point() for _ in range(2)]  # pylint: disable=invalid-name
    p4[0].x = x - 7; p4[0].y = y + 3
    p4[1].x = x - 9; p4[1].y = y + 6

    flat_points = itertools.chain.from_iterable(map(lambda p: (p.x, p.y), p4))
    polygon = canvas.create_polygon(*flat_points, outline=outline, fill='')
    items.append(polygon)

    return items


def stabbeur_fleet(x: int, y: int, canvas: typing.Any, outline: str) -> typing.List[typing.Any]:  # pylint: disable=invalid-name
    """ display a fleet the stabbeur way """

    items = []

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

    flat_points = itertools.chain.from_iterable(map(lambda p: (p.x, p.y), p1))
    polygon = canvas.create_polygon(*flat_points, outline=outline, fill='')
    items.append(polygon)

    # hublots
    for i in range(5):
        radius = 1
        oval = canvas.create_oval(x - 8 + 5 * i + 1 - radius, y + 1 - radius, x - 8 + 5 * i + 1 + radius, y + 1 + radius, outline=outline)
        items.append(oval)

    return items


class SelectedEnum(enum.Enum):
    """ SelectedEnum """

    NOTHING = 1
    LEGEND = 2
    UNIT = 3
    BOTH = 4

    def legend_selected(self) -> bool:
        """ legend_selected """
        return self in [SelectedEnum.LEGEND, SelectedEnum.BOTH]

    def unit_selected(self) -> bool:
        """ unit_selected """
        return self in [SelectedEnum.UNIT, SelectedEnum.BOTH]


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, map_file: str, variant_file: str, parameters_file: str, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # load variant data from json data file
        with open(variant_file, "r", encoding='utf-8') as read_file:
            try:
                self.json_variant_data = json.load(read_file)
            except Exception as exception:  # pylint: disable=broad-except
                print(f"Failed to load {variant_file} : {exception}")
                sys.exit(-1)

        # load parameters from json data file
        with open(parameters_file, "r", encoding='utf-8') as read_file:
            try:
                self.json_parameters_data = json.load(read_file)
            except Exception as exception:  # pylint: disable=broad-except
                print(f"Failed to load {parameters_file} : {exception}")
                sys.exit(-1)

        # data
        self.focused_num_zone: typing.Optional[int] = None
        self.selected = SelectedEnum.NOTHING

        # types
        regions_data = self.json_variant_data['regions']
        self.zone2type = {i + 1: r for i, r in enumerate(regions_data)}
        coastal_zones_data = self.json_variant_data['coastal_zones']
        self.zone2type.update({len(regions_data) + i + 1: c[0] for i, c in enumerate(coastal_zones_data)})

        # zones
        self.zones_data = self.json_parameters_data['zones']

        # speed
        self.speed = 1

        # items table
        self.item_table: typing.Dict[int, typing.Any] = {}

        # actual creation of widgets
        self.create_widgets(self, map_file, parameters_file)

    def create_widgets(self, main_frame: tkinter.Frame, map_file: str, parameters_file: str) -> None:
        """ create all widgets for application """

        def about() -> None:
            tkinter.messagebox.showinfo("About", str(VERSION_INFORMATION))

        def erase(num_zone: int) -> None:

            for item in self.item_table[num_zone]:
                self.canvas.delete(item)

        def draw(num_zone: int, highlited: bool) -> None:

            self.item_table[num_zone] = []

            zone_data = self.zones_data[str(num_zone)]

            fill = 'red' if highlited and self.selected.legend_selected() else 'black'
            x_pos_read = zone_data['x_legend_pos']
            y_pos_read = zone_data['y_legend_pos']

            item = self.canvas.create_text(x_pos_read + SHIFT_LEGEND_X, y_pos_read + SHIFT_LEGEND_Y, text=zone_data['name'], fill=fill, font=FONT)
            self.item_table[num_zone].append(item)

            outline = 'red' if highlited and self.selected.unit_selected() else 'black'
            x_pos_read = zone_data['x_pos']
            y_pos_read = zone_data['y_pos']

            if self.zone2type[num_zone] in (1, 2):
                items = stabbeur_army(x_pos_read, y_pos_read, self.canvas, outline=outline)
                self.item_table[num_zone].extend(items)
            if self.zone2type[num_zone] in (1, 3):
                items = stabbeur_fleet(x_pos_read, y_pos_read, self.canvas, outline=outline)
                self.item_table[num_zone].extend(items)

        def arrow_callback(event: typing.Any) -> None:

            if self.focused_num_zone is None:
                return

            # erase
            erase(self.focused_num_zone)

            zone_data = self.zones_data[str(self.focused_num_zone)]

            if self.selected.legend_selected():
                if event.keysym == 'Right':
                    zone_data['x_legend_pos'] += self.speed
                if event.keysym == 'Left':
                    zone_data['x_legend_pos'] -= self.speed
                if event.keysym == 'Down':
                    zone_data['y_legend_pos'] += self.speed
                if event.keysym == 'Up':
                    zone_data['y_legend_pos'] -= self.speed

            if self.selected.unit_selected():
                if event.keysym == 'Right':
                    zone_data['x_pos'] += self.speed
                if event.keysym == 'Left':
                    zone_data['x_pos'] -= self.speed
                if event.keysym == 'Down':
                    zone_data['y_pos'] += self.speed
                if event.keysym == 'Up':
                    zone_data['y_pos'] -= self.speed

            # draw
            draw(self.focused_num_zone, True)

        def rclick_callback(event: typing.Any) -> None:
            x_mouse, y_mouse = event.x, event.y

            # update on screen
            if self.focused_num_zone is not None:
                erase(self.focused_num_zone)
                draw(self.focused_num_zone, False)

            min_dist = 100000.
            self.focused_num_zone = None

            for num_zone_str, zone_data in self.zones_data.items():

                zone_x_1, zone_y_1 = zone_data['x_legend_pos'] + SHIFT_LEGEND_X, zone_data['y_legend_pos'] + SHIFT_LEGEND_Y
                zone_x_2, zone_y_2 = zone_data['x_pos'], zone_data['y_pos']
                zone_x = (zone_x_1 + zone_x_2) / 2
                zone_y = (zone_y_1 + zone_y_2) / 2

                dist = math.sqrt((zone_x - x_mouse) ** 2 + (zone_y - y_mouse) ** 2)

                if dist < min_dist:
                    min_dist = dist
                    self.selected = SelectedEnum.BOTH
                    self.focused_num_zone = int(num_zone_str)

            assert self.focused_num_zone is not None

            # update on screen
            erase(self.focused_num_zone)
            draw(self.focused_num_zone, True)

        def click_callback(event: typing.Any) -> None:
            x_mouse, y_mouse = event.x, event.y

            # update on screen
            if self.focused_num_zone is not None:
                erase(self.focused_num_zone)
                draw(self.focused_num_zone, False)

            min_dist = 100000.
            self.focused_num_zone = None

            for num_zone_str, zone_data in self.zones_data.items():

                zone_x, zone_y = zone_data['x_legend_pos'] + SHIFT_LEGEND_X, zone_data['y_legend_pos'] + SHIFT_LEGEND_Y
                dist = math.sqrt((zone_x - x_mouse) ** 2 + (zone_y - y_mouse) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    self.selected = SelectedEnum.LEGEND
                    self.focused_num_zone = int(num_zone_str)

                zone_x, zone_y = zone_data['x_pos'], zone_data['y_pos']
                dist = math.sqrt((zone_x - x_mouse) ** 2 + (zone_y - y_mouse) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    self.selected = SelectedEnum.UNIT
                    self.focused_num_zone = int(num_zone_str)

            assert self.focused_num_zone is not None

            # update on screen
            erase(self.focused_num_zone)
            draw(self.focused_num_zone, True)

        def key_callback(event: typing.Any) -> None:

            if event.keysym == 'Control_L':
                if self.speed > 1:
                    self.speed -= 1

            if event.keysym == 'Control_R':
                self.speed += 1

        def check_callback() -> None:

            for zone_data in self.zones_data.values():

                zone_legend_x, zone_legend_y = zone_data['x_legend_pos'], zone_data['y_legend_pos']
                zone_x, zone_y = zone_data['x_pos'], zone_data['y_pos']

                if zone_legend_x != zone_x and zone_data['name']:
                    print(f"Warning x<> for {zone_data['name']}")

                if zone_legend_y + 14 != zone_y and zone_data['name']:
                    print(f"Warning y<>y+14 for {zone_data['name']}")

        def save_callback() -> None:

            output = json.dumps(self.json_parameters_data, indent=4, ensure_ascii=False)
            with open(parameters_file, "w", encoding='utf-8') as write_file:
                write_file.write(output)

        self.menu_bar = tkinter.Menu(main_frame)

        self.menu_file = tkinter.Menu(self.menu_bar, tearoff=0)
        self.menu_file.add_command(label="Exit", command=self.menu_complete_quit)
        self.menu_bar.add_cascade(label="File", menu=self.menu_file)

        self.menu_help = tkinter.Menu(self.menu_bar, tearoff=0)
        self.menu_help.add_command(label="About...", command=about)
        self.menu_bar.add_cascade(label="Help", menu=self.menu_help)

        self.master.config(menu=self.menu_bar)  # type: ignore

        # frame title
        # -----------

        frame_title = tkinter.Frame(main_frame)
        frame_title.grid(row=1, column=1, sticky='we')

        label = tkinter.Label(frame_title, text=TITLE)
        label.grid(row=1, column=1, sticky='we')

        # frame carto
        # -----------

        frame_carto = tkinter.Frame(main_frame)
        frame_carto.grid(row=2, column=1, sticky='we')

        self.map_file = map_file
        self.filename = tkinter.PhotoImage(file=self.map_file)

        self.canvas = tkinter.Canvas(frame_carto, width=self.filename.width(), height=self.filename.height())
        self.canvas.grid(row=1, column=1)

        # map
        self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.filename)

        # legends and units
        for num_zone_str in self.zones_data:
            num_zone = int(num_zone_str)
            draw(num_zone, False)

        # clicking
        self.canvas.bind("<Button-1>", click_callback)
        self.canvas.bind("<Button-3>", rclick_callback)

        # arrows
        self.master.bind("<Left>", arrow_callback)
        self.master.bind("<Right>", arrow_callback)
        self.master.bind("<Up>", arrow_callback)
        self.master.bind("<Down>", arrow_callback)

        # ctrl
        self.master.bind("<Key>", key_callback)

        # frame buttons and information
        # -----------

        frame_buttons_information = tkinter.Frame(main_frame)
        frame_buttons_information.grid(row=2, column=2, sticky='nw')

        self.check_button = tkinter.Button(frame_buttons_information, text="check", command=check_callback)
        self.check_button.grid(row=1, column=1, sticky='we')

        self.save_button = tkinter.Button(frame_buttons_information, text="save", command=save_callback)
        self.save_button.grid(row=2, column=1, sticky='we')

    def menu_complete_quit(self) -> None:

        """ as it says """
        self.on_closing()

    def on_closing(self) -> None:
        """ User closed window """
        self.master.quit()


def main_loop(map_file: str, variant_file: str, parameters_file: str) -> None:
    """ main_loop """

    root = tkinter.Tk()

    # put main window upper left hand side
    root.geometry("+0+0")
    root.resizable(False, False)

    print(f"Working now with map file '{map_file}' and parameter file '{parameters_file}'...")

    # use description of first register as overall title
    window_name = "Diplomania map item position adjustment tool"

    # create app
    root.title(window_name)

    app = Application(map_file, variant_file, parameters_file, master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # tkinter main loop
    app.mainloop()

    # delete app
    del app
    root.destroy()


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--map_file', required=True, help='Load a map file at start')
    parser.add_argument('-v', '--variant_file', required=True, help='Load variant json file')
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    args = parser.parse_args()

    #  load files at start
    map_file = args.map_file
    variant_file = args.variant_file
    parameters_file = args.parameters_file

    if not os.path.exists(map_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    if not os.path.exists(variant_file):
        print(f"File '{variant_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    if not os.path.exists(parameters_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    main_loop(map_file, variant_file, parameters_file)

    print("The End")


if __name__ == "__main__":
    main()
