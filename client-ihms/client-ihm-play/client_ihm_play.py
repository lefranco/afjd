#!/usr/bin/env python3

"""
an ihm based on tkinter
this is the main module
"""

import typing
import datetime
import sys
import json
import time

import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext  # type: ignore

import requests

import font
import data
import forbiddens
import ownerships
import units
import orders
import canvas

SESSION = requests.Session()

DIPLOMACY_SEASON_CYCLE = [1, 2, 1, 2, 3]

HELP_FILE = "./help/help_content.txt"

COLOR_SCROLLED_INFO = 'Black'
COLOR_SCROLLED_WARNING = 'Orange'
COLOR_SCROLLED_ERROR = 'Red'

COLOR_INFO = "Blue"
COLOR_DATA = 'DimGrey'

# elements for tooltip
TOOLTIP_HELP_DELAY = 1000
TOOLTIP_X_OFFSET = 20
TOOLTIP_Y_OFFSET = 20
TOOLTIP_FONT = ("tahoma", "8", "normal")
TOOLTIP_COLOR = "Light Yellow"

# some separators are inserted
SEPARATOR_SIZE = 4

TEXT_BACKGROUND = 'Ghost White'

# This is a variable to notify done for this game
QUIT = False

# The token that serves to be identified
JWT_TOKEN = ''

# change this for a different disign
IMPOSED_DESIGN_NAME = 'stabbeur'

GAME_IDENTIFIER = -1
GAME_NAME = ''
ROLE_IDENTIFIER = -1


def load_variant_data() -> None:
    """ load standard data from server """

    assert data.VARIANT_NAME
    variant_name = data.VARIANT_NAME

    host = data.SERVER_CONFIG['GAME']['HOST']
    port = data.SERVER_CONFIG['GAME']['PORT']
    url = f"{host}:{port}/variants/{variant_name}"
    req_result = SESSION.get(url)
    if req_result.status_code != 200:
        print(f"ERROR from server  : {req_result.text}")
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        tkinter.messagebox.showerror("KO", f"Impossible de charger les données de la variante {message}")
        return

    data.VARIANT_DATA = req_result.json()


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # identification data to send to server
        self.login_var = tkinter.StringVar()
        self.password_var = tkinter.StringVar()

        # list of games
        self.selectable_game_list: typing.List[typing.Tuple[int, str]] = list()

        # current season
        self._advancement_season = 0
        self._advancement_year = 0

        # actual creation of widgets
        self.create_widgets(self)

    def create_widgets(self, frame: tkinter.Frame) -> None:
        """ create all widgets for application """

        def some_help() -> None:
            help_window = tkinter.Toplevel()
            help_window.title("Un peu d'aide")

            with open(HELP_FILE, 'r', encoding="utf-8") as file_ptr2:
                content = file_ptr2.readlines()
                text = ''.join(content)
                help_text = tkinter.Text(help_window, wrap="word")
                help_text.tag_configure("blue", foreground="blue")
                help_text.grid()
                help_text.insert("1.0", text)  # type: ignore
                ok_button = tkinter.Button(help_window, text='OK', command=help_window.destroy)
                ok_button.grid()

        def about() -> None:
            version_information = "Cette beta version est partiellement testée !"
            tkinter.messagebox.showinfo("A propos", str(version_information))

        self.main_frame = frame

        menu_bar = tkinter.Menu(self.main_frame)
        menu_file = tkinter.Menu(menu_bar, tearoff=0)

        menu_file.add_command(label="Charger les centres", command=self.menu_load_ownerships)  # type: ignore
        menu_file.add_command(label="Sauver les centres", command=self.menu_save_ownerships)  # type: ignore
        menu_file.add_command(label="Charger une position", command=self.menu_load_position)  # type: ignore
        menu_file.add_command(label="Sauver la position", command=self.menu_save_position)  # type: ignore
        menu_file.add_command(label="Charger un jeu d'ordres", command=self.menu_load_orders)  # type: ignore
        menu_file.add_command(label="Sauver le jeu d'ordres", command=self.menu_save_orders)  # type: ignore

        menu_file.add_separator()  # type: ignore

        menu_file.add_command(label="Sortie", command=self.on_closing)  # type: ignore
        menu_bar.add_cascade(label="Fichier", menu=menu_file)  # type: ignore

        menu_help = tkinter.Menu(menu_bar, tearoff=0)
        menu_help.add_command(label="Un peu d'aide", command=some_help)  # type: ignore
        menu_help.add_command(label="A propos...", command=about)  # type: ignore

        menu_bar.add_cascade(label="Aide", menu=menu_help)  # type: ignore

        self.master.configure(menu=menu_bar)

        frame_title = tkinter.Frame(self.main_frame)
        frame_title.grid(row=1, column=1, sticky='we')

        # a logo
        photo_diplo = tkinter.PhotoImage(file="./static/logo_diplo.png")
        label_photo = tkinter.Label(frame_title, image=photo_diplo, compound='top')
        label_photo.image = photo_diplo  # type: ignore # keep reference
        label_photo.grid(row=1, column=1, sticky='w')

        # put separator
        label_separator = tkinter.Label(frame_title, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=2)

        # button
        self.button_new = tkinter.Button(frame_title, text="Charger la liste des parties")
        self.button_new.config(state=tkinter.ACTIVE)
        self.button_new.bind("<Button-1>", self.callback_load_games_from_server)
        self.button_new.grid(row=1, column=3)

        # put separator
        label_separator = tkinter.Label(frame_title, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=4)

        # game selection field
        label_variant = tkinter.Label(frame_title, text="Partie :")
        label_variant.grid(row=1, column=5, sticky='w')

        self.listbox_selectable_game_input = tkinter.Listbox(frame_title, width=30, height=3, exportselection=0)
        self.listbox_selectable_game_input.grid(row=1, column=6, sticky='w')
        self.listbox_selectable_game_input.config(state=tkinter.DISABLED)

        # button
        self.button_select_game = tkinter.Button(frame_title, text="Recharger cette partie")
        self.button_select_game.config(state=tkinter.DISABLED)
        self.button_select_game.bind("<Button-1>", self.callback_load_game)
        self.button_select_game.grid(row=1, column=7)

        # put separator
        label_separator = tkinter.Label(frame_title, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=8)

        # login field
        label_login = tkinter.Label(frame_title, text="Login (pseudo) -->")
        label_login.grid(row=1, column=9)
        entry_login_input = tkinter.Entry(frame_title, textvariable=self.login_var)
        entry_login_input.grid(row=1, column=10)

        # put separator
        label_separator = tkinter.Label(frame_title, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=11)

        # password field
        label_password = tkinter.Label(frame_title, text="Mot de passe -->")
        label_password.grid(row=1, column=12)
        entry_password_input = tkinter.Entry(frame_title, show="*", textvariable=self.password_var)
        entry_password_input.grid(row=1, column=13)

        # put separator
        label_separator = tkinter.Label(frame_title, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=14)

        # button
        button_login = tkinter.Button(frame_title, text="Login")
        button_login.config(state=tkinter.ACTIVE)
        button_login.bind("<Button-1>", self.callback_login)
        button_login.grid(row=1, column=15)

        self.paned_middle = tkinter.PanedWindow(self.main_frame)
        self.paned_middle.grid(row=2, column=1)

        # LEFT COLUMN

        paned_middle_west = tkinter.PanedWindow(self.paned_middle, orient=tkinter.VERTICAL)

        # Above above map =======================
        frame_above_above_map = tkinter.LabelFrame(paned_middle_west, text="Partie")
        paned_middle_west.add(frame_above_above_map)  # type: ignore

        self.label_game = tkinter.Label(frame_above_above_map, fg=COLOR_INFO)
        self.label_game.grid(row=1, column=1)

        # put separator
        label_separator = tkinter.Label(frame_above_above_map, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=2)

        self.label_variant = tkinter.Label(frame_above_above_map, fg=COLOR_INFO)
        self.label_variant.grid(row=1, column=3)

        # put separator
        label_separator = tkinter.Label(frame_above_above_map, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=4)

        self.label_season = tkinter.Label(frame_above_above_map, fg=COLOR_INFO)
        self.label_season.grid(row=1, column=5)

        # put separator
        label_separator = tkinter.Label(frame_above_above_map, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=6)

        self.deadline_game = tkinter.Label(frame_above_above_map, fg=COLOR_INFO)
        self.deadline_game.grid(row=1, column=7)

        # Above map =======================
        frame_above_map = tkinter.LabelFrame(paned_middle_west, text="Actions")
        paned_middle_west.add(frame_above_map)  # type: ignore

        self.button_edit_centers = tkinter.Button(frame_above_map, text="Editer les possessions de centres")
        self.button_edit_centers.config(state=tkinter.DISABLED)
        self.button_edit_centers.bind("<Button-1>", self.callback_switch_edit_centers)
        self.button_edit_centers.grid(row=1, column=1)

        self.button_edit_position = tkinter.Button(frame_above_map, text="Editer les position des unités")
        self.button_edit_position.config(state=tkinter.DISABLED)
        self.button_edit_position.bind("<Button-1>", self.callback_switch_position_edition)
        self.button_edit_position.grid(row=1, column=2)

        self.button_enter_orders = tkinter.Button(frame_above_map, text="Retour à l'entrée d'ordres")
        self.button_enter_orders.config(state=tkinter.DISABLED)
        self.button_enter_orders.bind("<Button-1>", self.callback_switch_order_entry)
        self.button_enter_orders.grid(row=1, column=3)

        # label_information calculated later

        # Map  =======================

        self.canvas = canvas.MyCanvas(self, paned_middle_west, relief=tkinter.SUNKEN, borderwidth=5, width=canvas.IMPOSED_MAP_WIDTH, height=canvas.IMPOSED_MAP_HEIGHT)

        data.MAP_FILE = './static/background.png'
        self.canvas.put_map()

        paned_middle_west.add(self.canvas)  # type: ignore

        # Below map 1 =======================
        frame_just_just_below_map = tkinter.LabelFrame(paned_middle_west, text="Dernier(s) rapport(s) de résolution")
        paned_middle_west.add(frame_just_just_below_map)  # type: ignore
        self.text_report_information = tkinter.scrolledtext.ScrolledText(frame_just_just_below_map, height=7, background=TEXT_BACKGROUND, wrap=tkinter.WORD)
        self.text_report_information.configure(state=tkinter.DISABLED)
        self.text_report_information.grid(row=1, column=1, sticky='w')

        # Below map 2 =======================
        self._centers_edition_mode = "Mode édition des centres"
        self._position_edition_mode = "Mode édition de position"
        self._order_input_mode = "Mode entrée d'ordres"

        self._frame_below_map_upper = tkinter.LabelFrame(paned_middle_west, text=self._order_input_mode)
        paned_middle_west.add(self._frame_below_map_upper)  # type: ignore

        self._centers_edition_welcome_message = "Cliquez sur la carte pour éditer les centres avec la souris\nBouton gauche pour sélectionner ou supprimer et droit pour changer de rôle.\nDes instructions s'afficheront au fil de l'eau\n"
        self._position_edition_welcome_message = "Cliquez sur la carte pour éditer la position avec la souris\nBouton gauche pour sélectionner ou supprimer, milieu pour changer de type d'unité et droit pour changer de rôle.\nDes instructions s'afficheront au fil de l'eau\n"
        self._order_input_welcome_message = "Cliquez sur la carte pour passer les ordres avec la souris\nBouton gauche pour sélectionner, milieu pour changer d'ordre et droit pour valider.\nDes instructions s'afficheront au fil de l'eau\n"

        self.label_dynamic_information = tkinter.Label(self._frame_below_map_upper, height=4, text=self._order_input_welcome_message, fg=COLOR_INFO, justify=tkinter.LEFT)
        self.label_dynamic_information.grid(row=1, column=1, sticky='w')

        # Below map 3 =======================

        frame_logger = tkinter.LabelFrame(paned_middle_west, text="Log des événements")
        paned_middle_west.add(frame_logger)  # type: ignore

        self.scrolled_log = tkinter.scrolledtext.ScrolledText(frame_logger, height=5, background=TEXT_BACKGROUND, wrap=tkinter.WORD)
        self.scrolled_log.configure(state=tkinter.DISABLED)
        self.scrolled_log.tag_config('info', foreground=COLOR_SCROLLED_INFO)
        self.scrolled_log.tag_config('warning', foreground=COLOR_SCROLLED_WARNING)
        self.scrolled_log.tag_config('error', foreground=COLOR_SCROLLED_ERROR)
        self.scrolled_log.grid(row=1, column=1, sticky='nsew')

        # Button to erase
        self.button_erase = tkinter.Button(frame_logger, text="Effacer")
        self.button_erase.config(state=tkinter.DISABLED)
        self.button_erase.grid(row=1, column=2)
        self.button_erase.bind("<Button-1>", self.callback_erase_logs)

        self.paned_middle.add(paned_middle_west)  # type: ignore

        # RIGHT COLUMN

        self.paned_middle_east = tkinter.PanedWindow(self.paned_middle, orient=tkinter.VERTICAL)

        # Role =======================
        frame_role = tkinter.LabelFrame(self.paned_middle_east, text="Rôle")

        self.label_role = tkinter.Label(frame_role, text="", fg=COLOR_INFO, justify=tkinter.LEFT)
        self.label_role.grid(row=1, column=1, sticky='w')

        self.paned_middle_east.add(frame_role)  # type: ignore

        # Status of players =======================
        self.frame_players_status = tkinter.LabelFrame(self.paned_middle_east, text="Status des joueurs")

        # will be filled later
        self.fake = tkinter.Label(self.frame_players_status, text="")
        self.fake.grid(row=1, column=1, sticky='w')

        self.paned_middle_east.add(self.frame_players_status)  # type: ignore

        # Orders =======================
        frame_orders = tkinter.LabelFrame(self.paned_middle_east, text="Ordres")

        # Create text widget
        self.text_orders = tkinter.scrolledtext.ScrolledText(frame_orders, height=8, background=TEXT_BACKGROUND, wrap=tkinter.WORD)
        self.text_orders.configure(state=tkinter.DISABLED)
        self.text_orders.grid(row=1, column=1, rowspan=5, sticky="ew")

        self.button_reinit = tkinter.Button(frame_orders, text="Réinitialiser")
        self.button_reinit.config(state=tkinter.DISABLED)
        self.button_reinit.grid(row=1, column=2, sticky="w")
        self.button_reinit.bind("<Button-1>", self.callback_reinit)

        self.button_submit = tkinter.Button(frame_orders, text="Soumettre")
        self.button_submit.config(state=tkinter.DISABLED)
        self.button_submit.grid(row=3, column=2, sticky="w")
        self.button_submit.bind("<Button-1>", self.callback_submit)

        self.paned_middle_east.add(frame_orders)  # type: ignore

        # Messages =======================

        # will be filled later when variant is known
        self.frame_private = tkinter.LabelFrame(self.paned_middle_east, text="Messages")
        self.notebook_tab = tkinter.ttk.Notebook(self.frame_private)
        self.notebook_tab.grid(row=1, column=1)
        self.paned_middle_east.add(self.frame_private)  # type: ignore

        # fake to reserve some room
        self.set_negotiation_widget()

        # Declarations =======================
        frame_public = tkinter.LabelFrame(self.paned_middle_east, text="Déclarations")

        # Create text widget
        self.gazette = tkinter.scrolledtext.ScrolledText(frame_public, height=7, background=TEXT_BACKGROUND, wrap=tkinter.WORD)
        self.gazette.configure(state=tkinter.DISABLED)
        self.gazette.grid(row=1, column=1, columnspan=2, sticky="ew")
        self.gazette.tag_configure('blue', foreground='Blue', font=("Courier", 8, "normal"))

        self.content_express = tkinter.Text(frame_public, height=4)
        self.content_express.grid(row=2, column=1)

        # Button to add stuff
        self.button_express = tkinter.Button(frame_public, text="Publier")
        self.button_express.config(state=tkinter.DISABLED)
        self.button_express.grid(row=2, column=2)
        self.button_express.bind("<Button-1>", self.callback_express)
        self.paned_middle_east.add(frame_public)  # type: ignore

        # Game master =======================
        frame_master = tkinter.LabelFrame(self.paned_middle_east, text="Arbitrage")

        self.button_adjudicate = tkinter.Button(frame_master, text="Résoudre")
        self.button_adjudicate.config(state=tkinter.DISABLED)
        self.button_adjudicate.grid(row=1, column=1)
        self.button_adjudicate.bind("<Button-1>", self.callback_adjudicate)
        self.paned_middle_east.add(frame_master)  # type: ignore

        # put separator
        label_separator = tkinter.Label(frame_master, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=1, column=2)

        # Rectify =======================
        self.button_rectify = tkinter.Button(frame_master, text="Rectifier")
        self.button_rectify.config(state=tkinter.DISABLED)
        self.button_rectify.grid(row=1, column=3)
        self.button_rectify.bind("<Button-1>", self.callback_rectify)

        # Sandbox =======================
        frame_sandbox = tkinter.LabelFrame(self.paned_middle_east, text="Bac à sable")

        self.button_simulate = tkinter.Button(frame_sandbox, text="Simuler")
        self.button_simulate.config(state=tkinter.NORMAL)
        self.button_simulate.bind("<Button-1>", self.callback_simulate)
        self.button_simulate.grid(row=1, column=1)

        self.paned_middle_east.add(frame_sandbox)  # type: ignore
        self.paned_middle.add(self.paned_middle_east)  # type: ignore


    def set_negotiation_widget(self) -> None:
        """ This widget depends on variant (how many other players) """

        # remove former tabs
        for item in self.notebook_tab.winfo_children():  # type: ignore
            item.destroy()

        # List of roles
        role_names = ['']
        if data.VARIANT_DATA:
            role_names = [data.ROLE_DATA[str(role_id)]['name'] for role_id in range(int(data.VARIANT_DATA['roles']['number']) + 1)]

        # my role
        my_role = ''
        if data.VARIANT_DATA:
            if ROLE_IDENTIFIER != -1:
                my_role = data.ROLE_DATA[str(ROLE_IDENTIFIER)]['name']

        self.messages_with = dict()  # pylint: disable=attribute-defined-outside-init
        self.button_send = dict()  # pylint: disable=attribute-defined-outside-init
        self.content_send = dict()  # pylint: disable=attribute-defined-outside-init

        for role_name in role_names:

            if role_name and role_name == my_role:
                continue

            frame_tab = tkinter.Frame(self.notebook_tab)

            # Create text widget
            self.messages_with[role_name] = tkinter.scrolledtext.ScrolledText(frame_tab, height=16, background=TEXT_BACKGROUND, wrap=tkinter.WORD)
            self.messages_with[role_name].configure(state=tkinter.DISABLED)
            self.messages_with[role_name].grid(row=1, column=1, columnspan=2, sticky="ew")
            self.messages_with[role_name].tag_configure('blue', foreground='Blue', font=("Courier", 8, "normal"))
            self.messages_with[role_name].tag_configure('blue_italics', foreground='Blue', font=("Courier", 8, "italic"))

            self.content_send[role_name] = tkinter.Text(frame_tab, height=7)
            self.content_send[role_name].grid(row=2, column=1)

            self.button_send[role_name] = tkinter.Button(frame_tab, text="Envoyer")
            self.button_send[role_name].config(state=tkinter.DISABLED)
            self.button_send[role_name].grid(row=2, column=2)
            self.button_send[role_name].bind("<Button-1>", self.callback_send)

            self.notebook_tab.add(frame_tab, text=role_name)  # type: ignore

        self.invert_button_send = {v: k for k, v in self.button_send.items()}  # pylint: disable=attribute-defined-outside-init

    def set_season(self, advancement: int) -> None:
        """ store season """

        assert data.SEASON_DATA
        len_season_cycle = len(DIPLOMACY_SEASON_CYCLE)
        self._advancement_season = advancement % len_season_cycle + 1
        self._advancement_year = (advancement // len_season_cycle) + 1 + data.VARIANT_DATA['year_zero']

    def display_season(self) -> None:
        """ update dynamic display """

        season_name = data.SEASON_DATA[str(self._advancement_season)]['name']
        self.label_season.config(text=f"Saison {season_name} {self._advancement_year}")

    def reset_input_order_automaton(self) -> None:
        """ reset input order automaton """

        if self._advancement_season in [1, 3]:
            self.canvas.current_automaton = canvas.MoveOrderAutomaton(self.canvas)
        if self._advancement_season in [2, 4]:
            self.canvas.current_automaton = canvas.RetreatOrderAutomaton(self.canvas)
        if self._advancement_season in [5]:
            self.canvas.current_automaton = canvas.AdjustmentOrderAutomaton(self.canvas)

    def determine_role(self) -> None:
        """ determines the role the player is in the game (if possible) """

        global ROLE_IDENTIFIER
        ROLE_IDENTIFIER = -1
        self.label_role.config(text="")

        # make some buttons possible
        self.button_submit.config(state=tkinter.DISABLED)
        self.button_adjudicate.config(state=tkinter.DISABLED)
        self.button_rectify.config(state=tkinter.DISABLED)
        self.button_reinit.config(state=tkinter.DISABLED)
        for button in self.button_send.values():
            button.config(state=tkinter.DISABLED)
        self.button_express.config(state=tkinter.DISABLED)

        if GAME_IDENTIFIER == -1:
            return

        pseudo = self.login_var.get()  # type: ignore
        if pseudo == '':
            return

        # get player identifier
        host = data.SERVER_CONFIG['PLAYER']['HOST']
        port = data.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/player_identifiers/{pseudo}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return

        user_id = req_result.json()

        # get all allocations of the game
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{GAME_IDENTIFIER}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return

        json_dict = req_result.json()
        allocations_dict = json_dict

        if str(user_id) in allocations_dict:
            ROLE_IDENTIFIER = allocations_dict[str(user_id)]

        if ROLE_IDENTIFIER == -1:
            return

        # ok we have the player

        # display on console
        role_name = data.ROLE_DATA[str(ROLE_IDENTIFIER)]['name']
        # apply role in game
        self.label_role.config(text=f"Vous jouez {role_name}")

        # retrieve last visit on server
        json_dict = {
            'role_id': ROLE_IDENTIFIER,
            'pseudo': self.login_var.get(),  # type: ignore
        }

        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-visits/{GAME_IDENTIFIER}"
        req_result = SESSION.get(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Echec à la récupération de la dernière visite : {message}")
            return

        my_last_visit = req_result.json()['time_stamp']

        # log visit on server
        json_dict = {
            'role_id': ROLE_IDENTIFIER,
            'pseudo': self.login_var.get(),  # type: ignore
        }

        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-visits/{GAME_IDENTIFIER}"
        req_result = SESSION.post(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Echec à l'enregistrement de la visite : {message}")
            return

        # get this game - declarations (requires variant)

        # get from server
        # log visit on server
        json_dict = {
            'role_id': ROLE_IDENTIFIER,
            'pseudo': self.login_var.get(),  # type: ignore
        }

        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{GAME_IDENTIFIER}"
        req_result = SESSION.get(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Echec à la récupération des déclarations : {message}")
            return

        # update on screen
        json_dict = req_result.json()
        declarations_list = json_dict['declarations_list']

        self.gazette.configure(state=tkinter.NORMAL)
        self.gazette.delete('1.0', tkinter.END)

        number_new_declarations = 0
        for date_declaration, author_declaration, content_declaration in declarations_list:
            datetime_declaration = datetime.datetime.fromtimestamp(date_declaration)
            time_stamp_declaration = time.mktime(datetime_declaration.timetuple())

            if author_declaration != ROLE_IDENTIFIER:
                if time_stamp_declaration > my_last_visit:
                    number_new_declarations += 1

            date_desc = datetime_declaration.strftime('%Y-%m-%d %H:%M:%S')
            role_desc = data.ROLE_DATA[str(author_declaration)]['name']
            self.gazette.insert(tkinter.END, f"Le {date_desc} par {role_desc}:\n")
            self.gazette.insert(tkinter.END, f"{content_declaration}\n", 'blue')

        self.gazette.see("1.0")
        self.gazette.configure(state=tkinter.DISABLED)

        # make widgets for negotations (dynamic from role)
        self.set_negotiation_widget()

        # get this game - messages (requires variant)

        # get from server
        json_dict = {
            'role_id': ROLE_IDENTIFIER,
            'pseudo': self.login_var.get(),  # type: ignore
        }

        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{GAME_IDENTIFIER}"
        req_result = SESSION.get(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Echec à la récupération des messages : {message}")
            return

        # update on screen
        json_dict = req_result.json()
        messages_list = json_dict['messages_list']

        for tab_role_name in self.messages_with:
            self.messages_with[tab_role_name].configure(state=tkinter.NORMAL)
            self.messages_with[tab_role_name].delete('1.0', tkinter.END)

        number_new_messages = 0
        for date_message, author_message, addressee_message, content_message in messages_list:

            datetime_message = datetime.datetime.fromtimestamp(date_message)
            time_stamp_message = time.mktime(datetime_message.timetuple())

            date_desc = datetime_message.strftime('%Y-%m-%d %H:%M:%S')
            role_author = data.ROLE_DATA[str(author_message)]['name']
            role_addressee = data.ROLE_DATA[str(addressee_message)]['name']

            # identify other and myself
            if author_message == ROLE_IDENTIFIER:
                # sent
                tab_role_name = role_addressee
            else:
                # received
                tab_role_name = role_author
                # received and new
                if time_stamp_message > my_last_visit:
                    number_new_messages += 1

            self.messages_with[tab_role_name].insert(tkinter.END, f"Le {date_desc} par {role_author} pour {role_addressee}:\n")
            if author_message == ROLE_IDENTIFIER:
                self.messages_with[tab_role_name].insert(tkinter.END, f"{content_message}\n", 'blue_italics')
            else:
                self.messages_with[tab_role_name].insert(tkinter.END, f"{content_message}\n", 'blue')

        for tab_role_name in self.messages_with:
            self.messages_with[tab_role_name].see("1.0")
            self.messages_with[tab_role_name].configure(state=tkinter.DISABLED)

        # get orders

        # erase orders
        self.canvas.bag_orders.reinit()
        self.canvas.refresh()

        json_dict = {
            'role_id': ROLE_IDENTIFIER,
            'pseudo': self.login_var.get(),  # type: ignore
        }

        # get the orders of the player only or all if game master

        # load the orders (and fake units)
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-orders/{GAME_IDENTIFIER}"
        req_result = SESSION.get(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Impossible de charger les ordres de cette partie {message}")
            return

        # store request result
        json_dict = req_result.json()

        # load the fake units
        for _, unit_type, zone_num, role_num, _, _ in json_dict['fake_units']:
            unit_type_enum = data.TypeUnitEnum.decode(unit_type)
            assert unit_type_enum is not None
            fake_unit = units.Unit(self.canvas, unit_type_enum, role_num, zone_num, None)
            self.canvas.bag_units.add_fake_unit(fake_unit)

        # load the orders
        self.canvas.bag_orders.reinit()
        for _, _, order_type, active_unit_num, passive_unit_num, destination_zone in json_dict['orders']:
            # make order
            order = orders.Order(self.canvas)
            order.order_type = orders.OrderEnum.decode(order_type)
            if order.order_type is orders.OrderEnum.BUILD_ORDER:
                order.active_unit = self.canvas.bag_units.find_fake_unit(active_unit_num)
            else:
                order.active_unit = self.canvas.bag_units.find_unit(active_unit_num)
            order.passive_unit = self.canvas.bag_units.find_unit(passive_unit_num)
            order.destination_zone = destination_zone
            # add it
            self.canvas.bag_orders.add_update_order(order)

        # make it visible
        self.canvas.refresh()

        # make some buttons possible
        self.button_submit.config(state=tkinter.ACTIVE)
        self.button_reinit.config(state=tkinter.ACTIVE)
        for button in self.button_send.values():
            button.config(state=tkinter.ACTIVE)
        self.button_express.config(state=tkinter.ACTIVE)

        if ROLE_IDENTIFIER == 0:
            # set buttons for gm
            self.button_adjudicate.config(state=tkinter.ACTIVE)
            self.button_rectify.config(state=tkinter.ACTIVE)
        else:
            # set buttons for player
            self.button_adjudicate.config(state=tkinter.DISABLED)
            self.button_rectify.config(state=tkinter.DISABLED)

        if number_new_declarations:
            tkinter.messagebox.showinfo("Attention", f"Il y a {number_new_declarations} nouvelle(s) declarations(s)")

        if number_new_messages:
            tkinter.messagebox.showinfo("Attention", f"Vous avez {number_new_messages} nouveau(x) message(s) diplomatique(s)")

    def callback_load_games_from_server(self, event: typing.Any) -> None:
        """ Reloads games from server to here """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        # get all games
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Impossible de charger la liste des parties {message}")
            return

        # show them for selection
        self.selectable_game_list = list()
        json_dict = req_result.json()
        previous_state = self.listbox_selectable_game_input.cget("state")  # type: ignore
        self.listbox_selectable_game_input.config(state=tkinter.NORMAL)
        self.listbox_selectable_game_input.delete(0, tkinter.END)
        for identifier, name in json_dict.items():
            self.selectable_game_list.append((identifier, name))
            self.listbox_selectable_game_input.insert(tkinter.END, name)  # type: ignore
        self.listbox_selectable_game_input.selection_set(0)  # First
        self.listbox_selectable_game_input.config(state=previous_state)

        self.listbox_selectable_game_input.config(state=tkinter.NORMAL)
        self.button_select_game.config(state=tkinter.NORMAL)

    def callback_load_game(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        global GAME_IDENTIFIER
        global GAME_NAME
        game_index_sel, = self.listbox_selectable_game_input.curselection()  # type: ignore
        GAME_IDENTIFIER, GAME_NAME = self.selectable_game_list[game_index_sel]

        # get this game - game report
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-reports/{GAME_IDENTIFIER}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Echec à la récupération du rapport : {message}")
            return

        # update on screen
        json_dict = req_result.json()
        content = json_dict['content']

        self.text_report_information.configure(state=tkinter.NORMAL)
        self.text_report_information.delete('1.0', tkinter.END)
        self.text_report_information.insert(tkinter.END, content)
        self.text_report_information.see(tkinter.END)
        self.text_report_information.configure(state=tkinter.DISABLED)

        # get this game - game itself
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/games/{GAME_NAME}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Impossible de charger cette partie {message}")
            return

        # store request result
        json_dict = req_result.json()

        # update dynamic display information

        # apply name of game
        self.label_game.config(text=f"Partie {GAME_NAME}")

        # apply variant of game
        variant_name = json_dict['variant']
        self.label_variant.config(text=f"Variante {variant_name}")
        data.set_variant_name(variant_name)
        load_variant_data()

        # use design file locally present
        design_name = IMPOSED_DESIGN_NAME
        data.set_design_name(design_name)
        data.load_design_data()

        # map as background
        data.set_map_file()
        self.canvas.put_map()
        self.canvas.put_names()

        # advancement
        advancement = json_dict['current_advancement']
        self.set_season(advancement)
        self.display_season()

        # apply deadline of game
        deadline = json_dict['deadline']
        self.deadline_game.config(text=f"D.L. {deadline}")

        # init automaton
        self.reset_input_order_automaton()

        # get this game - position of the game
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-positions/{GAME_IDENTIFIER}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Impossible de charger la position de cette partie {message}")
            return

        # store request result
        json_dict = req_result.json()

        # load the ownerships
        self.canvas.bag_centers.reinit()
        for center_num, role in json_dict['ownerships'].items():
            center_ownership = ownerships.CenterOwnership(self.canvas, role, int(center_num))
            self.canvas.bag_centers.add_center(center_ownership)

        self.canvas.bag_units.reinit()

        # do not load the fake units

        # load the units
        for role, normal_units in json_dict['units'].items():
            for unit_type, zone_num in normal_units:
                unit_type_enum = data.TypeUnitEnum.decode(unit_type)
                assert unit_type_enum is not None
                unit = units.Unit(self.canvas, unit_type_enum, int(role), zone_num, None)
                self.canvas.bag_units.add_unit(unit)

        # load the dislodged units
        for role, dislodged in json_dict['dislodged_ones'].items():
            for unit_type, zone_num, origin_num in dislodged:
                unit_type_enum = data.TypeUnitEnum.decode(unit_type)
                assert unit_type_enum is not None
                dislodged_unit = units.Unit(self.canvas, unit_type_enum, int(role), zone_num, origin_num)
                self.canvas.bag_units.add_dislodged_unit(dislodged_unit)

        # load the forbidden
        self.canvas.bag_forbiddens.reinit()
        for region_num in json_dict['forbiddens']:
            forbidden = forbiddens.Forbidden(self.canvas, region_num)
            self.canvas.bag_forbiddens.add_forbidden(forbidden)

        # try to find out role from login and game
        self.determine_role()

        self.canvas.refresh()

        self.button_edit_centers.config(state=tkinter.ACTIVE)
        self.button_edit_position.config(state=tkinter.ACTIVE)

        # now fill players status information

        # get allocations of players in game
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-allocations/{GAME_IDENTIFIER}"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return False, message
        json_dict = req_result.json()
        playing_ones = {v:k for k, v in json_dict.items()}




        # get all players
        host = data.SERVER_CONFIG['PLAYER']['HOST']
        port = data.SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players"
        req_result = SESSION.get(url)
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return False, message
        json_dict = req_result.json()
        player_dict = json_dict

        # display information about players game

        # housekeeping
        for widget in self.frame_players_status.grid_slaves():
            widget.destroy()

        nb_roles = data.VARIANT_DATA['roles']['number']
        for role_id in range(1, nb_roles+1):

            # name of role
            role_name = data.ROLE_DATA[str(role_id)]['name']
            label_role_name = tkinter.Label(self.frame_players_status, text=f"{role_name}")
            label_role_name.grid(row=1, column=role_id)

            # player pseudo
            player_id = playing_ones[role_id]
            player_pseudo = player_dict[player_id]
            label_pseudo = tkinter.Label(self.frame_players_status, text=f"{player_pseudo}", fg=COLOR_INFO)
            label_pseudo.grid(row=2, column=role_id)

            # active or not
            active = "actif?"
            label_active = tkinter.Label(self.frame_players_status, text=f"{active}", fg=COLOR_INFO)
            label_active.grid(row=3, column=role_id)

            # orders in or not
            active = "ordres?"
            label_active = tkinter.Label(self.frame_players_status, text=f"{active}", fg=COLOR_INFO)
            label_active.grid(row=4, column=role_id)

            self.button_civil_disorder = tkinter.Button(self.frame_players_status, text="Mettre en DC")
            #self.button_civil_disorder.config(state=tkinter.DISABLED)
            self.button_civil_disorder.bind("<Button-1>", lambda event, arg=role_id: self.callback_put_in_civil_disorder(event, arg))
            self.button_civil_disorder.grid(row=5, column=role_id)

            self.button_remove_from_game = tkinter.Button(self.frame_players_status, text="Ejecter")
            #self.button_remove_from_game.config(state=tkinter.DISABLED)
            self.button_remove_from_game.bind("<Button-1>", lambda event, arg=role_id:  self.callback_remove_from_game(event, arg))
            self.button_remove_from_game.grid(row=6, column=role_id)

        # redraw from upper level
        self.main_frame.grid_remove()
        self.main_frame.grid()

        msg = f"Rechargement depuis le serveur de la partie {GAME_NAME} "
        self.scroll_message(msg, 'info')

    def callback_login(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        # Now I get token
        pseudo = self.login_var.get()  # type: ignore
        password = self.password_var.get()  # type: ignore

        host = data.SERVER_CONFIG['USER']['HOST']
        port = data.SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/login"
        req_result = SESSION.post(url, json={'user_name': pseudo, 'password': password})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Echec à l'identification : {message}")
            return

        # very important : extract token for authentication
        json_dict = req_result.json()
        global JWT_TOKEN
        JWT_TOKEN = json_dict['AccessToken']

        # try to find out role from login and game
        self.determine_role()

        tkinter.messagebox.showinfo("OK", "Identification réussie !")

    def callback_adjudicate(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        if GAME_IDENTIFIER == -1:
            tkinter.messagebox.showerror("KO", "Pas de partie choisie !")
            return

        if ROLE_IDENTIFIER != 0:
            tkinter.messagebox.showerror("KO", "Vous n'êtes pas arbitre !")
            return

        names_dict = data.extract_names()
        names_dict_json = json.dumps(names_dict)

        json_dict = {
            'pseudo': self.login_var.get(),  # type: ignore
            'names': names_dict_json
        }

        # present the authentication token  (we are asking adjudication)
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-adjudications/{GAME_IDENTIFIER}"
        req_result = SESSION.post(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            tkinter.messagebox.showerror("KO", f"Echec à la résolution : {message}")
            return

        tkinter.messagebox.showinfo("OK", f"Résolution réussie : {message}")

        msg = "Résolution réalisée sur le serveur"
        self.scroll_message(msg, 'info')

    def callback_rectify(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        if not tkinter.messagebox.askyesno("Attention", "Confimez vous la rectification de la position ?"):
            return

        if GAME_IDENTIFIER == -1:
            tkinter.messagebox.showerror("KO", "Pas de partie choisie !")
            return

        if ROLE_IDENTIFIER != 0:
            tkinter.messagebox.showerror("KO", "Vous n'êtes pas arbitre !")
            return

        # ownerships
        center_ownerships_list_dict = self.canvas.bag_centers.save_json()
        center_ownerships_list_dict_json = json.dumps(center_ownerships_list_dict, indent=4)

        # units and dislodged units
        units_list_dict = self.canvas.bag_units.save_json()
        dislodged_units_list_dict = self.canvas.bag_units.save_dislodged_json()
        units_list_dict_json = json.dumps(units_list_dict + dislodged_units_list_dict, indent=4)

        # forbiddens
        forbiddens_list_dict = self.canvas.bag_forbiddens.save_json()
        forbiddens_list_dict_json = json.dumps(forbiddens_list_dict, indent=4)

        json_dict = {
            'pseudo': self.login_var.get(),  # type: ignore
            'center_ownerships': center_ownerships_list_dict_json,
            'units': units_list_dict_json,
            'forbiddens': forbiddens_list_dict_json,
        }

        # present the authentication token  (we are rectifying situation)
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-positions/{GAME_IDENTIFIER}"
        req_result = SESSION.post(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Echec à la rectification : {message}")
            return

        tkinter.messagebox.showinfo("OK", "Rectification réussie !")

        msg = "Position rectifiée sur le serveur"
        self.scroll_message(msg, 'info')


    def callback_put_in_civil_disorder(self, event: typing.Any, role_id: int) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        print(f"put {role_id} in civil disorder not implemented")

    def callback_remove_from_game(self, event: typing.Any, role_id: int) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        print(f"remove {role_id} from game not implemented")


    def callback_reinit(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self.canvas.bag_orders.reinit()
        self.canvas.refresh()

    def callback_submit(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        if GAME_IDENTIFIER == -1:
            tkinter.messagebox.showerror("KO", "Pas de partie choisie !")
            return

        if ROLE_IDENTIFIER == -1:
            tkinter.messagebox.showerror("KO", "Pas de rôle déterminé !")
            return

        names_dict = data.extract_names()
        names_dict_json = json.dumps(names_dict)

        orders_list_dict = self.canvas.bag_orders.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict, indent=4)
        json_dict = {
            'role_id': ROLE_IDENTIFIER,
            'pseudo': self.login_var.get(),  # type: ignore
            'orders': orders_list_dict_json,
            'names': names_dict_json
        }

        # present the authentication token  (we are submitting orders)
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-orders/{GAME_IDENTIFIER}"
        req_result = SESSION.post(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            tkinter.messagebox.showerror("KO", f"Echec à la soumission : {message}")
            return

        tkinter.messagebox.showinfo("OK", f"Soumission réussie : {message}")

        role_name = data.ROLE_DATA[str(ROLE_IDENTIFIER)]['name']
        msg = f"Ordres soumis sur le serveur par {role_name}"
        self.scroll_message(msg, 'info')

    def callback_simulate(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        assert data.VARIANT_NAME
        variant_name = data.VARIANT_NAME

        names_dict = data.extract_names()
        names_dict_json = json.dumps(names_dict)

        # ownerships
        center_ownerships_list_dict = self.canvas.bag_centers.save_json()
        center_ownerships_list_dict_json = json.dumps(center_ownerships_list_dict, indent=4)

        # units
        units_list_dict = self.canvas.bag_units.save_json()
        units_list_dict_json = json.dumps(units_list_dict, indent=4)

        # orders
        orders_list_dict = self.canvas.bag_orders.save_json()
        orders_list_dict_json = json.dumps(orders_list_dict, indent=4)

        json_dict = {
            'variant_name': variant_name,
            'names': names_dict_json,
            'center_ownerships': center_ownerships_list_dict_json,
            'units': units_list_dict_json,
            'orders': orders_list_dict_json,
        }

        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/simulation"
        req_result = SESSION.post(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            tkinter.messagebox.showerror("KO", f"Echec à la simulation : {message}")
            return

        tkinter.messagebox.showinfo("OK", f"Simulation réussie : {message}")
        if 'result' in req_result.json():
            result = req_result.json()['result']
            tkinter.messagebox.showinfo("OK", f"Compte-rendu :\n\n{result}")

    def callback_send(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        dest = self.invert_button_send[event.widget]

        content = self.content_send[dest].get(1.0, tkinter.END)

        # retrieve number of dest
        dest_id = None
        for key, value in data.ROLE_DATA.items():
            if value['name'] == dest:
                dest_id = key
                break
        assert dest_id is not None

        json_dict = {
            'role_id': ROLE_IDENTIFIER,
            'pseudo': self.login_var.get(),  # type: ignore
            'dest_role_id': dest_id,
            'content': content
        }

        # present the authentication token  (we are submitting orders)
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-messages/{GAME_IDENTIFIER}"
        req_result = SESSION.post(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            tkinter.messagebox.showerror("KO", f"Echec à la rédaction : {message}")
            return

        tkinter.messagebox.showinfo("OK", f"Message envoyé : {message}")

    def callback_express(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        content = self.content_express.get(1.0, tkinter.END)

        json_dict = {
            'role_id': ROLE_IDENTIFIER,
            'pseudo': self.login_var.get(),  # type: ignore
            'content': content
        }

        # present the authentication token  (we are submitting orders)
        host = data.SERVER_CONFIG['GAME']['HOST']
        port = data.SERVER_CONFIG['GAME']['PORT']
        url = f"{host}:{port}/game-declarations/{GAME_IDENTIFIER}"
        req_result = SESSION.post(url, data=json_dict, headers={'AccessToken': JWT_TOKEN})
        message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
        if req_result.status_code != 201:
            print(f"ERROR from server  : {req_result.text}")
            tkinter.messagebox.showerror("KO", f"Echec à l'expression : {message}")
            return

        tkinter.messagebox.showinfo("OK", f"Déclaration exprimée : {message}")

    def callback_switch_edit_centers(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self._frame_below_map_upper.config(text=self._centers_edition_mode)
        self.label_dynamic_information.config(text=self._centers_edition_welcome_message)
        self.canvas.current_automaton = canvas.CentersEditionAutomaton(self.canvas)
        self.button_edit_centers.config(state=tkinter.DISABLED)
        self.button_edit_position.config(state=tkinter.ACTIVE)
        self.button_enter_orders.config(state=tkinter.ACTIVE)

        msg = "Passage en mode édition de centres"
        self.scroll_message(msg, 'info')

    def callback_switch_position_edition(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self._frame_below_map_upper.config(text=self._position_edition_mode)
        self.label_dynamic_information.config(text=self._position_edition_welcome_message)
        self.canvas.current_automaton = canvas.PositionEditionAutomaton(self.canvas)
        self.button_edit_centers.config(state=tkinter.ACTIVE)
        self.button_edit_position.config(state=tkinter.DISABLED)
        self.button_enter_orders.config(state=tkinter.ACTIVE)

        msg = "Passage en mode édition de position"
        self.scroll_message(msg, 'info')

    def callback_switch_order_entry(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self._frame_below_map_upper.config(text=self._order_input_mode)
        self.label_dynamic_information.config(text=self._order_input_welcome_message)
        self.reset_input_order_automaton()
        self.button_edit_centers.config(state=tkinter.ACTIVE)
        self.button_edit_position.config(state=tkinter.ACTIVE)
        self.button_enter_orders.config(state=tkinter.DISABLED)

        msg = "Retour en mode entrée d'ordres"
        self.scroll_message(msg, 'info')

    def callback_erase_logs(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self.scrolled_log.configure(state=tkinter.NORMAL)
        self.scrolled_log.delete('1.0', tkinter.END)
        self.scrolled_log.configure(state=tkinter.DISABLED)

        self.button_erase.config(state=tkinter.DISABLED)

    def menu_complete_quit(self) -> None:
        """ as it says """
        global QUIT
        QUIT = True
        self.on_closing()

    def menu_load_ownerships(self) -> None:
        """ From menu File """

        filename = tkinter.filedialog.askopenfilename(  # type: ignore
            initialdir="./work",
            title="Sélectionner le fichier json avec les centres à charger",
            filetypes=(("json", "*.json"), ("all files", "*.*")))  # pylint: disable=no-member

        if not filename:
            return

        self.canvas.bag_centers.load_from_file(filename)
        self.canvas.refresh()

        msg = f"Chargement des centres depuis le fichier '{filename}'"
        self.scroll_message(msg, 'info')

    def menu_save_ownerships(self) -> None:
        """ From menu File """

        filehandle = tkinter.filedialog.asksaveasfile(
            initialdir="./work",
            title="Sélectionner le fichier json dans lequel sauvegarder les centres",
            filetypes=(("json", "*.json"), ("all files", "*.*")))

        if not filehandle:
            return

        self.canvas.bag_centers.save_to_file(filehandle)

    def menu_load_position(self) -> None:
        """ From menu File """

        filename = tkinter.filedialog.askopenfilename(  # type: ignore
            initialdir="./work",
            title="Sélectionner le fichier json avec la position à charger",
            filetypes=(("json", "*.json"), ("all files", "*.*")))  # pylint: disable=no-member

        if not filename:
            return

        self.canvas.bag_units.load_from_file(filename)
        self.canvas.refresh()

        msg = f"Chargement de la position depuis le fichier '{filename}'"
        self.scroll_message(msg, 'info')

    def menu_save_position(self) -> None:
        """ From menu File """

        filehandle = tkinter.filedialog.asksaveasfile(
            initialdir="./work",
            title="Sélectionner le fichier json dans lequel sauvegarder la position",
            filetypes=(("json", "*.json"), ("all files", "*.*")))

        if not filehandle:
            return

        self.canvas.bag_units.save_to_file(filehandle)

    def menu_load_orders(self) -> None:
        """ From menu File """

        filename = tkinter.filedialog.askopenfilename(  # type: ignore
            initialdir="./work",
            title="Sélectionner le fichier json avec les ordres à charger",
            filetypes=(("json", "*.json"), ("all files", "*.*")))  # pylint: disable=no-member

        if not filename:
            return

        self.canvas.bag_orders.load_from_file(filename)
        self.canvas.refresh()

        msg = f"Chargement des ordres depuis le fichier '{filename}'"
        self.scroll_message(msg, 'info')

    def menu_save_orders(self) -> None:
        """ From menu File """

        filehandle = tkinter.filedialog.asksaveasfile(
            initialdir="./work",
            title="Sélectionner le fichier json dans lequel sauvegarder les ordres",
            filetypes=(("json", "*.json"), ("all files", "*.*")))

        if not filehandle:
            return

        self.canvas.bag_orders.save_to_file(filehandle)

    def scroll_message(self, msg: str, level: str = 'info') -> None:
        """ service to add a message in scroll message """

        date_now = datetime.datetime.now()
        date_desc = date_now.strftime('%Y-%m-%d %H:%M:%S')
        self.scrolled_log.configure(state=tkinter.NORMAL)
        self.scrolled_log.insert(tkinter.END, f"{date_desc} : {msg}\n", level)
        self.scrolled_log.see(tkinter.END)
        self.scrolled_log.configure(state=tkinter.DISABLED)

        self.button_erase.config(state=tkinter.NORMAL)

    def on_closing(self) -> None:
        """ User closed window """

        self.master.quit()  # type: ignore
        sys.exit(0)


def main() -> None:
    """ main """

    data.load_servers_config()

    x_pos, y_pos = 0, 0

    while True:

        root = tkinter.Tk()

        root.geometry(f"+{x_pos}+{y_pos}")
        root.resizable(False, False)

        # font for all widgets
        root.option_add("*Font", f"{font.FONT_USED} {font.FONT_SIZE}")

        # font for tabs too
        style = tkinter.ttk.Style()
        style.configure('TNotebook.Tab', font=(font.FONT_USED, font.FONT_SIZE))

        # use description of first register as overall title
        window_name = "Démonstrateur client IHM jeu - projet ANJD (Diplomatie)"

        root.title(window_name)

        app = Application(master=root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()

        # remember where window is to put new one same place
        x_pos, y_pos = root.winfo_x(), root.winfo_y()  # type: ignore

        del app
        root.destroy()

        if QUIT:
            break


if __name__ == "__main__":
    main()
