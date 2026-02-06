#!/usr/bin/env python3


"""
Justs sends plenty of emails
"""

import typing
import argparse
import configparser
import datetime
import os
import sys
import time
import smtplib
import locale

import flask
import flask_mail  # type: ignore


INTERVAL = 5

# mailing suject
SUBJECT = "Convocation pour l'Assemblée Générale de l'Association des Joueurs Francophones de Diplomacy"

# mailing body
BODY = """
Cher joueur de Diplomacy,

Bonjour, nous vous proposons de vous retrouver le samedi 21 février pour notre assemblée générale annuelle à 15h sur Discord.

L'ordre du jour est le suivant :

    1) Présentation des actions menées et soutenues par l'AFJD en 2025,
    2) Présentation des comptes,
    3) Autres questions posées par les participants,
    4) Election du nouveau conseil d'administration.

La réunion se tiendra dans le salon vocal de Discord.

Lien pour assister à cette Assemblée Générale :
    https://discord.gg/mUWes7yEqR

C'est aussi le moment de l'adhésion annuelle pour 2026 qui nous permet notamment de financer les serveurs et soutenir des tournois.
Le montant minimum est de 10€ mais si vous pouvez mettre plus cela nous aiderait !

Lien pour cotiser pour 2026:
    https://www.helloasso.com/associations/association-francophone-des-joueurs-de-diplomacy/adhesions/adhesion-2026

Venez nombreux!

Ludiquement
Jérémie
Secrétaire de l'Association
"""

# mailing official sender
NAME_SENDER = "Lettre d'information de la part de l'A.f.J.D. (Diplomania)'"
MAIL_SENDER = "afjdiplo_server_noreply@diplomania2.fr"

SENDER = f"{NAME_SENDER} <{MAIL_SENDER}>"

# mailing real sender
REPLY_TO = "jeremie.lefrancois@gmail.com"

# list of attached files (must be PDF)
PDF_ATT_FILES: typing.List[str] = []

MAILER = None

APP = flask.Flask(__name__)


# In French please
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')


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

        assert APP.config['MAIL_USERNAME'] == MAIL_SENDER, "Use from same as sender to avoid being tagged as spam"

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

    if not os.path.exists(victim_list_file):
        print(f"File '{victim_list_file}' does not seem to exist, please advise !", file=sys.stderr)
        sys.exit(-1)

    load_mail_config()

    assert APP is not None

    with APP.app_context():

        already_spammed = set()
        failed_to_spam = set()
        start_time = datetime.datetime.now()

        with open(victim_list_file, encoding='utf-8') as filepointer:

            victims = [ll.rstrip('\n').replace(' ', '').lower() for ll in filepointer if ll.rstrip('\n') and not ll.startswith("#")]
            nb_victims = len(victims)
            print(f"We have {nb_victims} victims... ")

            for rank, victim in enumerate(victims):

                print(f"{rank+1:4} spamming '{victim}'... ", end='')

                # check we do not send twice to same
                if victim in already_spammed:
                    print("=================== ALREADY SPAMMED!")
                    continue

                percent = round((rank + 1) / nb_victims * 100)

                try:
                    send_mail(victim)
                except smtplib.SMTPRecipientsRefused:
                    print("=================== FAILED!")
                    failed_to_spam.add(victim)
                else:
                    print(f"DONE! {percent}%")

                already_spammed.add(victim)

                if (rank + 1) % 10 == 0:
                    elapsed = (datetime.datetime.now() - start_time).total_seconds()
                    speed = elapsed / (rank + 1)
                    still = len(victims) - (rank + 1)
                    rest_time = datetime.timedelta(seconds=(still * speed))
                    eta = datetime.datetime.now() + rest_time
                    print(f"Estimated ETA : {eta.strftime('%Y-%m-%d %H:%M:%S')}")

                time.sleep(INTERVAL)

        if failed_to_spam:
            print("Failed to spam:")
            print(' '.join(failed_to_spam))


if __name__ == '__main__':
    main()
