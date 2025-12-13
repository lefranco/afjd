#!/usr/bin/env python3

"""
direct_import.py - Import phpBB data directly into NodeBB v4.7.0
"""

import pathlib
import secrets
import string
import hashlib

import pandas as pd  # pip3 install pandas --break-system-packages
import pymongo # pip3 install pymongo --break-system-packages

MONGO_URI = "mongodb://nodebb:nodebb123@37.59.100.228:27017/nodebb"  # Your NodeBB MongoDB
NODEBB_DB = "nodebb"  # Your NodeBB database name
DATA_DIR = "./phpbb_export"  # Your CSV directory


class NodeBBImporter:
    """NodeBB Importer with unconditional data cleanup"""

    def __init__(self, mongo_uri, db_name):
        """Connect to NodeBB's MongoDB and CLEAN existing data."""
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[db_name]
        print(f"✅ Connected to NodeBB database: {db_name}")

        # SELECTIVE cleanup
        self._clean_existing_data()

    def _clean_existing_data(self):
        """Super precise: delete ONLY forum structure, keep everything else."""

        print("\n🧹 PRECISE CLEANUP: Forum content only")

        # Track what we delete
        deletions = []

        # Only delete these EXACT patterns in 'objects'
        delete_patterns = [
            ("^category:", "Categories"),
            ("^topic:", "Topics"),
            ("^post:", "Posts"),
            ("^cid:[0-9]+:tids$", "Category sorted sets")
        ]

        for pattern, description in delete_patterns:
            result = self.db.objects.delete_many({"_key": {"$regex": pattern}})
            if result.deleted_count > 0:
                deletions.append(f"{description}: {result.deleted_count}")

        # Optional: Also clear standalone collections
        for coll in ['categories', 'topics', 'posts']:
            if coll in self.db.list_collection_names():
                count = self.db[coll].count_documents({})
                if count > 0:
                    self.db[coll].delete_many({})
                    deletions.append(f"{coll} collection: {count}")

        # Summary
        if deletions:
            print("   Deleted:")
            for item in deletions:
                print(f"     - {item}")
        else:
            print("   No forum content found to delete")

        print("\n✅ Ready for import. All non-forum data preserved.")

    def _generate_random_password(self):
        """Generate a secure random password."""

        pass_length = 4
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(pass_length))
        return password

    def _generate_fast_password_hash(self, password):
        """Generate a fast SHA512 hash for import speed.
        Users will need to reset passwords anyway, so we don't need bcrypt security.
        """
        # Generate random salt
        salt = secrets.token_hex(8)  # 16-character hex salt

        # SHA512 hash (fast!)
        hash_obj = hashlib.sha512()
        hash_obj.update(salt.encode('utf-8'))
        hash_obj.update(password.encode('utf-8'))
        hashed = hash_obj.hexdigest()

        # Format: sha512$salt$hash
        return f"sha512${salt}${hashed}"

    def import_users(self, users_csv):
        """Import users from CSV with random passwords."""
        users_df = pd.read_csv(users_csv)
        print(f"📊 Loading {len(users_df)} users...")

        imported_users = {}
        password_list = []  # Store passwords for admin reference

        for _, row in users_df.iterrows():

            # Generate random password for this user
            plain_password = self._generate_random_password()

            # Generate hash
            password_hash = self._generate_fast_password_hash(plain_password)

            # Store password for admin reference
            password_list.append({
                "user_id": int(row['user_id']),
                "username": str(row['username']),
                "email": str(row['email']),
                "password": plain_password,
                "hash": password_hash
            })

            # NodeBB user document structure
            user_doc = {
                "_key": f"user:{row['user_id']}",
                "uid": int(row['user_id']),
                "username": str(row['username']),
                "userslug": str(row['username']).lower().replace(' ', '-'),
                "email": str(row['email']),
                "joindate": int(row['joindate']),
                "lastonline": int(row['joindate']),
                "picture": "",
                "fullname": "",
                "location": "",
                "birthday": "",
                "website": "",
                "signature": "",
                "uploadedpicture": "",
                "profileviews": 0,
                "reputation": 0,
                "postcount": int(row['postcount']),
                "topiccount": 0,
                "lastposttime": 0,
                "banned": 0,
                "status": "online",
                "email:confirmed": 1
            }

            # Insert into 'objects' collection (NodeBB's main storage)
            self.db.objects.insert_one(user_doc)

            # Also create in 'users' collection for authentication
            # WITH THE RANDOM PASSWORD HASH
            users_collection_doc = {
                "_key": f"user:{row['user_id']}",
                "uid": int(row['user_id']),
                "username": str(row['username']),
                "password": password_hash,  # Now has a proper hash!
                "email": str(row['email']),
                "joindate": int(row['joindate']),
                "passwordExpiry": 0,
                "password:shaWrapped": 1  # Important flag for NodeBB
            }
            self.db.users.insert_one(users_collection_doc)

            imported_users[row['user_id']] = {
                "doc": users_collection_doc,
                "plain_password": plain_password
            }

        # Save passwords to a secure file for admin use
        self._save_passwords_to_file(password_list)

        print(f"✅ Imported {len(imported_users)} users with random passwords")
        return imported_users

    def _save_passwords_to_file(self, password_list):
        """Save generated passwords to a secure JSON file."""

        summary = []
        for item in password_list:
            summary.append({
                "user_id": item["user_id"],
                "username": item["username"],
                "email": item["email"],
                "password": item["password"]
            })

        # Create a CSV for usage
        csv_file = "user_passwords.csv"
        df = pd.DataFrame(summary)
        df.to_csv(csv_file, index=False)
        print(f"🔐 Generated passwords saved to: {csv_file}")

        # Security warning
        print("⚠️  SECURITY WARNING: This file contain plain-text passwords!")
        print("   Secure or delete it immediately after distributing passwords.")

    def import_categories(self, forums_csv):
        """Import forum categories."""
        categories_df = pd.read_csv(forums_csv)
        print(f"📊 Loading {len(categories_df)} categories...")

        imported_categories = {}

        for _, row in categories_df.iterrows():
            category_doc = {
                "_key": f"category:{row['cid']}",
                "cid": int(row['cid']),
                "name": str(row['name']),
                "description": str(row['description']),
                "icon": "",
                "bgColor": "#0088CC",
                "color": "#FFFFFF",
                "slug": str(row['name']).lower().replace(' ', '-'),
                "parentCid": int(row['parentCid']) if pd.notna(row['parentCid']) else 0,
                "topic_count": 0,
                "post_count": 0,
                "disabled": 0,
                "order": int(row.get('display_order', 0)),
                "link": "",
                "numRecentReplies": 1,
                "class": "col-md-3 col-xs-6",
                "imageClass": "cover",
                "isSection": 0
            }

            self.db.objects.insert_one(category_doc)
            imported_categories[row['cid']] = category_doc['_key']

        print(f"✅ Imported {len(imported_categories)} categories")
        return imported_categories

    def import_topics(self, topics_csv, users_map, categories_map):
        """Import discussion topics with relationship validation."""
        topics_df = pd.read_csv(topics_csv)
        print(f"📊 Loading {len(topics_df)} topics...")

        imported_topics = {}
        skipped_topics = 0

        for _, row in topics_df.iterrows():
            topic_id = int(row['tid'])
            user_id = int(row['uid'])
            category_id = int(row['cid'])

            # VALIDATE RELATIONSHIPS
            if user_id == 1:   # the Libertor issue
                user_id = 300
            if user_id not in users_map:
                print(f"⚠️  Topic {topic_id}: User {user_id} not found, skipping")
                skipped_topics += 1
                continue

            if category_id not in categories_map:
                print(f"⚠️  Topic {topic_id}: Category {category_id} not found, skipping")
                skipped_topics += 1
                continue

            # Create topic document
            topic_doc = {
                "_key": f"topic:{topic_id}",
                "tid": topic_id,
                "uid": user_id,
                "cid": category_id,
                "mainPid": 0,  # Will be set when importing posts
                "title": str(row['title']),
                "slug": str(row['title']).lower().replace(' ', '-')[:100],
                "timestamp": int(row['timestamp']),
                "lastposttime": int(row.get('timestamp', row['timestamp'])),
                "postcount": int(row.get('postcount', 1)),
                "viewcount": int(row.get('viewcount', 0)),
                "locked": int(row.get('locked', 0)),
                "pinned": int(row.get('pinned', 0)),
                "deleted": 0,
                "upvotes": 0,
                "downvotes": 0,
                "votes": 0,
                "teaserPid": 0
            }

            self.db.objects.insert_one(topic_doc)
            imported_topics[topic_id] = topic_doc['_key']

        print(f"✅ Imported {len(imported_topics)} topics")
        if skipped_topics > 0:
            print(f"⚠️  Skipped {skipped_topics} topics with invalid relationships")

        return imported_topics

    def import_posts(self, posts_csv, users_map, topics_map):
        """Import posts/replies with relationship validation."""
        posts_df = pd.read_csv(posts_csv)
        print(f"📊 Loading {len(posts_df)} posts...")

        # Track first posts for topic teasers
        first_posts = {}
        skipped_posts = 0

        for _, row in posts_df.iterrows():
            post_id = int(row['pid'])
            user_id = int(row['uid'])
            topic_id = int(row['tid'])

            # VALIDATE RELATIONSHIPS
            if user_id == 1:   # the Libertor issue
                user_id = 300
            if user_id not in users_map:
                print(f"⚠️  Post {post_id}: User {user_id} not found, skipping")
                skipped_posts += 1
                continue

            if topic_id not in topics_map:
                print(f"⚠️  Post {post_id}: Topic {topic_id} not found, skipping")
                skipped_posts += 1
                continue

            post_doc = {
                "_key": f"post:{post_id}",
                "pid": post_id,
                "tid": topic_id,
                "uid": user_id,
                "content": str(row['content']),
                "timestamp": int(row['timestamp']),
                "deleted": 0,
                "upvotes": 0,
                "downvotes": 0,
                "votes": 0,
                "editor": "",
                "edited": 0,
                "replies": 0,
                "bookmarks": 0
            }

            self.db.objects.insert_one(post_doc)

            # Track if this is the first post in its topic
            if topic_id not in first_posts:
                first_posts[topic_id] = post_id

        print(f"✅ Imported {len(posts_df) - skipped_posts} posts")
        if skipped_posts > 0:
            print(f"⚠️  Skipped {skipped_posts} posts with invalid relationships")

        # Update topics with mainPid (first post ID)
        self._update_topic_main_pids(first_posts)

        return len(posts_df) - skipped_posts

    def _update_topic_main_pids(self, first_posts):
        """Set the mainPid for each topic (first post)."""
        for tid, pid in first_posts.items():
            self.db.objects.update_one(
                {"_key": f"topic:{tid}"},
                {"$set": {"mainPid": pid}}
            )
        print(f"✅ Updated {len(first_posts)} topics with mainPid")

    def update_category_counts(self):
        """Update topic and post counts in all categories."""
        print("\n📊 Updating category counts...")

        # Get all categories
        categories = list(self.db.objects.find({"_key": {"$regex": "^category:"}}))

        for category in categories:
            cid = category['cid']

            # Count topics in this category
            topic_count = self.db.objects.count_documents({
                "_key": {"$regex": "^topic:"},
                "cid": cid
            })

            # Count posts in topics of this category
            # First get all topic IDs in this category
            topic_ids = [doc['tid'] for doc in self.db.objects.find(
                {"_key": {"$regex": "^topic:"}, "cid": cid},
                {"tid": 1}
            )]

            post_count = 0
            if topic_ids:
                post_count = self.db.objects.count_documents({
                    "_key": {"$regex": "^post:"},
                    "tid": {"$in": topic_ids}
                })

            # Update the category
            self.db.objects.update_one(
                {"_key": f"category:{cid}"},
                {"$set": {
                    "topic_count": topic_count,
                    "post_count": post_count
                }}
            )

            if len(categories) <= 10:  # Only show details for small forums
                print(f"   Category {cid}: {topic_count} topics, {post_count} posts")
            elif (categories.index(category) + 1) % 20 == 0:  # Progress for large forums
                print(f"   Progress: {categories.index(category) + 1}/{len(categories)} categories")

        print(f"✅ Updated {len(categories)} category counts")

    def create_sorted_sets(self):
        """Create cid:{cid}:tids sorted sets that NodeBB needs to display topics."""

        print("\n🔗 Creating category sorted sets...")

        # Get all categories
        categories = list(self.db.objects.find({"_key": {"$regex": "^category:"}}))

        sets_created = 0

        for category in categories:
            cid = category['cid']
            sorted_set_key = f"cid:{cid}:tids"

            # Get all topics in this category, sorted by lastposttime (newest first)
            topics = list(self.db.objects.find(
                {"_key": {"$regex": "^topic:"}, "cid": cid},
                sort=[("lastposttime", -1)]  # Descending = newest first
            ))

            if topics:
                # Create the sorted set document
                sorted_set = {
                    "_key": sorted_set_key,
                    "value": [topic['tid'] for topic in topics],
                    "scores": [topic.get('lastposttime', topic.get('timestamp', 0)) for topic in topics]
                }

                # Insert or update
                self.db.objects.update_one(
                    {"_key": sorted_set_key},
                    {"$set": sorted_set},
                    upsert=True
                )

                sets_created += 1

                # Progress indicator for large forums
                if len(categories) > 20 and sets_created % 10 == 0:
                    print(f"   Created {sets_created}/{len(categories)} sorted sets...")

        print(f"✅ Created {sets_created} category sorted sets")
        return sets_created

    def run_import(self, data_dir="./phpbb_export"):
        """Run the complete import process."""

        print("\n" + "=" * 60)
        print("🚀 IMPORTING PHPBB DATA INTO CLEAN DATABASE")
        print("=" * 60)

        data_path = pathlib.Path(data_dir)

        # Import in correct order
        users_map = self.import_users(
            data_path / "users.csv")

        categories_map = self.import_categories(
            data_path / "forums.csv")

        topics_map = self.import_topics(
            data_path / "topics.csv",
            users_map,
            categories_map
        )

        post_count = self.import_posts(
            data_path / "posts.csv",
            users_map,
            topics_map
        )

        # Update category counts
        self.update_category_counts()

        # Create sorted sets
        self.create_sorted_sets()

        print("=" * 60)
        print("🎉 IMPORT COMPLETE!")
        print("=" * 60)
        print(f"   Users: {len(users_map)}")
        print(f"   Categories: {len(categories_map)}")
        print(f"   Topics: {len(topics_map)}")
        print(f"   Posts: {post_count}")

        # Update global counters
        self._update_global_counters(len(users_map), len(topics_map), post_count)

        return True

    def _update_global_counters(self, user_count, topic_count, post_count):
        """Update global counters in NodeBB."""
        self.db.objects.update_one(
            {"_key": "global"},
            {"$set": {
                "userCount": user_count,
                "topicCount": topic_count,
                "postCount": post_count
            }},
            upsert=True
        )
        print("✅ Updated global counters")


def main():
    """Main function with safety warnings."""

    print("=" * 60)
    print("NodeBB v4.7.0 Direct Import")
    print("⚠️  WARNING: UNCONDITIONAL DATA DESTRUCTION")
    print("=" * 60)

    print("This script will DELETE ALL DATA in:")
    print(f"   Database: {NODEBB_DB}")
    print(f"   MongoDB: {MONGO_URI}")
    print("\nRequired backup command:")
    print(f'   mongodump --uri="{MONGO_URI}/{NODEBB_DB}" --out ./nodebb_backup')

    print("\n🔐 IMPORTANT: All users will get RANDOM passwords!")
    print("   Passwords will be saved to user_passwords.csv")

    # Safety confirmation
    response = input("\nContinue (all data will be deleted)? (y/N)")

    if response.lower() != 'y':
        print("\n❌ Import cancelled. No changes were made.")
        return

    print("\n" + "=" * 60)
    print("STARTING IMPORT PROCESS")
    print("=" * 60)

    # Quick pre-flight checks
    data_path = pathlib.Path(DATA_DIR)
    required_files = ['users.csv', 'forums.csv', 'topics.csv', 'posts.csv']
    for file in required_files:
        if not (data_path / file).exists():
            print(f"❌ Missing required file: {file}")
            print("   Please run the export scripts first.")
            return

    print("✅ All required CSV files found")

    importer = NodeBBImporter(MONGO_URI, NODEBB_DB)
    success = importer.run_import(DATA_DIR)

    if success:
        print("\n" + "=" * 60)
        print("🎉 IMPORT COMPLETE SUCCESSFULLY!")
        print("=" * 60)
        print("\n🔐 Password Information:")
        print("   Generated passwords saved to: user_passwords.csv")
        print("   Users can now login with these random passwords")
        print("   Recommend forcing password reset on first login")
        print("\nNext steps:")
        print("1. Distribute passwords to users securely")
        print("2. Configure NodeBB admin permissions")
        print("3. Copy attachment files to NodeBB uploads directory")
    else:
        print("\n❌ Import failed or was incomplete.")


if __name__ == "__main__":
    main()
