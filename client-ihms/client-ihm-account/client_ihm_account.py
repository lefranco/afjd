#!/usr/bin/env python3

"""
an ihm based on tkinter
this is the main module
"""

import typing
import sys
import csv
import re
import configparser
import collections

import tkinter
import tkinter.ttk
import tkinter.messagebox
import tkinter.filedialog
import tkinter.scrolledtext  # type: ignore

import requests

import font

SESSION = requests.Session()

HELP_FILE = "./help/help_content.txt"

COLOR_SCROLLED_INFO = 'Black'
COLOR_SCROLLED_WARNING = 'Orange'
COLOR_SCROLLED_ERROR = 'Red'

COLOR_INFO = "Blue"
COLOR_WARNING = 'Purple'

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

# for checking input
EMAIL_PATTERN = r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$'
MAX_LEN_PSEUDO = 12

COUNTRY_CODE_DEFAULT = 66  # France
TIME_ZONE_CODE_DEFAULT = 14  # Paris


class ConfigFile:
    """    Just reads an ini file   """

    def __init__(self, filename: str) -> None:
        self._config = configparser.ConfigParser(inline_comment_prefixes='#',    # do not accept ';'
                                                 empty_lines_in_values=False,    # as it says
                                                 interpolation=None)             # do not use variables

        assert self._config.read(filename, encoding='utf-8'), f"Missing ini file named {filename}"

    def section(self, section_name: str) -> configparser.SectionProxy:
        """ Accesses a section of a config file  """
        assert self._config.has_section(section_name), "Missing section in ini file"
        return self._config[section_name]

    def section_list(self) -> typing.List[str]:
        """ Accesses the list of sections of a config file  """
        return self._config.sections()


SERVER_CONFIG: typing.Dict[str, typing.Dict[str, typing.Any]] = collections.defaultdict(dict)


def load_servers_config() -> None:
    """ read servers config """

    global SERVER_CONFIG

    servers_config = ConfigFile('./config/servers.ini')
    for server in servers_config.section_list():
        server_data = servers_config.section(server)
        SERVER_CONFIG[server]['HOST'] = server_data['HOST']
        SERVER_CONFIG[server]['PORT'] = int(server_data['PORT'])


class Application(tkinter.Frame):
    """ Tkinter application """

    def __init__(self, master: tkinter.Tk):

        # standard stuff
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.grid()

        # identification data to send to server
        self.login_var = tkinter.StringVar()
        self.old_password_var = tkinter.StringVar()
        self.new_password_var = tkinter.StringVar()
        self.new_password_repeated_var = tkinter.StringVar()
        self.email_var = tkinter.StringVar()
        self.email_confirmed_var = tkinter.IntVar()
        self.email_confirmation_code_var = tkinter.StringVar()
        self.telephone_var = tkinter.StringVar()
        self.replace_var = tkinter.IntVar()
        self.family_name_var = tkinter.StringVar()
        self.first_name_var = tkinter.StringVar()

        # actual creation of widgets
        self.create_widgets(self)

    def create_widgets(self, main_frame: tkinter.Frame) -> None:
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
            version_information = "Cette beta version est très incomplète !"
            tkinter.messagebox.showinfo("A propos", str(version_information))

        menu_bar = tkinter.Menu(main_frame)
        menu_file = tkinter.Menu(menu_bar, tearoff=0)

        menu_file.add_separator()  # type: ignore

        menu_file.add_command(label="Recommencer", command=self.menu_restart)  # type: ignore
        menu_file.add_command(label="Sortie", command=self.on_closing)  # type: ignore
        menu_bar.add_cascade(label="Fichier", menu=menu_file)  # type: ignore

        menu_help = tkinter.Menu(menu_bar, tearoff=0)
        menu_help.add_command(label="Un peu d'aide", command=some_help)  # type: ignore
        menu_help.add_command(label="A propos...", command=about)  # type: ignore

        menu_bar.add_cascade(label="Aide", menu=menu_help)  # type: ignore

        self.master.configure(menu=menu_bar)

        frame_title = tkinter.Frame(main_frame)
        frame_title.grid(row=1, column=1, sticky='we')

        # a logo
        photo_diplo = tkinter.PhotoImage(file="./static/logo_diplo.png")
        label_photo = tkinter.Label(frame_title, image=photo_diplo, compound='top')
        label_photo.image = photo_diplo  # type: ignore # keep reference
        label_photo.grid(row=1, column=1, sticky='w')

        # ENTRY
        paned_up = tkinter.PanedWindow(main_frame)
        paned_up.grid(row=1, column=1)

        # Buttons =======================
        frame_buttons = tkinter.LabelFrame(paned_up, text="Entrée")
        paned_up.add(frame_buttons)  # type: ignore

        # button
        self.button_new = tkinter.Button(frame_buttons, text="Créer un nouveau compte")
        self.button_new.config(state=tkinter.ACTIVE)
        self.button_new.bind("<Button-1>", self.callback_new)
        self.button_new.grid(row=20, column=1)

        # button
        self.button_already = tkinter.Button(frame_buttons, text="Modifier, confirmer ou supprimer un compte existant")
        self.button_already.config(state=tkinter.ACTIVE)
        self.button_already.bind("<Button-1>", self.callback_already)
        self.button_already.grid(row=20, column=2)

        # EDITION
        paned_middle = tkinter.PanedWindow(main_frame, orient=tkinter.HORIZONTAL)
        paned_middle.grid(row=2, column=1)

        # Identification =======================
        frame_identification = tkinter.LabelFrame(paned_middle, text="Informations d'identification")
        paned_middle.add(frame_identification)  # type: ignore

        # login field
        label_login = tkinter.Label(frame_identification, text="Login (pseudo) (**) -->")
        label_login.grid(row=1, column=1, sticky='w')
        self.entry_login_input = tkinter.Entry(frame_identification, textvariable=self.login_var, width=MAX_LEN_PSEUDO)
        self.entry_login_input.grid(row=1, column=2, sticky='w')
        self.entry_login_input.config(state=tkinter.DISABLED)

        # put separator
        label_separator = tkinter.Label(frame_identification, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=2, column=1, sticky='w')

        # old password field
        self.label_old_password = tkinter.Label(frame_identification, text="Mot de passe -->")
        self.label_old_password.grid(row=3, column=1, sticky='w')
        self.entry_old_password_input = tkinter.Entry(frame_identification, show="*", textvariable=self.old_password_var)
        self.entry_old_password_input.grid(row=3, column=2, sticky='w')
        self.entry_old_password_input.config(state=tkinter.DISABLED)

        # put separator
        label_separator = tkinter.Label(frame_identification, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=4, column=1, sticky='w')

        # new password field
        label_new_password = tkinter.Label(frame_identification, text="Nouveau mot de passe -->")
        label_new_password.grid(row=5, column=1, sticky='w')
        self.entry_new_password_input = tkinter.Entry(frame_identification, show="*", textvariable=self.new_password_var)
        self.entry_new_password_input.grid(row=5, column=2, sticky='w')
        self.entry_new_password_input.config(state=tkinter.DISABLED)

        # put separator
        label_separator = tkinter.Label(frame_identification, text=" " * SEPARATOR_SIZE)
        label_separator.grid(row=6, column=1, sticky='w')

        # new password repeated field
        self.label_new_password_repeated = tkinter.Label(frame_identification, text="Nouveau mot de passe répété -->")
        self.label_new_password_repeated.grid(row=7, column=1, sticky='w')
        self.entry_new_password_repeated_input = tkinter.Entry(frame_identification, show="*", textvariable=self.new_password_repeated_var)
        self.entry_new_password_repeated_input.grid(row=7, column=2, sticky='w')
        self.entry_new_password_repeated_input.config(state=tkinter.DISABLED)

        # Communication =======================
        frame_communication = tkinter.LabelFrame(paned_middle, text="Informations de communication")
        paned_middle.add(frame_communication)  # type: ignore

        # email field
        label_email = tkinter.Label(frame_communication, text="Adresse email (*) -->")
        label_email.grid(row=5, column=1, sticky='w')
        self.entry_email_input = tkinter.Entry(frame_communication, textvariable=self.email_var, width=30)
        self.entry_email_input.grid(row=5, column=2, sticky='w')
        self.entry_email_input.config(state=tkinter.DISABLED)

        # email confirmed
        label_email_confirmed_desc = tkinter.Label(frame_communication, text="Adresse email confirmée ? --> ")
        label_email_confirmed_desc.grid(row=6, column=1, sticky='w')

        self.checkbutton_email_confirmed_fake_input = tkinter.Checkbutton(frame_communication, variable=self.email_confirmed_var)
        self.checkbutton_email_confirmed_fake_input.grid(row=6, column=2, sticky='w')
        self.checkbutton_email_confirmed_fake_input.config(state=tkinter.DISABLED)

        # email confirmation field
        label_email = tkinter.Label(frame_communication, text="Code vérification de l'adresse email -->")
        label_email.grid(row=7, column=1, sticky='w')
        self.entry_email_confirmation_code_input = tkinter.Entry(frame_communication, textvariable=self.email_confirmation_code_var, width=4)
        self.entry_email_confirmation_code_input.grid(row=7, column=2, sticky='w')
        self.entry_email_confirmation_code_input.config(state=tkinter.DISABLED)

        # phone field
        label_phone = tkinter.Label(frame_communication, text="Numéro de téléphone (*) -->")
        label_phone.grid(row=8, column=1, sticky='w')
        self.entry_phone_input = tkinter.Entry(frame_communication, textvariable=self.telephone_var, width=15)
        self.entry_phone_input.grid(row=8, column=2, sticky='w')
        self.entry_phone_input.config(state=tkinter.DISABLED)

        # Game =======================
        frame_game = tkinter.LabelFrame(paned_middle, text="Informations de jeu")
        paned_middle.add(frame_game)  # type: ignore

        # family name field
        label_family_name = tkinter.Label(frame_game, text="D'accord pour remplacer (**) -->")
        label_family_name.grid(row=1, column=1, sticky='w')
        self.checkbutton_replace = tkinter.Checkbutton(frame_game, variable=self.replace_var)
        self.checkbutton_replace.grid(row=1, column=2, sticky='w')
        self.checkbutton_replace.config(state=tkinter.DISABLED)

        # Personal =======================
        frame_personal = tkinter.LabelFrame(paned_middle, text="Informations personnelles")
        paned_middle.add(frame_personal)  # type: ignore

        # family name field
        label_family_name = tkinter.Label(frame_personal, text="Nom de famille (*) -->")
        label_family_name.grid(row=1, column=1, sticky='w')
        self.entry_family_name_input = tkinter.Entry(frame_personal, textvariable=self.family_name_var, width=30)
        self.entry_family_name_input.grid(row=1, column=2, sticky='w')
        self.entry_family_name_input.config(state=tkinter.DISABLED)

        # first name field
        label_first_name = tkinter.Label(frame_personal, text="Prénom (*) -->")
        label_first_name.grid(row=2, column=1, sticky='w')
        self.entry_first_name_input = tkinter.Entry(frame_personal, textvariable=self.first_name_var, width=20)
        self.entry_first_name_input.grid(row=2, column=2, sticky='w')
        self.entry_first_name_input.config(state=tkinter.DISABLED)

        # country field
        label_country = tkinter.Label(frame_personal, text="Pays (**) -->")
        label_country.grid(row=3, column=1, sticky='w')

        self.country_code_list: typing.List[str] = list()
        self.listbox_country_input = tkinter.Listbox(frame_personal, width=40, exportselection=0)
        with open("./static/country_list.csv", newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for country_code, country_name in reader:
                self.country_code_list.append(country_code)
                self.listbox_country_input.insert(tkinter.END, country_name)  # type: ignore
        self.listbox_country_input.grid(row=3, column=2, sticky='w')
        self.listbox_country_input.selection_set(COUNTRY_CODE_DEFAULT)
        self.listbox_country_input.config(state=tkinter.DISABLED)

        # time zone field
        label_time_zone = tkinter.Label(frame_personal, text="Fuseau horaire (**) -->")
        label_time_zone.grid(row=4, column=1, sticky='w')

        self.timezone_code_list: typing.List[str] = list()
        self.listbox_timezone_input = tkinter.Listbox(frame_personal, width=80, exportselection=0)
        with open("./static/timezone_list.csv", newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for timezone_code, timezone_cities in reader:
                self.timezone_code_list.append(timezone_code)
                self.listbox_timezone_input.insert(tkinter.END, f"{timezone_code} ({timezone_cities})")  # type: ignore
        self.listbox_timezone_input.grid(row=4, column=2, sticky='w')
        self.listbox_timezone_input.selection_set(TIME_ZONE_CODE_DEFAULT)
        self.listbox_timezone_input.config(state=tkinter.DISABLED)

        # INFO
        paned_before_down = tkinter.PanedWindow(main_frame)
        paned_before_down.grid(row=3, column=1)
        frame_info = tkinter.LabelFrame(paned_before_down, text="Informations complémentaires")
        paned_before_down.add(frame_info)  # type: ignore
        label_info_1 = tkinter.Label(frame_info, text="(*) privé (non visible sur le site)")
        label_info_1.grid(row=1, column=1, sticky='w')
        label_info_2 = tkinter.Label(frame_info, text="(**) public (visible sur le site)")
        label_info_2.grid(row=2, column=1, sticky='w')

        # ACTION
        paned_down = tkinter.PanedWindow(main_frame)
        paned_down.grid(row=4, column=1)

        # Buttons =======================
        frame_buttons = tkinter.LabelFrame(paned_down, text="Action")
        paned_down.add(frame_buttons)  # type: ignore

        # button
        self.button_create_account = tkinter.Button(frame_buttons, text="Créer le compte avec ces informations")
        self.button_create_account.config(state=tkinter.DISABLED)
        self.button_create_account.bind("<Button-1>", self.callback_create_account)
        self.button_create_account.grid(row=20, column=1)

        # button
        self.button_login_account = tkinter.Button(frame_buttons, text="M'identifer sur le compte")
        self.button_login_account.config(state=tkinter.DISABLED)
        self.button_login_account.bind("<Button-1>", self.callback_login_account)
        self.button_login_account.grid(row=20, column=2)

        # button
        self.button_validate_account = tkinter.Button(frame_buttons, text="Valider mon adresse mail avec le code")
        self.button_validate_account.config(state=tkinter.DISABLED)
        self.button_validate_account.bind("<Button-1>", self.callback_validate_account)
        self.button_validate_account.grid(row=20, column=3)

        # button
        self.button_edit_account = tkinter.Button(frame_buttons, text="Mettre à jour le compte avec ces informations")
        self.button_edit_account.config(state=tkinter.DISABLED)
        self.button_edit_account.bind("<Button-1>", self.callback_edit_account)
        self.button_edit_account.grid(row=20, column=4)

        # button
        self.button_change_password = tkinter.Button(frame_buttons, text="Changer de mot de passe")
        self.button_change_password.config(state=tkinter.DISABLED)
        self.button_change_password.bind("<Button-1>", self.callback_change_password)
        self.button_change_password.grid(row=20, column=5)

        # button
        self.button_delete_account = tkinter.Button(frame_buttons, text="Supprimer le compte")
        self.button_delete_account.config(state=tkinter.DISABLED)
        self.button_delete_account.bind("<Button-1>", self.callback_suppress_account)
        self.button_delete_account.grid(row=20, column=6)

    def reload_from_server(self) -> typing.Tuple[bool, str]:
        """ Reloads everything from server to here """

        pseudo = self.login_var.get()  # type: ignore
        host = SERVER_CONFIG['PLAYER']['HOST']
        port = SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"
        # present the authentication token (we are reading content of an account)
        req_result = SESSION.get(url, headers={'access_token': JWT_TOKEN})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            return False, message

        json_dict = req_result.json()

        self.email_var.set(json_dict['email'])  # type: ignore
        self.email_confirmed_var.set(json_dict['email_confirmed'])  # type: ignore

        if not self.email_confirmed_var.get():  # type: ignore
            self.button_validate_account.config(state=tkinter.NORMAL)
            self.entry_email_confirmation_code_input.config(state=tkinter.NORMAL)
        else:
            self.button_validate_account.config(state=tkinter.DISABLED)
            self.entry_email_confirmation_code_input.config(state=tkinter.DISABLED)

        self.telephone_var.set(json_dict['telephone'])  # type: ignore
        self.replace_var.set(json_dict['replace'])  # type: ignore
        self.family_name_var.set(json_dict['family_name'])  # type: ignore
        self.first_name_var.set(json_dict['first_name'])  # type: ignore

        country = json_dict['country']
        country_code = self.country_code_list.index(country)

        previous_state = self.listbox_country_input.cget("state")  # type: ignore
        self.listbox_country_input.config(state=tkinter.NORMAL)
        self.listbox_country_input.selection_clear(0, tkinter.END)
        self.listbox_country_input.selection_set(country_code)
        self.listbox_country_input.see(country_code)  # type: ignore
        self.listbox_country_input.config(state=previous_state)

        time_zone = json_dict['time_zone']
        time_zone_code = self.timezone_code_list.index(time_zone)

        previous_state = self.listbox_timezone_input.cget("state")  # type: ignore
        self.listbox_timezone_input.config(state=tkinter.NORMAL)
        self.listbox_timezone_input.selection_clear(0, tkinter.END)
        self.listbox_timezone_input.selection_set(time_zone_code)
        self.listbox_timezone_input.see(time_zone_code)  # type: ignore
        self.listbox_timezone_input.config(state=previous_state)

        return True, ""

    def upload_on_server(self, new: bool, password_change: bool) -> typing.Tuple[bool, str]:
        """ Uploads everything here to server """

        country_code, = self.listbox_country_input.curselection()  # type: ignore
        country = self.country_code_list[country_code]

        time_zone_code, = self.listbox_timezone_input.curselection()  # type: ignore
        time_zone = self.timezone_code_list[time_zone_code]

        pseudo = self.login_var.get()  # type: ignore

        json_dict = {
            'pseudo': pseudo,
            'password': "",
            'email': self.email_var.get(),  # type: ignore
            'email_confirmed': self.email_confirmed_var.get(),  # type: ignore
            'telephone': self.telephone_var.get(),  # type: ignore
            'replace': self.replace_var.get(),  # type: ignore
            'family_name': self.family_name_var.get(),  # type: ignore
            'first_name': self.first_name_var.get(),  # type: ignore
            'country': country,
            'time_zone': time_zone,
        }

        if new or password_change:
            json_dict['password'] = self.new_password_var.get()  # type: ignore

        if new:
            # do not present the authentication token  (we are creating an account)
            host = SERVER_CONFIG['PLAYER']['HOST']
            port = SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/players"
            req_result = SESSION.post(url, data=json_dict)
            if req_result.status_code != 201:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                return False, message
        else:
            # present the authentication token  (we are updating an account)
            host = SERVER_CONFIG['PLAYER']['HOST']
            port = SERVER_CONFIG['PLAYER']['PORT']
            url = f"{host}:{port}/players/{pseudo}"
            req_result = SESSION.put(url, data=json_dict, headers={'access_token': JWT_TOKEN})
            if req_result.status_code != 200:
                print(f"ERROR from server  : {req_result.text}")
                message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
                return False, message

        return True, ""

    def callback_new(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self.entry_login_input.config(state=tkinter.NORMAL)
        self.entry_new_password_input.config(state=tkinter.NORMAL)
        self.entry_new_password_repeated_input.config(state=tkinter.NORMAL)
        self.entry_email_input.config(state=tkinter.NORMAL)
        self.entry_phone_input.config(state=tkinter.NORMAL)
        self.checkbutton_replace.config(state=tkinter.NORMAL)
        self.entry_family_name_input.config(state=tkinter.NORMAL)
        self.entry_first_name_input.config(state=tkinter.NORMAL)
        self.listbox_country_input.config(state=tkinter.NORMAL)
        self.listbox_timezone_input.config(state=tkinter.NORMAL)

        self.button_create_account.config(state=tkinter.ACTIVE)

        self.button_new.config(state=tkinter.DISABLED)
        self.button_already.config(state=tkinter.DISABLED)

    def callback_create_account(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        pseudo = self.login_var.get()  # type: ignore
        if not pseudo:
            tkinter.messagebox.showerror("KO", "Vous n'avez pas indiqué de pseudo")
            return
        if len(pseudo) > MAX_LEN_PSEUDO:
            tkinter.messagebox.showerror("KO", "Votre pseudo est trop long")
            return
        email = self.email_var.get()  # type: ignore
        if not re.match(EMAIL_PATTERN, email):
            tkinter.messagebox.showerror("KO", "Votre adresse email est incorrecte")
            return

        password = self.new_password_var.get()  # type: ignore
        if not password:
            tkinter.messagebox.showerror("KO", "Vous n'avez pas indiqué de mot de passe")
            return

        password_repeated = self.new_password_repeated_var.get()  # type: ignore
        if not password_repeated:
            tkinter.messagebox.showerror("KO", "Vous n'avez pas indiqué de mot de passe répété")
            return

        if password_repeated != password:
            tkinter.messagebox.showerror("KO", "Vos deux mots de passe sont différents")
            return

        status, message = self.upload_on_server(True, False)
        if not status:
            tkinter.messagebox.showerror("KO", f"Votre compte n'a pas été créé : {message}")
            return

        tkinter.messagebox.showinfo("OK", "Votre compte a été créé")

    def callback_already(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        self.entry_login_input.config(state=tkinter.NORMAL)
        self.entry_old_password_input.config(state=tkinter.NORMAL)

        self.button_login_account.config(state=tkinter.ACTIVE)

        self.button_new.config(state=tkinter.DISABLED)
        self.button_already.config(state=tkinter.DISABLED)

    def callback_login_account(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        # Now I get token
        pseudo = self.login_var.get()  # type: ignore
        password = self.old_password_var.get()  # type: ignore

        host = SERVER_CONFIG['USER']['HOST']
        port = SERVER_CONFIG['USER']['PORT']
        url = f"{host}:{port}/login_user"
        req_result = SESSION.post(url, json={'user_name': pseudo, 'password': password})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showerror("KO", f"Il y a eu un problème : {message}")
            return

        # very important : extract token for authentication
        json_dict = req_result.json()
        global JWT_TOKEN
        JWT_TOKEN = json_dict['access_token']

        status, message = self.reload_from_server()
        if not status:
            tkinter.messagebox.showerror("KO", f"Il y a eu un problème : {message}")
            return

        self.entry_old_password_input.config(state=tkinter.DISABLED)
        self.entry_new_password_input.config(state=tkinter.NORMAL)
        self.entry_new_password_repeated_input.config(state=tkinter.NORMAL)

        # erase password content
        self.old_password_var.set("")  # type: ignore

        self.entry_email_input.config(state=tkinter.NORMAL)
        self.entry_phone_input.config(state=tkinter.NORMAL)
        self.checkbutton_replace.config(state=tkinter.NORMAL)
        self.entry_family_name_input.config(state=tkinter.NORMAL)
        self.entry_first_name_input.config(state=tkinter.NORMAL)
        self.listbox_country_input.config(state=tkinter.NORMAL)
        self.listbox_timezone_input.config(state=tkinter.NORMAL)

        self.button_login_account.config(state=tkinter.DISABLED)
        self.button_edit_account.config(state=tkinter.ACTIVE)
        self.button_change_password.config(state=tkinter.ACTIVE)
        self.button_delete_account.config(state=tkinter.ACTIVE)

        self.button_new.config(state=tkinter.DISABLED)
        self.button_already.config(state=tkinter.DISABLED)

        tkinter.messagebox.showinfo("OK", "Identification réussie !")

    def callback_validate_account(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        pseudo = self.login_var.get()  # type: ignore

        code_str = self.email_confirmation_code_var.get()  # type: ignore
        try:
            code = int(code_str)
        except:  # noqa: E722 pylint: disable=bare-except
            tkinter.messagebox.showerror("KO", "Le code de confirmation doit être un entier")
            return

        if not 1000 <= code <= 9999:
            tkinter.messagebox.showerror("KO", "Le code de confirmation doit être sur 4 chiffres")
            return

        # present the email validation code
        host = SERVER_CONFIG['PLAYER']['HOST']
        port = SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/emails"
        req_result = SESSION.post(url, json={'pseudo': pseudo, 'code': code})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showwarning("KO", f"Il y a eu un problème : {message}")
            return

        status, message = self.reload_from_server()
        if not status:
            tkinter.messagebox.showerror("!?", f"Votre adresse email a été validée mais il y a un erreur : {message}")
            return

        self.email_confirmation_code_var.set("")  # type: ignore
        self.entry_email_confirmation_code_input.config(state=tkinter.DISABLED)

        tkinter.messagebox.showinfo("OK", "Félicitations, votre adresse email est validée !")

    def callback_edit_account(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        email = self.email_var.get()  # type: ignore
        if not re.match(EMAIL_PATTERN, email):
            tkinter.messagebox.showerror("KO", "Votre adresse email est incorrecte")
            return

        status, message = self.upload_on_server(False, False)
        if not status:
            tkinter.messagebox.showerror("KO", f"Votre compte n'a pas été mis à jour : {message}")
            return

        status, message = self.reload_from_server()
        if not status:
            tkinter.messagebox.showerror("!?", f"Votre compte a été mis à jour mais il y a un erreur : {message}")
            return

        tkinter.messagebox.showinfo("OK", "Votre compte a été mis à jour")

    def callback_change_password(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        pseudo = self.login_var.get()  # type: ignore
        if not pseudo:
            tkinter.messagebox.showerror("KO", "Vous n'avez pas indiqué de pseudo")
            return
        if len(pseudo) > MAX_LEN_PSEUDO:
            tkinter.messagebox.showerror("KO", "Votre pseudo est trop long")
            return

        password = self.new_password_var.get()  # type: ignore
        if not password:
            tkinter.messagebox.showerror("KO", "Vous n'avez pas indiqué de mot de passe")
            return

        password_repeated = self.new_password_repeated_var.get()  # type: ignore
        if not password_repeated:
            tkinter.messagebox.showerror("KO", "Vous n'avez pas indiqué de mot de passe répété")
            return

        if password_repeated != password:
            tkinter.messagebox.showerror("KO", "Vos deux mots de passe sont différents")
            return

        status, message = self.upload_on_server(False, True)
        if not status:
            tkinter.messagebox.showerror("KO", f"Votre mot de passe n'a pas été mis à jour : {message}")
            return

        tkinter.messagebox.showinfo("OK", "Votre mot de passe a été mis à jour")

    def callback_suppress_account(self, event: typing.Any) -> None:
        """ callback button pushed """

        # button disabled
        if str(event.widget['state']) == 'disabled':
            return

        pseudo = self.login_var.get()  # type: ignore
        if len(pseudo) > MAX_LEN_PSEUDO:
            tkinter.messagebox.showerror("KO", f"Votre pseudo est trop long : {len(pseudo)}")
            return

        if not tkinter.messagebox.askyesno("Attention", "Confimez vous la suppression du compte ?"):
            return

        # present the authentication token (we are suppressing an account)
        host = SERVER_CONFIG['PLAYER']['HOST']
        port = SERVER_CONFIG['PLAYER']['PORT']
        url = f"{host}:{port}/players/{pseudo}"
        req_result = SESSION.delete(url, headers={'access_token': JWT_TOKEN})
        if req_result.status_code != 200:
            print(f"ERROR from server  : {req_result.text}")
            message = req_result.json()['msg'] if 'msg' in req_result.json() else "???"
            tkinter.messagebox.showwarning("KO", f"Il y a eu un problème : {message}")
            return

        self.entry_new_password_input.config(state=tkinter.DISABLED)
        self.entry_login_input.config(state=tkinter.DISABLED)
        self.entry_new_password_repeated_input.config(state=tkinter.DISABLED)
        self.entry_old_password_input.config(state=tkinter.DISABLED)
        self.entry_email_input.config(state=tkinter.DISABLED)
        self.entry_phone_input.config(state=tkinter.DISABLED)
        self.checkbutton_replace.config(state=tkinter.DISABLED)
        self.entry_family_name_input.config(state=tkinter.DISABLED)
        self.entry_first_name_input.config(state=tkinter.DISABLED)
        self.listbox_country_input.config(state=tkinter.DISABLED)
        self.listbox_timezone_input.config(state=tkinter.DISABLED)

        self.entry_email_confirmation_code_input.config(state=tkinter.DISABLED)

        self.button_edit_account.config(state=tkinter.DISABLED)
        self.button_change_password.config(state=tkinter.DISABLED)
        self.button_delete_account.config(state=tkinter.DISABLED)

        tkinter.messagebox.showinfo("OK", "Votre compte a été supprimé")

    def menu_complete_quit(self) -> None:
        """ as it says """
        global QUIT
        QUIT = True
        self.on_closing()

    def menu_restart(self) -> None:
        """ From menu change context """

        # quit application
        self.master.quit()  # type: ignore

    def on_closing(self) -> None:
        """ User closed window """

        self.master.quit()  # type: ignore
        sys.exit(0)


def main() -> None:
    """ main """

    load_servers_config()

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
        window_name = "Démonstrateur client IHM création de compte - projet AJDS (Diplomatie)"

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
