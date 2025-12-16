#!/usr/bin/env python3

"""
Check converter
"""

import html
import pathlib
import re
import secrets
import string
import sys
import time

import pandas as pd  # pip3 install pandas --break-system-packages

import converter

DATA_DIR = "./phpbb_export"
CSV_ENCODING = "utf-8"


def check_topics_and_posts(data_path: pathlib.Path, my_converter) -> None:
    """Check topics and posts from CSV files."""

    # Load topics
    topics_csv = data_path / "topics.csv"
    if not topics_csv.exists():
        print(f"❌ Topics CSV not found: {topics_csv}")
        return

    df_topics = pd.read_csv(topics_csv, encoding=CSV_ENCODING)

    # Load posts
    posts_csv = data_path / "posts.csv"
    if not posts_csv.exists():
        print(f"❌ Posts CSV not found: {posts_csv}")
        return

    df_posts = pd.read_csv(posts_csv, encoding=CSV_ENCODING)
    df_posts = df_posts.sort_values('timestamp', ascending=True)

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

        # Check if this topic has posts
        if old_tid not in posts_by_topic or not posts_by_topic[old_tid]:
            print(f"⚠️  Skipping topic {old_tid}: no posts")
            continue

        # Process first post (topic content)
        first_post = posts_by_topic[old_tid][0]
        content = str(first_post['content'])

        # conversion phpbb3 -> nodebb
        print("<<<<<<<<<<<<<<<<<<<<<<<<<")
        print(content)
        content = my_converter.convert(content)
        print("++++++++++++++++++++++++")
        print(content)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>")

        # Create replies (remaining posts)
        if len(posts_by_topic[old_tid]) > 1:

            for post_idx, post_row in enumerate(posts_by_topic[old_tid][1:], 2):

                post_content = str(post_row['content'])

                # conversion phpbb3 -> nodebb
                print("<<<<<<<<<<<<<<<<<<<<<<<<<")
                print(post_content)
                post_content =  my_converter.convert(post_content)
                print("++++++++++++++++++++++++")
                print(post_content)
                print(">>>>>>>>>>>>>>>>>>>>>>>>>")


# -------------------------
# Main
# -------------------------
def main() -> None:
    """Main."""

    # Check data directory
    data_path = pathlib.Path(DATA_DIR)
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_path}")
        sys.exit(1)

    # 1. Make a converter
    my_converter = converter.PhpBBToNodeBBConverter()

    # 2. Import topics and posts
    check_topics_and_posts(data_path, my_converter)


if __name__ == "__main__":
    main()
