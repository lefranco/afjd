#!/usr/bin/env python3

"""
Input:
phpbb_export/users.csv
phpbb_export/forums.csv
phpbb_export/topics.csv
phpbb_export/posts.csv
phpbb_export/uploads/ → fichiers joints, nom original ou attachment_<ID>.<ext>
phpbb_export/avatars/ → user_<uid>.jpg ou .png

After:

Check:
ls -la ./public/uploads/avatars/
ls -la ./data/uploads/

mongo mongodb://nodebb:nodebb123@37.59.100.228:27017/nodebb
> db.objects.count({"_key": /^topic:/})
> db.objects.count({"_key": /^post:/})

Restart:
./nodebb build
./nodebb restart

Check:
Les avatars s’affichent correctement
Les posts contiennent bien les attachments avec URL NodeBB
Les topics et catégories sont visibles et triés correctement
"""

import pathlib
import shutil
import re

import pandas as pd
import pymongo # pip3 install pymongo --break-system-packages
import slugify # pip3 install slugify --break-system-packages

# -------------------------
# CONFIGURATION
# -------------------------
# database:
MONGO_URI = "mongodb://nodebb:nodebb123@37.59.100.228:27017/nodebb"
DB_NAME = "nodebb"
# source
DATA_DIR = "./phpbb_export"
# dest:
UPLOADS_DIR = "./data/uploads"
AVATARS_DIR = "./data/public/uploads/avatars"


def main():
    """Main."""

    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    data_path = pathlib.Path(DATA_DIR)

    # -------------------------
    # 0️⃣ Import Users + Avatars
    # -------------------------
    users_csv = data_path / "users.csv"
    df_users = pd.read_csv(users_csv)
    users_map = {}
    nb_avatars = 0

    for _, row in df_users.iterrows():
        uid = int(row['user_id'])

        # or picture_file = f"/uploads/avatars/{slugify.slugify(row['username'])}.jpg"
        picture_file = f"/uploads/avatars/user_{uid}.jpg"

        user_doc = {
            "_key": f"user:{uid}",
            "uid": uid,
            "username": str(row['username']),
            "userslug": slugify.slugify(row['username']),
            "email": str(row['email']),
            "joindate": int(row['joindate']),
            "postcount": int(row['postcount']),
            "topiccount": 0,
            "status": "online",
            "banned": 0,
            "picture": picture_file,
            "fullname": "",
            "location": "",
            "birthday": "",
            "website": "",
            "signature": "",
            "uploadedpicture": "",
            "profileviews": 0,
            "reputation": 0,
            "lastonline": int(row['joindate']),
            "lastposttime": 0,
            "email:confirmed": 1
        }
        db.objects.update_one({"_key": user_doc["_key"]}, {"$set": user_doc}, upsert=True)

        auth_doc = {
            "_key": f"user:{uid}",
            "uid": uid,
            "username": str(row['username']),
            "email": str(row['email']),
            "password": "password",
            "joindate": int(row['joindate']),
            "passwordExpiry": 0,
            "password:shaWrapped": 1
        }
        db.users.update_one({"_key": auth_doc["_key"]}, {"$set": auth_doc}, upsert=True)
        users_map[uid] = user_doc["_key"]

        # Copy avatar
        for ext in ['.jpg', '.png']:
            src_avatar = data_path / "avatars" / f"user_{uid}{ext}"
            if src_avatar.exists():
                shutil.copy(src_avatar, AVATARS_DIR)
                print(f"Copied avatar for user {row['username']}")
                nb_avatars += 1
                break

    print(f"✅ Imported {len(users_map)} users + {nb_avatars} avatars")

    # -------------------------
    # 1️⃣ Import Categories
    # -------------------------
    forums_csv = data_path / "forums.csv"
    df_forums = pd.read_csv(forums_csv)
    categories_map = {}
    for _, row in df_forums.iterrows():
        cid = int(row['cid'])
        category_doc = {
            "_key": f"category:{cid}",
            "cid": cid,
            "name": str(row['name']),
            "description": str(row['description']),
            "slug": str(row['name']).lower().replace(' ', '-'),
            "parentCid": int(row['parentCid']),
            "topic_count": 0,
            "post_count": 0,
            "disabled": 0,
            "order": int(row.get('display_order', 0)),
            "isSection": 0
        }
        db.objects.update_one({"_key": category_doc["_key"]}, {"$set": category_doc}, upsert=True)
        categories_map[cid] = category_doc["_key"]

    print(f"✅ Imported {len(categories_map)} categories")

    # -------------------------
    # 2️⃣ Import Topics
    # -------------------------
    topics_csv = data_path / "topics.csv"
    df_topics = pd.read_csv(topics_csv)
    topics_map = {}
    for _, row in df_topics.iterrows():
        tid = int(row['tid'])
        topic_doc = {
            "_key": f"topic:{tid}",
            "tid": tid,
            "uid": int(row['uid']),
            "cid": int(row['cid']),
            "title": str(row['title']),
            "slug": str(row['title']).lower().replace(' ', '-')[:100],
            "timestamp": int(row['timestamp']),
            "lastposttime": int(row['timestamp']),
            "viewcount": int(row.get('viewcount', 0)),
            "postcount": int(row.get('postcount', 0)),
            "locked": int(row.get('locked', 0)),
            "pinned": int(row.get('pinned', 0)),
            "deleted": 0,
            "mainPid": 0
        }
        db.objects.update_one({"_key": topic_doc["_key"]}, {"$set": topic_doc}, upsert=True)
        topics_map[tid] = topic_doc["_key"]

    print(f"✅ Imported {len(topics_map)} topics")

    # -------------------------
    # 3️⃣ Import Posts + attachments
    # -------------------------
    posts_csv = data_path / "posts.csv"
    df_posts = pd.read_csv(posts_csv)
    df_posts = df_posts.sort_values('timestamp', ascending=True)

    first_posts = {}
    nb_attachments = 0

    for _, row in df_posts.iterrows():
        pid = int(row['pid'])
        tid = int(row['tid'])
        content = str(row['content'])

        # Replacement des tags [attachment=ID] par URL NodeBB
        def replace_attachment_tag(match, pid=pid):
            """Replace attachment tag"""
            attach_id = match.group(1)
            # Suppose que le fichier existe : attachment_<ID>.<ext>
            for f in (data_path / "uploads").glob(f"attachment_{attach_id}.*"):
                shutil.copy(f, UPLOADS_DIR)
                print(f"Copied attachment for post {pid}")
                nb_attachments += 1
                return f"/uploads/{f.name}"
            return f"[missing attachment {attach_id}]"

        content = re.sub(r'\[attachment=(\d+)\]', replace_attachment_tag, content)

        post_doc = {
            "_key": f"post:{pid}",
            "pid": pid,
            "tid": tid,
            "uid": int(row['uid']),
            "content": content,
            "timestamp": int(row['timestamp']),
            "deleted": 0
        }
        db.objects.update_one({"_key": post_doc["_key"]}, {"$set": post_doc}, upsert=True)

        # Seulement le premier post du topic (maintenant que c'est trié par timestamp)
        if tid not in first_posts:
            first_posts[tid] = pid
            print(f"  First post for topic {tid} is {pid} (timestamp: {row['timestamp']})")

    print(f"✅ Imported {len(df_posts)} posts + {nb_attachments} attachments")

    # -------------------------
    # 4️⃣ Update mainPid in topics
    # -------------------------
    for tid, pid in first_posts.items():
        db.objects.update_one({"_key": f"topic:{tid}"}, {"$set": {"mainPid": pid}})

    print(f"✅ Updated mainPid for {len(first_posts)} topics")

    # -------------------------
    # 5️⃣ Update Category Counts
    # -------------------------
    for cid, cat_key in categories_map.items():
        topic_count = db.objects.count_documents({"_key": {"$regex": "^topic:"}, "cid": cid})
        topic_ids = [t['tid'] for t in db.objects.find({"_key": {"$regex": "^topic:"}, "cid": cid}, {"tid":1})]
        post_count = db.objects.count_documents({"_key": {"$regex": "^post:"}, "tid": {"$in": topic_ids}})
        db.objects.update_one({"_key": cat_key}, {"$set": {"topic_count": topic_count, "post_count": post_count}})

    print("✅ Updated category topic/post counts")

    # -------------------------
    # 6️⃣ Create Category Sorted Sets
    # -------------------------
    for cid in categories_map:
        sorted_set_key = f"cid:{cid}:tids"
        topics_in_cat = list(db.objects.find({"_key": {"$regex": "^topic:"}, "cid": cid}, {"tid":1, "lastposttime":1}).sort("lastposttime", -1))
        tids = [t['tid'] for t in topics_in_cat]
        scores = [t.get('lastposttime',0) for t in topics_in_cat]
        db.objects.update_one({"_key": sorted_set_key}, {"$set": {"value": tids, "scores": scores}}, upsert=True)

    print("✅ Created category sorted sets")

    # -------------------------
    # 7️⃣ Update Global Counters
    # -------------------------
    user_count = db.objects.count_documents({"_key": {"$regex": "^user:"}})
    topic_count = db.objects.count_documents({"_key": {"$regex": "^topic:"}})
    post_count = db.objects.count_documents({"_key": {"$regex": "^post:"}})
    db.objects.update_one({"_key": "global"}, {"$set": {"userCount": user_count, "topicCount": topic_count, "postCount": post_count}}, upsert=True)
    print(f"✅ Updated global counters: users={user_count}, topics={topic_count}, posts={post_count}")

    # -------------------------
    # Bonus: create some indexes
    # -------------------------
    db.objects.create_index("_key")
    db.objects.create_index("cid")
    db.objects.create_index("tid")

    print("🎉 COMPLETE IMPORT NodeBB 4.7.0 with avatars and attachments done !")


if __name__ == "__main__":
    main()
