#!/usr/bin/env python3

"""
sudo apt install mysql-server
sudo systemctl status mysql => must be active
sudo apt install default-mysql-client

sudo mysql -u root -e "CREATE DATABASE IF NOT EXISTS forum_afjd CHARACTER SET utf8mb4;"
sudo mysql -u root forum_afjd < ../data/forum_afjd.sql  # a bit long

sudo mysql -u root <<EOF
CREATE USER 'exporter'@'localhost' IDENTIFIED BY 'safe_password_123';
GRANT ALL PRIVILEGES ON forum_afjd.* TO 'exporter'@'localhost';
FLUSH PRIVILEGES;
EOF
"""

import pathlib
import time

import pandas as pd  # pip3 install pandas --break-system-packages
import pymysql # pip3 install pymysql --break-system-packages


CONFIG = {
    'host': 'localhost',
    'database': 'forum_afjd',
    'user': 'exporter',
    'password': 'safe_password_123',
    'table_prefix': 'phpbb_'  # From your config.php
}


def add_custom_user_to_csv_files(export_dir):
    """Add custom user to exported CSV files."""

    users_csv = export_dir / 'users.csv'
    if users_csv.exists():
        df_users = pd.read_csv(users_csv)

        # Custom user details
        custom_user = {
            'user_id': 300,   # must not exist
            'username': 'Libertor',
            'email': 'custom.user@example.com',
            'joindate': int(time.time()),
            'postcount': 0
        }

        # Check if user already exists
        if custom_user['user_id'] not in df_users['user_id'].values:
            new_user_row = pd.DataFrame([custom_user])
            df_users = pd.concat([df_users, new_user_row], ignore_index=True)
            df_users.to_csv(users_csv, index=False)
            print(f"✅ Added custom user '{custom_user['username']}' to users.csv")
        else:
            print("⚠️ Custom user already exists in users.csv")
    else:
        print("❌ users.csv not found")


def main():
    """Main."""

    # 1. CONNECT TO DATABASE
    try:
        connection = pymysql.connect(  # Changed from mysql.connector.connect
            host=CONFIG['host'],
            database=CONFIG['database'],
            user=CONFIG['user'],
            password=CONFIG['password'],
            charset='utf8mb4'  # CRITICAL: Add this for proper encoding
        )
        print("✅ Connected to phpBB database successfully.")

    except pymysql.Error as err:  # Changed exception type
        print(f"❌ Connection failed: {err}")
        return

    # 2. DEFINE EXPORT QUERIES (Using your table prefix)
    prefix = CONFIG['table_prefix']

    queries = {
        # Core tables for NodeBB import
        'users': f"""
            SELECT user_id, username, user_email as email, user_regdate as joindate,
                user_sig as signature, user_posts as postcount
            FROM {prefix}users
            WHERE user_type != 2 -- Exclude bots (INACTIVE)
            ORDER BY user_id
        """,
        'forums': f"""
            SELECT forum_id as cid, forum_name as name, forum_desc as description,
                parent_id as parentCid, left_id as display_order
            FROM {prefix}forums
            ORDER BY left_id
        """,
        'topics': f"""
            SELECT topic_id as tid, forum_id as cid, topic_poster as uid,
                topic_title as title, topic_time as timestamp,
                topic_views as viewcount, topic_posts_approved as postcount,
                topic_status as locked, topic_type as pinned
            FROM {prefix}topics
            WHERE topic_visibility = 1 -- Only visible topics
            ORDER BY topic_id
        """,
        'posts': f"""
            SELECT post_id as pid, topic_id as tid, poster_id as uid,
                post_text as content, post_time as timestamp
            FROM {prefix}posts
            WHERE post_visibility = 1 -- Only visible posts
            ORDER BY post_id
        """,
        'attachments': f"""
            SELECT  attach_id,  physical_filename,  real_filename,  attach_comment, post_msg_id as pid
            FROM {prefix}attachments
            ORDER BY attach_id;
        """
    }

    # 3. EXTRACT AND SAVE DATA
    export_dir = pathlib.Path('./phpbb_export')
    export_dir.mkdir(exist_ok=True)

    for name, query in queries.items():
        try:
            df = pd.read_sql(query, connection)
            csv_path = export_dir / f'{name}.csv'
            df.to_csv(csv_path, index=False)
            print(f"✅ Exported {len(df)} records to {csv_path}")
        except Exception as e:
            print(f"❌ Failed to export {name}: {e}")

    # 4. CLEANUP
    connection.close()

    # 5. ADD CUSTOM USER
    add_custom_user_to_csv_files(export_dir)  # The Libertor issue : we need him so we add him

    print("🎉 Export complete! Check the 'phpbb_export' directory.")

if __name__ == "__main__":
    main()
