#!/usr/bin/env python3

"""DMARC."""

from __future__ import annotations

import imaplib
import email
import email.policy
import argparse
import pathlib
import sys
import typing
import tkinter
import tkinter.messagebox

import yaml

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 900

IMAP_SERVER = ''
IMAP_PORT = 0
IMAP_USER = ''
IMAP_PASSWORD = ''
IMAP_MAILBOX = ''
MAX_EMAILS = 0
WORK_DIR = ''

HOST_REPORTER = "This is the mail system at host "
THE_MAIL_SYSTEM = "The mail system"
SAID = 'said:'


def parse_content(content: str) -> tuple[str, str, str, str, str, str, str, str, str]:
    """Parse a string that is the content of a bounce message."""

    print(content)
    print("================")

    host_reporter = ""
    subject = ""
    discourse = ""
    state = 'init'

    for line in content.split('\n'):

        if not line:
            continue

        match state:
            case 'init':
                if line.startswith(HOST_REPORTER):
                    host_reporter = line[len(HOST_REPORTER):].strip().rstrip('.')
                    continue

                if THE_MAIL_SYSTEM in line:
                    state = 'mail'
                    continue

            case 'mail':
                if SAID not in line:
                    subject += line
                else:
                    subject1, _, discourse = line.partition(SAID)
                    subject += subject1
                    state = 'said'
                    continue

            case 'said':
                discourse += " " + line

    # Extract recipient email
    email_dest, _, rest = subject.partition(':')
    email_dest = email_dest.strip('<>').strip()

    # Extract reporter host and IP
    _, _, rest = rest.partition('host ')
    reporter_host, _, reporter_ip = rest.partition('[')
    reporter_host = reporter_host.strip()
    reporter_ip = reporter_ip.strip('] ')
    reporter_ip = reporter_ip.strip()

    # Extract code and explanation
    if ';' in discourse:
        code_part, _, rest = discourse.partition(';')
    elif ',' in discourse:
        code_part, _, rest = discourse.partition(',')
    else:
        assert False, "Missing terminator"
    code_part = ' '.join(code_part.split())
    code_class, _, code_part = code_part.partition(' ')
    code_class = code_class.strip()
    code_value, _, code_desc = code_part.partition(' ')
    code_value = ' '.join(code_value.split())
    code_desc = ' '.join(code_desc.split())

    client, _, explanations = rest.partition(']')
    _, _, client_ip = client.partition('[')
    client_ip = client_ip.strip()
    explanations = ' '.join(explanations.split())

    #print(f"{host_reporter=}\n{email_dest=}\n{reporter_host=}\n{reporter_ip=}\n{code_class=}\n{code_value=}\n{code_desc=}\n{client_ip=}\n{explanations=}")

    return host_reporter, email_dest, reporter_host, reporter_ip, code_class, code_value, code_desc, client_ip, explanations


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


ITEMS_DICT: dict[str, tuple[str, bool, str, str]] = {}
IHM_TABLE: dict[str, tuple[tkinter.Button, tkinter.Button]] = {}


def display_callback(description: str, body_text: list[str]) -> None:
    """Display information about content in email."""
    tkinter.messagebox.showinfo(description, body_text)


def delete_mail(message_id: str) -> None:
    """Delete an identified email."""

    print(f"Connecting to {IMAP_SERVER}:{IMAP_PORT} ...")
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
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
    imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    imap.login(IMAP_USER, IMAP_PASSWORD)
    imap.select(IMAP_MAILBOX)

    status, data = imap.search(None, "ALL")
    assert status == "OK", f"Search failed {data}"

    for num in data[0].split():

        status, msg_data = imap.fetch(num, '(BODY.PEEK[])')
        assert status == "OK", f"Fetch failed {data}"

        item = msg_data[0]
        if isinstance(item, tuple):
            raw_email = item[1]
        elif isinstance(item, bytes):
            raw_email = item
        else:
            assert False, f"Unexpected fetch result: {item}"

        msg = email.message_from_bytes(raw_email, policy=email.policy.default)

        body_text = None
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")

            # On cherche la partie texte principale (plain ou HTML)
            if "attachment" in content_disposition:
                continue
            if content_type in ("text/plain", "text/html"):
                try:
                    body_text = part.get_content()
                    host_reporter, email_dest, reporter_host, reporter_ip, code_class, code_value, code_desc, client_ip, explanations = parse_content(body_text)
                except Exception as e:
                    print(f"Error decoding body: {e}")
                    body_text = None
                break

        if not body_text:
            body_text = "(Pas de corps trouvé)"
        else:
            title = f"{email_dest}[{client_ip}] {code_class} {code_value} {num.decode()}"
            message_id = num.decode()
            description = body_text.replace('\r\n\r\n', '\r\n')
            attention = False  # TODO : think of something
            ITEMS_DICT[title] = (message_id, attention, description)

        print(".", end='', flush=True)

    print()

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


TITLE = "My BOUNCING elements"


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
    for i, (description, (message_id, attention, content)) in enumerate(sorted(ITEMS_DICT.items(), key=lambda t: t[0])):

        fg = 'Red' if attention else 'Black'

        # to display
        display_button = tkinter.Button(buttons_frame, text=description, font=("Arial", 8), fg=fg, command=lambda d=description, c=content: display_callback(d, c))  # type: ignore[misc]
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

#    content = """ """
#    parse_content(content)

    main()
