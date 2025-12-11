#!/usr/bin/env python3
"""
final_check
"""

import pandas as pd  # pip3 install pandas --break-system-packages


def main():
    """Main."""

    df = pd.read_csv('./phpbb_export/posts.csv')
    html_count = df['content'].astype(str).str.contains(r'<[^>]+>', regex=True).sum()
    total = len(df)

    print(f"Posts with HTML: {html_count}/{total}")
    print(f"Percentage: {(html_count/total*100):.2f}%")

    if html_count == 0:
        print("✅ PERFECT! All HTML cleaned.")
    else:
        print(f"⚠️  {html_count} posts may need manual review.")
        # Show which posts
        problem_idx = df['content'].astype(str).str.contains(r'<[^>]+>', regex=True)
        print("Problematic post IDs:", df[problem_idx]['pid'].tolist())


if __name__ == "__main__":
    main()
