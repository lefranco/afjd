#!/usr/bin/env python3
"""
convert_posts.py
Convert phpBB posts from BBCode/HTML to Markdown for NodeBB import.
"""

import re
import sys
import pathlib
import datetime
import html

import pandas as pd  # pip3 install pandas --break-system-packages
import html2text  # pip3 install html2text  --break-system-packages
import bbcode  # pip3 install bbcode  --break-system-packages


# Initialize converters
HTML_PARSER = html2text.HTML2Text()
HTML_PARSER.ignore_links = False
HTML_PARSER.ignore_images = False
HTML_PARSER.body_width = 0  # No line wrapping

BBCODE_PARSER = bbcode.Parser()


def setup_custom_bbcode():
    """Add custom handlers for phpBB-specific BBCode."""

    # Handle [quote="username"]...[/quote]
    def quote_renderer(_tag_name, value, options, _parent, _context):
        author = options.get('quote', '')
        if author:
            return f"> **{author} wrote:**\n> {value}\n\n"
        return f"> {value}\n\n"

    BBCODE_PARSER.add_formatter('quote', quote_renderer, replace_links=False)

    # Handle [code]...[/code] and [code=language]...[/code]
    def code_renderer(_tag_name, value, options, _parent, _context):
        language = options.get('code', '')
        if language:
            return f"```{language}\n{value}\n```\n\n"
        return f"```\n{value}\n```\n\n"

    BBCODE_PARSER.add_formatter('code', code_renderer, replace_links=False)

    # Handle URLs with text: [url=link]text[/url]
    def url_renderer(_tag_name, value, options, _parent, _context):
        url = options.get('url', '')
        if url:
            return f"[{value}]({url})"
        return f"[{value}]({value})"  # Fallback

    BBCODE_PARSER.add_formatter('url', url_renderer, replace_links=False)


def clean_phpbb_text(text):
    """Remove phpBB-specific formatting and clean up text."""
    if not isinstance(text, str):
        return ""

    # Remove bbcode_uid (e.g., :1q2w3e4r)
    text = re.sub(r':[a-z0-9]{8}', '', text)

    # Remove smilies text codes (e.g., :) :D :() - keep as is or convert to emoji
    # text = re.sub(r'(?<!\w):(\)|\(|D|P|O|S|\||/)', '', text)

    # Fix common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&quot;', '"')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text

def phpbb_to_markdown(post_text):
    """Improved conversion with proper HTML entity handling."""
    if not isinstance(post_text, str) or not post_text.strip():
        return ""

    # Step 1: Decode ALL HTML entities FIRST
    try:
        text = html.unescape(post_text)
    except:
        # Manual unescape if html module not available
        text = post_text
        replacements = [
            ('&amp;', '&'),
            ('&lt;', '<'),
            ('&gt;', '>'),
            ('&quot;', '"'),
            ('&apos;', "'"),
            ('&nbsp;', ' '),
            ('&#039;', "'"),
            ('&#39;', "'"),
            ('&#034;', '"'),
            ('&#34;', '"'),
            ('&#038;', '&'),
            ('&#38;', '&'),
            ('&#060;', '<'),
            ('&#60;', '<'),
            ('&#062;', '>'),
            ('&#62;', '>'),
        ]
        for old, new in replacements:
            text = text.replace(old, new)

    # Step 2: Clean phpBB-specific formatting
    text = re.sub(r':[a-z0-9]{8}', '', text)  # Remove bbcode_uid

    # Step 3: Check if content has BBCode or is plain text
    has_bbcode = '[' in text and ']' in text

    if has_bbcode:
        # Step 4: Process BBCode with better error handling
        try:
            # First pass: convert common BBCode to temporary markers
            # This prevents html2text from messing with BBCode

            # Save URLs before conversion
            url_pattern = r'\[url=(.*?)\](.*?)\[/url\]'
            urls = re.findall(url_pattern, text, re.IGNORECASE)
            for i, (url, label) in enumerate(urls):
                text = text.replace(f'[url={url}]{label}[/url]', f'__URL{i}__')

            # Save images
            img_pattern = r'\[img\](.*?)\[/img\]'
            images = re.findall(img_pattern, text, re.IGNORECASE)
            for i, img_url in enumerate(images):
                text = text.replace(f'[img]{img_url}[/img]', f'__IMG{i}__')

            # Parse remaining BBCode
            parsed = BBCODE_PARSER.format(text)

            # Convert to Markdown
            markdown = HTML_PARSER.handle(parsed)

            # Restore URLs and images
            for i, (url, label) in enumerate(urls):
                markdown = markdown.replace(f'__URL{i}__', f'[{label}]({url})')
            for i, img_url in enumerate(images):
                markdown = markdown.replace(f'__IMG{i}__', f'![image]({img_url})')

        except Exception as e:
            print(f"  Warning: BBCode parsing failed: {e}")
            # Fallback: just decode HTML entities and clean up
            markdown = text
    else:
        # No BBCode, just convert any HTML to Markdown
        markdown = HTML_PARSER.handle(text)

    # Step 5: Final cleanup
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Remove excessive newlines

    # Fix common issues
    markdown = re.sub(r'\[/\w+\]', '', markdown)  # Remove any remaining closing tags
    markdown = re.sub(r'\[\w+[^\]]*\]', '', markdown)  # Remove any remaining opening tags

    # Ensure & characters are preserved
    markdown = markdown.replace('&amp;', '&').replace('&#38;', '&')

    return markdown.strip()


def process_attachments_in_content(content, post_id, attachments_df):
    """Add attachment references to post content."""
    if attachments_df is None or content is None:
        return content

    # Find attachments for this post
    post_attachments = attachments_df[attachments_df['post_id'] == post_id]

    if len(post_attachments) == 0:
        return content

    # Add attachments section
    attachment_text = "\n\n---\n**Attachments:**\n"
    for _, attachment in post_attachments.iterrows():
        filename = attachment.get('original_filename', attachment.get('real_filename', 'file'))
        # Use a placeholder path - adjust based on your NodeBB setup
        link = f"- [{filename}](/assets/uploads/{attachment.get('stored_filename', 'unknown')})"
        attachment_text += link + "\n"

    return content + attachment_text


def main():
    """Main conversion function."""
    print("=" * 60)
    print("phpBB to Markdown Converter")
    print("=" * 60)

    setup_custom_bbcode()

    # Paths
    export_dir = pathlib.Path('./phpbb_export')
    posts_file = export_dir / 'posts.csv'
    attachments_file = export_dir / 'attachments.csv'
    backup_dir = export_dir / 'backup'

    # Check if posts file exists
    if not posts_file.exists():
        print(f"❌ Error: {posts_file} not found!")
        print("   Run export.py first to create the CSV files.")
        sys.exit(1)

    # Create backup
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f'posts_backup_{timestamp}.csv'

    print(f"📁 Input: {posts_file}")
    print(f"📁 Backup: {backup_file}")

    # Load posts
    try:
        posts_df = pd.read_csv(posts_file)
        print(f"📊 Loaded {len(posts_df)} posts")

        # Create backup
        posts_df.to_csv(backup_file, index=False)
        print("✅ Created backup")
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        sys.exit(1)

    # Load attachments if available
    attachments_df = None
    if attachments_file.exists():
        try:
            attachments_df = pd.read_csv(attachments_file)
            print(f"📎 Loaded {len(attachments_df)} attachments")
        except:
            print("⚠️  Could not load attachments.csv")

    # Check if conversion is needed
    sample_content = posts_df['content'].iloc[0] if len(posts_df) > 0 else ""
    if isinstance(sample_content, str) and ('[' in sample_content or '<' in sample_content):
        print("🔍 Detected BBCode/HTML content - conversion needed")
    else:
        print("⚠️  Content may already be in Markdown format")
        response = input("   Proceed with conversion anyway? (y/N): ")
        if response.lower() != 'y':
            print("Conversion cancelled.")
            sys.exit(0)

    # Convert posts
    print("\n🔄 Converting posts to Markdown...")
    converted_count = 0
    total_posts = len(posts_df)

    for idx in range(total_posts):
        post_id = posts_df.loc[idx, 'pid'] if 'pid' in posts_df.columns else idx + 1
        original_content = posts_df.loc[idx, 'content']

        # Convert content
        markdown_content = phpbb_to_markdown(original_content)

        # Add attachments if available
        if attachments_df is not None:
            markdown_content = process_attachments_in_content(
                markdown_content, post_id, attachments_df
            )

        # Update dataframe
        posts_df.loc[idx, 'content'] = markdown_content

        # Progress indicator
        converted_count += 1
        if converted_count % 100 == 0 or converted_count == total_posts:
            print(f"   Progress: {converted_count}/{total_posts} posts")

    # Save converted posts
    try:
        posts_df.to_csv(posts_file, index=False)
        print(f"\n✅ Converted {converted_count} posts")
        print(f"💾 Saved to: {posts_file}")

        # Create a sample file to check conversion
        sample_file = export_dir / 'conversion_sample.txt'
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write("SAMPLE CONVERSION - FIRST 5 POSTS\n")
            f.write("=" * 50 + "\n\n")
            for i in range(min(5, len(posts_df))):
                f.write(f"POST {i+1}:\n")
                f.write("-" * 30 + "\n")
                f.write(str(posts_df['content'].iloc[i])[:500])
                f.write("\n\n" + "=" * 50 + "\n\n")

        print(f"📝 Sample output: {sample_file}")

    except Exception as e:
        print(f"❌ Failed to save converted posts: {e}")
        sys.exit(1)

    print("\n🎉 Conversion complete!")
    print("\nNext steps:")
    print("1. Check the sample file to verify conversion quality")
    print("2. Copy phpBB attachments to NodeBB's upload directory")
    print("3. Set up NodeBB v1.12.1 and install nodebb-plugin-import")
    print("4. Run the import using your phpbb_export directory")

if __name__ == "__main__":
    main()
