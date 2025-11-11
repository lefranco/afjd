#!/usr/bin/env python3

"""DMARC."""

from __future__ import annotations

import imaplib
import email
from email.header import decode_header
import argparse
import pathlib
import os
import zipfile
import xml.etree.ElementTree as ET
import gzip
import shutil
import sys
import typing
import tkinter
import tkinter.messagebox

import yaml

IMAP_SERVER = ''
IMAP_PORT = 0
IMAP_USER = ''
IMAP_PASSWORD = ''
IMAP_MAILBOX = ''
MAX_EMAILS = 0
WORK_DIR = ''


def read_config(config_file: pathlib.Path) -> None:
    """ read_config """

    global IMAP_SERVER
    global IMAP_PORT
    global IMAP_USER
    global IMAP_PASSWORD
    global IMAP_MAILBOX

    global WORK_DIR

    if not config_file.is_file():
        print(f"Error : file '{config_file}' not found")
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    IMAP_SERVER = config["imap"]["server"]
    IMAP_PORT = int(config["imap"]["port"])
    IMAP_USER = config["imap"]["user"]
    IMAP_PASSWORD = config["imap"]["password"]
    IMAP_MAILBOX = config["imap"]["mailbox"]

    WORK_DIR = config["work_dir"]


ITEMS_DICT = {}
IHM_TABLE = {}


def parse_xml(xml_file: str) -> None:
    """Parse an XML file."""

    print(f"Parsing {xml_file=}...", end='')

    tree = ET.parse(xml_file)
    root = tree.getroot()

    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]  # garde seulement le nom après }

    # Récupérer les infos du rapport
    report_metadata = root.find("report_metadata")
    assert report_metadata, "No metadata!"
    report_id = report_metadata.find("report_id").text
    org_name = report_metadata.find("org_name").text
    #  print(f"Rapport {report_id} de {org_name}")

    # Domaine testé
#    policy = root.find("policy_published")
#    domain = policy.find("domain").text
#    adkim = policy.find("adkim").text
#    aspf = policy.find("aspf").text
#    print(f"  Domaine testé: {domain}, DKIM={adkim}, SPF={aspf}")

    # Parcourir les enregistrements
    attention = False
    stuff = []
    for record in root.findall("record"):
        source_ip = record.find("row/source_ip").text
        count = record.find("row/count").text
        disposition = record.find("row/policy_evaluated/disposition").text
        dkim = record.find("row/policy_evaluated/dkim").text
        spf = record.find("row/policy_evaluated/spf").text
        line = f"  IP: {source_ip}, Count: {count}, Disposition: {disposition}, DKIM: {dkim}, SPF: {spf}"
        if disposition != 'none':
            attention = True
        stuff.append(line)

    description = f"{org_name}/{report_id}"
    print("done!")
    return description, attention, stuff


def display_callback(stuff: list[str]) -> None:
    """Display information about content in email."""
    tkinter.messagebox.showinfo("Info", '\n'.join(stuff))


def delete_mail(message_id) -> None:
    """ main """

    print(f"Connecting to {IMAP_SERVER}:{IMAP_PORT} ...")
    imap = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    imap.starttls()
    imap.login(IMAP_USER, IMAP_PASSWORD)
    imap.select(IMAP_MAILBOX)

    print(f"Deleting email with {message_id=}")

    # Mark the email for deletion
    status, data = imap.store(message_id, '+FLAGS', '(\\Deleted)')
    assert status == 'OK', f"Failed to set Deleted flag on UID {message_id}: {data}"

    # Permanently delete flagged emails
    status, data = imap.expunge()
    assert status == 'OK', f"Expunge failed: {data}"

    print("Deleted successfully.")
    imap.logout()


def delete_callback(message_id: str, description: str) -> None:
    """Delete email."""

    # delete from server
    delete_mail(message_id)

    # delete from ihm
    display_button, delete_button = IHM_TABLE[description]
    display_button.destroy()
    delete_button.destroy()
    del IHM_TABLE[description]


def load_mails() -> None:
    """ main """

    print(f"Connecting to {IMAP_SERVER}:{IMAP_PORT} ...")
    imap = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    imap.starttls()
    imap.login(IMAP_USER, IMAP_PASSWORD)
    imap.select(IMAP_MAILBOX)

    status, data = imap.search(None, "ALL")
    assert status == "OK"

    print("Number of mails :", len(data[0].split()))

    for num in data[0].split():

        status, msg_data = imap.fetch(num, '(BODY.PEEK[])')
        assert status == "OK"

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        message_id = num.decode()
        description = str(message_id)
        attention = False
        stuff = []

        # Parcours des parties du mail
        for part in msg.walk():

            disposition = part.get_content_disposition()

            # Attachment
            if disposition != "attachment":
                continue

            filename = part.get_filename()
            assert filename
            filename = decode_header(filename)[0][0]
            if isinstance(filename, bytes):
                filename = filename.decode("utf-8", errors="replace")

            # TODO code for zip and gz should be more similar

            if filename.lower().endswith('zip'):
                print("Found zip file!")
                zip_path = os.path.join(WORK_DIR, filename)
                payload = part.get_payload(decode=True)
                assert payload, "No payload"
                with open(zip_path, "wb") as fic:
                    fic.write(payload)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    files_in_zip = zip_ref.namelist()
                    zip_ref.extractall(WORK_DIR)
                os.remove(zip_path)
                extracted_files = [os.path.join(WORK_DIR, f) for f in files_in_zip]
                for xml_file in extracted_files:
                    assert xml_file.lower().endswith('xml'), f"{xml_file} : Not XML file"
                    description, attention, stuff = parse_xml(xml_file)
                    ITEMS_DICT[description] = (message_id, attention, stuff)

            elif filename.lower().endswith(".gz"):
                print("Found gz file!")
                gz_path = os.path.join(WORK_DIR, filename)
                payload = part.get_payload(decode=True)
                assert payload, "No payload"
                with open(gz_path, "wb") as fic:
                    fic.write(payload)
                extracted_file = os.path.join(WORK_DIR, os.path.splitext(filename)[0])  # data.xml
                files_in_gzip = [extracted_file]
                with gzip.open(gz_path, 'rb') as f_in, open(extracted_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(gz_path)
                for xml_file in files_in_gzip:
                    assert xml_file.lower().endswith('xml'), f"{xml_file} : Not XML file"
                    description, attention, stuff = parse_xml(xml_file)
                    ITEMS_DICT[description] = (message_id, attention, stuff)

            else:
                print(f"Unknown attachment type {filename=}")

    imap.logout()


def position(root: typing.Any) -> None:
    """Place the window on screen."""
    root.update_idletasks()

    # size of desktop
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # mouse position
    try:
        x_mouse = root.winfo_pointerx()
        y_mouse = root.winfo_pointery()
    except tkinter.TclError:
        x_mouse = screen_width // 2
        y_mouse = screen_height // 2

    # size of window
    window_width = root.winfo_width()
    window_height = root.winfo_height()

    # relative center
    x = int(x_mouse - window_width / 2)
    y = int(y_mouse - window_height / 2)

    # make sure on screen
    x = max(0, min(x, screen_width - window_width))
    y = max(0, min(y, screen_height - window_height))

    # geometry string
    root.geometry(f"+{x}+{y}")


TITLE = "My DMARC elements"


def main() -> None:
    """Main."""

    parser = argparse.ArgumentParser(description="IMAP parameters to read emails")
    parser.add_argument("-c", "--config", required=True, help="Path to YAML file")
    args = parser.parse_args()
    config_file = pathlib.Path(args.config)
    read_config(config_file)

    # from server
    load_mails()

    # create
    root = tkinter.Tk()

    # title
    title_label = tkinter.Label(root, text=TITLE, font=("Arial", 10), fg="blue")
    title_label.pack()

    # frame for buttons
    buttons_frame = tkinter.Frame(root)
    buttons_frame.pack()

    # all buttons inside
    for i, (description, (message_id, attention, stuff)) in enumerate(ITEMS_DICT.items()):

        fg = 'Red' if attention else 'Black'

        # to display
        display_button = tkinter.Button(buttons_frame, text=description, font=("Arial", 8), fg=fg, command=lambda s=stuff: display_callback(s))
        display_button.grid(row=i, column=0)

        # to delete
        delete_button = tkinter.Button(buttons_frame, text='delete me', font=("Arial", 8), fg=fg, command=lambda m=message_id, d=description: delete_callback(m, d))
        delete_button.grid(row=i, column=1)

        # remember so to destroy
        IHM_TABLE[description] = (display_button, delete_button)

    # position window
    position(root)

    # tkinter loop
    root.mainloop()


if __name__ == "__main__":
    main()
