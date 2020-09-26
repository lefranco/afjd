#!/usr/bin/env python3


"""
File : mailer.py

Justs sends an email
"""

import typing

import flask_mail  # type: ignore

import lowdata

SUBJECT = "Ceci est un email pour indiquer que la partie a avancé"
BODY_1 = "la partie en question est :"
BODY_2 = "Ne pas répondre à ce message !"
SENDER = "jeremie.lefrancois@laposte.net"

MAILER = None


def load_mail_config(app: typing.Any) -> None:
    """ read mail config """

    mail_config = lowdata.ConfigFile('./config/mail.ini')
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


def send_game_progess_report(name: str, email_dest: str) -> None:
    """ send email """

    msg = flask_mail.Message(SUBJECT, sender=SENDER, recipients=[email_dest])
    msg.body = f"{BODY_1}\n{name}\n{BODY_2}"

    assert MAILER is not None
    MAILER.send(msg)


if __name__ == '__main__':
    assert False, "Do not run this script"
