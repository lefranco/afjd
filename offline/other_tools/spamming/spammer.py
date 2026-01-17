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
SUBJECT = "Diplomania : la résurrection"

# mailing body
BODY = """
Cher joueur de Diplomacy,

** Interruption de service **

Le site qui nous permet de jouer accumulant les frais d'hébergement (un composant back end et un composant front end) il a été envisagé de tout déplacer sur des ordinateurs de la société d'un membre de l'association.
Au cours de la copie une mauvaise manipulation a entrainé le blocage de tous les serveurs back end. Identifier le problème a pris du temps, et il n'a jamais été possible de rétablir la situation malgré les efforts de plusieurs personnes.
Le problème a donc été résolu en réalisant une nouvelle installation, à partir de rien, plus simple, sur un nouveau back end.
Ce, avec une formule d'hébergement beaucoup moins chère mais équivalente en terme de performances.

=> Le site est rétabli hier Mercredi 5 Novembre.

A noter : à ce jour le front end reste à migrer également, cela sera fait dans le jours qui suivent.
En attendant le service est rétabli et nous présentons nos excuses pour la gène occasionnée.

Nous pouvons reprendre nos parties !

** Invitations **

Sur le face à face, nous en profitons pour vous inviter à deux événements dans un futur immédiat :

========== OPEN DE PARIS ================

Open international de Paris / Championnat d'Île-de-France 2025
Tournoi principal de la région Île-de-France pour 2025. Il s'agit d'un tournoi mixte de négociation/blitz (speedboat).
L'Open de Paris est une étape du Grand Prix européen 2025 et du Tour de France 2024/2025.

Organisation
  Organisateur : Lei Saarlainen
  Assistant organisateur : Olivier Prigent
  Directeur du tournoi : Olivier Prigent
  Assistant directeur du tournoi : Emmanuel du Pontavice

Lieu
  France Île-de-France Paris
  Hôtel La Louisianne, 60 rue de Seine

Structure du tournoi
  6 rondes : 3 négociation, 3 speedboat
  Fin de l'année : 1907 (négociation) 1906 (speedboat)
  Système de scorage : C-Diplo Namur
  Agrégation des résultats : 3 meilleurs résultats (Speedboat à 70 %)

Programme :
  Vendredi 5 décembre 20 h / Speedboat 1
  Vendredi 5 décembre 22 h / Speedboat 2
  Samedi 6 décembre 10 h / Négociation 1
  Samedi 6 décembre 15H / Négociation 2
  Samedi 6 décembre 20H Repas communautaire
  Dimanche 7 décembre 10H / Speedboat 3
  Dimanche 7 décembre 12H30 / Négociation 3
  Dimanche 7 décembre 16H30 / Remise des prix

Championnat de France Speedboat / Blitz Live
  Les 3 rondes Speedboat font partie du Championnat de France Speedboat.
  Les autres rondes seront jouées sur le serveur Diplomania au cours de l'année à venir jusqu'au prochain CDF à Paris

Les résultats seront agrégés comme suit : addition de tous les scores/parties + 3

Ligue d'Ile de France
  Les 3 manches de négociation feront partie de la Ligue d'Ile de France
  Les autres manches se dérouleront en Ile de France au cours de l'année à venir jusqu'au prochain CDF à Paris

Les résultats seront agrégés comme suit : addition de tous les scores/parties+3

Contact pour question ou préinscription : lei saarlainen sur Discord ou par mail leisaarlainen@gmail.com

(Lei)

===  CHAMPIONNAT DE BRETAGNE  ==================

Ô diplomates, les vendredi 21 et samedi 22 novembre (donc dans moins de 3 semaines), j'organise des parties de ***Diplomatie*** à Rennes au resto-bar culturel La Reine de Cœur.

C'est le 4e championnat de Bretagne. C'est ouvert à tous, à vous joueurs expérimentés, à vous joueurs intermédiaires, à vous joueurs novices, y compris complets débutants. Toutes les parties (au nombre de trois) précédées d'une initiation de 30 à 45 minutes une heure avant le lancement du jeu. Suivre une initiation n'engage à rien, ni à jouer la partie qui suit ni les deux autres parties du week-end.

Lieu : La Reine de Cœur, 48 rue de Saint-Brieuc (près de l'Agro) dans l'ouest de Rennes.
Prix : une consommation obligatoire minimum par partie.

Horaires : vendredi soir de 20h à minuit (initiation à 19h), samedi après-midi de 14 à 18h (initiation à 13h) et samedi soir de 20h à minuit (initiation à 19h). Remise des prix à minuit et demi.

Possibilité de s'inscrire sur place jusqu'au dernier moment, les inscriptions à chaque partie sont indépendantes les unes des autres. + d'infos ou pré-inscription en me contactant par messagerie privée Discord ou par texto (06 89 14 64 06) ou https://tdfdiplo.fandom.com/fr/wiki/Règlement_du_championnat_de_Bretagne.

(Gabriel)

=============================================

Jérémie
Administrateur du site
https://diplomania2.fr
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
