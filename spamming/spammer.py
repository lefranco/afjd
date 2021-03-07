#!/usr/bin/env python3


"""
File : mailer.py

Justs sends an email
"""

import typing
import configparser
import sys
import pathlib
import time
import smtplib

import flask
import flask_mail  # type: ignore


INTERVAL = 2

SUBJECT = "2021 L'année pour jouer à Diplomacy"

SENDER = "jeremie.lefrancois@orange.fr"
#SENDER = "palpatine.darksedious@gmail.com"

BODY_FILE = "./body_NewsLetter2.html"

MAILER = None

APP = flask.Flask(__name__)

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

def load_mail_config(app: typing.Any) -> None:
    """ read mail config """

    mail_config = ConfigFile('./config/mail.ini')
    for mailer in mail_config.section_list():

        assert mailer == 'mail', "Section name is not 'mail' in mail configuration file"
        mail_data = mail_config.section(mailer)

        app.config['MAIL_SERVER'] = mail_data['MAIL_SERVER']
        app.config['MAIL_PORT'] = int(mail_data['MAIL_PORT'])
        app.config['MAIL_USE_TLS'] = bool(int(mail_data['MAIL_USE_TLS']))
        app.config['MAIL_USE_SSL'] = bool(int(mail_data['MAIL_USE_SSL']))
        app.config['MAIL_USERNAME'] = mail_data['MAIL_USERNAME']
        app.config['MAIL_PASSWORD'] = mail_data['MAIL_PASSWORD']

    global MAILER
    MAILER = flask_mail.Mail(app)


def send_mail(email_dest: str) -> None:
    """ send email """

    msg = flask_mail.Message(SUBJECT, sender=SENDER, recipients=[email_dest])

    # Body of message
    with open(BODY_FILE, 'r') as filepointer:
        # Create a text/plain message
        msg.html = filepointer.read()

    assert MAILER is not None
    MAILER.send(msg)


def main():

    # check arguments
    if len(sys.argv) != 2:
        print("Argument expected : <file with list of victims>")
        return

    victim_list_file = sys.argv[1]

    path = pathlib.Path(victim_list_file)
    if not path.exists():
        print(f"Seems file '{victim_list_file}' does not exist")
        return

    load_mail_config(APP)
    with APP.app_context():

        already_spammed = set()

        with open(victim_list_file) as filepointer:
            for line in filepointer:
                line = line.rstrip('\n')
                if line and not line.startswith("#"):
                    dest = line
                    dest = dest.lower() # otherwise rejected

                print(f"spamming '{dest}'... ", end='')

                # check we do not send twice to same
                if dest in already_spammed:
                    print("NO : Have already spammed that one !")
                    continue

                try:
                    send_mail(dest)
                except smtplib.SMTPRecipientsRefused:
                    print("=================== FAILED!")
                else:
                    print("DONE!")

                already_spammed.add(dest)

                time.sleep(INTERVAL)

if __name__ == '__main__':
    main()