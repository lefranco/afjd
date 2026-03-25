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
import collections
import tkinter
import tkinter.scrolledtext

import yaml

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


ITEMS_DICT: dict[str, tuple[str, bool, bool, dict[str, list[str]]]] = {}
IHM_TABLE: dict[str, tuple[tkinter.Button, tkinter.Button]] = {}


def parse_xml(xml_file: str, dump: bool) -> tuple[str, bool, dict[str, list[str]]]:
    """Parse an XML file."""

    def get_text(parent: xml.etree.ElementTree.Element, tag: str) -> str:
        """Find and return text for a nested tag, respecting namespace."""
        path = "/".join(f"{tag_prefix}{t}" for t in tag.split("/"))
        elem = parent.find(path, ns)
        if elem is None or elem.text is None:
            raise ValueError(f"Missing or empty <{tag}> element in {xml_file}")
        return elem.text.strip()

    if dump:
        with open(xml_file, 'r', encoding='utf-8') as fic:
            content = fic.read()
        print()
        print("####################################################")
        print(content)
        print("####################################################")
        print()

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
    content_dict = collections.defaultdict(list)
    for record in root.findall(f"{tag_prefix}record", ns):
        source_ip = get_text(record, "row/source_ip")
        count = get_text(record, "row/count")
        disposition = get_text(record, "row/policy_evaluated/disposition")
        dkim = get_text(record, "row/policy_evaluated/dkim")
        spf = get_text(record, "row/policy_evaluated/spf")
        attention = (disposition != 'none' or dkim != 'pass' or spf != 'pass')
        if attention:
            overall_attention = True
            line = f"Count: {count}, Disposition: {disposition}, DKIM: {dkim}, SPF: {spf}"
            content_dict[source_ip].append(line)

    description = f"{org_name}/{report_id}"

    return description, overall_attention, content_dict


def display_callback(description: str, nomarc: bool, content_dict: dict[str, str]) -> None:
    """Display information about content in email."""

    def copy_selection() -> None:
        try:
            selected_text = txt.get(tkinter.SEL_FIRST, tkinter.SEL_LAST)
        except tkinter.TclError:
            return
        win.clipboard_clear()
        win.clipboard_append(selected_text)
        win.update()

    win = tkinter.Toplevel()
    win.title(description)
    txt = tkinter.scrolledtext.ScrolledText(win, wrap=tkinter.WORD)
    txt.pack(expand=True, fill="both", padx=10, pady=10)

    for source_ip, lines_text in content_dict.items():
        lines = '\n '.join(lines_text)
        txt.insert(tkinter.END, f"{source_ip}:\n {lines}")
        txt.insert(tkinter.END, '\n')
        txt.insert(tkinter.END, '\n')

    if nomarc:
        txt.insert(tkinter.END, '\n')
        txt.insert(tkinter.END, 'Not DMARC content here.')

    txt.focus()

    # Handle Right Click
    menu_contextuel = tkinter.Menu(win, tearoff=0)
    menu_contextuel.add_command(label="Copy", command=copy_selection)
    menu_contextuel.add_command(label="Select All", command=lambda: txt.tag_add("sel", "1.0", "end"))
    txt.bind("<Button-3>", lambda e: menu_contextuel.post(e.x_root, e.y_root))

    # Forbid edition
    txt.bind("<Key>", lambda e: "break")


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


def load_mails(dump: bool, headers: bool) -> None:
    """ load_mails """

    print(f"Connecting to {IMAP_SERVER}:{IMAP_PORT} ...")
    imap = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    imap.starttls()
    imap.login(IMAP_USER, IMAP_PASSWORD)
    imap.select(IMAP_MAILBOX)

    status, data = imap.uid("search", None, "ALL")  # type: ignore[arg-type]
    assert status == "OK", f"Search failed {data}"

    for uid in data[0].split():

        print(".", flush=True, end='')

        if headers:
            status, msg_data = imap.uid("fetch", uid, "(BODY.PEEK[HEADER])")
            assert status, "Failed to get email header"
            with open(f"header_{uid.decode()}.eml", "a", encoding="utf-8") as file:
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        raw_header = response_part[1].decode('utf-8', errors='ignore')  # pylint: disable=unsubscriptable-object
                        file.write(raw_header)
                        file.write("-------------")

        status, msg_data = imap.uid("fetch", uid, '(BODY.PEEK[])')
        assert status == "OK", f"Fetch failed {data}"

        item = msg_data[0]
        if isinstance(item, tuple):
            raw_email = item[1]
        elif isinstance(item, bytes):
            raw_email = item
        else:
            assert False, f"Unexpected fetch result: {item}"

        if dump:
            print("========")
            assert isinstance(raw_email, bytes), "Bad raw_email not bytes"
            full_content_str = raw_email.decode('utf-8', errors='ignore')
            print(full_content_str)
            print("========")

        msg = email.message_from_bytes(raw_email, policy=email.policy.default)
        date_message = msg['date']

        message_uid = uid.decode()

        added = False
        body = ""

        # Go through email parts
        num_part = 0
        for part in msg.walk():

            disposition = part.get_content_disposition()

            # Attachment
            if disposition != "attachment":
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    assert isinstance(payload, bytes)
                    if not body:
                        body = payload.decode(part.get_content_charset() or 'utf-8', errors='ignore')
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
                assert isinstance(payload, bytes)
                with open(zip_path, "wb") as fic:
                    fic.write(payload)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    files_in_zip = zip_ref.namelist()
                    zip_ref.extractall(WORK_DIR)
                os.remove(zip_path)
                extracted_files = [os.path.join(WORK_DIR, f) for f in files_in_zip]
                for xml_file in extracted_files:
                    #  assert xml_file.lower().endswith('xml'), f"{xml_file} : Not XML file"
                    description, attention, content_dict = parse_xml(xml_file, dump)
                    os.remove(xml_file)
                    ITEMS_DICT[f"{date_message}-{description}"] = (str(message_uid), False, attention, content_dict)
                    added = True

            elif filename.lower().endswith(".gz"):
                gz_path = os.path.join(WORK_DIR, filename)
                payload = part.get_payload(decode=True)
                assert payload, "No payload"
                assert isinstance(payload, bytes)
                with open(gz_path, "wb") as fic:
                    fic.write(payload)
                extracted_file = os.path.join(WORK_DIR, os.path.splitext(filename)[0])
                with gzip.open(gz_path, 'rb') as f_in, open(extracted_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(gz_path)
                for xml_file in [extracted_file]:
                    #  assert xml_file.lower().endswith('xml'), f"{xml_file} : Not XML file"
                    description, attention, content_dict = parse_xml(xml_file, dump)
                    os.remove(xml_file)
                    ITEMS_DICT[f"{date_message}-{description}"] = (str(message_uid), False, attention, content_dict)
                    added = True

            else:
                print(f"Unknown attachment type {filename=}")

        # This will add a line for non dmarc emails
        if not added:
            description = msg['subject']
            ITEMS_DICT[f"{date_message}-{description}"] = (message_uid, True, False, {'': [body]})

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
    parser.add_argument('-d', '--dump', action='store_true', help="Dump report content")
    parser.add_argument('-H', '--header', action='store_true', help="Dump emails headers")
    args = parser.parse_args()
    config_file = pathlib.Path(args.config)
    read_config(config_file)

    # from server
    load_mails(args.dump, args.header)

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
    for i, (description, (message_id, nomarc, attention, content_dict)) in enumerate(ITEMS_DICT.items()):

        fg = 'Blue' if nomarc else 'Red' if attention else 'Black'

        # to display
        display_button = tkinter.Button(buttons_frame, text=description, font=("Arial", 8), fg=fg, command=lambda d=description, nm=nomarc, cd=content_dict: display_callback(d, nm, cd))  # type: ignore[misc]
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
