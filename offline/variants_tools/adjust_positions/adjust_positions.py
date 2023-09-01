#!/usr/bin/env python3


"""
Graphic tool to adjust positions
"""

import argparse
import typing
import os
import configparser
import sys
import json
import math

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext

# Important : name of file with version information
VERSION_FILE_NAME = "./version.ini"

VERSION_SECTION = "version"


TITLE = "Ajusting positions..."


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

SHIFT_X = 0
SHIFT_Y = -6
RADIUS = 7


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, map_file: str, parameters_file: str, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # data
        self.focused_zone_data: typing.Optional[typing.Dict[str, typing.Any]] = None
        self.legend_selected = True  # TODO change

        # actual creation of widgets
        self.create_widgets(self, map_file, parameters_file)

    def create_widgets(self, main_frame: tkinter.Frame, map_file: str, parameters_file: str) -> None:
        """ create all widgets for application """

        def about() -> None:
            tkinter.messagebox.showinfo("About", str(VERSION_INFORMATION))

        def redraw() -> None:

            # map
            self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.filename)

            # legends and units
            zones_data = self.json_parameters_data['zones']
            for zone_data in zones_data.values():

                fill = 'red' if zone_data is self.focused_zone_data and self.legend_selected else 'black'
                x_pos_read = zone_data['x_legend_pos']
                y_pos_read = zone_data['y_legend_pos']
                self.canvas.create_text(x_pos_read + SHIFT_X, y_pos_read + SHIFT_Y, text=zone_data['name'], fill=fill, font=FONT)

                fill = 'red' if zone_data is self.focused_zone_data and not self.legend_selected else 'black'
                x_pos_read = zone_data['x_pos']
                y_pos_read = zone_data['y_pos']
                self.canvas.create_oval(x_pos_read + SHIFT_X - RADIUS, y_pos_read + SHIFT_Y - RADIUS, x_pos_read + SHIFT_X + RADIUS, y_pos_read + SHIFT_Y + RADIUS, width=1, outline=fill)

        def arrow_callback(event: typing.Any) -> None:

            if self.focused_zone_data is None:
                return

            if self.legend_selected:

                if event.keysym == 'Right':
                    self.focused_zone_data['x_legend_pos'] += 1
                if event.keysym == 'Left':
                    self.focused_zone_data['x_legend_pos'] -= 1
                if event.keysym == 'Down':
                    self.focused_zone_data['y_legend_pos'] += 1
                if event.keysym == 'Up':
                    self.focused_zone_data['y_legend_pos'] -= 1

            else:

                if event.keysym == 'Right':
                    self.focused_zone_data['x_pos'] += 1
                if event.keysym == 'Left':
                    self.focused_zone_data['x_pos'] -= 1
                if event.keysym == 'Down':
                    self.focused_zone_data['y_pos'] += 1
                if event.keysym == 'Up':
                    self.focused_zone_data['y_pos'] -= 1

            # redraw
            redraw()

        def click_callback(event: typing.Any) -> None:
            x_mouse, y_mouse = event.x, event.y

            print("click_callback")

            min_dist = 100000.

            zones_data = self.json_parameters_data['zones']

            for zone_data in zones_data.values():

                zone_x, zone_y = zone_data['x_legend_pos'] + SHIFT_X, zone_data['y_legend_pos'] + SHIFT_Y
                dist = math.sqrt((zone_x - x_mouse) ** 2 + (zone_y - y_mouse) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    self.legend_selected = True
                    self.focused_zone_data = zone_data

                zone_x, zone_y = zone_data['x_pos'] + SHIFT_X, zone_data['y_pos'] + SHIFT_Y
                dist = math.sqrt((zone_x - x_mouse) ** 2 + (zone_y - y_mouse) ** 2)
                if dist < min_dist:
                    min_dist = dist
                    self.legend_selected = False
                    self.focused_zone_data = zone_data

            assert self.focused_zone_data is not None

            redraw()

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

        # load parameters from json data file
        with open(parameters_file, "r", encoding='utf-8') as read_file:
            try:
                self.json_parameters_data = json.load(read_file)
            except Exception as exception:  # pylint: disable=broad-except
                print(f"Failed to load {parameters_file} : {exception}")
                sys.exit(-1)

        # draw
        redraw()

        # clicking
        self.canvas.bind("<Button-1>", click_callback)

        # arrows
        self.master.bind("<Left>", arrow_callback)
        self.master.bind("<Right>", arrow_callback)
        self.master.bind("<Up>", arrow_callback)
        self.master.bind("<Down>", arrow_callback)

        # frame buttons and information
        # -----------

        frame_buttons_information = tkinter.Frame(main_frame)
        frame_buttons_information.grid(row=2, column=2, sticky='nw')

        self.mouse_pos_button = tkinter.Button(frame_buttons_information, text="save", command=save_callback)
        self.mouse_pos_button.grid(row=1, column=1, sticky='we')

    def menu_complete_quit(self) -> None:

        """ as it says """
        self.on_closing()

    def on_closing(self) -> None:
        """ User closed window """
        self.master.quit()


def main_loop(map_file: str, parameters_file: str) -> None:
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

    app = Application(map_file, parameters_file, master=root)
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
    parser.add_argument('-p', '--parameters_file', required=True, help='Load a parameters file at start')
    args = parser.parse_args()

    #  load files at start
    map_file = args.map_file
    parameters_file = args.parameters_file

    if not os.path.exists(map_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    if not os.path.exists(parameters_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    main_loop(map_file, parameters_file)

    print("The End")


if __name__ == "__main__":
    main()
