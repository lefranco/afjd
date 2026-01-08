#!/usr/bin/env python3

"""
Complete NodeBB Importer using API v3.

Clears existing data and imports from phpBB CSV files
Need to have :
    phpbbexport/avatars = phpBB3/images/avatars/upload
    phpbbexport/uploads = phpBB3/files/

IMPORTANT:
  Need to:
    - manually add pdf and zip in authorized extensions (admin console)
    - comment out line 16 "data.timestamp = Date.now()" in src/api/helpers.js + stop + build + start
"""

import contextlib
import collections
import html
import mimetypes
import os
import pathlib
import re
import secrets
import string
import sys
import signal
import time
import typing
import types
#  import urllib3   # COMPANY

import magic  # sudo apt install libmagic1 + pip3 install python-magic --break-system-packages
import pandas as pd  # pip3 install pandas --break-system-packages
import requests  # pip3 install requests --break-system-packages
import pymongo  # pip3 install pymongo --break-system-packages
import spacy  # pip3 install spacy --break-system-packages + pip3 install https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.7.0/fr_core_news_sm-3.7.0-py3-none-any.whl --break-system-packages)

import converter

# TODO fill these
DATABASE_PASSWORD = ""
ADMIN_PASSWORD = ""

# -------------------------
# CONFIGURATION
# -------------------------
NODEBB_URL = "https://forum.diplomania2.fr"
ADMIN_USERNAME = "admin"

MONGO_URI = f"mongodb://nodebb:{DATABASE_PASSWORD}@37.59.100.228:27017/nodebb"
NODEBB_DB = "nodebb"

DATA_DIR = "./phpbb_export"
CSV_ENCODING = "utf-8"

# Get from admin interface
ADMIN_TOKEN = '7abaf72c-c895-4c12-af6d-71103995ae31'

# Identify admin
ADMIN_UID = 1

# Be patient if server is busy
TIMEOUT = 60

# Need this type
SignalHandler = typing.Callable[[int, types.FrameType | None], None]

# Cancels warnings
#  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # COMPANY


# -------------------------
# Low level tools
# -------------------------
@contextlib.contextmanager
def delayed_ctrl_c() -> typing.Iterator[None]:
    """Ctrl-C will be triggered at exit of critical uninterruptable section."""

    received: dict[str, typing.Any] = {
        "sig": None,
        "frame": None,
    }

    def handler(sig: int, frame: types.FrameType | None) -> None:
        received["sig"] = sig
        received["frame"] = frame
        print("Ctrl+C received, interruption postponed...")

    old_handler_raw = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, handler)

    try:
        yield
    finally:
        signal.signal(signal.SIGINT, old_handler_raw)

        if received["sig"] is not None and callable(old_handler_raw):
            old_handler_raw(received["sig"], received["frame"])


# -------------------------
# Tools
# -------------------------
def generate_random_password() -> str:
    """Generate a secure random password."""

    pass_length = 8
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(pass_length))
    return password


def save_passwords_to_file(password_list: list[dict[str, typing.Any]]) -> None:
    """Save generated passwords to a secure CSV file."""

    # Create a CSV for usage
    csv_file = "user_passwords.csv"
    df = pd.DataFrame(password_list)
    df.to_csv(csv_file, index=False)
    print(f"🔐 Generated passwords saved to: {csv_file}")

    # Security warning
    print("⚠️  SECURITY WARNING: This file contain plain-text passwords!")
    print("   Secure or delete it immediately after distributing passwords.")


# -------------------------
# DATABASE Client
# -------------------------
class NodeBBMongoDB:
    """For direct access to MongoDb database (tweaking)."""

    def __init__(self, mongo_uri: str, db_name: str) -> None:
        """Connect to NodeBB's MongoDB."""

        self.client: pymongo.MongoClient[typing.Any] = pymongo.MongoClient(mongo_uri)
        self.db = self.client[db_name]
        print(f"✅ Connected to NodeBB database: {db_name}")

    def give_enough_reputation(self, uid: int) -> bool:
        """Give enough reputation (need 3 to post faster than every 120 seconds)."""

        return True  # Will not work at company TODO PUT BACK

        reputation_value = 3    # pylint: disable=unreachable

        result = self.db.objects.update_one(
            {"_key": f"user:{uid}"},
            {"$set": {"reputation": reputation_value}}
        )

        return result.acknowledged

    def close(self) -> None:
        """Close."""
        self.client.close()


# -------------------------
# API Client
# -------------------------
class NodeBBApiSession(requests.Session):
    """Importer."""

    def __init__(self, username: str, password: str) -> None:
        """Connect to NodeBB's API."""

        super().__init__()

        #  self.verify = False  # COMPANY

        # Very important
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        print(f"🔍 Generate CSRF for {username}...")
        csrf = self.generate_csrf(username, password)
        if not csrf:
            print("❌ Failed to generate CSRF for Admin")
            sys.exit(0)
        self.api_csrf = csrf

    # -----------
    # Low level API access
    # -----------

    def _make_request(self, method: str, endpoint: str, data: dict[str, typing.Any] | None = None, additional_header: dict[str, typing.Any] | None = None) -> typing.Any:
        """Make authenticated API request."""

        url = f"{NODEBB_URL}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "x-csrf-token": self.api_csrf
        }

        # Add header (TODO REMOVE)
        if additional_header:
            headers |= additional_header

        # Need data
        if data is None:
            data = {}

        # Add precious csrf
        data["_csrf"] = self.api_csrf

        #  print(f"{url=} {headers=} {data=}")

        try:

            match method:
                case "GET":
                    response = self.get(url, headers=headers, timeout=TIMEOUT)
                case "POST":
                    response = self.post(url, headers=headers, json=data, timeout=TIMEOUT)
                case "DELETE":
                    response = self.delete(url, headers=headers, timeout=TIMEOUT)
                case "PUT":
                    response = self.put(url, headers=headers, json=data, timeout=TIMEOUT)
                case _:
                    raise ValueError(f"Unsupported method: {method}")

        except Exception as e:   # pylint: disable=broad-exception-caught
            print(f"❌ Request error: {e} ({url=} {method=} {data=})")
            return None

        if response.status_code not in [200, 201]:
            print(f"❌ API Error ({response.status_code}): {response.text} ({url=} {method=} {data=})")
            return None

        return response.json()

    # -----------
    # CSRF
    # -----------

    def generate_csrf(self, username: str, password: str) -> str:
        """Fetching Initial CSRF."""

        # Get config
        r_config = self.get(f"{NODEBB_URL}/api/config")
        init_data = r_config.json()
        csrf = init_data.get('csrf_token')
        if not csrf:
            print("❌ Upload error: Failed to get initial CSRF token.")
            return ''

        # Log In
        login_payload = {
            "username": username,
            "password": password,
            "_csrf": csrf
        }
        r_login = self.post(f"{NODEBB_URL}/login", data=login_payload)
        if r_login.status_code != 200:
            print("❌ Upload error: Failed to log in.")
            return ''

        # Checkig login ok
        r_api_config = self.get(f"{NODEBB_URL}/api/config")
        config_data = r_api_config.json()
        is_logged_in = config_data.get('loggedIn', False)
        if not is_logged_in:
            print("❌ Upload error: Login failed: Check credentials or CSRF handling.")
            return ''

        # Return it : so precious
        return str(config_data.get('csrf_token'))

    # -----------
    # Getters all
    # -----------

    def get_all_users(self) -> list[dict[str, typing.Any]]:
        """Get all users (a page actually)."""
        result = self._make_request("GET", "/api/users")
        return list(result['users']) if result else []

    def get_all_categories(self) -> list[dict[str, typing.Any]]:
        """Get all categories (a page actually)."""
        result = self._make_request("GET", "/api/categories")
        return list(result['categories']) if result else []

    def get_all_topics(self) -> list[dict[str, typing.Any]]:
        """Get all topics (a page actually)."""
        result = self._make_request("GET", "/api/recent")
        return list(result['topics']) if result else []

    def get_all_posts(self) -> list[dict[str, typing.Any]]:
        """Get all posts (a page actually)."""
        result = self._make_request("GET", "/api/recent/posts")
        return list(result) if result else []

    # -----------
    # Deleters
    # -----------

    def delete_user(self, uid: int) -> bool:
        """Delete a user (except admin)."""
        print(f"🗑️  Deleting user {uid}...")
        result = self._make_request("DELETE", f"/api/v3/users/{uid}")
        return result is not None

    def delete_category(self, cid: int) -> bool:
        """Delete a category."""
        print(f"🗑️  Deleting category {cid}...")
        result = self._make_request("DELETE", f"/api/v3/categories/{cid}")
        return result is not None

    def delete_topic(self, tid: int) -> bool:
        """Delete a topic."""
        print(f"🗑️  Deleting topic {tid}...")
        result = self._make_request("DELETE", f"/api/v3/topics/{tid}")
        return result is not None

    def delete_post(self, pid: int) -> bool:
        """Delete a post."""
        print(f"🗑️  Deleting post {pid}...")
        result = self._make_request("DELETE", f"/api/v3/posts/{pid}")
        return result is not None

    # -----------
    # Creaters
    # -----------

    def create_user(self, username: str, email: str, password: str) -> int | None:
        """Create a new user."""

        user_data = {
            "username": username,
            "password": password,
            "email": email,
        }
        result = self._make_request("POST", "/api/v3/users", data=user_data)
        if result and 'response' in result:
            return int(result['response']['uid'])
        return None

    def create_category(self, name: str, description: str = "", parent_cid: int = 0, order: int = 0) -> int | None:
        """Create a new category."""

        category_data = {
            "name": name,
            "description": description,
            "parentCid": parent_cid,
            "order": order
        }
        result = self._make_request("POST", "/api/v3/categories", data=category_data)
        if result and 'response' in result:
            return int(result['response']['cid'])
        return None

    def create_topic(self, cid: int, title: str, content: str, timestamp: int, tags: list[str]) -> tuple[int, int] | None:
        """Create a new topic."""

        topic_data = {
            "cid": cid,
            "title": title,
            "timestamp": timestamp * 1000,
            "content": content,
            "tags": tags
        }

        result = self._make_request("POST", "/api/v3/topics", data=topic_data)
        if result and 'response' in result:
            return int(result['response']['tid']), int(result['response']['mainPid'])
        return None

    def create_post(self, tid: int, content: str, timestamp: int) -> int | None:
        """Create a reply post."""

        post_data = {
            "content": content,
            "timestamp": timestamp * 1000
        }

        result = self._make_request("POST", f"/api/v3/topics/{tid}", data=post_data)
        if result and 'response' in result:
            return int(result['response']['pid'])
        return None

    # -----------
    # Editers (readers / writers)
    # -----------

    def get_topic_first_post(self, tid: int) -> int | None:
        """Extract first post of a topic."""

        result = self._make_request("GET", f"/api/v3/topics/{tid}")
        if result and 'response' in result:
            return int(result['response']['mainPid'])
        return None

    def get_post_content(self, pid: int) -> str | None:
        """Extract a post."""

        result = self._make_request("GET", f"/api/v3/posts/{pid}")
        if result and 'response' in result:
            return str(result['response']['content'])
        return None

    def put_post_content(self, pid: int, new_content: str) -> bool:
        """Update/patch a post."""

        edit_data = {
            "content": new_content
        }

        result = self._make_request("PUT", f"/api/v3/posts/{pid}", data=edit_data)
        return result is not None

    # -----------
    # Avatar
    # -----------

    def add_avatar_user(self, uid: int, url_used: str) -> bool:
        """Add avatar to user."""

        avatar_data = {
            "type": "external",
            "url": url_used,
            "bgColor": "0xAAAAAA",  # does not seem to work
        }

        # use csrf
        result = self._make_request("PUT", f"/api/v3/users/{uid}/picture", data=avatar_data)
        return result is not None

    # -----------
    # Signature
    # -----------

    def add_signature_user(self, uid: int, signature: str) -> bool:
        """Add signature to user."""

        user_data = {
            "signature": signature,
        }

        # use csrf
        result = self._make_request("PUT", f"/api/v3/users/{uid}", data=user_data)
        return result is not None

    # -----------
    # Verifying
    # -----------

    def set_user_verified(self, uid: int) -> bool:
        """Set user acoucnt (email) as verified (otherwise may not do much)."""

        user_data = {
            "emailConfirmed": True,
        }

        result = self._make_request("PUT", f"/api/v3/users/{uid}", data=user_data)
        return result is not None

    # -----------
    # Tweaks
    # -----------
    def set_inter_post_delay(self, fast: bool) -> bool:
        """Set delay between posts."""

        config_data = {
            "value": 0 if fast else 10
        }

        result = self._make_request("PUT", "/api/v3/admin/settings/postDelay", data=config_data)
        return result is not None

    def increase_allowed_extensions(self) -> bool:
        """Add some extensions."""

        original_list = ['png', 'jpg', 'bmp', 'txt', 'webp', 'webm', 'mp4', 'gif']
        added_list = ['pdf', 'zip']
        config_data = {
            "value": ','.join(original_list + added_list)
        }

        result = self._make_request("PUT", "/api/v3/admin/settings/fileUpload.allowedExtensions", data=config_data)
        print(f"result of request to add extensions = {result}")
        return result is not None

    # -----------
    # Uploaders
    # -----------

    def upload_file(self, file_path: pathlib.Path, uid: int) -> str | None:
        """Upload a file and return its URL."""

        if not file_path.exists():
            print(f"❌ Upload error: File does not exist {file_path=}")
            return None

        # If file does not have extension, find it to add to file name
        if file_path.suffix:
            file_path_used = file_path
            ext = file_path.suffix
        else:
            try:
                mime = magic.from_file(str(file_path), mime=True)
            except:  # noqa: E722 pylint: disable=bare-except
                print(f"❌ Upload error: Could not find file extension of {file_path=} (Exception)")
                return None

            if mime is None:
                print(f"❌ Upload error: Could not find file extension of {file_path=} (None)")
                return None
            ext_guessed = mimetypes.guess_extension(mime)
            if ext_guessed is None:
                print(f"❌ Upload error: Unknown file extension of {file_path=}")
                return None
            file_path_used = file_path.with_suffix(ext_guessed)
            ext = ext_guessed  # for error display

        # Build url
        url = f"{NODEBB_URL}/api/post/upload"

        # Upload the file
        with open(file_path, "rb") as file_ptr:
            files: dict[str, tuple[str, typing.BinaryIO, str]] = {"files[]": (str(file_path_used), file_ptr, "text/plain")}
            data = {"_csrf": self.api_csrf}
            r_upload = self.post(url, files=files, data=data)

        if r_upload.status_code not in [200, 201]:
            print(f"❌ Upload failed: {r_upload.json()=} {ext=} {file_path=} {url=} {uid=} {data=}")
            return None

        return str(r_upload.json()['response']['images'][0]['url'])


def set_import_configuration(session: NodeBBApiSession) -> None:
    """Need some tweaking beforehand."""

    session.set_inter_post_delay(fast=True)
    session.increase_allowed_extensions()  # does not work


def set_operational_configuration(session: NodeBBApiSession) -> None:
    """Cancel tweaking beforehand."""

    session.set_inter_post_delay(fast=False)


# Charger le modèle français (le modèle 'sm' est léger et rapide)
NATURAL_LANGUAGE_PARSER = spacy.load("fr_core_news_sm")
TEXT_SIZE_LIMIT_TAG = 30
TAG_LIMIT = 3


def get_tags_from_title_and_content(text: str) -> list[str]:
    """Calculate automatic tags."""

    if not text or len(text) < TEXT_SIZE_LIMIT_TAG:  # Ignore too short posts
        return []

    doc = NATURAL_LANGUAGE_PARSER(text)

    # Intelligent extraction  :
    # Take second names(PROPN) and common names (NOUN)
    # Exclude "stop words" (le, de, alors...)
    keywords = [token.lemma_.lower() for token in doc if token.pos_ in ("NOUN", "PROPN") and not token.is_stop and len(token.text) > 2]

    # Récupérer les mots les plus fréquents
    most_common = [tag for tag, count in collections.Counter(keywords).most_common(TAG_LIMIT)]
    return most_common


# -------------------------
# Main Import Functions
# -------------------------
def clear_existing_data(session: NodeBBApiSession) -> None:
    """Clear all existing posts, topics, categories, and users (except admin)."""

    print("\n" + "=" * 50)
    print("🧹 CLEARING EXISTING DATA")
    print("=" * 50)

    # 1. Delete all posts
    print("\n🗑️  Deleting posts...")
    while True:
        posts = session.get_all_posts()
        if not posts:
            break
        for post in posts:
            with delayed_ctrl_c():
                session.delete_post(post['pid'])

    # 2. Delete all topics
    print("\n🗑️  Deleting topics...")
    while True:
        topics = session.get_all_topics()
        if not topics:
            break
        for topic in topics:
            with delayed_ctrl_c():
                session.delete_topic(topic['tid'])

    # 3. Delete all categories
    print("\n🗑️  Deleting categories...")
    while True:
        categories = session.get_all_categories()
        if not categories:
            break
        for category in categories:
            with delayed_ctrl_c():
                session.delete_category(int(category['cid']))

    # 4. Delete all users (except admin)
    print("\n🗑️  Deleting users...")
    while True:
        users = session.get_all_users()
        if len(users) <= 1:
            break
        for user in users:
            if user['uid'] == ADMIN_UID:
                print(f"⚠️  Skipping admin user {user['uid']}")
                continue
            with delayed_ctrl_c():
                session.delete_user(user['uid'])

    print("✅ Data cleared successfully")


def import_users(db: NodeBBMongoDB, session: NodeBBApiSession, data_path: pathlib.Path) -> tuple[dict[int, int], dict[int, tuple[str, str]]]:
    """Import users from CSV and return mapping old_uid -> new_uid and new_uid."""

    print("\n" + "=" * 50)
    print("👤 IMPORTING USERS")
    print("=" * 50)

    users_csv = data_path / "users.csv"
    if not users_csv.exists():
        print(f"❌ Users CSV not found: {users_csv}")
        return {}, {}

    df_users = pd.read_csv(users_csv, encoding=CSV_ENCODING)
    user_map: dict[int, int] = {}  # old_uid -> new_uid

    print(f"Found {len(df_users)} users to import")

    password_list: list[dict[str, typing.Any]] = []
    credential_map: dict[int, tuple[str, str]] = {}

    for _, row in df_users.iterrows():

        # directly
        old_uid = int(row['user_id'])
        username = str(row['username']).strip()
        email = str(row['email']).strip()

        # indirectly
        signature = str(row['signature']).strip()

        print(f"  Creating user: {username}")

        # Create user via API
        plain_password = generate_random_password()

        new_uid = session.create_user(username, email, plain_password)

        if not new_uid:
            print(f"    ❌ Failed to create {username}")
            continue

        user_map[old_uid] = new_uid
        print(f"    ✅ Created (UID: {new_uid})")

        # Store password for admin reference
        password_list.append({
            "user_id": new_uid,
            "username": username,
            "email": email,
            "password": plain_password,
        })

        # give some reputation to user (otherwise cannot post)
        if not db.give_enough_reputation(new_uid):
            print(f"    ❌ Failed to give reputation for {username}")
        print("    ✅ Given some reputation too!")

        # put signature to user
        if signature != 'nan':
            # For some reason no signature comes out as 'nan' (probably declared as integer)
            signature, _ = converter.convert(signature)
            if not session.add_signature_user(new_uid, signature):
                print(f"    ❌ Failed to add signature for {username}")
            print("    ✅ Added signature too!")

        # set user as verify
        if not session.set_user_verified(new_uid):
            print(f"    ❌ Failed to set user as verified for {username}")
        print("    ✅ Set as verified too!")

        credential_map[new_uid] = (username, plain_password)

    save_passwords_to_file(password_list)

    print(f"\n✅ Imported {len(user_map)} users with random passwords")
    return user_map, credential_map


def import_categories(session: NodeBBApiSession, data_path: pathlib.Path) -> dict[int, int]:
    """Import categories from CSV and return mapping old_cid -> new_cid."""

    print("\n" + "=" * 50)
    print("📂 IMPORTING CATEGORIES")
    print("=" * 50)

    categories_csv = data_path / "forums.csv"  # In exported database these are called 'forums'
    if not categories_csv.exists():
        print(f"❌ Forums CSV not found: {categories_csv}")
        return {}

    df_categories = pd.read_csv(categories_csv, encoding=CSV_ENCODING)
    category_map: dict[int, int] = {}  # old_cid -> new_cid

    print(f"Found {len(df_categories)} categories to import")

    # First import parent categories
    parent_categories = {}
    for _, row in df_categories.iterrows():
        if int(row['parentCid']) == 0:
            old_cid = int(row['cid'])
            name = str(row['name']).strip()
            description: str = str(row['description']).strip() if pd.notna(row['description']) else ""
            order = int(row.get('display_order', 0))

            print(f"  Creating parent category: {name}")
            new_cid = session.create_category(name, description, 0, order)
            if new_cid:
                category_map[old_cid] = new_cid
                parent_categories[old_cid] = new_cid
                print(f"    ✅ Created (CID: {new_cid})")

                # DEBUG
                print(f"CATEGORY (parent)-----------> {old_cid=} {new_cid=}", file=sys.stderr)

            else:
                print(f"    ❌ Failed to create {name}")

    # Then import child categories
    for _, row in df_categories.iterrows():
        parent_cid = int(row['parentCid'])
        if parent_cid != 0 and parent_cid in parent_categories:
            old_cid = int(row['cid'])
            name = str(row['name']).strip()
            description = str(row['description']).strip() if pd.notna(row['description']) else ""
            order = int(row.get('display_order', 0))

            print(f"  Creating child category: {name}")

            new_cid = session.create_category(name, description, parent_categories[parent_cid], order)
            if new_cid:
                category_map[old_cid] = new_cid
                print(f"    ✅ Created (CID: {new_cid})")

                # DEBUG
                print(f"CATEGORY (child)-----------> {old_cid=} {new_cid=}", file=sys.stderr)

            else:
                print(f"    ❌ Failed to create {name}")

    print(f"\n✅ Imported {len(category_map)} categories")
    return category_map


def import_topics_and_posts(admin_session: NodeBBApiSession, data_path: pathlib.Path, user_map: dict[int, int], category_map: dict[int, int], credential_map: dict[int, tuple[str, str]], session_map: dict[int, NodeBBApiSession]) -> tuple[list[int], list[int], dict[int, int], dict[int, int]]:
    """Import topics and posts from CSV files."""

    print("\n" + "=" * 50)
    print("📝 IMPORTING TOPICS & POSTS")
    print("=" * 50)

    # Load topics
    topics_csv = data_path / "topics.csv"
    if not topics_csv.exists():
        print(f"❌ Topics CSV not found: {topics_csv}")
        return [], [], {}, {}

    df_topics = pd.read_csv(topics_csv, encoding=CSV_ENCODING)
    print(f"Found {len(df_topics)} topics to import")

    # Load posts
    posts_csv = data_path / "posts.csv"
    if not posts_csv.exists():
        print(f"❌ Posts CSV not found: {posts_csv}")
        return [], [], {}, {}

    df_posts = pd.read_csv(posts_csv, encoding=CSV_ENCODING)
    df_posts['timestamp'] = df_posts['timestamp'].astype(int)
    df_posts = df_posts.sort_values(by='timestamp').reset_index(drop=True)  # ascending is the default
    print(f"Found {len(df_posts)} posts to import")

    # Group posts by topic
    posts_by_topic: dict[int, list[pd.Series[typing.Any]]] = {}  # pylint: disable=unsubscriptable-object
    for _, row in df_posts.iterrows():
        tid = int(row['tid'])
        if tid not in posts_by_topic:
            posts_by_topic[tid] = []
        posts_by_topic[tid].append(row)

    # Load attachments
    attachments_csv = data_path / "attachments.csv"
    if not attachments_csv.exists():
        print(f"❌ Attachments CSV not found: {attachments_csv}")
        return [], [], {}, {}

    df_attachments = pd.read_csv(attachments_csv, encoding=CSV_ENCODING)
    print(f"Found {len(df_attachments)} attachments to insert")

    # Group attachments by post/topic + real filename
    attachments_by_post_file: dict[tuple[int, str], str] = {}
    for _, row in df_attachments.iterrows():
        pid = int(row['pid'])
        real_filename = str(row['real_filename'])
        physical_filename = str(row['physical_filename'])
        if (pid, real_filename) in attachments_by_post_file:
            print(f"❌ Attachments conflict {pid=} {real_filename}")
            continue
        attachments_by_post_file[(pid, real_filename)] = physical_filename

    topic_map: dict[int, int] = {}  # old_tid -> new_tid
    post_map: dict[int, int] = {}  # old_pid -> new_pid
    topics_patch_list: list[int] = []  # topics with reference inside
    posts_patch_list: list[int] = []  # posts with reference inside

    # Import each topic
    success_count = 0
    for idx, topic_row in enumerate(df_topics.iterrows(), 1):

        _, row = topic_row
        old_tid = int(row['tid'])
        old_cid = int(row['cid'])
        old_uid = int(row['uid'])

        if old_uid == 1:  # the Libertor issue
            old_uid = 300

        # Skip if category doesn't exist in our maps
        if old_cid not in category_map:
            print(f"⚠️  Skipping topic {old_tid}: category {old_cid} not found")
            continue

        new_cid = category_map[old_cid]

        # Skip if user doesn't exist in our maps
        if old_uid not in user_map:
            print(f"⚠️  Skipping topic {old_tid}: user {old_uid} not found")
            continue

        new_uid = user_map[old_uid]

        # Check if this topic has posts
        if old_tid not in posts_by_topic or not posts_by_topic[old_tid]:
            print(f"⚠️  Skipping topic {old_tid}: no posts (should not happen)")
            continue

        # Create session if necessary
        if new_uid not in session_map:
            username, password = credential_map[new_uid]
            user_session = NodeBBApiSession(username, password)
            session_map[new_uid] = user_session
        else:
            user_session = session_map[new_uid]

        # Process first post (topic content)
        first_post = posts_by_topic[old_tid][0]
        old_pid_first_post = int(first_post['pid'])
        content = str(first_post['content'])
        timestamp = int(first_post['timestamp'])

        # conversion phpbb3 -> nodebb
        content, reference_present = converter.convert(content)

        # Handle attachments in first post
        content = process_attachments_in_post(admin_session, content, data_path, old_pid_first_post, new_uid, attachments_by_post_file)

        # Create topic
        title = str(row['title']).strip()
        title = html.unescape(title)

        # Tags
        generated_tags = get_tags_from_title_and_content(title + "\n" + content)

        result = user_session.create_topic(new_cid, title, content, timestamp, generated_tags)

        if not result:
            print(f"❌ Failed to create topic for {old_tid}")
            continue

        new_tid, main_pid = result

        print(f"\n📄 Topic {idx}/{len(df_topics)}: {row['title']}")

        # DEBUG
        print(f"TOPIC -----------> {old_tid=} {new_tid=} ({old_pid_first_post=} {main_pid=})", file=sys.stderr)

        topic_map[old_tid] = new_tid

        post_map[old_pid_first_post] = main_pid

        # DEBUG
        print(f"POST (main)-----------> {old_pid_first_post=} {main_pid=} added (topic {old_tid=} {new_tid=})", file=sys.stderr)

        # note topics to path later
        if reference_present:
            topics_patch_list.append(new_tid)

        success_count += 1

        # Create replies (remaining posts)
        if len(posts_by_topic[old_tid]) > 1:
            print(f"  Creating {len(posts_by_topic[old_tid]) - 1} replies...")

            for post_idx, post_row in enumerate(posts_by_topic[old_tid][1:], 2):

                old_post_pid = int(post_row['pid'])
                old_post_uid = int(post_row['uid'])

                if old_post_uid == 1:  # the Libertor issue
                    old_post_uid = 300

                if old_post_uid not in user_map:
                    print(f"❌ Failed to find post author {old_post_uid} in user_map")
                    continue

                post_uid = user_map[old_post_uid]
                post_content = str(post_row['content'])
                post_timestamp = int(post_row['timestamp'])

                # Create session if necessary
                if post_uid not in session_map:
                    username, password = credential_map[post_uid]
                    user_session2 = NodeBBApiSession(username, password)
                    session_map[post_uid] = user_session2
                else:
                    user_session2 = session_map[post_uid]

                # conversion phpbb3 -> nodebb
                post_content, reference_present = converter.convert(post_content)

                # Handle attachments in reply
                post_content = process_attachments_in_post(admin_session, post_content, data_path, old_post_pid, post_uid, attachments_by_post_file)

                # Create reply
                new_pid = user_session2.create_post(new_tid, post_content, post_timestamp)

                if not new_pid:
                    print(f"❌ Failed to create post for {old_post_pid}")
                    continue

                post_map[old_post_pid] = new_pid

                # DEBUG
                print(f"POST (reply)-----------> {old_post_pid=} {new_pid=} added (follows)", file=sys.stderr)

                # note topics to path later
                if reference_present:
                    posts_patch_list.append(new_pid)

                if post_idx % 10 == 0:
                    print(f"    Created {post_idx} replies...")

        # Progress indicator
        if idx % 10 == 0:
            print(f"===== Progress: {idx}/{len(df_topics)} topics imported")

    print(f"\n✅ Successfully imported {success_count}/{len(df_topics)} topics")
    return topics_patch_list, posts_patch_list, topic_map, post_map


def patch_topics_and_posts(admin_session: NodeBBApiSession, topics_patch_list: list[int], posts_patch_list: list[int], topic_map: dict[int, int], post_map: dict[int, int]) -> None:
    """Patch references from old forum to new forum."""

    def replace_tid(match: re.Match[str]) -> str:
        """Replace."""
        old_topic = int(match.group(1))
        if old_topic not in topic_map:
            print(f"❌ ERROR {old_topic=} not in topic_map")
            return f"{old_topic=}"
        topic = topic_map[old_topic]
        return f"{topic}"

    def replace_pid(match: re.Match[str]) -> str:
        """Replace."""
        old_post = int(match.group(1))
        if old_post not in post_map:
            print(f"❌ ERROR {old_post=} not in post_map")
            return f"{old_post=}"
        post = post_map[old_post]
        return f"{post}"

    patched_topics = 0
    for topic_id in topics_patch_list:
        #  print(f"patching {topic_id=}")
        first_post_id = admin_session.get_topic_first_post(topic_id)
        if not first_post_id:
            continue
        #  print(f"patching {first_post_id=}")
        content = admin_session.get_post_content(first_post_id)
        if not content:
            continue
        content = re.sub(r'\[old_tid_ref=(\d+)\]', replace_tid, content, flags=re.IGNORECASE)
        content = re.sub(r'\[old_pid_ref=(\d+)\]', replace_pid, content, flags=re.IGNORECASE)
        admin_session.put_post_content(first_post_id, content)
        patched_topics += 1
    print(f"\n✅ Successfully patched {patched_topics} topics")

    patched_posts = 0
    for post_id in posts_patch_list:
        #  print(f"patching {post_id=}")
        content = admin_session.get_post_content(post_id)
        if not content:
            continue
        content = re.sub(r'\[old_tid_ref=(\d+)\]', replace_tid, content, flags=re.IGNORECASE)
        content = re.sub(r'\[old_pid_ref=(\d+)\]', replace_pid, content, flags=re.IGNORECASE)
        admin_session.put_post_content(post_id, content)
        patched_posts += 1
    print(f"\n✅ Successfully patched {patched_posts} posts")


def import_avatars(admin_session: NodeBBApiSession, data_path: pathlib.Path, user_map: dict[int, int], credential_map: dict[int, tuple[str, str]], session_map: dict[int, NodeBBApiSession]) -> None:
    """Import user avatars."""

    def find_avatar_file(uid: int, avatars_dir: pathlib.Path) -> pathlib.Path | None:
        """Find avatar file (once you know the method used to store them)."""

        for file_name in os.listdir(avatars_dir):
            base, _ = os.path.splitext(file_name)
            if base.endswith(f"_{uid}"):
                return avatars_dir / file_name
        return None

    print("\n" + "=" * 50)
    print("🖼️  IMPORTING AVATARS")
    print("=" * 50)

    avatars_dir = data_path / "avatars"
    if not avatars_dir.exists():
        print(f"❌ Avatars directory not found: {avatars_dir}")
        return

    success_count = 0
    for old_uid, new_uid in user_map.items():

        # Look for avatar
        avatar_file = find_avatar_file(old_uid, avatars_dir)
        if avatar_file:

            # 1 Create session if necessary
            if new_uid not in session_map:
                username, password = credential_map[new_uid]
                user_session = NodeBBApiSession(username, password)
                session_map[new_uid] = user_session
            else:
                user_session = session_map[new_uid]

            # 2 upload file
            file_url = admin_session.upload_file(avatar_file, new_uid)  # strange: need to be admin for this !
            if not file_url:
                print("    ⚠️  Failed to upload avatar file")
                continue

            # 3 put as avatar
            if not user_session.add_avatar_user(new_uid, file_url):
                print("    ⚠️  Failed to put avatar")
                continue

            print("    ✅ Avatar uploaded")
            success_count += 1

    print(f"\n✅ Uploaded {success_count} avatars")


def process_attachments_in_post(admin_session: NodeBBApiSession, content: str, data_path: pathlib.Path, pid: int, uid: int, attachments_by_post_file: dict[tuple[int, str], str]) -> str:
    """Process [attachment=ID] tags and replace with uploaded file URLs."""

    def replace_attachment(match: re.Match[str]) -> str:
        """Deal with an attachment."""

        real_file = match.group(1)

        # Find and upload file
        if (pid, real_file) not in attachments_by_post_file:
            # File not found
            print(f"⚠️  Attachment file {real_file} not found {pid=}, skipping...")
            return f'[attachment {real_file} missing]'
        physical_filename = attachments_by_post_file[(pid, real_file)]
        complete_path = uploads_dir / physical_filename
        file_url = admin_session.upload_file(complete_path, uid)  # strange: need to be admin for this !
        if not file_url:
            # Failed to upload
            print(f"⚠️  Failed to upload attachment {pid=}, skipping...")
            return f'[attachment {real_file} failed to load]'
        # Create a clickable link
        link = f'![{real_file}]({file_url})'
        return link

    uploads_dir = data_path / "uploads"
    if not uploads_dir.exists():
        print(f"⚠️  Uploads directory {uploads_dir} not found, skipping...")
        return content

    pattern = r'<ATTACHMENT\s+filename="([^"]+)"[^>]*>([^<]+)</ATTACHMENT>'
    content = re.sub(pattern, replace_attachment, content)
    return content


# -------------------------
# Main
# -------------------------
def main() -> None:
    """Main."""

    start = time.time()

    print("🚀 NodeBB PHPBB Import Script")
    print("=" * 50)

    # Check data directory
    data_path = pathlib.Path(DATA_DIR)
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_path}")
        sys.exit(1)

    # Initialize DB client
    db = NodeBBMongoDB(MONGO_URI, NODEBB_DB)

    # Initialize API client
    admin_session = NodeBBApiSession(ADMIN_USERNAME, ADMIN_PASSWORD)

    # 1. Set tweak (as admin)
    print("1️⃣ Tweak config")
    set_import_configuration(admin_session)

    # 2. Clear existing data (as admin)
    print("2️⃣ Clearing existing data")
    clear_existing_data(admin_session)

    # 3. Import users, signatures, create map old -> new and map new -> user/pass (as admin)
    print("3️⃣ Import users")
    user_map, credential_map = import_users(db, admin_session, data_path)

    # 4. Import categories (as admin)
    print("4️⃣ Import categories")
    category_map = import_categories(admin_session, data_path)

    # We make sessions for users on the fly and memorize them for reuse
    session_map: dict[int, NodeBBApiSession] = {}

    # 5. Import topics and posts (and attachments)
    print("5️⃣ Import topics and posts")
    # First: do actual conversion
    topics_patch_list, posts_patch_list, topic_map, post_map = import_topics_and_posts(admin_session, data_path, user_map, category_map, credential_map, session_map)
    # Second: patch references (as admin : simpler)
    patch_topics_and_posts(admin_session, topics_patch_list, posts_patch_list, topic_map, post_map)

    # 6. Import avatars
    print("6️⃣ Import avatars")
    import_avatars(admin_session, data_path, user_map, credential_map, session_map)

    # 7. Unset tweak (as admin)
    print("1️⃣ Tweak config back")
    set_operational_configuration(admin_session)

    # 8. Close db
    print("1️⃣ Close db")
    db.close()

    print("\n" + "=" * 50)
    print("🎉 IMPORT COMPLETE!")
    print("=" * 50)
    print(f"   Users imported: {len(user_map)}")
    print(f"   Categories imported: {len(category_map)}")
    print(f"   Forum URL: {NODEBB_URL}")

    print("\n⚠️  IMPORTANT: Users should change their passwords!")

    end = time.time()
    elapsed = int(end - start)
    print(f"Time elapsed : {elapsed // 60} min {elapsed % 60} secs")


if __name__ == "__main__":
    main()
