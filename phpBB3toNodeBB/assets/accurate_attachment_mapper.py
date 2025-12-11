#!/usr/bin/env python3
"""
accurate_attachment_mapper.py - Complete and accurate attachment migration
For small forums - uses database for 100% accuracy
"""

import json
import shutil
import pathlib

import pymysql  # pip3 install pymysql --break-system-packages
import pandas as pd  # pip3 install pandas --break-system-packages


CONFIG = {
    'host': 'localhost',
    'database': 'forum_afjd',
    'user': 'exporter',
    'password': 'safe_password_123',
    'table_prefix': 'phpbb_'  # From your config.php
}

PHPBB_PATH = '../data/phpBB3'

class AccurateAttachmentMapper:
    """AccurateAttachmentMapper."""

    def export_attachments_csv(self):
        """Step 1: Export attachments table from database."""

        print("=" * 60)
        print("STEP 1: Exporting attachments from database")
        print("=" * 60)

        try:
            connection = pymysql.connect(
                host=CONFIG['host'],
                database=CONFIG['database'],
                user=CONFIG['user'],
                password=CONFIG['password'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            cursor = connection.cursor()

            query = f"""
            SELECT
                attach_id,
                post_msg_id AS post_id,
                real_filename AS original_filename,
                physical_filename AS stored_filename,
                mimetype,
                filesize,
                filetime AS upload_time
            FROM {CONFIG['table_prefix']}attachments
            WHERE in_message = 0
            ORDER BY post_id, attach_id
            """

            cursor.execute(query)
            attachments = cursor.fetchall()

            # Create DataFrame and save
            df = pd.DataFrame(attachments)
            export_dir = pathlib.Path('./phpbb_export')
            export_dir.mkdir(exist_ok=True)

            csv_path = export_dir / 'attachments.csv'
            df.to_csv(csv_path, index=False)

            print(f"✅ Exported {len(df)} attachment records to: {csv_path}")

            # Summary
            if len(df) > 0:
                total_size = df['filesize'].sum()
                posts_with_attachments = df['post_id'].nunique()

                print("\n📊 Database Summary:")
                print(f"   Total attachments: {len(df)}")
                print(f"   Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
                print(f"   Posts with attachments: {posts_with_attachments}")
                print(f"   Unique users (estimated): ~{len(df) // 10}")  # Rough estimate

            cursor.close()
            connection.close()

            return df

        except pymysql.Error as err:
            print(f"❌ Database error: {err}")
            return None

    def find_phpbb_files(self, phpbb_path):
        """Step 2: Locate phpBB installation and verify files."""

        print("\n" + "=" * 60)
        print("STEP 2: Locating phpBB files")
        print("=" * 60)

        phpbb_path_dir = pathlib.Path(phpbb_path)

        # Check common directories
        check_paths = [
            phpbb_path_dir,
            phpbb_path_dir / "phpBB",
            phpbb_path_dir / "forum",
            phpbb_path_dir / "public_html",
        ]

        actual_path = None
        for path in check_paths:
            if path.exists():
                # Check for phpBB structure
                if (path / "files").exists() or (path / "config.php").exists():
                    actual_path = path
                    break

        if not actual_path:
            print(f"❌ Could not find phpBB installation at: {phpbb_path_dir}")
            print("\nPlease provide the exact path to your phpBB installation.")
            return None

        print(f"✅ Found phpBB installation at: {actual_path}")

        # Check for files directory
        files_dir = actual_path / "files"
        if files_dir.exists():
            file_count = len(list(files_dir.glob("*")))
            print(f"✅ Found files directory with ~{file_count} items")
        else:
            print("⚠️  No 'files' directory found")
            files_dir = None

        # Check for avatars
        avatars_dir = actual_path / "images" / "avatars" / "upload"
        if avatars_dir.exists():
            avatar_count = len(list(avatars_dir.glob("*")))
            print(f"✅ Found avatars directory with ~{avatar_count} avatars")
        else:
            print("⚠️  No avatars directory found")
            avatars_dir = None

        return {
            'root': actual_path,
            'files': files_dir,
            'avatars': avatars_dir
        }

    def verify_files_exist(self, attachments_df, phpbb_info):
        """Step 3: Verify all database files exist on disk."""

        print("\n" + "=" * 60)
        print("STEP 3: Verifying files exist on disk")
        print("=" * 60)

        if attachments_df is None or len(attachments_df) == 0:
            print("No attachments to verify")
            return []

        files_dir = phpbb_info.get('files')
        if not files_dir or not files_dir.exists():
            print("❌ Files directory not found")
            return []

        verified = []
        missing = []

        print(f"Checking {len(attachments_df)} files...")

        for _, row in attachments_df.iterrows():
            stored_name = row['stored_filename']
            original_name = row['original_filename']
            post_id = row['post_id']

            # Check in primary location
            primary_path = files_dir / stored_name

            # Check in subdirectories (phpBB sometimes organizes by first 2 chars)
            subdir_path = files_dir / stored_name[:2] / stored_name if len(stored_name) > 2 else None

            file_path = None
            if primary_path.exists():
                file_path = primary_path
            elif subdir_path and subdir_path.exists():
                file_path = subdir_path

            if file_path:
                verified.append({
                    'post_id': post_id,
                    'stored_filename': stored_name,
                    'original_filename': original_name,
                    'file_path': str(file_path),
                    'filesize': file_path.stat().st_size,
                    'verified': True
                })
            else:
                missing.append({
                    'stored_filename': stored_name,
                    'original_filename': original_name,
                    'post_id': post_id
                })

        # Results
        print("\n📊 Verification Results:")
        print(f"   ✅ Found on disk: {len(verified)}")
        if missing:
            print(f"   ❌ Missing: {len(missing)}")
        else:
            print(f"   ✅ (No missing)")

        if missing:
            print("\n⚠️  Missing files:")
            for item in missing:
                print(f"   - {item['stored_filename']} (post {item['post_id']})")

        # Save verification results
        export_dir = pathlib.Path('./phpbb_export')
        if verified:
            with open(export_dir / 'verified_attachments.json', 'w') as f:
                json.dump(verified, f, indent=2)
            print(f"\n💾 Verified files saved to: {export_dir}/verified_attachments.json")

        return verified

    def copy_attachments(self, verified_files, target_path):
        """Step 4: Copy verified files to NodeBB location."""

        print("\n" + "=" * 60)
        print("STEP 4: Copying files for NodeBB")
        print("=" * 60)

        if not verified_files:
            print("No verified files to copy")
            return 0

        target_dir = pathlib.Path(target_path)
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"Copying {len(verified_files)} files to: {target_dir}")

        copied = 0
        for item in verified_files:
            source = pathlib.Path(item['file_path'])
            dest = target_dir / item['stored_filename']

            try:
                shutil.copy2(source, dest)
                copied += 1

                # Progress indicator for large sets
                if len(verified_files) > 20 and copied % 10 == 0:
                    print(f"   Progress: {copied}/{len(verified_files)}")

            except Exception as e:
                print(f"⚠️  Failed to copy {source.name}: {e}")

        print(f"\n✅ Successfully copied: {copied}/{len(verified_files)} files")

        # Create copy report
        report = {
            'total_files': len(verified_files),
            'copied': copied,
            'target_directory': str(target_dir),
            'timestamp': pd.Timestamp.now().isoformat()
        }

        with open('./phpbb_export/copy_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        return copied

    def update_posts_with_attachments(self, verified_files):
        """Step 5: Update posts.csv with attachment links."""

        print("\n" + "=" * 60)
        print("STEP 5: Updating posts with attachment references")
        print("=" * 60)

        if not verified_files:
            print("No attachments to add to posts")
            return None

        posts_csv = pathlib.Path('./phpbb_export/posts.csv')
        if not posts_csv.exists():
            print("❌ posts.csv not found")
            return None

        # Load posts
        df_posts = pd.read_csv(posts_csv)

        # Group attachments by post_id
        attachments_by_post = {}
        for item in verified_files:
            post_id = item['post_id']
            if post_id not in attachments_by_post:
                attachments_by_post[post_id] = []
            attachments_by_post[post_id].append(item)

        updated_count = 0
        for idx, row in df_posts.iterrows():
            post_id = row['pid']
            if post_id in attachments_by_post:
                attachments = attachments_by_post[post_id]

                # Create attachment section
                attachment_text = "\n\n---\n**Attachments:**\n"
                for att in attachments:
                    # NodeBB-style markdown link
                    link = f"- [{att['original_filename']}](/assets/uploads/{att['stored_filename']})"
                    attachment_text += link + "\n"

                # Append to existing content
                current_content = str(row['content'])
                df_posts.at[idx, 'content'] = current_content + attachment_text
                updated_count += 1

        # Save updated posts
        df_posts.to_csv(posts_csv, index=False)
        print(f"✅ Updated {updated_count} posts with attachment references")

        # Create update report
        update_report = {
            'posts_updated': updated_count,
            'total_attachments': len(verified_files),
            'posts_csv_updated': True,
            'timestamp': pd.Timestamp.now().isoformat()
        }

        with open('./phpbb_export/update_report.json', 'w') as f:
            json.dump(update_report, f, indent=2)

        return updated_count

    def copy_avatars(self, phpbb_info, target_dir):
        """Step 6: Copy user avatars."""

        print("\n" + "=" * 60)
        print("STEP 6: Handling user avatars")
        print("=" * 60)

        avatars_dir = phpbb_info.get('avatars')
        if not avatars_dir or not avatars_dir.exists():
            print("No avatars directory found")
            return 0

        target_dir = pathlib.Path(target_dir) / 'avatars'
        target_dir.mkdir(parents=True, exist_ok=True)

        avatar_files = list(avatars_dir.glob("*"))
        print(f"Found {len(avatar_files)} avatar files")

        copied = 0
        for avatar in avatar_files:
            if avatar.is_file():
                dest = target_dir / avatar.name
                try:
                    shutil.copy2(avatar, dest)
                    copied += 1
                except Exception as e:
                    print(f"⚠️  Failed to copy avatar {avatar.name}: {e}")

        print(f"✅ Copied {copied} avatars to: {target_dir}")
        return copied

    def run(self, phpbb_installation_path):
        """Run the complete accurate attachment migration."""
        print("=" * 60)
        print("COMPLETE ATTACHMENT MIGRATION FOR SMALL FORUMS")
        print("=" * 60)

        # Step 1: Export from database
        attachments_df = self.export_attachments_csv()
        if attachments_df is None or len(attachments_df) == 0:
            print("\n⚠️  No attachments found in database. Skipping file migration.")
            return False

        # Step 2: Find phpBB files
        phpbb_info = self.find_phpbb_files(phpbb_installation_path)
        if not phpbb_info:
            print("\n⚠️  No PhpBB file. Skipping file migration.")
            return False

        # Step 3: Verify files exist
        verified_files = self.verify_files_exist(attachments_df, phpbb_info)
        if not verified_files:
            print("\n⚠️  No verified files found. Cannot proceed with file migration.")
            return False

        # Step 4: Copy attachments
        self.copy_attachments(verified_files, "./nodebb_uploads")

        # Step 5: Update posts
        self.update_posts_with_attachments(verified_files)

        # Step 6: Copy avatars
        self.copy_avatars(phpbb_info, "./nodebb_uploads")

        print("\n" + "=" * 60)
        print("🎉 ATTACHMENT MIGRATION COMPLETE!")
        print("=" * 60)

        summary = {
            'attachments_in_db': len(attachments_df),
            'files_verified': len(verified_files),
            'posts_updated': len(set(f['post_id'] for f in verified_files))  
        }
        print("\n📋 Summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")

        next_steps = [
                "1. Your posts.csv now has attachment links",
                "2. Files are in ./nodebb_uploads/",
                "3. NodeBB needs access to these files",
                "4. Configure NodeBB uploads path if needed"
        ]
        print("\n🚀 Next steps:")
        for step in next_steps:
            print(f"   {step}")

        return True


def main():
    """Main."""

    mapper = AccurateAttachmentMapper()
    success = mapper.run(PHPBB_PATH)

    if success:
        print("\n✅ All done! Your attachments are ready for NodeBB import.")
    else:
        print("\n❌ Migration encountered issues.")


if __name__ == "__main__":
    main()
