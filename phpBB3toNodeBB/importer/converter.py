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


class Node:
    """ For imbricated quotes."""

    def __init__(self, type_: str, author: str | None = None) -> None:
        self.type = type_
        self.author = author
        self.children: list[Node | str] = []


def parse_bbcode(text: str) -> Node:
    """BBcode -> ast."""

    root = Node("root")
    stack = [root]
    pos = 0

    for m in re.finditer(r'\[quote(?:=([^\]]+))?\]|\[/quote\]', text, re.DOTALL | re.IGNORECASE):

        if m.start() > pos:
            stack[-1].children.append(text[pos:m.start()])

        if m.group(0).lower().startswith("[quote"):
            node = Node("quote", m.group(1))
            stack[-1].children.append(node)
            stack.append(node)
        else:  # [/quote]
            if len(stack) > 1:
                stack.pop()

        pos = m.end()

    if pos < len(text):
        stack[-1].children.append(text[pos:])

    return root


def render_markdown(depth: int, node: Node) -> str:
    """Ast -> markdown."""

    lines = []
    prefix = "> " * depth

    for child in node.children:
        if isinstance(child, str):
            for line in child.splitlines():
                if prefix and not line:
                    continue
                lines.append(f"{prefix}{line}")
        else:  # quote
            if child.author:
                header = f"**{child.author}** a écrit :"
            else:
                header = "**Citation** :"
            lines.append(f"{prefix}{header}")
            lines.extend(
                render_markdown(depth + 1, child).splitlines()
            )

    return '\n'.join(lines)


def convert(text: str) -> tuple[str, bool]:
    """Convert phpBB3 content (BBCode + HTML) to NodeBB3 markdown format."""

    reference_present = False

    def handle_site_links(txt: str) -> str:
        """Links inside site."""

        txt = re.sub(r'diplomania-gen.fr', "diplomania2.fr", txt, flags=re.IGNORECASE)
        txt = re.sub(r'https://diplomania2.fr/frequentation', "https://frequentation/diplomania2.fr", txt, flags=re.IGNORECASE)
        txt = re.sub(r'https://diplomania2.fr/dokuwiki', "https://dokuwiki/diplomania2.fr", txt, flags=re.IGNORECASE)
        txt = re.sub(r'https://diplomania2.fr/dokuwiki2', "https://dokuwiki2/diplomania2.fr", txt, flags=re.IGNORECASE)

        # link to forum : a bit more complicated
        # generic
        txt = re.sub(r'https://diplomania2.fr/forum/phpBB3', "https://forum/diplomania2.fr", txt, flags=re.IGNORECASE)
        # displayed part of link
        txt = re.sub(r'\[viewtopic\.php\?t=\d+\]', '[aller voir le topic]', txt, flags=re.IGNORECASE)
        txt = re.sub(r'\[viewtopic\.php\?p=\d+#p\d+\]', '[aller voir le post]', txt, flags=re.IGNORECASE)
        # actual link
        nonlocal reference_present
        # will convert topic num old -> new somewhere else
        txt, changed = re.subn(r'/viewtopic\.php\?t=(\d+)', r'/topic/[old_tid_ref=\1]', txt, flags=re.IGNORECASE)
        if changed:
            reference_present = True
        # will convert post num old -> new somewhere else
        txt, changed = re.subn(r'/viewtopic\.php\?p=(\d+)#p(\d+)', r'/topic/[old_tid_ref=\1]/[old_pid_ref=\2]', txt, flags=re.IGNORECASE)
        if changed:
            reference_present = True

        return txt

    def replace_smiley(match: re.Match[str]) -> str:
        """Smiley."""

        smiley = match.group(1)
        if smiley in SMILIES_MAP:
            return SMILIES_MAP[smiley]

        print(f"Warning : unknown smiley >[{smiley}]<")
        return "???"

    def handle_quotes_recursive(txt: str) -> str:
        """Should work both with and without author. Cannot just use a regex here."""

        # First we remove quote html
        txt = re.sub(r'</?quote\b[^>]*>', '', txt, flags=re.DOTALL | re.IGNORECASE)  # remove HTML

        # Then we simplify bbcode
        txt = re.sub(r'\[quote=([^\]\s]+)(?:\s+(?:post_id|time|user_id)=\d+)*\]', r'[quote=\1]', txt, flags=re.DOTALL | re.IGNORECASE)

        # Finally we translate BB code to markdown
        ast = parse_bbcode(txt)
        markdown_text = render_markdown(0, ast)
        return markdown_text

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

        # Img (handled differently)
        txt = re.sub(r'\[/?img\]', '', txt, flags=re.IGNORECASE)  # remove BB
        txt = re.sub(r'\<img src="(.*?)"\>(.*?)\</img\>', r'![\2](\1)', txt, flags=re.DOTALL | re.IGNORECASE)  # convert HTML

        # URL + link text  # TODO A REVOIR TRAITER TOUS LES CAS lien, image etc...
        def convert_url(match: re.Match[str]) -> str:
            url = match.group(1)
            text = match.group(2) if match.group(2) else match.group(3) if match.group(3) else url
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

    return text, reference_present


def main() -> None:
    """Main for a single test."""

    sample = """<r>super sympa le graph !<br/>

<QUOTE author="Kakitaievitch" post_id="2166" time="1686076102" user_id="61"><s>[quote=Kakitaievitch post_id=2166 time=1686076102 user_id=61]</s>
<URL url="https://zupimages.net/viewer.php?id=23/23/fokq.png"><s>[url=https://zupimages.net/viewer.php?id=23/23/fokq.png]</s><IMG src="https://zupimages.net/up/23/23/fokq.png"><s>[img]</s>https://zupimages.net/up/23/23/fokq.png<e>[/img]</e></IMG><e>[/url]</e></URL><br/>
<br/>
Félicitations essaime !<br/>
<br/>
(j'ai eu chaud)
<e>[/quote]</e></QUOTE></r>"""

    print(sample)
    result, _ = convert(sample)
    print("===========")
    print(result)


if __name__ == "__main__":
    main()
