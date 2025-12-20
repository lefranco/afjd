#!/usr/bin/env python3

"""
Complete NodeBB Importer using API v3.

Clears existing data and imports from phpBB CSV files
Need to have :
    phpbbexport/avatars = phpBB3/images/avatars/upload
    phpbbexport/uploads = phpBB3/files/
"""

import html
import os
import pathlib
import re
import secrets
import string
import sys
import time
import typing

import urllib3  # pip3 install urllib3 --break-system-packages
import pandas as pd  # pip3 install pandas --break-system-packages
import requests  # pip3 install requests --break-system-packages
import pymongo  # pip3 install pymongo --break-system-packages

import converter

# -------------------------
# CONFIGURATION
# -------------------------
NODEBB_URL = "https://forum.diplomania2.fr"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

MONGO_URI = "mongodb://nodebb:nodebb123@37.59.100.228:27017/nodebb"  # Your NodeBB MongoDB
NODEBB_DB = "nodebb"  # Your NodeBB database name

DATA_DIR = "./phpbb_export"
CSV_ENCODING = "utf-8"

# Rate limiting (seconds between API calls)
RATE_LIMIT = 0.2

# Get from admin interface
ADMIN_TOKEN = '8d72634b-fded-471d-95a7-adf26a38d2cf'

# Identify admin
ADMIN_UID = 1

# Be patient if server is busy
TIMEOUT = 30

# Suppress the warning messages in the console
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # at company only


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
        self.tweaked = False

    def set_account_creation_date(self, uid: int, timestamp: int) -> bool:
        """Set account creation."""

        timestamp_ms = timestamp * 1000
        result = self.db.objects.update_one(
            {"_key": f"user:{uid}"},
            {"$set": {"joined": timestamp_ms}}
        )
        self.tweaked = True
        return result.acknowledged

    def give_enough_reputation(self, uid: int) -> bool:
        """Give enough reputation (need 3 to post faster than every 120 seconds)."""

        reputation_value = 3
        result = self.db.objects.update_one(
            {"_key": f"user:{uid}"},
            {"$set": {"reputation": reputation_value}}
        )
        return result.acknowledged

    def set_post_creation_date(self, pid: int, timestamp: int) -> bool:
        """Set post creation date."""

        timestamp_ms = timestamp * 1000
        result = self.db.objects.update_one(
            {"_key": f"post:{pid}"},
            {"$set": {"timestamp": timestamp_ms}}
        )
        self.tweaked = True
        return result.acknowledged

    def set_topic_creation_date(self, tid: int, timestamp: int) -> bool:
        """Set topic creation date."""

        timestamp_ms = timestamp * 1000
        result = self.db.objects.update_one(
            {"_key": f"topic:{tid}"},
            {"$set": {"timestamp": timestamp_ms}}
        )
        self.tweaked = True
        return result.acknowledged

    def clean_stuck_delete_users(self) -> None:
        """ Because previously Ctrl-C caused damage """

        result = self.db.objects.update_many(
           {"deleting": {"$in": [True, "true"]}},
           {"$unset": {"deleting": ""}}
        )

        if result.modified_count:
            print(f"🧹 Cleaned: {result.modified_count} document(s)")


# -------------------------
# API Client
# -------------------------
class NodeBBApi:
    """Importer."""

    def __init__(self, base_url: str) -> None:
        """Connect to NodeBB's API."""

        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        # only in company
        self.session.verify = False   # at company only

        # Very important: at company only : Many company filters block the default 'python-requests' agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # generate csrf and keep it for later
        self.api_csrf = self._generate_csrf()
        self.token = ADMIN_TOKEN

    # -----------
    # Low level API access
    # -----------

    def _generate_csrf(self) -> str:
        """Fetching Initial CSRF."""

        # Get config
        r_config = self.session.get(f"{self.base_url}/api/config")
        init_data = r_config.json()
        csrf = init_data.get('csrf_token')
        if not csrf:
            print("❌ Upload error: Failed to get initial CSRF token.")
            return ''

        # Log In
        login_payload = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD,
            "_csrf": csrf
        }
        r_login = self.session.post(f"{self.base_url}/login", data=login_payload)
        if r_login.status_code != 200:
            print("❌ Upload error: Failed to log in.")
            return ''

        # Checkig login ok
        r_api_config = self.session.get(f"{self.base_url}/api/config")
        config_data = r_api_config.json()
        is_logged_in = config_data.get('loggedIn', False)
        if not is_logged_in:
            print("❌ Upload error: Login failed: Check credentials or CSRF handling.")
            return ''

        # Return it : so precious
        return str(config_data.get('csrf_token'))

    def _make_request(self, method: str, endpoint: str, data: dict[str, typing.Any] | None = None, specific_token: str | None = None) -> typing.Any:
        """Make authenticated API request."""

        time.sleep(RATE_LIMIT)

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {specific_token if specific_token else self.token}",
            "Content-Type": "application/json",
            "x-csrf-token": self.api_csrf
        }

        # Add precious csrf
        if data is None:
            data = {}
        data["_csrf"] = self.api_csrf

        try:

            match method:
                case "GET":
                    response = self.session.get(url, headers=headers, timeout=TIMEOUT)
                case "POST":
                    response = self.session.post(url, headers=headers, json=data, timeout=TIMEOUT)
                case "DELETE":
                    response = self.session.delete(url, headers=headers, timeout=TIMEOUT)
                case "PUT":
                    response = self.session.put(url, headers=headers, json=data, timeout=TIMEOUT)
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

    def get_all_posts_in_topics(self, pid: int) -> list[dict[str, typing.Any]]:
        """Get all posts in topic (a page actually)."""
        result = self._make_request("GET", f"/api/posts/{pid}/replies")
        return list(result['replies']) if result else []

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

    def revoke_token(self, uid: int, token: str) -> bool:
        """Revoke token of a user."""
        print(f"🗑️  Revoking user token {uid}...")
        result = self._make_request("DELETE", f"/api/v3/admin/tokens/{token}")
        return result is not None

    # -----------
    # Creaters
    # -----------

    def create_user(self, username: str, email: str, password: str) -> int | None:
        """Create a new user."""

        user_data = {
            "username": username,
            "password": password,
            "email": email
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

    def create_topic(self, cid: int, title: str, content: str, uid: int, user_tokens_map: dict[int, str]) -> int | None:
        """Create a new topic."""

        topic_data = {
            "cid": cid,
            "title": title,
            "content": content,
            "tags": []  # no tag for the moment, we be done manually after forum is operational
        }

        # To force author need to use token
        specific_token = user_tokens_map.get(uid, ADMIN_TOKEN)

        result = self._make_request("POST", "/api/v3/topics", data=topic_data, specific_token=specific_token)
        if result and 'response' in result:
            return int(result['response']['tid'])
        return None

    def create_post(self, tid: int, content: str, uid: int, user_tokens_map: dict[int, str]) -> int | None:
        """Create a reply post."""

        post_data = {
            "content": content,
        }

        # To force author need to use token
        specific_token = user_tokens_map.get(uid, ADMIN_TOKEN)

        result = self._make_request("POST", f"/api/v3/topics/{tid}", data=post_data, specific_token=specific_token)
        if result and 'response' in result:
            return int(result['response']['pid'])
        return None

    # -----------
    # Token
    # -----------

    def create_token(self, uid: int) -> str | None:
        """Create a new user."""

        token_data = {
            "uid": uid,
            "description": "temporary token"
        }

        result = self._make_request("POST", "/api/v3/admin/tokens", data=token_data)
        if result and 'response' in result:
            return str(result['response']['token'])
        return None

    # -----------
    # Avatar
    # -----------

    def add_avatar_user(self, uid: int, url_used: str) -> bool:
        """Add avatar to user."""

        avatar_data = {
            "picture": url_used,
        }

        result = self._make_request("PUT", f"/api/v3/users/{uid}", data=avatar_data)
        return result is not None

    # -----------
    # Signature
    # -----------

    def add_signature_user(self, uid: int, signature: str) -> bool:
        """Add signature to user."""

        user_data = {
            "signature": signature,
        }

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
    # Tweak
    # -----------
    def tweak(self, fast: bool) -> bool:
        """Tweak delay between posts."""

        config_data = {
            "value": 0 if fast else 10
        }

        result = self._make_request("PUT", "/api/v3/admin/settings/postDelay", data=config_data)
        return result is not None

    # -----------
    # Uploaders
    # -----------

    def upload_file(self, file_path: pathlib.Path, uid: int) -> str | None:
        """Upload a file and return its URL."""

        if not file_path.exists():
            print(f"❌ Upload error: File does not exist {file_path=}")
            return None

        # Upload the file
        with open(file_path, "rb") as file_ptr:
            files: dict[str, tuple[str, typing.BinaryIO, str]] = {"files[]": (str(file_path), file_ptr, "text/plain")}
            data = {"_csrf": self.api_csrf}
            r_upload = self.session.post(f"{self.base_url}/api/post/upload", files=files, data=data)

        if r_upload.status_code not in [200, 201]:
            print(f"❌ Upload failed: {r_upload.json()=} {file_path=} {uid=} {data=}")
            return None

        print("✅ File upload successful!")
        return str(r_upload.json()['response']['images'][0]['url'])


def tweak_configuration(api: NodeBBApi, fast: bool) -> None:
    """Need some tweaking beforehand."""
    api.tweak(fast)


# -------------------------
# Main Import Functions
# -------------------------
def clear_existing_data(db: NodeBBMongoDB, api: NodeBBApi) -> None:
    """Clear all existing posts, topics, categories, and users (except admin)."""

    print("\n" + "=" * 50)
    print("🧹 CLEARING EXISTING DATA")
    print("=" * 50)

    # 1. Clean stuk
    db.clean_stuck_delete_users()

    # 2. Delete all topics and posts
    print("\n🗑️  Deleting topics (and posts)...")
    while True:
        topics = api.get_all_topics()
        if not topics:
            break
        for topic in topics:
            api.delete_topic(topic['tid'])

    # 2. Delete all categories (except default ones)
    print("\n🗑️  Deleting categories...")
    while True:
        categories = api.get_all_categories()
        if not categories:
            break
        for category in categories:
            api.delete_category(int(category['cid']))

    # 3. Delete all users (except admin)
    print("\n🗑️  Deleting users...")
    while True:
        users = api.get_all_users()
        if len(users) <= 1:
            break
        for user in users:
            if user['uid'] == ADMIN_UID:
                print(f"⚠️  Skipping admin user {user['uid']}")
                continue
            api.delete_user(user['uid'])

    print("✅ Data cleared successfully")


def import_users(db: NodeBBMongoDB, api: NodeBBApi, data_path: pathlib.Path) -> tuple[dict[int, int], dict[int, str]]:
    """Import users from CSV and return mapping old_uid -> new_uid and new_uid -> temporary token."""

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
    user_tokens_map: dict[int, str] = {}

    for _, row in df_users.iterrows():

        # directly
        old_uid = int(row['user_id'])
        username = str(row['username']).strip()
        email = str(row['email']).strip()

        # indirectly
        timestamp = int(row['joindate'])
        signature = str(row['signature']).strip()

        print(f"  Creating user: {username}")

        # Create user via API
        plain_password = generate_random_password()

        new_uid = api.create_user(username, email, plain_password)

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

        # create a token for user and store it
        token_uid = api.create_token(new_uid)
        if not token_uid:
            print(f"    ❌ Failed to create token for {username}")
            continue
        user_tokens_map[new_uid] = token_uid
        print("    ✅ Created token too!")

        # set creation date to user
        if not db.set_account_creation_date(new_uid, timestamp):
            print(f"    ❌ Failed to set creation date for {username}")
        print("    ✅ Set account creation date too!")

        # give some reputation to user (otherwise cannot post)
        if not db.give_enough_reputation(new_uid):
            print(f"    ❌ Failed to give reputation for {username}")
        print("    ✅ Given some reputation too!")

        # put signature to user
        signature = converter.convert(signature)
        if not api.add_signature_user(new_uid, signature):
            print(f"    ❌ Failed to add signature for {username}")
        print("    ✅ Added signature too!")

        # set user as verify
        if not api.set_user_verified(new_uid):
            print(f"    ❌ Failed to set user as verified for {username}")
        print("    ✅ Added to registered group too!")

    save_passwords_to_file(password_list)

    print(f"\n✅ Imported {len(user_map)} users with random passwords")
    return user_map, user_tokens_map


def import_categories(api: NodeBBApi, data_path: pathlib.Path) -> dict[int, int]:
    """Import categories from CSV and return mapping old_cid -> new_cid."""

    print("\n" + "=" * 50)
    print("📂 IMPORTING CATEGORIES")
    print("=" * 50)

    forums_csv = data_path / "forums.csv"
    if not forums_csv.exists():
        print(f"❌ Forums CSV not found: {forums_csv}")
        return {}

    df_forums = pd.read_csv(forums_csv, encoding=CSV_ENCODING)
    category_map = {}  # old_cid -> new_cid

    print(f"Found {len(df_forums)} categories to import")

    # First import parent categories
    parent_categories = {}
    for _, row in df_forums.iterrows():
        if int(row['parentCid']) == 0:
            old_cid = int(row['cid'])
            name = str(row['name']).strip()
            description = str(row['description']).strip() if pd.notna(row['description']) else ""
            order = int(row.get('display_order', 0))

            print(f"  Creating parent category: {name}")

            new_cid = api.create_category(name, description, 0, order)
            if new_cid:
                category_map[old_cid] = new_cid
                parent_categories[old_cid] = new_cid
                print(f"    ✅ Created (CID: {new_cid})")
            else:
                print(f"    ❌ Failed to create {name}")

    # Then import child categories
    for _, row in df_forums.iterrows():
        parent_cid = int(row['parentCid'])
        if parent_cid != 0 and parent_cid in parent_categories:
            old_cid = int(row['cid'])
            name = str(row['name']).strip()
            description = str(row['description']).strip() if pd.notna(row['description']) else ""
            order = int(row.get('display_order', 0))

            print(f"  Creating child category: {name}")

            new_cid = api.create_category(name, description, parent_categories[parent_cid], order)
            if new_cid:
                category_map[old_cid] = new_cid
                print(f"    ✅ Created (CID: {new_cid})")
            else:
                print(f"    ❌ Failed to create {name}")

    print(f"\n✅ Imported {len(category_map)} categories")
    return category_map


def import_topics_and_posts(db: NodeBBMongoDB, api: NodeBBApi, data_path: pathlib.Path, user_map: dict[int, int], user_tokens_map: dict[int, str], category_map: dict[int, int]) -> None:
    """Import topics and posts from CSV files."""

    print("\n" + "=" * 50)
    print("📝 IMPORTING TOPICS & POSTS")
    print("=" * 50)

    # Load topics
    topics_csv = data_path / "topics.csv"
    if not topics_csv.exists():
        print(f"❌ Topics CSV not found: {topics_csv}")
        return

    df_topics = pd.read_csv(topics_csv, encoding=CSV_ENCODING)
    print(f"Found {len(df_topics)} topics to import")

    # Load posts
    posts_csv = data_path / "posts.csv"
    if not posts_csv.exists():
        print(f"❌ Posts CSV not found: {posts_csv}")
        return

    df_posts = pd.read_csv(posts_csv, encoding=CSV_ENCODING)
    df_posts = df_posts.sort_values('timestamp', ascending=True)
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
    if not posts_csv.exists():
        print(f"❌ Attachments CSV not found: {posts_csv}")
        return

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

        # Skip if user doesn't exist in our maps
        if old_uid not in user_map:
            print(f"⚠️  Skipping topic {old_tid}: user {old_uid} not found")
            continue

        new_cid = category_map[old_cid]
        new_uid = user_map[old_uid]

        # Check if this topic has posts
        if old_tid not in posts_by_topic or not posts_by_topic[old_tid]:
            print(f"⚠️  Skipping topic {old_tid}: no posts")
            continue

        print(f"\n📄 Topic {idx}/{len(df_topics)}: {row['title']}")

        # Process first post (topic content)
        first_post = posts_by_topic[old_tid][0]
        old_pid_first_post = int(first_post['pid'])
        content = str(first_post['content'])
        timestamp = int(first_post['timestamp'])

        # conversion phpbb3 -> nodebb
        content = converter.convert(content)

        # Handle attachments in first post
        content = process_attachments_in_post(api, content, data_path, old_pid_first_post, new_uid, attachments_by_post_file)

        # Create topic
        title = str(row['title']).strip()
        title = html.unescape(title)

        new_tid = api.create_topic(new_cid, title, content, new_uid, user_tokens_map)

        if not new_tid:
            print(f"❌ Failed to create topic for {old_tid}")
            continue

        if not db.set_topic_creation_date(new_tid, timestamp):
            print(f"❌ Failed to set topic creation date {new_tid}")

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

                # conversion phpbb3 -> nodebb
                post_content = converter.convert(post_content)

                # Handle attachments in reply
                post_content = process_attachments_in_post(api, post_content, data_path, old_post_pid, post_uid, attachments_by_post_file)

                # Create reply
                new_pid = api.create_post(new_tid, post_content, post_uid, user_tokens_map)

                if not new_pid:
                    print(f"❌ Failed to create post for {old_post_pid}")
                    continue

                if not db.set_post_creation_date(new_pid, post_timestamp):
                    print(f"❌ Failed to set post creation date {new_pid}")

                if post_idx % 10 == 0:
                    print(f"    Created {post_idx} replies...")

        # Progress indicator
        if idx % 10 == 0:
            print(f"===== Progress: {idx}/{len(df_topics)} topics imported")

    print(f"\n✅ Successfully imported {success_count}/{len(df_topics)} topics")


def import_avatars(api: NodeBBApi, data_path: pathlib.Path, user_map: dict[int, int]) -> None:
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
        print("⚠️  Avatars directory not found, skipping...")
        return

    success_count = 0
    for old_uid, new_uid in user_map.items():
        # Look for avatar
        avatar_file = find_avatar_file(old_uid, avatars_dir)
        if avatar_file:

            # 1 upload file
            file_url = api.upload_file(avatar_file, new_uid)
            if not file_url:
                print("    ⚠️  Failed to upload avatar file")
                continue

            # 2 put as avatar
            if not api.add_avatar_user(new_uid, file_url):
                print("    ⚠️  Failed to put avatar")
                continue

            print("    ✅ Avatar uploaded")
            success_count += 1

    print(f"\n✅ Uploaded {success_count} avatars")


def process_attachments_in_post(api: NodeBBApi, content: str, data_path: pathlib.Path, pid: int, uid: int, attachments_by_post_file: dict[tuple[int, str], str]) -> str:
    """Process [attachment=ID] tags and replace with uploaded file URLs."""

    def replace_attachment(match: re.Match[str]) -> str:
        """Deal with an attachment."""

        real_file = match.group(1)

        # Find and upload file
        if (pid, real_file) not in attachments_by_post_file:
            # File not found
            print("⚠️  Attachment file not found, skipping...")
            return f'[attachment {real_file} missing]'
        physical_filename = attachments_by_post_file[(pid, real_file)]
        complete_path = uploads_dir / physical_filename
        file_url = api.upload_file(complete_path, uid)
        if not file_url:
            # Failed to upload
            print("⚠️  Failed to upload attachment, skipping...")
            return f'[attachment {real_file} failed to load]'
        # Create a clickable link
        link = f'[{real_file}]({file_url})'
        return link

    uploads_dir = data_path / "uploads"
    if not uploads_dir.exists():
        print("⚠️  Uploads directory not found, skipping...")
        return content

    pattern = r'<ATTACHMENT\s+filename="([^"]+)"[^>]*>([^<]+)</ATTACHMENT>'
    content = re.sub(pattern, replace_attachment, content)
    return content


def revoke_user_tokens(api: NodeBBApi, user_tokens_map: dict[int, str]) -> None:
    """Revoke users tokens that were necessary."""

    print("\n" + "=" * 50)
    print("👤 REVOKING TEMPORARY USERS TOKENS")
    print("=" * 50)

    for uid, token in user_tokens_map.items():
        api.revoke_token(uid, token)


# -------------------------
# Main
# -------------------------
def main() -> None:
    """Main."""

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
    api = NodeBBApi(NODEBB_URL)

    # Ask for confirmation
    print("\n⚠️  WARNING: This will DELETE ALL EXISTING DATA!")
    print("   (categories, topics, posts, and non-admin users)")
    response = 'y'  # TEMPORARY input("   Continue? (y/N): ")

    if response.lower() != 'y':
        print("❌ Import cancelled")
        sys.exit(0)

    # 1. Set tweak
    print("1️⃣ Tweak config")
    tweak_configuration(api, True)

    # 2. Clear existing data
    print("2️⃣ Clearing existing data")
    clear_existing_data(db, api)

    return

    # 2. Import users, signatures, create temporary tokens and create map
    print("3️⃣ Import users")
    user_map, user_tokens_map = import_users(db, api, data_path)

    # 3. Import avatars
    print("4️⃣ Import avatars")
    import_avatars(api, data_path, user_map, user_tokens_map)

    # 4. Import categories
    print("5️⃣ Import categories")
    category_map = import_categories(api, data_path)

    # 5. Import topics and posts (and attachments)
    print("6️⃣ Import topics and posts")
    import_topics_and_posts(db, api, data_path, user_map, user_tokens_map, category_map)

    # 6. Revoke temporary tokens
    print("7️⃣ Revoking temporary tokens")
    revoke_user_tokens(api, user_tokens_map)

    # 7. Set tweak
    print("1️⃣ Tweak config")
    tweak_configuration(api, False)

    print("\n" + "=" * 50)
    print("🎉 IMPORT COMPLETE!")
    print("=" * 50)
    print(f"   Users imported: {len(user_map)}")
    print(f"   Categories imported: {len(category_map)}")
    print(f"   Forum URL: {NODEBB_URL}")

    if db.tweaked:
        print("🚀 Some direct operations on Mongo database were performed.")
        print("   TODO : ./nodebb stop + ./nodebb build + ./nodebb start.")
    print("\n⚠️  IMPORTANT: Users should change their passwords!")


if __name__ == "__main__":
    main()
