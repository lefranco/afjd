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

BATCH = 10

# mailing suject
SUBJECT = "Les cartes sont distribuées... où es-tu ?..."

# mailing body
BODY = """
Tu as rejoint les rangs de diplomania, mais ton état-major est désespérément vide. Pendant que tu hésites, d'autres sont déjà en train de redessiner les frontières et de sceller des pactes secrets.

Le monde ne va pas s'emparer tout seul, et tes futurs alliés (ou tes futurs rivaux) n'attendent que toi pour lancer les hostilités.

Ton plan de campagne pour aujourd'hui :
- Choisis ton terrain : Parcours la liste des parties en attente de joueurs. Voire des tournois, en variante ou en standard.
- Prends place : Inscris-toi dans une partie qui te botte.
- Négocie : Envoie ton premier message et fais comprendre aux autres que tu n'es pas là pour faire de la figuration.

Les parties avec de la place sont visbles depuis la page d'accueil.

Ne reste pas spectateur de l'Histoire alors que tu pourrais en être l'acteur principal. On se retrouve sur une partie ?

Bons plans et trahisons,

L'équipe de diplomania
Le Haut Commandement de https://diplomania2.fr
"""

# mailing official sender
NAME_SENDER = "Lettre d'information de la part de l'A.f.J.D. (Diplomania)"
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

        with open(victim_list_file, encoding='utf-8') as filepointer:

            victims = [ll.rstrip('\n').replace(' ', '').lower() for ll in filepointer if ll.rstrip('\n') and not ll.startswith("#")]
            nb_victims = len(victims)
            print(f"We have {nb_victims} victims... ")

            start_batch_time = datetime.datetime.now()
            
            for rank, victim in enumerate(victims, start=1):

                print(f"{rank:4} spamming '{victim}'... ", end='')

                # check we do not send twice to same
                if victim in already_spammed:
                    print("=================== ALREADY SPAMMED!")
                    continue

                percent = round(rank / nb_victims * 100)

                try:
                    send_mail(victim)
                except smtplib.SMTPRecipientsRefused:
                    print("=================== FAILED!")
                    failed_to_spam.add(victim)
                else:
                    print(f"DONE! {percent}%")

                already_spammed.add(victim)

                if rank % BATCH == 0:
                    elapsed = (datetime.datetime.now() - start_batch_time).total_seconds()
                    start_batch_time = datetime.datetime.now()
                    speed = elapsed / BATCH
                    still = len(victims) - rank
                    rest_time = datetime.timedelta(seconds=(still * speed))
                    eta = datetime.datetime.now() + rest_time
                    print(f"Estimated ETA : {eta.strftime('%Y-%m-%d %H:%M:%S')}")

                time.sleep(INTERVAL)

        if failed_to_spam:
            print("Failed to spam:")
            print(' '.join(failed_to_spam))


if __name__ == '__main__':
    main()
