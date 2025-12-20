#!/usr/bin/env python3

"""THE converter."""

import re
import html

SMILIES_MAP = {
    ':D': '😄',
    ':)': '🙂',
    ':-)': '🙂',
    ':(': '🙁',
    ':-(': '🙁',
    ';)': '😉',
    ';-)': '😉',
    ':P': '😛',
    ':p': '😛',
    ':-P': '😛',
    ':-p': '😛',
    ':o': '😮',
    ':-o': '😮',
    ':?:': '🤔',
    ':?': '🤔',
    ':-?': '🤔',
    '8)': '😎',
    '8-)': '😎',
    ':lol:': '😂',
    ':x': '😡',
    ':-x': '😡',
    ':twisted:': '😈',
    ':evil:': '😈',
    ':roll:': '🙄',
    ':|': '😐',
    ':-|': '😐',
    ':oops:': '😳',
    ':cry:': '😢',
    ':mrgreen:': '😁',
    ':!:': '⚠️',
    ':arrow:': '➡️',
    ':idea:': '💡',
    ':question:': '❓',
    ':exclaim:': '❗',
    ':shock:': '😲',
    ':confused:': '🤔',
    ':cool:': '😎',
    ':mad:': '😡',
    ':razz:': '😛',
    ':wink:': '😉',
    ':sad:': '🙁',
    ':smile:': '🙂',
    ':eek:': '😮',
    ':love:': '❤️',
    '<3': '❤️',
    '</3': '💔',
    ':thumbup:': '👍',
    ':thumbdown:': '👎',
    ':check:': '✅',
    ':cross:': '❌',
    ':star:': '⭐',
    ':heart:': '❤️',
    ':geek:': '🤓',
    ':ugeek:': '🤓',
    ':neutral:': '😐',
    ':roll eyes:': '🙄',
    ':|)': '😴',
}

# Otherwise rejected
MIN_POST_SIZE = 10


def convert(text: str) -> str:
    """Convert phpBB3 content (BBCode + HTML) to NodeBB3 markdown format."""

    def handle_site_links(txt: str) -> str:
        """Links inside site."""

        txt = re.sub(r'diplomania-gen.fr', "diplomania2.fr", txt, flags=re.IGNORECASE)
        txt = re.sub(r'https://diplomania2.fr/forum', "https://forum/diplomania2.fr/", txt, flags=re.IGNORECASE)
        txt = re.sub(r'https://diplomania2.fr/frequentation', "https://frequentation/diplomania2.fr/", txt, flags=re.IGNORECASE)
        txt = re.sub(r'https://diplomania2.fr/dokuwiki', "https://dokuwiki/diplomania2.fr/", txt, flags=re.IGNORECASE)
        txt = re.sub(r'https://diplomania2.fr/dokuwiki2', "https://dokuwiki2/diplomania2.fr/", txt, flags=re.IGNORECASE)
        txt = re.sub(r"\[viewtopic\.php\?t=\d+\]", "[viewtopic]", txt, flags=re.IGNORECASE)
        txt = re.sub(r"\[viewtopic\.php\?p=\d+#p\d+\]", "[viewpost]", txt, flags=re.IGNORECASE)

        # TODO
        # https://forum/diplomania2.fr//phpBB3/viewtopic.php?t=<old_numtopic> -> https://forum/diplomania2.fr/topic/<new_numtopic>
        # https://forum/diplomania2.fr//phpBB3/viewtopic.php?p=<old_numtopic>#p<old_numtopic> -> https://forum/diplomania2.fr/topic/<new_numtopic>/<num_post>

        return txt

    def replace_smiley(match: re.Match[str]) -> str:
        """Smiley."""

        smiley = match.group(1)
        if smiley in SMILIES_MAP:
            return SMILIES_MAP[smiley]

        print(f"Warning : unknown smiley >[{smiley}]<")
        return "???"

    def handle_quotes_recursive(txt: str) -> str:
        """Should work both with and without author."""

        # TODO : probably must be done differently, witout RE

        match = re.search(r'<QUOTE(?:[^>]*author="([^"]+)")?[^>]*>(.*)</QUOTE>', txt, flags=re.DOTALL | re.IGNORECASE)
        if not match:
            return txt

        author = match.group(1) if match.group(1) else "Quelqu'un"
        content = match.group(2)

        content = re.sub(r'<s>.*?</s>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'\[/?quote[^\]]*\]', '', content, flags=re.IGNORECASE)

        # yes : recursive !
        content = handle_quotes_recursive(content)

        content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)

        quoted = '\n'.join(f'> {line}' for line in content.splitlines() if line.strip())
        replacement = f'**{author}** a écrit :\n{quoted}'

        new_txt = txt[:match.start()] + replacement + txt[match.end():]
        return new_txt

    def replace_bb_code(txt: str) -> str:
        """Replace all BB code (or tries to)."""

        # html things like &gt;
        txt = html.unescape(txt)

        # Size (simplified to bold)
        txt = re.sub(r'\[size=[^\]]*\](.*?)\[/size\]', r'**\1**', txt, flags=re.DOTALL | re.IGNORECASE)  # convert  BB
        txt = re.sub(r'<size [^>]*>(.*?)</size>', r'\1', txt, flags=re.DOTALL | re.IGNORECASE)  # remove HTML

        # Bold
        txt = re.sub(r'\[b\](.*?)\[/b\]', r'**\1**', txt, flags=re.DOTALL | re.IGNORECASE)   # convert BB
        txt = re.sub(r'</?b\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML

        # Italic
        txt = re.sub(r'\[i\](.*?)\[/i\]', r'*\1*', txt, flags=re.DOTALL | re.IGNORECASE)  # convert BB
        txt = re.sub(r'</?i\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML

        # Underscore (simplified to bold)
        txt = re.sub(r'\[u\](.*?)\[/u\]', r'**\1**', txt, flags=re.DOTALL | re.IGNORECASE)  # convert BB
        txt = re.sub(r'</?u\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML

        # Barred
        txt = re.sub(r'\[barre\](.*?)\[/barre\]', r'~~\1~~', txt, flags=re.DOTALL | re.IGNORECASE)  # convert BB
        txt = re.sub(r'</?barre\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML

        # URL + img (must be before next one)
        txt = re.sub(r'<URL[^>]*>\[url=[^\]]*\].*?<IMG[^>]*src="([^"]+)".*?</URL>', r'[img](\1)', txt, flags=re.IGNORECASE | re.DOTALL)

        # URL + link text
        def convert_url(match: re.Match[str]) -> str:
            url = match.group(1)
            text = match.group(2) if match.group(2) else url
            return f'[{text}]({url})'
        pattern = r'<URL url="([^"]+)">\s*(?:<LINK_TEXT text="([^"]+)">.*?</LINK_TEXT>|(.*?))\s*</URL>'
        txt = re.sub(pattern, convert_url, txt, flags=re.IGNORECASE | re.DOTALL)

        # Code
        txt = re.sub(r'\[code\](.*?)\[/code\]', r'``\1```', txt, flags=re.DOTALL | re.IGNORECASE)   # convert BB
        txt = re.sub(r'</?code\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML

        # Lists
        def convert_list(match: re.Match[str]) -> str:
            """List."""
            content = match.group(1)
            content = re.sub(r'</?LI\b[^>]*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<s>|<e>', '', content, flags=re.IGNORECASE)
            items = re.findall(r'\[\*\](.*)', content)
            return '\n'.join(f'- {item.strip()}' for item in items)
        txt = re.sub(r'\[list[^\]]*\](.*?)\[/list\]', convert_list, txt, flags=re.DOTALL | re.IGNORECASE)
        txt = re.sub(r'</?list\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML

        # Tables
        def convert_table(match: re.Match[str]) -> str:
            """Table."""
            table_content = match.group(1)
            rows = re.findall(r'\[tr[^\]]*\](.*?)\[/tr\]', table_content, flags=re.DOTALL | re.IGNORECASE)
            md = []
            for i, r in enumerate(rows):
                cells = re.findall(r'\[t[dh][^\]]*\](.*?)\[/t[dh]\]', r, flags=re.DOTALL | re.IGNORECASE)
                cells = [re.sub(r'<.*?>', '', c.strip()) for c in cells]
                if cells:
                    md.append('| ' + ' | '.join(cells) + ' |')
                    if i == 0:
                        md.append('| ' + ' | '.join(['---'] * len(cells)) + ' |')
            return '\n'.join(md)
        txt = re.sub(r'\[table[^\]]*\](.*?)\[/table\]', convert_table, txt, flags=re.DOTALL | re.IGNORECASE)
        txt = re.sub(r'</?table\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML
        txt = re.sub(r'</?tr\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML
        txt = re.sub(r'</?th\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML
        txt = re.sub(r'</?td\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove HTML

        # Emojis
        txt = re.sub(r'<EMOJI[^>]*>(.*?)</EMOJI>', r'\1', txt, flags=re.DOTALL | re.IGNORECASE)  # simplify HTML

        # Youtube
        pattern = r'<YOUTUBE content="([^"]+)">.*?\[/youtube\]</YOUTUBE>'
        txt = re.sub(pattern, lambda m: f'[Voir la vidéo YouTube](https://www.youtube.com/watch?v={m.group(1)})', txt, flags=re.IGNORECASE | re.DOTALL)

        # Attachments
        txt = re.sub(r'\[(?:\/)?attachment(?:=\d+)?\]', '', txt, flags=re.IGNORECASE)  # remove bbcode (will use HTML)
        # we leave <ATTACHEMENT www >yyy</ATTACHMENT> for later processing

        return txt

    # remove useless e, r, s, t tags
    text = re.sub(r'</?e\b[^>]*>', '', text)
    text = re.sub(r'</?r\b[^>]*>', '', text)
    text = re.sub(r'</?s\b[^>]*>', '', text)
    text = re.sub(r'</?t\b[^>]*>', '', text)
    text = re.sub(r'</?t\b[^>]*>', '', text)

    # smileys
    text = re.sub(r'<E>(.*?)</E>', replace_smiley, text, flags=re.DOTALL)

    # bbcode
    text = replace_bb_code(text)

    # occurence of link to site (after bb_code which changes URL)
    text = handle_site_links(text)

    # remove all <br>
    text = re.sub(r'<br\s*/?>', '', text, flags=re.IGNORECASE)

    # quotes
    text = handle_quotes_recursive(text)

    # remove empty lines
    text = re.sub(r'\n\s*\n+', '\n\n', text)

    # make it long enough so not to be rejected
    text = text.ljust(MIN_POST_SIZE, '.')

    return text


def main() -> None:
    """Main for a sigle test."""

    sample = """
<r><QUOTE author="OrangeCar" post_id="3284" time="1702653292" user_id="59"><s>[quote=OrangeCar post_id=3284 time=1702653292 user_id=59]</s>
Après avoir lu la description du scorage sur le wiki, je voudrais comprendre le mécanisme d'attribution des points de survie.<br/>

<QUOTE><s>[quote]</s>"35 points par jusqu'à un maximum de 210 points"<e>[/quote]</e></QUOTE>

=&gt; Ne manque-t-il pas un mot entre "par" et "jusqu'à" ?
<e>[/quote]</e></QUOTE>
par année de survie</r>
"""

    print(sample)
    result = convert(sample)
    print("===========")
    print(result)


if __name__ == "__main__":
    main()
