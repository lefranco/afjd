#!/usr/bin/env python3

"""DMARC."""

from __future__ import annotations

import imaplib
import email
import email.header
import email.policy
import argparse
import pathlib
import os
import zipfile
import xml.etree.ElementTree
import gzip
import shutil
import sys
import typing
import tkinter
import tkinter.scrolledtext

import yaml

DUMP_FILE = False

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 900

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


ITEMS_DICT: dict[str, tuple[str, bool, list[str]]] = {}
IHM_TABLE: dict[str, tuple[tkinter.Button, tkinter.Button]] = {}


def parse_xml(xml_file: str) -> tuple[str, bool, list[str]]:
    """Parse an XML file."""

    def get_text(parent: xml.etree.ElementTree.Element, tag: str) -> str:
        """Find and return text for a nested tag, respecting namespace."""
        path = "/".join(f"{tag_prefix}{t}" for t in tag.split("/"))
        elem = parent.find(path, ns)
        if elem is None or elem.text is None:
            raise ValueError(f"Missing or empty <{tag}> element in {xml_file}")
        return elem.text.strip()

    if DUMP_FILE:
        with open(xml_file, 'r', encoding='utf-8') as fic:
            content = fic.read()
        print("====")
        print(content)
        print("====")

    tree = xml.etree.ElementTree.parse(xml_file)
    root = tree.getroot()

    # Detect namespace, if exists
    ns = {}
    if root.tag.startswith("{"):
        uri = root.tag.split("}")[0].strip("{")
        ns["ns"] = uri
        tag_prefix = "ns:"
    else:
        tag_prefix = ""

    # Retrieve info from report
    report_metadata = root.find(f"{tag_prefix}report_metadata", ns)
    assert report_metadata, "No metadata!"
    report_id = get_text(report_metadata, "report_id")
    org_name = get_text(report_metadata, "org_name")

    # Scan records
    overall_attention = False
    content_list = []
    for record in root.findall(f"{tag_prefix}record", ns):
        source_ip = get_text(record, "row/source_ip")
        count = get_text(record, "row/count")
        disposition = get_text(record, "row/policy_evaluated/disposition")
        dkim = get_text(record, "row/policy_evaluated/dkim")
        spf = get_text(record, "row/policy_evaluated/spf")
        attention = (disposition != 'none' or dkim != 'pass' or spf != 'pass')
        if attention:
            overall_attention = True
            line = f"  IP: {source_ip}, Count: {count}, Disposition: {disposition}, DKIM: {dkim}, SPF: {spf}"
            content_list.append(line)

    description = f"{org_name}/{report_id}"
    return description, overall_attention, content_list


def display_callback(description: str, content_list: list[str]) -> None:
    """Display information about content in email."""
    win = tkinter.Toplevel()
    win.title(description)
    txt = tkinter.scrolledtext.ScrolledText(win, wrap=tkinter.WORD)
    txt.pack(expand=True, fill="both", padx=10, pady=10)

    txt.tag_config('red_highlight', foreground='red')

    for line_text in sorted(content_list):
        start_index = txt.index("end-1c")
        txt.insert(tkinter.END, line_text)
        end_index = f"{start_index} + {len(line_text)}c"
        txt.tag_add('red_highlight', start_index, end_index)
        txt.insert(tkinter.END, '\n')
    txt.config(state=tkinter.DISABLED)


def delete_mail(message_uid: str) -> None:
    """Delete an identified email."""

    assert message_uid.isdigit()

    print(f"Connecting to {IMAP_SERVER}:{IMAP_PORT} ...")
    imap = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    imap.starttls()
    imap.login(IMAP_USER, IMAP_PASSWORD)
    status, data = imap.select(IMAP_MAILBOX, readonly=False)
    print(f"Select: {status=} {data=}")

    print(f"Deleting email with {message_uid=}")

    # Mark the email for deletion
    status, data = imap.uid("store", message_uid, "+FLAGS.SILENT", "(\\Deleted)")
    print("STORE:", status, data)
    assert status == "OK", f"Store failed: {data}"

    # Permanently delete flagged emails
    status, data = imap.expunge()
    assert status == 'OK', f"Expunge failed: {data}"

    # Check
    status, data = imap.uid("fetch", message_uid, "(FLAGS)")
    assert status == 'OK', "Failed to check"
    print("After expunge:", data)
    assert data[0] is None, "Not suppressed!"

    imap.close()
    imap.logout()
    print("Deleted successfully.")


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

    status, data = imap.uid("search", None, "ALL")
    assert status == "OK", f"Search failed {data}"

    for uid in data[0].split():

        print(".", flush=True, end='')

        status, msg_data = imap.uid("fetch", uid, '(BODY.PEEK[])')
        assert status == "OK", f"Fetch failed {data}"

        item = msg_data[0]
        if isinstance(item, tuple):
            raw_email = item[1]
        elif isinstance(item, bytes):
            raw_email = item
        else:
            assert False, f"Unexpected fetch result: {item}"

        msg = email.message_from_bytes(raw_email, policy=email.policy.default)
        date_message = msg['date']

        message_uid = uid.decode()

        # Go through email parts
        num_part = 0
        for part in msg.walk():

            disposition = part.get_content_disposition()

            # Attachment
            if disposition != "attachment":
                continue

            num_part += 1
            assert num_part == 1, "More than one attachement"
            filename_part = part.get_filename()
            assert filename_part, "No fileame for attachment"
            filename1 = email.header.decode_header(filename_part)[0][0]
            if isinstance(filename1, bytes):
                filename = filename1.decode("utf-8", errors="replace")
            else:
                filename = filename1

            if filename.lower().endswith('zip'):
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
                    #  assert xml_file.lower().endswith('xml'), f"{xml_file} : Not XML file"
                    description, attention, content_list = parse_xml(xml_file)
                    os.remove(xml_file)
                    ITEMS_DICT[f"{date_message}-{description}"] = (message_uid, attention, content_list)

            elif filename.lower().endswith(".gz"):
                gz_path = os.path.join(WORK_DIR, filename)
                payload = part.get_payload(decode=True)
                assert payload, "No payload"
                with open(gz_path, "wb") as fic:
                    fic.write(payload)
                extracted_file = os.path.join(WORK_DIR, os.path.splitext(filename)[0])
                with gzip.open(gz_path, 'rb') as f_in, open(extracted_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(gz_path)
                for xml_file in [extracted_file]:
                    #  assert xml_file.lower().endswith('xml'), f"{xml_file} : Not XML file"
                    description, attention, content_list = parse_xml(xml_file)
                    os.remove(xml_file)
                    ITEMS_DICT[f"{date_message}-{description}"] = (message_uid, attention, content_list)

            else:
                print(f"Unknown attachment type {filename=}")

    imap.logout()
    print("")


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

    def on_frame_configure(_: typing.Any) -> None:
        """Move cursor."""
        canvas.configure(scrollregion=canvas.bbox("all"))

    parser = argparse.ArgumentParser(description="IMAP parameters to read emails")
    parser.add_argument("-c", "--config", required=True, help="Path to YAML file")
    args = parser.parse_args()
    config_file = pathlib.Path(args.config)
    read_config(config_file)

    # from server
    load_mails()

    if not ITEMS_DICT:
        print("Nothing in mailbox!")
        sys.exit(0)

    # create
    root = tkinter.Tk()
    root.title(TITLE)

    # Canvas pour faire défiler
    canvas = tkinter.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
    canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)

    # Scrollbar verticale
    scrollbar = tkinter.Scrollbar(root, command=canvas.yview)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    canvas.configure(yscrollcommand=scrollbar.set)

    # frame for buttons
    buttons_frame = tkinter.Frame(canvas)
    canvas.create_window((0, 0), window=buttons_frame, anchor="nw")

    buttons_frame.bind("<Configure>", on_frame_configure)

    # all buttons inside
    for i, (description, (message_id, attention, content_list)) in enumerate(ITEMS_DICT.items()):

        fg = 'Red' if attention else 'Black'

        # to display
        display_button = tkinter.Button(buttons_frame, text=description, font=("Arial", 8), fg=fg, command=lambda d=description, cl=content_list: display_callback(d, cl))  # type: ignore[misc]
        display_button.grid(row=i + 1, column=0)

        # to delete
        delete_button = tkinter.Button(buttons_frame, text='delete me', font=("Arial", 8), fg=fg, command=lambda m=message_id, d=description: delete_callback(m, d))  # type: ignore[misc]
        delete_button.grid(row=i + 1, column=1)

        # remember so to destroy
        IHM_TABLE[description] = (display_button, delete_button)

    # position window
    position(root)

    # tkinter loop
    root.mainloop()


if __name__ == "__main__":
    main()
