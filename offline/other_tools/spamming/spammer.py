#!/usr/bin/env python3


"""
File : mailer.py

Justs sends an email
"""

import typing
import argparse
import configparser
import pathlib
import time
import smtplib

import flask
import flask_mail  # type: ignore


INTERVAL = 5

# mailing suject
SUBJECT = "2023 : Les dernières nouvelles de l'association diplomatie A.F.J.D !"

# mailing body
BODY = """
Bonjour.
Vous trouverez en pièces jointes le compte rendu de la dernière assemblée générale, ainsi que la lettre du diplomate, en vous souhaitant bonne lecture.
Si vous ne savez pas quoi faire ce week-end, pensez au championnat du monde francophone en face à face virtuel !
Bien amicalement.
Le bureau.
"""

# mailing official sender
SENDER = "afjd_serveur_jeu@diplomania-gen.fr"

# mailing real sender
REPLY_TO = "afjdiplo@gmail.com"

# list of attached files (must be PDF)
PDF_ATT_FILES = ['newletter_5.docx.pdf', 'AG_28_01_2023.pptx.pdf']


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


def load_mail_config() -> None:
    """ read mail config """

    mail_config = ConfigFile('./config/mail.ini')
    for mailer in mail_config.section_list():

        assert mailer == 'mail', "Section name is not 'mail' in mail configuration file"
        mail_data = mail_config.section(mailer)

        APP.config['MAIL_SERVER'] = mail_data['MAIL_SERVER']
        APP.config['MAIL_PORT'] = int(mail_data['MAIL_PORT'])
        APP.config['MAIL_USE_TLS'] = bool(int(mail_data['MAIL_USE_TLS']))
        APP.config['MAIL_USE_SSL'] = bool(int(mail_data['MAIL_USE_SSL']))
        APP.config['MAIL_USERNAME'] = mail_data['MAIL_USERNAME']
        APP.config['MAIL_PASSWORD'] = mail_data['MAIL_PASSWORD']

        assert APP.config['MAIL_USERNAME'] == SENDER, "Use from same as sender to avoid being tagged as spam"

    global MAILER
    MAILER = flask_mail.Mail(APP)


def send_mail(email_dest: str) -> None:
    """ send email """

    # make message
    msg = flask_mail.Message(SUBJECT, sender=SENDER, body=BODY, reply_to=REPLY_TO, recipients=[email_dest])

    assert APP is not None

    # add attachments
    for att_file in PDF_ATT_FILES:
        with APP.open_resource(att_file) as filepointer:
            msg.attach(att_file, 'application/pdf', filepointer.read())

    assert MAILER is not None

    # send
    MAILER.send(msg)


def main() -> None:
    """ main """

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--victims_file', required=True, help='file with emails of victims')
    args = parser.parse_args()

    victim_list_file = args.victims_file

    path = pathlib.Path(victim_list_file)
    assert path.exists(), f"Seems file '{victim_list_file}' does not exist"

    load_mail_config()

    assert APP is not None

    with APP.app_context():

        already_spammed = set()

        with open(victim_list_file, encoding='utf-8') as filepointer:
            for line in filepointer:
                line = line.rstrip('\n')
                if line and not line.startswith("#"):
                    dest = line
                    dest = dest.lower()  # otherwise rejected

                print(f"spamming '{dest}'... ", end='')

                # check we do not send twice to same
                if dest in already_spammed:
                    print("=================== ALREADY SPAMMED!")
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
