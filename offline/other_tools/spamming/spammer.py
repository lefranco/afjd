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

SUBJECT = "Evénements du face-à-face à venir"

# Corps du message en HTML avec images inline
BODY_HTML = """
<html>
<body>
<h2>Événements du face-à-face à venir</h2>

<p>Deux tournois en face-à-face comptant pour le Tour de France cet été :</p>
<ul>
  <li><strong>Open de Paris</strong> 27-28 juin</li>
  <li><strong>Championnat de Bretagne</strong> 24-25 juillet</li>
</ul>

<p><strong>A noter :</strong> Le championnat de France aura lieu à Paris cet hiver 4-6 décembre...</p>

<h3>Open de Paris</h3>
<img src="cid:open_paris" alt="Open de Paris" style="max-width:100%;">

<h3>Championnat de Bretagne</h3>
<img src="cid:championnat_bretagne" alt="Championnat de Bretagne" style="max-width:100%;">

<p>L'équipe de diplomania<br>
Jérémie Lefrançois<br>
Administrateur<br>
<a href="https://diplomania2.fr">https://diplomania2.fr</a></p>
Désabonnement : répondre à ce message.
</body>
</html>
"""

# Corps texte brut (pour les clients qui n'affichent pas le HTML)
BODY_TEXT = """
Événements du face-à-face à venir

Deux tournois en face-à-face comptant pour le Tour de France cet été :
  - Open de Paris 27-28 juin
  - Championnat de Bretagne 24-25 juillet

Détails dans les images en pièce jointe.

A noter : Le championnat de France aura lieu à Paris cet hiver 4-6 décembre...

L'équipe de diplomania
Jérémie Lefrançois
Administrateur
https://diplomania2.fr
Désabonnement : répondre à ce message.
"""

# Images à incorporer dans le corps (inline)
INLINE_IMAGES = [
    ('open_paris.png', 'open_paris'),
    ('championnat_bretagne.png', 'championnat_bretagne'),
]

NAME_SENDER = "Lettre d'information de la part de l'A.F.J.D. (Diplomania)"
MAIL_SENDER = "afjdiplo_server_noreply@diplomania2.fr"
SENDER = f"{NAME_SENDER} <{MAIL_SENDER}>"
REPLY_TO = "jeremie.lefrancois@gmail.com"

APP = flask.Flask(__name__)
MAILER = None

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')


class ConfigFile:
    """Just reads an ini file"""

    def __init__(self, filename: str) -> None:
        self._config = configparser.ConfigParser(inline_comment_prefixes='#',    # do not accept ';'
                                                 empty_lines_in_values=False,    # as it says
                                                 interpolation=None)             # do not use variables

        assert self._config.read(filename, encoding='utf-8'), f"Missing ini file named {filename}"

    def section(self, section_name: str) -> configparser.SectionProxy:
        """Accesses a section of a config file."""
        assert self._config.has_section(section_name), "Missing section in ini file"
        return self._config[section_name]

    def section_list(self) -> typing.List[str]:
        """Accesses the list of sections of a config file."""
        return self._config.sections()


def load_mail_config() -> None:
    """Read mail config."""

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
    """ send email."""

    msg = flask_mail.Message(
        SUBJECT,
        sender=SENDER,
        recipients=[email_dest],
        reply_to=REPLY_TO
    )

    # Corps du message (HTML avec images inline)
    msg.html = BODY_HTML
    msg.body = BODY_TEXT

    # Ajout des images inline (pas en pièces jointes !)
    for image_file, cid_name in INLINE_IMAGES:
        assert os.path.exists(image_file), f"ERROR: {image_file} not found"
        with APP.open_resource(image_file) as fp:
            # Lire l'image et la convertir en base64 (méthode flask-mail)
            # Flask-Mail accepte les images inline via 'msg.attach' avec disposition 'inline'
            msg.attach(
                filename=image_file,
                content_type='image/png',
                data=fp.read(),
                disposition='inline',
                headers=[['Content-ID', f'<{cid_name}>']]
            )

    assert MAILER is not None
    MAILER.send(msg)


def main() -> None:
    """main"""

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
                    rest_time = datetime.timedelta(seconds=still * speed)
                    eta = datetime.datetime.now() + rest_time
                    print(f"Estimated ETA : {eta.strftime('%Y-%m-%d %H:%M:%S')}")

                time.sleep(INTERVAL)

    if failed_to_spam:
        print("Failed to spam:")
        print(' '.join(failed_to_spam))

    eta = datetime.datetime.now()
    print(f"Finished at: {eta.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()
