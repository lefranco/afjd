#!/usr/bin/env python3
"""
final_verification.py - Comprehensive import verification
"""

import pymongo # pip3 install pymongo --break-system-packages

MONGO_URI = "mongodb://nodebb:nodebb123@37.59.100.228:27017/nodebb"  # Your NodeBB MongoDB
NODEBB_DB = "nodebb"  # Your NodeBB database name

def main():
    """Main."""

    client = pymongo.MongoClient(MONGO_URI)
    db = client[NODEBB_DB]

    print("=" * 60)
    print("FINAL IMPORT VERIFICATION")
    print("=" * 60)

    # 1. Basic counts
    counts = {
        'Users': db.objects.count_documents({'_key': {'$regex': '^user:'}}),
        'Categories': db.objects.count_documents({'_key': {'$regex': '^category:'}}),
        'Topics': db.objects.count_documents({'_key': {'$regex': '^topic:'}}),
        'Posts': db.objects.count_documents({'_key': {'$regex': '^post:'}})
    }

    print("\n📊 DATABASE COUNTS:")
    for name, count in counts.items():
        print(f"   {name}: {count}")

    # 2. Check category integrity
    print("\n🔍 CATEGORY INTEGRITY:")
    categories = list(db.objects.find({'_key': {'$regex': '^category:'}},
                                    {'cid': 1, 'name': 1, 'topic_count': 1, 'post_count': 1}))

    for cat in categories:
        cid = cat['cid']
        actual_topics = db.objects.count_documents({'_key': {'$regex': '^topic:'}, 'cid': cid})

        status = "✅" if cat.get('topic_count', 0) == actual_topics else "❌"
        print(f"   {status} Category {cid} ({cat.get('name', 'Unknown')}): "
            f"DB says {cat.get('topic_count', 0)}, actually {actual_topics}")

    # 3. Check recent content
    print("\n🕒 RECENT CONTENT:")
    recent_topic = db.objects.find_one({'_key': {'$regex': '^topic:'}},
                                    sort=[('lastposttime', -1)])
    if recent_topic:
        print(f"   Most recent topic: #{recent_topic.get('tid')} - "
            f"'{recent_topic.get('title', 'No title')}...'")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
