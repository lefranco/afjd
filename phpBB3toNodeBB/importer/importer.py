#!/usr/bin/env python3

"""
Complete NodeBB Importer using API v3
Clears existing data and imports from phpBB CSV files
"""

import time
import pathlib
import re
import sys
import secrets
import string

import requests
import pandas as pd

# -------------------------
# CONFIGURATION
# -------------------------
NODEBB_URL = "https://forum.diplomania2.fr"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

DATA_DIR = "./phpbb_export"
CSV_ENCODING = "utf-8"

# Rate limiting (seconds between API calls)
RATE_LIMIT = 0.1

# Get from admin interface
TOKEN = '8d72634b-fded-471d-95a7-adf26a38d2cf'

# Identify admin
ADMIN_UID = 1

# Be patient if server is busy
TIMEOUT = 30


# -------------------------
# Tools
# -------------------------
def generate_random_password() -> str:
    """Generate a secure random password."""

    pass_length = 8
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for _ in range(pass_length))
    return password


def save_passwords_to_file(password_list: list[dict]):
    """Save generated passwords to a secure CSV file."""

    # Create a CSV for usage
    csv_file = "user_passwords.csv"
    df = pd.DataFrame(password_list)
    df.to_csv(csv_file, index=False)
    print(f"🔐 Generated passwords saved to: {csv_file}")

    # Security warning
    print("⚠️  SECURITY WARNING: This file contain plain-text passwords!")
    print("   Secure or delete it immediately after distributing passwords.")


def convert_bbcode_to_nodebb(content: str) -> str:
    """Convert phpBB BBCode to NodeBB format."""

    if not isinstance(content, str):
        return str(content) if content else ""

    # Preserve line breaks
    content = content.replace('\n', '<br>')

    # Bold: [b]text[/b] → **text**
    content = re.sub(r'\[b\](.*?)\[/b\]', r'**\1**', content, flags=re.IGNORECASE)

    # Italic: [i]text[/i] → *text*
    content = re.sub(r'\[i\](.*?)\[/i\]', r'*\1*', content, flags=re.IGNORECASE)

    # Underline: [u]text[/u] → <u>text</u>
    content = re.sub(r'\[u\](.*?)\[/u\]', r'<u>\1</u>', content, flags=re.IGNORECASE)

    # Strikethrough: [s]text[/s] → ~~text~~
    content = re.sub(r'\[s\](.*?)\[/s\]', r'~~\1~~', content, flags=re.IGNORECASE)

    # Code blocks: [code]text[/code] → ```text```
    content = re.sub(r'\[code\](.*?)\[/code\]', r'```\1```', content, flags=re.IGNORECASE)

    # Inline code: [inline]text[/inline] → `text`
    content = re.sub(r'\[inline\](.*?)\[/inline\]', r'`\1`', content, flags=re.IGNORECASE)

    # Quotes: [quote]text[/quote] → > text
    # Multi-line quote handling
    def replace_quote(match):
        quote_text = match.group(1).strip()
        # Add > to each line
        lines = quote_text.split('<br>')
        quoted_lines = [f'> {line}' if line.strip() else '>' for line in lines]
        return '<br>'.join(quoted_lines)

    content = re.sub(r'\[quote\](.*?)\[/quote\]', replace_quote, content, flags=re.IGNORECASE | re.DOTALL)

    # URLs: [url]http://...[/url] → http://...
    content = re.sub(r'\[url\](.*?)\[/url\]', r'\1', content, flags=re.IGNORECASE)

    # URLs with text: [url=http://...]text[/url] → [text](http://...)
    content = re.sub(r'\[url=(.*?)\](.*?)\[/url\]', r'[\2](\1)', content, flags=re.IGNORECASE)

    # Images: [img]http://...[/img] → ![](http://...)
    content = re.sub(r'\[img\](.*?)\[/img\]', r'![](\1)', content, flags=re.IGNORECASE)

    # Lists: [list][*]item[/list] → * item
    content = re.sub(r'\[list\](.*?)\[/list\]', r'\1', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'\[\*\](.*?)(?=\[\*\]|\[/list\]|$)', r'* \1<br>', content, flags=re.IGNORECASE)

    # Size (simplify): [size=85]text[/size] → text
    content = re.sub(r'\[size=.*?\](.*?)\[/size\]', r'\1', content, flags=re.IGNORECASE)

    # Color (remove): [color=red]text[/color] → text
    content = re.sub(r'\[color=.*?\](.*?)\[/color\]', r'\1', content, flags=re.IGNORECASE)

    # Clean up any remaining BBCode tags
    content = re.sub(r'\[/\w+\]', '', content)
    content = re.sub(r'\[\w+[^\]]*\]', '', content)

    return content


# -------------------------
# API Client
# -------------------------
class NodeBBImporter:
    """Importer."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = TOKEN

    def _make_request(self, method: str, endpoint: str, data=None, params=None) -> dict:
        """Make authenticated API request"""

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=TIMEOUT)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=TIMEOUT)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, params=params, timeout=TIMEOUT)
            elif method == "PUT":
                response = self.session.put(url, headers=headers, json=data, timeout=TIMEOUT)
            else:
                raise ValueError(f"Unsupported method: {method}")

            time.sleep(RATE_LIMIT)

            if response.status_code not in [200, 201]:
                print(f"❌ API Error ({response.status_code}): {response.text} ({method=} {url=})")
                return None

            return response.json()

        except Exception as e:
            print(f"❌ Request error: {e} ({method=} {url=} {endpoint=})")
            return None

    # -----------
    # Getters all
    # -----------

    def get_all_users(self) -> list[dict]:
        """Get all users"""
        result = self._make_request("GET", "/api/users")
        return result['users'] if result else []

    def get_all_categories(self) -> list[dict]:
        """Get all categories"""
        result = self._make_request("GET", "/api/categories")
        return result['categories'] if result else []

    def get_all_topics(self) -> list[dict]:
        """Get all topics"""
        result = self._make_request("GET", "/api/recent")
        return result['topics'] if result else []

    def get_all_posts_in_topics(self, pid: int) -> list[dict]:
        """Get all posts in topic"""
        result = self._make_request("GET", f"/api/posts/{pid}/replies")
        return result['replies'] if result else []

    # -----------
    # Deleters
    # -----------

    def delete_user(self, uid: int) -> bool:
        """Delete a user (except admin)"""
        print(f"🗑️  Deleting user {uid}...")
        result = self._make_request("DELETE", f"/api/v3/users/{uid}")
        return result is not None

    def delete_category(self, cid: int) -> bool:
        """Delete a category"""
        print(f"🗑️  Deleting category {cid}...")
        result = self._make_request("DELETE", f"/api/v3/categories/{cid}")
        return result is not None

    def delete_topic(self, tid: int) -> bool:
        """Delete a topic"""
        print(f"🗑️  Deleting topic {tid}...")
        result = self._make_request("DELETE", f"/api/v3/topics/{tid}")
        return result is not None

    def delete_post(self, pid: int) -> bool:
        """Delete a post"""
        print(f"🗑️  Deleting post {pid}...")
        result = self._make_request("DELETE", f"/api/v3/posts/{pid}")
        return result is not None

    # -----------
    # Creaters
    # -----------

    def create_user(self, username: str, email: str, password: str) -> dict | None:
        """Create a new user"""

        user_data = {
            "username": username,
            "password": password,
            "email": email
        }
        result = self._make_request("POST", "/api/v3/users", data=user_data)
        if result and 'response' in result:
            return result['response']['uid']
        return None

    def create_category(self, name: str, description: str = "", parent_cid: int = 0, order: int = 0) -> int | None:
        """Create a new category"""

        category_data = {
            "name": name,
            "description": description,
            "parentCid": parent_cid,
            "order": order
        }
        result = self._make_request("POST", "/api/v3/categories", data=category_data)
        if result and 'response' in result:
            return result['response']['cid']
        return None

    def create_topic(self, cid: int, title: str, content: str, uid: int, timestamp: int | None = None) -> dict | None:
        """Create a new topic"""

        # convert
        content2 = convert_bbcode_to_nodebb(content)

        topic_data = {
            "cid": cid,
            "title": title,
            "content": content2,
            "uid": uid
        }
        if timestamp:
            # NodeBB might not accept custom timestamps via API
            # You might need to adjust this based on your NodeBB version
            pass
        result = self._make_request("POST", "/api/v3/topics", data=topic_data)
        if result and 'response' in result:
            return result['response']
        return None

    def create_post(self, tid: int, content: str, uid: int) -> int | None:
        """Create a reply post"""

        # convert
        content2 = convert_bbcode_to_nodebb(content)

        post_data = {
            "tid": tid,
            "content": content2,
            "uid": uid
        }
        result = self._make_request("POST", f"/api/v3/topics/{tid}", data=post_data)
        if result and 'response' in result:
            return result['response']['pid']
        return None

    # -----------
    # Uploaders
    # -----------

    def upload_file(self, file_path: pathlib.Path, uid: int) -> str | None:
        """Upload a file and return its URL"""

        if not file_path.exists():
            return None

        url = f"{self.base_url}/api/v3/users/{uid}/uploads"
        try:
            with open(file_path, 'rb') as f:
                files = {'files[]': (file_path.name, f, 'application/octet-stream')}
                headers = {'Authorization': f'Bearer {self.token}'}

                response = self.session.post(url, files=files, headers=headers, timeout=TIMEOUT)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('response') and len(data['response']) > 0:
                        return data['response'][0]['url']
        except Exception as e:
            print(f"❌ Upload error: {e}")

        return None


# -------------------------
# Main Import Functions
# -------------------------
def clear_existing_data(api: NodeBBImporter) -> None:
    """Clear all existing posts, topics, categories, and users (except admin)"""

    print("\n" + "=" * 50)
    print("🧹 CLEARING EXISTING DATA")
    print("=" * 50)

    # 1. Delete all topics and posts
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


def import_users(api: NodeBBImporter, data_path: pathlib.Path) -> dict[int, int]:
    """Import users from CSV and return mapping old_uid -> new_uid"""
    print("\n" + "=" * 50)
    print("👤 IMPORTING USERS")
    print("=" * 50)

    users_csv = data_path / "users.csv"
    if not users_csv.exists():
        print(f"❌ Users CSV not found: {users_csv}")
        return {}

    df_users = pd.read_csv(users_csv, encoding=CSV_ENCODING)
    user_map = {}  # old_uid -> new_uid

    print(f"Found {len(df_users)} users to import")

    password_list = []

    for _, row in df_users.iterrows():
        old_uid = int(row['user_id'])
        username = str(row['username']).strip()
        email = str(row['email']).strip()

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

    save_passwords_to_file(password_list)

    print(f"\n✅ Imported {len(user_map)} users with random passwords")
    return user_map


def import_categories(api: NodeBBImporter, data_path: pathlib.Path) -> dict[int, int]:
    """Import categories from CSV and return mapping old_cid -> new_cid"""
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


def import_topics_and_posts(api: NodeBBImporter, data_path: pathlib.Path, user_map: dict[int, int], category_map: dict[int, int]) -> None:
    """Import topics and posts from CSV files"""

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
    posts_by_topic = {}
    for _, row in df_posts.iterrows():
        tid = int(row['tid'])
        if tid not in posts_by_topic:
            posts_by_topic[tid] = []
        posts_by_topic[tid].append(row)

    # Cache for uploaded files
    uploaded_files = {}

    # Import each topic
    success_count = 0
    for idx, topic_row in enumerate(df_topics.iterrows(), 1):
        _, row = topic_row
        old_tid = int(row['tid'])
        old_cid = int(row['cid'])
        old_uid = int(row['uid'])

        # Skip if category or user doesn't exist in our maps
        if old_cid not in category_map or old_uid not in user_map:
            print(f"⚠️  Skipping topic {old_tid}: category or user not found")
            continue

        new_cid = category_map[old_cid]
        new_uid = user_map[old_uid]

        # Check if this topic has posts
        if old_tid not in posts_by_topic or not posts_by_topic[old_tid]:
            print(f"⚠️  Skipping topic {old_tid}: no posts")
            continue

        print(f"\n📄 Topic {idx}/{len(df_topics)}: {row['title'][:50]}...")

        # Process first post (topic content)
        first_post = posts_by_topic[old_tid][0]
        content = str(first_post['content'])

        # Handle attachments in first post
        content = process_attachments(content, data_path, new_uid, api, uploaded_files)

        # Create topic
        title = str(row['title']).strip()
        topic_data = api.create_topic(new_cid, title, content, new_uid)

        if not topic_data:
            print(f"❌ Failed to create topic {old_tid}")
            continue

        new_tid = topic_data['tid']
        success_count += 1

        # Create replies (remaining posts)
        if len(posts_by_topic[old_tid]) > 1:
            print(f"  Creating {len(posts_by_topic[old_tid]) - 1} replies...")

            for post_idx, post_row in enumerate(posts_by_topic[old_tid][1:], 2):
                post_uid = user_map.get(int(post_row['uid']), new_uid)
                post_content = str(post_row['content'])

                # Handle attachments in reply
                post_content = process_attachments(post_content, data_path, post_uid, api, uploaded_files)

                # Create reply
                api.create_post(new_tid, post_content, post_uid)

                if post_idx % 10 == 0:
                    print(f"    Created {post_idx} replies...")

        # Progress indicator
        if idx % 10 == 0:
            print(f"===== Progress: {idx}/{len(df_topics)} topics imported")

    print(f"\n✅ Successfully imported {success_count}/{len(df_topics)} topics")


def process_attachments(content: str, data_path: pathlib.Path, uid: int, api: NodeBBImporter, uploaded_files: dict) -> str:
    """Process [attachment=ID] tags and replace with uploaded file URLs"""

    uploads_dir = data_path / "uploads"

    def replace_attachment(match: re.Match) -> str:
        attach_id = match.group(1)

        # Check cache first
        if attach_id in uploaded_files:
            return str(uploaded_files[attach_id])

        # Find and upload file
        for file_path in uploads_dir.glob(f"attachment_{attach_id}.*"):
            file_url = api.upload_file(file_path, uid)
            if file_url:
                # Create a clickable link
                link = f'[url={file_url}]{file_path.name}[/url]'
                uploaded_files[attach_id] = link
                return link

        # File not found
        return f'[attachment {attach_id} missing]'

    # Replace all [attachment=ID] tags
    content = re.sub(r'\[attachment=(\d+)\]', replace_attachment, content)
    return content


def import_avatars(api: NodeBBImporter, data_path: pathlib.Path, user_map: dict[int, int]) -> None:
    """Import user avatars"""
    print("\n" + "=" * 50)
    print("🖼️  IMPORTING AVATARS")
    print("=" * 50)

    avatars_dir = data_path / "avatars"
    if not avatars_dir.exists():
        print("⚠️  Avatars directory not found, skipping...")
        return

    success_count = 0
    for old_uid, new_uid in user_map.items():
        # Look for avatar files
        for ext in ['.jpg', '.png', '.gif', '.jpeg']:
            avatar_path = avatars_dir / f"user_{old_uid}{ext}"
            if avatar_path.exists():
                print(f"  Uploading avatar for UID {new_uid}...")
                # Note: Avatar upload via API might require different endpoint
                # This is a placeholder - you might need to adjust
                file_url = api.upload_file(avatar_path, new_uid)
                if file_url:
                    success_count += 1
                    print("    ✅ Avatar uploaded")
                break

    print("\n✅ Uploaded {success_count} avatars")


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

    # Initialize API client
    api = NodeBBImporter(NODEBB_URL)

    # Ask for confirmation
    print("\n⚠️  WARNING: This will DELETE ALL EXISTING DATA!")
    print("   (categories, topics, posts, and non-admin users)")
    response = 'y'  # TEMPORARY input("   Continue? (y/N): ")

    if response.lower() != 'y':
        print("❌ Import cancelled")
        sys.exit(0)

    # 1. Clear existing data
    clear_existing_data(api)

    # 2. Import users and create map
    user_map = import_users(api, data_path)

    # 3. Import categories
    category_map = import_categories(api, data_path)

    # 4. Import topics and posts
    import_topics_and_posts(api, data_path, user_map, category_map)

    # 5. Import avatars (optional)
    import_avatars(api, data_path, user_map)

    print("\n" + "=" * 50)
    print("🎉 IMPORT COMPLETE!")
    print("=" * 50)
    print(f"   Users imported: {len(user_map)}")
    print(f"   Categories imported: {len(category_map)}")
    print(f"\n   Forum URL: {NODEBB_URL}")
    print("   Default password for imported users: password123")
    print("\n⚠️  IMPORTANT: Users should change their passwords!")


if __name__ == "__main__":
    main()
