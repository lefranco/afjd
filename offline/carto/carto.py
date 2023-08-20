#!/usr/bin/env python3

"""

# Below code to display a cv image
import PIL.Image
import PIL.ImageTk

    imgpil = PIL.Image.fromarray(CV2_IMAGE)
    imgtk = PIL.ImageTk.PhotoImage(image=imgpil)
    label = tkinter.Label(main_frame, image=imgtk)
    label.image = imgtk  # type: ignore # keep reference
    label.grid(row=1, column=1, sticky='we')


# Below code to put legends
    for zone_data in parameters_data['zones'].values():
        name = zone_data['name']
        x_legend_pos = zone_data['x_legend_pos']
        y_legend_pos = zone_data['y_legend_pos']
        self.canvas.create_text(x_legend_pos, y_legend_pos, font=("Arial", 8), text=name, fill='black')

# Below code to put polygons
    for zone_data in parameters_data['zone_areas'].values():
        area = zone_data['area']
        point_prec: typing.Optional[typing.Tuple[int]] = None
        for point in area:
            if point_prec:
                self.canvas.create_line(point_prec[0], point_prec[1], point[0], point[1], fill="yellow")
            point_prec = point
"""

import argparse
import typing
import os
import configparser
import json

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext

import cv2  #type: ignore

# Important : name of file with version information
VERSION_FILE_NAME = "./version.ini"

VERSION_SECTION = "version"

INFO_HEIGHT1 = 10
INFO_WIDTH1 = 30

INFO_HEIGHT2 = 20
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

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        tkinter.Text.__init__(self, *args, **kwargs)
        self.config(state=tkinter.DISABLED)

    def display(self, content: str) -> None:
        """ display """

        self.config(state=tkinter.NORMAL)
        self.delete(1.0, tkinter.END)
        self.insert(tkinter.END, content)
        self.see("end")
        self.config(state=tkinter.DISABLED)


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, parameter_file: str, map_file: str, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # actual creation of widgets
        self.create_widgets(self, parameter_file, map_file)

    def create_widgets(self, main_frame: tkinter.Frame, parameter_file: str, map_file: str) -> None:
        """ create all widgets for application """

        def about() -> None:
            tkinter.messagebox.showinfo("About", str(VERSION_INFORMATION))

        def click_callback(event: typing.Any) -> None:

            information1 = f"clicked on x={event.x} y={event.y} !"
            self.mouse_pos.display(information1)

            information2 = "xxx"
            self.polygon.display(information2)

        def do_callback() -> None:
            print("do button was pressed")

        self.menu_bar = tkinter.Menu(main_frame)

        self.menu_file = tkinter.Menu(self.menu_bar, tearoff=0)
        self.menu_file.add_command(label="Reload map", command=self.menu_reload_map)
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

        with open(parameter_file, "r", encoding="utf-8") as read_file:
            parameters_data = json.load(read_file)
        width = parameters_data['map']['width']
        height = parameters_data['map']['height']

        print(f"Map : {width=} {height=}")

        self.canvas = tkinter.Canvas(frame_carto, width=width, height=height)
        self.canvas.grid(row=1, column=1)

        self.canvas.bind("<Button-1>", click_callback)

        self.filename = tkinter.PhotoImage(file=map_file)
        self.canvas.create_image(0, 0, anchor=tkinter.NW, image=self.filename)

        # frame buttons and information
        # -----------

        frame_buttons_information = tkinter.Frame(main_frame)
        frame_buttons_information.grid(row=2, column=2, sticky='nw')

        self.button = tkinter.Button(frame_buttons_information, text="do", command=do_callback)
        self.button.grid(row=1, column=1, sticky='we')

        self.mouse_pos = MyText(frame_buttons_information, height=INFO_HEIGHT1, width=INFO_WIDTH1)
        self.mouse_pos.grid(row=2, column=1, sticky='we')

        self.polygon = MyText(frame_buttons_information, height=INFO_HEIGHT2, width=INFO_WIDTH2)
        self.polygon.grid(row=3, column=1, sticky='we')

    def menu_reload_map(self) -> None:
        """ as it says """
        # TODO
        print("should reload map")

    def menu_complete_quit(self) -> None:
        """ as it says """
        self.on_closing()

    def on_closing(self) -> None:
        """ User closed window """
        self.master.quit()


CV2_IMAGE = None


def main_loop(parameter_file: str, map_file: str) -> None:
    """ main_loop """

    global CV2_IMAGE

    root = tkinter.Tk()

    # put main window upper left hand side
    root.geometry("+0+0")
    root.resizable(False, False)

    print(f"Working now with file parameter file {parameter_file} and map file {map_file}...")

    # use description of first register as overall title
    window_name = "Diplomania map zone extracting tool"

    # create app
    root.title(window_name)

    app = Application(parameter_file, map_file, master=root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # for polygons : use opencv
    tmp_image = cv2.imread(map_file)  # pylint: disable=c-extension-no-member
    blue, green, red = cv2.split(tmp_image)  # pylint: disable=c-extension-no-member
    CV2_IMAGE = cv2.merge((red, green, blue))  # pylint: disable=c-extension-no-member

    # tkinter main loop
    app.mainloop()

    # delete app
    del app
    root.destroy()


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--map_file', required=True, help='Load a map file at start')
    parser.add_argument('-p', '--parameter_file', required=True, help='Load a map file at start')
    args = parser.parse_args()

    #  load files at start
    map_file = args.map_file
    parameter_file = args.parameter_file

    main_loop(parameter_file, map_file)

    print("The End")


if __name__ == "__main__":
    main()
