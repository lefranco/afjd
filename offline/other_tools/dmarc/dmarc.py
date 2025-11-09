#!/usr/bin/env python3
import imaplib
import email
from email.header import decode_header
import yaml
import argparse
from pathlib import Path
import os
import zipfile
import xml.etree.ElementTree as ET
import gzip
import shutil

IMAP_SERVER = ''
IMAP_PORT = 0
IMAP_USER = ''
IMAP_PASSWORD = ''
IMAP_MAILBOX = ''
MAX_EMAILS = 0
WORK_DIR = ''


def read_config(config_file):
    """ read_config """

    global IMAP_SERVER
    global IMAP_PORT
    global IMAP_USER
    global IMAP_PASSWORD
    global IMAP_MAILBOX
    global MAX_EMAILS

    global WORK_DIR

    if not config_file.is_file():
        print(f"Error : file '{config_file}' not found")
        exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    IMAP_SERVER = config["imap"]["server"]
    IMAP_PORT = int(config["imap"]["port"])
    IMAP_USER = config["imap"]["user"]
    IMAP_PASSWORD = config["imap"]["password"]
    IMAP_MAILBOX = config["imap"]["mailbox"]
    MAX_EMAILS = int(config["imap"]["max_emails"])

    WORK_DIR = config["work_dir"]

def parse_xml(xml_file):

    print(f"{xml_file=}")

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Récupérer les infos du rapport
    report_metadata = root.find("report_metadata")
    report_id = report_metadata.find("report_id").text
    org_name = report_metadata.find("org_name").text
    print(f"Rapport {report_id} de {org_name}")

    # Domaine testé
    policy = root.find("policy_published")
    domain = policy.find("domain").text
    adkim = policy.find("adkim").text
    aspf = policy.find("aspf").text
    print(f"Domaine testé: {domain}, DKIM={adkim}, SPF={aspf}")

    # Parcourir les enregistrements
    for record in root.findall("record"):
        source_ip = record.find("row/source_ip").text
        count = record.find("row/count").text
        disposition = record.find("row/policy_evaluated/disposition").text
        dkim = record.find("row/policy_evaluated/dkim").text
        spf = record.find("row/policy_evaluated/spf").text
        print(f"IP: {source_ip}, Count: {count}, Disposition: {disposition}, DKIM: {dkim}, SPF: {spf}")    


def main():
    """ main """

    parser = argparse.ArgumentParser(description="IMAP parameters to read emails")
    parser.add_argument("-c", "--config", required=True, help="Path to YAML file")
    args = parser.parse_args()
    config_file = Path(args.config)
    read_config(config_file)

    print(f"Connecting to {IMAP_SERVER}:{IMAP_PORT} ...")
    imap = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    imap.starttls()
    imap.login(IMAP_USER, IMAP_PASSWORD)
    imap.select(IMAP_MAILBOX)

    typ, data = imap.search(None, "ALL")
    if typ != "OK":
        print("Failed to retrieve emails")
        return

    print("Number of mails :", len(data[0].split()))
    print()

    uids = data[0].split()[-MAX_EMAILS:]
    for uid in uids:
        #print(f"UID {uid.decode()}")
        typ, msg_data = imap.fetch(uid, "(RFC822)")
        if typ != "OK":
            continue
        msg = email.message_from_bytes(msg_data[0][1])

        # Subject
        subject = decode_header(msg.get("Subject"))[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode("utf-8", errors="replace")
        #print("Subject: {subject}")

        # Sender
        from_ = decode_header(msg.get("From"))[0][0]
        if isinstance(from_, bytes):
            from_ = from_.decode("utf-8", errors="replace")
        #print(f"From: {from_}")

        # Parcours des parties du mail
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()

            # Attachment
            if disposition == "attachment":
                filename = part.get_filename()
                if filename:
                    filename = decode_header(filename)[0][0]
                    if isinstance(filename, bytes):
                        filename = filename.decode("utf-8", errors="replace")

                    if filename.lower().endswith('zip'):
                        filepath = os.path.join(WORK_DIR, filename)
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        with zipfile.ZipFile(filepath, 'r') as zip_ref:
                            files_in_zip = zip_ref.namelist()
                            zip_ref.extractall(WORK_DIR)
                        os.remove(filepath)
                        extracted_files = [os.path.join(WORK_DIR, f) for f in files_in_zip]
                        for xml_file in extracted_files:
                            assert xml_file.lower().endswith('xml'), "Not XML file"
                            parse_xml(xml_file)

                    elif filename.lower().endswith(".gz"):
                        filepath = os.path.join(WORK_DIR, filename[:-3])
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        with gzip.open(filepath, 'rb') as gzip_ref:
                            extracted_file = os.path.join(WORK_DIR, os.path.basename(filepath)[:-3])
                            files_in_gzip = [extracted_file]
                            with open(out_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        os.remove(filepath)         
                        extracted_files = [os.path.join(WORK_DIR, f) for f in files_in_gzip]
                        for xml_file in extracted_files:
                            assert xml_file.lower().endswith('xml'), "Not XML file"
                            parse_xml(xml_file)

                    else:
                        pass
                        # print("Unknown attachment type")               

            # Body 
            elif content_type == "text/plain" and disposition is None:
                body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                #print("Body (text) :")
                #print(body)

            elif content_type == "text/html" and disposition is None:
                html_body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                #print("Body (HTML) :")
                #print(html_body)

        print("----------")

    imap.logout()

if __name__ == "__main__":
    main()
