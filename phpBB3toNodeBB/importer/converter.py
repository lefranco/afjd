#!/usr/bin/env python3

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

class PhpBBToNodeBBConverter:
    """
    Convert phpBB3 content (BBCode + HTML) to NodeBB3 markdown format.
    """


    def convert(self, text: str) -> str:
        """ Convert """

        def replace_smiley(match):
            smiley = match.group(1)
            # Retourne l'emoji correspondant ou garde le smiley si non trouvé
            return SMILIES_MAP.get(smiley, smiley)

        def handle_quotes_recursive(txt):
            """Should work both with and without author"""

            match = re.search(r'<QUOTE(?:[^>]*author="([^"]+)")?[^>]*>(.*?)</QUOTE>', txt, flags=re.DOTALL | re.IGNORECASE)
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

        def replace_bb_code(txt):

            # html things like &gt;
            txt = html.unescape(txt)

            # Size (ignored)
            txt = re.sub(r'\[size=[^\]]*\](.*?)\[/size\]', r'\1', txt, flags=re.DOTALL | re.IGNORECASE) # convert (ignore) BB
            txt = re.sub(r'<size [^>]*>(.*?)</size>', r'\1', txt, flags=re.DOTALL | re.IGNORECASE) # remove HTML

            # Bold
            txt = re.sub(r'\[b\](.*?)\[/b\]', r'**\1**', txt, flags=re.DOTALL | re.IGNORECASE)   # convert BB
            txt = re.sub(rf'</?b\b[^>]*>', '', txt, flags=re.IGNORECASE)  # remove html

            # Italic
            txt = re.sub(r'\[i\](.*?)\[/i\]', r'*\1*', txt, flags=re.DOTALL | re.IGNORECASE)  # convert BB
            txt = re.sub(rf'</?i\b[^>]*>', '', txt, flags=re.IGNORECASE) # remove HTML

            # Barred
            txt = re.sub(r'\[barre\](.*?)\[/barre\]', r'~~\1~~', txt, flags=re.DOTALL | re.IGNORECASE)  # convert BB
            txt = re.sub(rf'</?barre\b[^>]*>', '', txt, flags=re.IGNORECASE) # remove HTML

            # URL 
            def convert_url(match):
                url = match.group(1)
                text = match.group(2) if match.group(2) else url
                return f'[{text}]({url})'
            pattern = r'<URL url="([^"]+)">\s*(?:<LINK_TEXT text="([^"]+)">.*?</LINK_TEXT>|(.*?))\s*</URL>'
            txt = re.sub(pattern, convert_url, txt, flags=re.IGNORECASE | re.DOTALL)

            # Code
            txt = re.sub(r'\[code\](.*?)\[/code\]', r'``\1```', txt, flags=re.DOTALL | re.IGNORECASE)   # convert BB
            txt = re.sub(rf'</?code\b[^>]*>', '', txt, flags=re.IGNORECASE) # remove HTML

            # Lists
            def convert_list(match):
                content = match.group(1)
                content = re.sub(r'</?LI\b[^>]*>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'<s>|<e>', '', content, flags=re.IGNORECASE)
                items = re.findall(r'\[\*\](.*)', content)
                return '\n'.join(f'- {item.strip()}' for item in items)
            txt = re.sub(r'\[list[^\]]*\](.*?)\[/list\]', convert_list, txt, flags=re.DOTALL | re.IGNORECASE)
            txt = re.sub(r'</?list\b[^>]*>', '', txt, flags=re.IGNORECASE) # remove HTML

            # Tables
            def convert_table(match):
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

            # Img
            # TODO : put the file
            txt = re.sub(r'\[img\](.*?)\[/img\]', r'![](\1)', txt, flags=re.IGNORECASE)   # convert BB
            txt = re.sub(r'</?img[^>]*>', '', txt, flags=re.IGNORECASE) # remove HTML

            # Youtube
            pattern = r'<YOUTUBE content="([^"]+)">.*?\[/youtube\]</YOUTUBE>'
            txt = re.sub(pattern, lambda m: f'[Voir la vidéo YouTube](https://www.youtube.com/watch?v={m.group(1)})', txt, flags=re.IGNORECASE | re.DOTALL)

            return txt

        # remove r, s, t tags
        text = re.sub(r'</?r\b[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</?t\b[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</?s\b[^>]*>', '', text, flags=re.IGNORECASE)

        # smileys
        text = re.sub(r'<e>(.*?)</e>', replace_smiley, text, flags=re.DOTALL | re.IGNORECASE)

        # emojis TODO : check
        text = re.sub(r'<emoji[^>]*>(.*?)</emoji>', lambda m: m.group(1), text, flags=re.DOTALL | re.IGNORECASE)

        # bbcode
        text = replace_bb_code(text)

        # remove all <br>
        text = re.sub(r'<br\s*/?>', '', text, flags=re.IGNORECASE)

        # quotes
        text = handle_quotes_recursive(text)

        # remove empty lines
        text = re.sub(r'\n\s*\n+', '\n\n', text)    

        return text

sample = """
<r><B><s>[b]</s>Les inscriptions pour le Tournoi du Scorpion de l’Astrocup 2025 sont ouvertes jusqu’au vendredi 24 Octobre. <e>[/b]</e></B><br/>
L’Astrocup, c’est une partie blitz par tournoi, deux si vous vous qualifiez en Finale. Vous n’êtes pas obligés de jouer les 12 tournois si vous jouez la victoire d’étape.<br/>
<br/>
Cela reste conseillé si vous jouez le classement général, car la concurrence est rude !<br/>
<br/>
Pour vous inscrire, c'est directement par ici :<br/>
<URL url="https://diplomania-gen.fr/?event=ASTROCUP_2025_Scorpion_Qualifications_Inscriptions"><LINK_TEXT text="https://diplomania-gen.fr/?event=ASTROC ... scriptions">https://diplomania-gen.fr/?event=ASTROCUP_2025_Scorpion_Qualifications_Inscriptions</LINK_TEXT></URL><br/>
<br/>
Inscriptions ouvertes jusqu'au vendredi 24 Octobre.<br/>
<br/>
Le règlement est disponible ici : <br/>
<URL url="https://diplomania-gen.fr/forum/phpBB3/viewtopic.php?p=5109#p5109"><LINK_TEXT text="viewtopic.php?p=5109#p5109">https://diplomania-gen.fr/forum/phpBB3/viewtopic.php?p=5109#p5109</LINK_TEXT></URL><br/>
Règlement de l'ASTROCUP 2025 - Forum du site diplomania-gen.fr</r>
"""

converter = PhpBBToNodeBBConverter()
result = converter.convert(sample)
print(sample)
print("===========")
print(result)