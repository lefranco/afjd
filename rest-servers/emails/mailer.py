#!/usr/bin/env python3


"""
File : mailer.py

Justs sends an email
"""

import typing
import smtplib

import flask_mail  # type: ignore

import lowdata

SENDER = None
MAILER = None

SITE_ADDRESS = "https://diplomania-gen.fr/"


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
    global SENDER
    SENDER = app.config['MAIL_USERNAME']


def send_mail(subject: str, body: str, addressee: str) -> bool:
    """ send_mail """

    sender = SENDER

    msg = flask_mail.Message(subject, sender=sender, recipients=[addressee])

    msg.body = body
    msg.body += "\n"
    msg.body += "\n"
    msg.body += f"adresse web du site : {SITE_ADDRESS}"
    msg.body += "\n"
    msg.body += "Ne pas répondre à ce message !"

    assert MAILER is not None
    try:
        MAILER.send(msg)
    except smtplib.SMTPRecipientsRefused:
        return False

    return True


if __name__ == '__main__':
    assert False, "Do not run this script"
