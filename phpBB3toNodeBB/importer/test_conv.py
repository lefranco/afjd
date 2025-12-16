#!/usr/bin/env python3

"""Unitary tests on the delicate software converter is."""

import pathlib
import sys
import typing

import pandas as pd  # pip3 install pandas --break-system-packages

import converter

DATA_DIR = "./phpbb_export"
CSV_ENCODING = "utf-8"


def check_topics_and_posts(data_path: pathlib.Path) -> None:
    """Check topics and posts from CSV files."""

    topic_count = 0
    post_count = 0

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
    posts_by_topic: dict[int, list[pd.Series[typing.Any]]] = {}  # pylint: disable=unsubscriptable-object
    for _, row in df_posts.iterrows():
        tid = int(row['tid'])
        if tid not in posts_by_topic:
            posts_by_topic[tid] = []
        posts_by_topic[tid].append(row)

    # Import each topic
    for _, topic_row in df_topics.iterrows():

        old_tid = int(topic_row['tid'])

        # Check if this topic has posts
        if old_tid not in posts_by_topic or not posts_by_topic[old_tid]:
            print(f"⚠️  Skipping topic {old_tid}: no posts")
            continue

        # Process first post (topic content)
        first_post = posts_by_topic[old_tid][0]
        old_pid_first_post = first_post['pid']
        content = str(first_post['content'])

        # conversion phpbb3 -> nodebb
        print("<<<<<<<<<<<<<<<<<<<<<<<<<")
        print(content)
        content = converter.convert(content)
        print(f"++++t{old_tid} p{old_pid_first_post}++++++++++")
        print(content)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>")

        topic_count += 1

        # Create replies (remaining posts)
        if len(posts_by_topic[old_tid]) > 1:

            for post_row in posts_by_topic[old_tid][1:]:

                old_post_pid = post_row['pid']
                post_content = str(post_row['content'])

                # conversion phpbb3 -> nodebb
                print("<<<<<<<<<<<<<<<<<<<<<<<<<")
                print(post_content)
                post_content = converter.convert(post_content)
                print(f"++++++++++p{old_post_pid}++++++++++")
                print(post_content)
                print(">>>>>>>>>>>>>>>>>>>>>>>>>")

                post_count += 1

    print(f"We have {topic_count} topic and {post_count} posts.")


# -------------------------
# Main
# -------------------------
def main() -> None:
    """Main."""

    # 1. Check data directory
    data_path = pathlib.Path(DATA_DIR)
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_path}")
        sys.exit(1)

    # 2. Import topics and posts
    check_topics_and_posts(data_path)


if __name__ == "__main__":
    main()
