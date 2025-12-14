#!/usr/bin/env python3
"""
check_all_posts.py - Comprehensive check of ALL converted posts
"""

import re
import pathlib
import random

import pandas as pd  # pip3 install pandas --break-system-packages


def main():
    """Main."""

    print("=" * 60)
    print("COMPREHENSIVE POST CONVERSION CHECK")
    print("=" * 60)

    # Load the converted posts
    posts_file = pathlib.Path('./phpbb_export/posts.csv')
    if not posts_file.exists():
        print(f"❌ Error: {posts_file} not found!")
        return

    df = pd.read_csv(posts_file)
    total_posts = len(df)
    print(f"📊 Analyzing ALL {total_posts:,} posts...\n")

    # 1. BASIC STATISTICS
    print("1. BASIC STATISTICS")
    print("-" * 40)

    total_chars = df['content'].astype(str).str.len().sum()
    avg_length = total_chars / total_posts if total_posts > 0 else 0

    print(f"   Total posts: {total_posts:,}")
    print(f"   Total characters: {total_chars:,}")
    print(f"   Average post length: {avg_length:.0f} chars")
    print(f"   Posts with content: {(df['content'].astype(str).str.strip() != '').sum():,}")
    print(f"   Empty posts: {(df['content'].astype(str).str.strip() == '').sum():,}")

    # 2. CHECK FOR UNCONVERTED ELEMENTS (ALL POSTS)
    print("\n2. UNCONVERTED ELEMENTS CHECK")
    print("-" * 40)

    patterns = {
        'BBCode tags': r'\[/?\w+\]',
        'HTML tags': r'<[^>]+>',
        'PHPBB uids': r':[a-z0-9]{8}',
    }

    # Count posts containing each pattern
    for pattern_name, pattern in patterns.items():
        matches = df['content'].astype(str).str.contains(pattern, regex=True, na=False)
        count = matches.sum()
        if count > 0:
            # Get examples from affected posts
            affected = df[matches]
            examples = []
            for content in affected['content'].head(3):
                found = re.search(pattern, str(content))
                if found:
                    # Show context around the match
                    start = max(0, found.start() - 20)
                    end = min(len(content), found.end() + 20)
                    examples.append(f"...{content[start:end]}...")

            print(f"   ❌ {pattern_name}: Found in {count:,} posts")
            if examples:
                print("      Examples:")
                for ex in examples[:2]:  # Show max 2 examples
                    print(f"        {ex}")
        else:
            print(f"   ✅ {pattern_name}: None found in any post")

    # 3. MARKDOWN FORMATTING ANALYSIS
    print("\n3. MARKDOWN FORMATTING ANALYSIS")
    print("-" * 40)

    markdown_patterns = {
        'Bold text (**text**)': r'\*\*.+?\*\*',
        'Italic text (*text*)': r'(?<!\*)\*[^*]+?\*(?!\*)',
        'Links ([text](url))': r'\[.*?\]\(.*?\)',
        'Images (![alt](url))': r'!\[.*?\]\(.*?\)',
        'Blockquotes (> text)': r'^> .+',
        'Code blocks (```code```)': r'```.*?```',
        'Inline code (`code`)': r'(?<!`)`[^`]+`(?!`)',
        'Lists (- item)': r'^[ \t]*[-*+] .+',
        'Headings (# Header)': r'^#{1,6} .+',
    }

    for desc, pattern in markdown_patterns.items():
        # Use dotall for multiline patterns where needed
        dotall = pattern.startswith('^')  # Patterns starting with ^ are multiline
        flags = re.MULTILINE | re.DOTALL if dotall else re.MULTILINE

        try:
            # Count posts containing this markdown
            count = df['content'].astype(str).str.contains(pattern, regex=True, flags=flags, na=False).sum()
            percentage = (count / total_posts * 100) if total_posts > 0 else 0
            print(f"   {desc}: {count:,} posts ({percentage:.1f}%)")
        except:
            print(f"   {desc}: Error in pattern")

    # 4. POST LENGTH DISTRIBUTION
    print("\n4. POST LENGTH DISTRIBUTION")
    print("-" * 40)

    lengths = df['content'].astype(str).str.len()
    print(f"   Shortest post: {lengths.min()} chars")
    print(f"   Longest post: {lengths.max():,} chars")
    print(f"   25th percentile: {lengths.quantile(0.25):.0f} chars")
    print(f"   Median (50th): {lengths.median():.0f} chars")
    print(f"   75th percentile: {lengths.quantile(0.75):.0f} chars")

    # 5. SAMPLE POSTS FOR VISUAL VERIFICATION
    print("\n5. RANDOM SAMPLES FOR VISUAL CHECK")
    print("-" * 40)

    sample_indices = random.sample(range(min(100, total_posts)), min(3, total_posts))

    for i, idx in enumerate(sample_indices, 1):
        content = str(df.iloc[idx]['content'])
        print(f"\n   Sample {i} (Post #{idx}):")
        print("   " + "=" * 35)

        # Replace newlines for cleaner display
        content = content.replace('\n', '\n   ')
        print(f"   {content}")

        # Show stats for this post
        lines = content.count('\n') + 1
        words = len(content.split())
        print(f"   Stats: {len(content)} chars, {words} words, {lines} lines")

    # 6. SPECIAL CASE: SMILEY CHECK (informational only)
    print("\n6. TEXT SMILEY ANALYSIS")
    print("-" * 40)

    smiley_patterns = {
        ':) :-)': r':-?\)',
        ':( :-(': r':-?\(',
        ':D :-D': r':-?D',
        ':P :-P': r':-?P',
        ';) ;-)': r';-?\)',
    }

    total_smilies = 0
    for desc, pattern in smiley_patterns.items():
        count = df['content'].astype(str).str.count(pattern).sum()
        if count > 0:
            print(f"   {desc}: {count:,} occurrences")
            total_smilies += count

    if total_smilies > 0:
        print(f"   Total smilies: {total_smilies:,}")
        print("   Note: Smilies are TEXT, not BBCode. They're fine as-is.")
    else:
        print("   No text smilies found")

    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 60)

    # Summary assessment
    if total_posts > 0:
        # Check if conversion appears successful
        has_bbcode = df['content'].astype(str).str.contains(r'\[/?\w+\]', regex=True, na=False).any()
        has_html = df['content'].astype(str).str.contains(r'<[^>]+>', regex=True, na=False).any()

        if not has_bbcode and not has_html:
            print("\n🎉 EXCELLENT: No BBCode or HTML tags found!")
            print("   Your conversion appears to be 100% successful.")
        else:
            if has_bbcode:
                number = df['content'].astype(str).str.contains(r'\[/?\w+\]', regex=True, na=False).sum()
                print(f"\n⚠️  WARNING: Found {number} posts with BBCode")
            if has_html:
                number = df['content'].astype(str).str.contains(r'<[^>]+>', regex=True, na=False).sum()
                print(f"\n⚠️  WARNING: Found {number} posts with HTML")
    else:
        print("\n❌ ERROR: No posts found in the CSV file")


if __name__ == "__main__":
    main()
