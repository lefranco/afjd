#!/usr/bin/env python3


"""
Extracts positions, polygons, polygon middle from map
Uses opencv version is 4.6.0
"""

import argparse
import typing
import os
import configparser
import sys
import itertools

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext

import cv2  # type: ignore

import geometry
import polylabel

# Important : name of file with version information
VERSION_FILE_NAME = "./version.ini"

VERSION_SECTION = "version"

INFO_HEIGHT1 = 3
INFO_WIDTH1 = 30

INFO_HEIGHT2 = 15
INFO_WIDTH2 = 30

TITLE = "Détection de position de polygone..."


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


class MyText(tkinter.Text):
    """ MyText """

    def __init__(self, root: typing.Any, *args: typing.Any, **kwargs: typing.Any) -> None:
        tkinter.Text.__init__(self, *args, **kwargs)
        self.config(state=tkinter.DISABLED)
        self._root = root
        self._content = ""

    def display(self, content: str) -> None:
        """ display """

        self._content = content

        self.config(state=tkinter.NORMAL)
        self.delete(1.0, tkinter.END)
        self.insert(tkinter.END, content)
        #  self.see("end")
        self.config(state=tkinter.DISABLED)

    def clipboard(self) -> None:
        """ clipboard """

        self._root.clipboard_clear()
        self._root.clipboard_append(self._content)


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, map_file: str, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # actual creation of widgets
        self.create_widgets(self, map_file)

    def create_widgets(self, main_frame: tkinter.Frame, map_file: str) -> None:
        """ create all widgets for application """

        def about() -> None:
            tkinter.messagebox.showinfo("About", str(VERSION_INFORMATION))

        def click_callback(event: typing.Any) -> None:

            x_mouse, y_mouse = event.x, event.y

            information1 = f'"x_pos": {x_mouse},\n"y_pos": {y_mouse}'
            self.mouse_pos.display(information1)

            information2 = ""

            # erase
            self.polygon.display(information2)

            # create image map
            self.image_map = tkinter.PhotoImage(file=map_file)  # pylint: disable=attribute-defined-outside-init

            # canvas
            self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.image_map)

            for x_pos, y_pos, w_val, h_val in CONTOUR_TABLE:

                # must be inside box
                if not x_pos <= x_mouse <= x_pos + w_val and y_pos <= y_mouse <= y_pos + h_val:
                    continue

                # get poly created
                poly = CONTOUR_TABLE[(x_pos, y_pos, w_val, h_val)]

                # must be inside poly
                designated_pos = geometry.PositionRecord(x_pos=x_mouse, y_pos=y_mouse)
                area_poly = geometry.Polygon([geometry.PositionRecord(*t) for t in poly])  # type: ignore
                if not area_poly.is_inside_me(designated_pos):
                    continue

                # display on map
                flat_points = itertools.chain.from_iterable(poly)  # type: ignore
                self.canvas.create_polygon(*flat_points, fill='red', outline='blue', stipple='gray25')

                # display as text
                information2 = str(poly)
                self.polygon.display(information2)

                # middle
                polygons = [poly]
                polylabel_x_f, polylabel_y_f = polylabel.polylabel(polygons, precision=0.1)  # type: ignore
                polylabel_x, polylabel_y = round(polylabel_x_f), round(polylabel_y_f)
                self.canvas.create_line(polylabel_x + 5, polylabel_y, polylabel_x - 5, polylabel_y, fill='blue')
                self.canvas.create_line(polylabel_x, polylabel_y + 5, polylabel_x, polylabel_y - 5, fill='blue')
                information2 = f'"x_pos": {polylabel_x},\n"y_pos": {y_mouse}'
                self.middle_pos.display(information2)

                # only first
                break

            else:
                information2 = "Failed!"
                self.polygon.display(information2)

        def copy_position_callback() -> None:
            self.mouse_pos.clipboard()

        def copy_area_callback() -> None:
            self.polygon.clipboard()

        def copy_position2_callback() -> None:
            self.middle_pos.clipboard()

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

        # clicking
        self.canvas.bind("<Button-1>", click_callback)
        self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.filename)

        # frame buttons and information
        # -----------

        frame_buttons_information = tkinter.Frame(main_frame)
        frame_buttons_information.grid(row=2, column=2, sticky='nw')

        self.mouse_pos_label = tkinter.Label(frame_buttons_information, text="Position of click :")
        self.mouse_pos_label.grid(row=1, column=1, sticky='we')

        self.mouse_pos = MyText(self.master, frame_buttons_information, height=INFO_HEIGHT1, width=INFO_WIDTH1)
        self.mouse_pos.grid(row=2, column=1, sticky='we')

        self.mouse_pos_button = tkinter.Button(frame_buttons_information, text="copy click position", command=copy_position_callback)
        self.mouse_pos_button.grid(row=3, column=1, sticky='we')

        self.polygon_label = tkinter.Label(frame_buttons_information, text="Polygon around click :")
        self.polygon_label.grid(row=4, column=1, sticky='we')

        self.polygon = MyText(self.master, frame_buttons_information, height=INFO_HEIGHT2, width=INFO_WIDTH2)
        self.polygon.grid(row=5, column=1, sticky='we')

        self.polygon_button = tkinter.Button(frame_buttons_information, text="copy area", command=copy_area_callback)
        self.polygon_button.grid(row=6, column=1, sticky='we')

        self.middle_pos_label = tkinter.Label(frame_buttons_information, text="Position of middle of polygon :")
        self.middle_pos_label.grid(row=7, column=1, sticky='we')

        self.middle_pos = MyText(self.master, frame_buttons_information, height=INFO_HEIGHT1, width=INFO_WIDTH1)
        self.middle_pos.grid(row=8, column=1, sticky='we')

        self.middle_pos_button = tkinter.Button(frame_buttons_information, text="copy middle position", command=copy_position2_callback)
        self.middle_pos_button.grid(row=9, column=1, sticky='we')

    def menu_complete_quit(self) -> None:
        """ as it says """
        self.on_closing()

    def on_closing(self) -> None:
        """ User closed window """
        self.master.quit()


def study_image(map_file: str, debug: bool) -> None:
    """ study_image """

    global CONTOUR_TABLE

    CONTOUR_TABLE = {}

    image = cv2.imread(map_file)  # pylint: disable=c-extension-no-member

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # pylint: disable=c-extension-no-member

    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)  # pylint: disable=c-extension-no-member

    # Filter using contour h
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # pylint: disable=c-extension-no-member

    for current_contour in contours:

        x_pos, y_pos, w_val, h_val = cv2.boundingRect(current_contour)  # pylint: disable=c-extension-no-member

        current_contour2 = cv2.approxPolyDP(current_contour, 1, True)  # pylint: disable=c-extension-no-member

        CONTOUR_TABLE[(x_pos, y_pos, w_val, h_val)] = list(map(lambda p: p[0], current_contour2.tolist()))  # type: ignore

    # sort to put smaller first bounding rect first
    CONTOUR_TABLE = {k: CONTOUR_TABLE[k] for k in sorted(CONTOUR_TABLE, key=lambda b: b[2] * b[3])}

    if debug:
        print(CONTOUR_TABLE)
        cv2.imshow('image', thresh)  # pylint: disable=c-extension-no-member
        cv2.waitKey()  # pylint: disable=c-extension-no-member
        sys.exit()


CONTOUR_TABLE: typing.Dict[typing.Tuple[int, int, int, int], typing.List[int]] = {}


def main_loop(debug: bool, map_file: str) -> None:
    """ main_loop """

    root = tkinter.Tk()

    # put main window upper left hand side
    root.geometry("+0+0")
    root.resizable(False, False)

    print(f"Working now with map file '{map_file}'...")

    # use description of first register as overall title
    window_name = "Diplomania map zone extracting tool"

    # create app
    root.title(window_name)

    app = Application(map_file, master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # for polygons : use opencv
    study_image(map_file, debug)

    # tkinter main loop
    app.mainloop()

    # delete app
    del app
    root.destroy()


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', required=False, help='Show contours (debug)', action='store_true')
    parser.add_argument('-m', '--map_file', required=True, help='Load a map file at start')
    args = parser.parse_args()

    #  load files at start
    debug = args.debug
    map_file = args.map_file

    if not os.path.exists(map_file):
        print(f"File '{map_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    main_loop(debug, map_file)

    print("The End")


if __name__ == "__main__":
    main()
