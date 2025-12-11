#!/usr/bin/env python3
"""
fix_html_posts.py - Find and fix posts with HTML remnants
"""

import re
import pathlib

import pandas as pd  # pip3 install pandas --break-system-packages


def main():
    """Main."""

    print("🔍 Finding posts with HTML remnants...")

    # Load posts
    df = pd.read_csv('./phpbb_export/posts.csv')

    # Find posts with HTML tags
    html_pattern = r'<[^>]+>'
    html_mask = df['content'].astype(str).str.contains(html_pattern, regex=True)

    # Get the problematic posts
    problem_posts = df[html_mask].copy()
    print(f"Found {len(problem_posts)} posts with HTML\n")

    if len(problem_posts) > 0:
        print("=" * 60)
        print("PROBLEMATIC POSTS")
        print("=" * 60)

        for idx, row in problem_posts.iterrows():
            content = str(row['content'])

            # Find all HTML tags in this post
            html_tags = re.findall(html_pattern, content)
            unique_tags = set(html_tags)

            print(f"\n📝 Post ID: {row['pid']} (index: {idx})")
            print(f"   Topic ID: {row['tid']}")
            print(f"   User ID: {row['uid']}")
            print(f"   HTML tags found: {', '.join(unique_tags)}")

            # Show context (100 chars before/after first HTML tag)
            first_match = re.search(html_pattern, content)
            if first_match:
                start = max(0, first_match.start() - 50)
                end = min(len(content), first_match.end() + 50)
                context = content[start:end]
                print(f"   Context: ...{context}...")

            # Show the fix
            fixed_content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'<p[^>]*>', '\n\n', fixed_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'</p>', '\n\n', fixed_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', fixed_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', fixed_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', fixed_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', fixed_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'<u[^>]*>(.*?)</u>', r'_\1_', fixed_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', fixed_content, flags=re.IGNORECASE)
            fixed_content = re.sub(r'<img[^>]*src="([^"]*)"[^>]*>', r'![](\1)', fixed_content, flags=re.IGNORECASE)

            # Remove any remaining HTML tags
            fixed_content = re.sub(r'<[^>]+>', '', fixed_content)

            # Clean up extra whitespace
            fixed_content = re.sub(r'\n{3,}', '\n\n', fixed_content)
            fixed_content = fixed_content.strip()

            # Update the dataframe
            df.at[idx, 'content'] = fixed_content

            print("   Fixed: HTML removed/converted to Markdown")

        print("\n" + "=" * 60)
        print("💾 Saving fixes...")

        # Backup first
        backup_file = pathlib.Path('./phpbb_export/backup/posts_pre_html_fix.csv')
        df.to_csv(backup_file, index=False)
        print(f"   Backup saved: {backup_file}")

        # Save fixed version
        df.to_csv('./phpbb_export/posts.csv', index=False)
        print("   Fixed posts saved to: ./phpbb_export/posts.csv")

        # Verify fix
        remaining_html = df['content'].astype(str).str.contains(html_pattern, regex=True).sum()
        print(f"\n✅ Verification: {remaining_html} posts still contain HTML")

        if remaining_html == 0:
            print("🎉 ALL HTML TAGS HAVE BEEN CLEANED!")
        else:
            print(f"⚠️  {remaining_html} posts still need manual attention")

    else:
        print("✅ No posts with HTML found!")

    # Show a quick summary of what was fixed
    print("\n" + "=" * 60)
    print("FIX SUMMARY")
    print("=" * 60)

    if len(problem_posts) > 0:
        # Re-check for common HTML tags
        common_tags = ['<br>', '<p>', '<strong>', '<b>', '<em>', '<i>', '<a>', '<img>']
        for tag in common_tags:
            pattern = re.escape(tag.replace('>', '')) + r'[^>]*>'
            count_before = problem_posts['content'].astype(str).str.contains(pattern, regex=True).sum()
            count_after = df['content'].astype(str).str.contains(pattern, regex=True).sum()
            if count_before > 0:
                print(f"{tag}: {count_before} → {count_after} (fixed {count_before - count_after})")
    else:
        print("No fixes were needed.")


if __name__ == "__main__":
    main()
