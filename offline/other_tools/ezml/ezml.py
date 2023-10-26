#!/usr/bin/env python3


"""
EZML parser

"""

import argparse
import os
import sys
import pathlib
import typing


# DEBUG mode
DEBUG = False

# extension of files to scan
EXTENSION_EXPECTED = ".ezml"

# does not seem to be necessary for '<' and '>'
SUBSTITUTION_TABLE: typing.Dict[str, str] = {}


class Block:
    """ Block """

    @staticmethod
    def terminator(name: str) -> str:
        """ terminator """
        return name.replace('<', '</')

    def __init__(self, name: str) -> None:
        if DEBUG:
            print(f"DEBUG: make {name}", file=sys.stderr)
        self.name = name
        self.attributes: typing.Dict[str, str] = {}
        self.childs: typing.List[typing.Union[str, 'Block']] = []

    def html(self, level: int = 0) -> str:
        """ HTML output for checking """

        # HTML
        name = self.name.rstrip('>').lstrip('<')
        if self.attributes:
            name += ' ' + ' '.join([f"{k}={v}" for k, v in self.attributes.items()])
        if self.childs:
            text = ' ' * level + f"<{name}>"
            text += '\n'
            childs_str = '\n'.join([c if isinstance(c, str) else c.html(level + 1) for c in self.childs])
            text += childs_str
            text += '\n'
            terminator_str = Block.terminator(self.name)
            text += ' ' * level + terminator_str
        else:
            text = ' ' * level + f"<{name} />"
        return text


def parse_file(parsed_file: str) -> None:
    """ parse_file """

    def fail(mess: str) -> None:
        """ fail """
        print(f"ERROR: {mess} line {num_line}", file=sys.stderr)
        sys.exit(1)

    def debug(mess: str) -> None:
        """ debug """
        print(f"DEBUG: {mess} line {num_line}", file=sys.stderr)

    with open(parsed_file, encoding='utf-8') as file_ptr:

        header = True
        within_code = False
        within_description = False
        prev_line_empty = False
        title = ""
        author = ""
        date_ = ""
        stack = []
        cur_list_level = 0
        cur_chapter_level = 0
        cur_table_level = 0
        cur_block = Block('<body>')
        stack.append(cur_block)

        for num, line in enumerate(file_ptr.readlines()):

            # line number
            num_line = num + 1

            # strip ending '\n'
            line = line.rstrip('\n')

            # empty line
            if not line:

                # separator after header
                if not title:
                    fail("Missing title!")
                if header:
                    header = False
                    continue

                # list terminator
                if cur_block.name == '<li>':
                    debug("closing list")
                    while cur_block.name in ('<li>', '<ol>', '<ul>'):
                        _ = stack.pop()
                        cur_block = stack[-1]
                    cur_list_level = 0
                    continue

                # description list terminator
                if cur_block.name == '<dd>':
                    debug("closing description list")
                    while cur_block.name in ('<dd>', '<dl>'):
                        _ = stack.pop()
                        cur_block = stack[-1]
                    within_description = False
                    continue

                # actual empty line
                if prev_line_empty:
                    new_block = Block('<br>')
                    cur_block.childs.append(new_block)
                    continue

                prev_line_empty = True
                continue

            # so line was not empty
            prev_line_empty = False

            # comment
            if line.startswith('//'):
                continue

            # preamble
            if header:
                if not title:
                    title = line
                    new_block = Block('<h2>')
                    new_block.childs.append(f"{title}")
                    cur_block.childs.append(new_block)
                    debug("Found title !")
                    continue
                if not author:
                    author = line
                    new_block = Block('<h3>')
                    new_block.childs.append(f"Auteur : {author}")
                    cur_block.childs.append(new_block)
                    continue
                if not date_:
                    date_ = line
                    new_block = Block('<h3>')
                    new_block.childs.append(f"Date : {date_}")
                    cur_block.childs.append(new_block)
                    continue

            # special
            if within_code:
                if not line.startswith('<'):
                    # all is taken as raw
                    cur_block.childs.append(line)
                    continue

            # chapters
            if line.startswith('$'):
                start_line, _, line = line.partition(' ')
                if not all(c == start_line[0] for c in start_line):
                    fail("Issue with chapter: not homogeneous")
                new_chapter_level = len(start_line)
                if abs(new_chapter_level - cur_chapter_level) > 1:
                    fail("Issue with chapter: level not same/incremented/decremented")
                cur_chapter_level = new_chapter_level
                new_block = Block(f"<h{new_chapter_level + 2}>")
                new_block.childs.append(line)
                cur_block.childs.append(new_block)
                continue

            # horizontal line
            if line == '_':
                new_block = Block('<hr>')
                cur_block.childs.append(new_block)
                continue

            # block
            if line.startswith('<'):
                if line in [f"<{b}>" for b in ('center', 'code', 'blockquote')]:
                    if line == '<code>':
                        within_code = True
                    new_block = Block(line)
                    cur_block.childs.append(new_block)
                    stack.append(new_block)
                    cur_block = new_block
                    continue
                if line in [f"</{b}>" for b in ('center', 'code', 'quotation')]:
                    if line == '</code>':
                        within_code = False
                    if not stack:
                        fail("Issue with block: end but no start")
                    _ = stack.pop()
                    if cur_block.name != line.replace('/', ''):
                        fail("Issue with block: end does not match")
                    cur_block = stack[-1]
                    continue
                fail("Issue with block start: incorrect")

            # (un)ordered list
            if line.startswith('#') or line.startswith('-'):
                if line.find(' ') == -1:
                    fail("Issue with (un)ordered list: missing space")
                start_line, _, line = line.partition(' ')
                if not all(c == start_line[0] for c in start_line):
                    fail("Issue with (un)ordered list: not homogeneous")
                new_list_level = len(start_line)
                if abs(new_list_level - cur_list_level) > 1:
                    fail("Issue with (un)ordered list: level not same/incremented/decremented")
                # down
                if new_list_level > cur_list_level:
                    # create implicit ol
                    new_block = Block('<ol>' if start_line.startswith('#') else '<ul>')
                    cur_block.childs.append(new_block)
                    stack.append(new_block)
                    cur_block = new_block
                    cur_list_level = new_list_level
                    # create li
                    new_block = Block('<li>')
                    new_block.childs.append(line)
                    cur_block.childs.append(new_block)
                    stack.append(new_block)
                    cur_block = new_block
                    continue
                # up
                if new_list_level < cur_list_level:
                    # go up
                    if not stack:
                        fail("Issue with (un)ordered list: end but no start")
                    _ = stack.pop()
                    # go up
                    if not stack:
                        fail("Issue with (un)ordered list: end but no start")
                    _ = stack.pop()
                    cur_block = stack[-1]
                    cur_list_level = new_list_level
                    # create li
                    new_block = Block('<li>')
                    new_block.childs.append(line)
                    cur_block.childs.append(new_block)
                    stack.append(new_block)
                    cur_block = new_block
                    continue
                # same list continues
                assert new_list_level == cur_list_level
                # go up
                if not stack:
                    fail("Issue with (un)ordered list: end but no start")
                _ = stack.pop()
                cur_block = stack[-1]
                # create li
                new_block = Block('<li>')
                new_block.childs.append(line)
                cur_block.childs.append(new_block)
                stack.append(new_block)
                cur_block = new_block
                continue

            # table
            if line.startswith('='):
                # close table
                if line == '=':
                    debug("end table")
                    cur_table_level -= 1
                    if not stack:
                        fail("Issue with table: closing: end but no start")
                    if stack[-1].name != '<table>':
                        fail("Issue with table: closing: expecting1 a table on top of stack!")
                    _ = stack.pop()
                    cur_block = stack[-1]
                    continue
                cur_table_level += 1
                if line.find(' ') == -1:
                    fail("Issue with table: missing space")
                _, __, line = line.partition(' ')
                # create table
                debug("create table")
                new_block = Block('<table>')
                new_block.attributes['border'] = '1'
                cur_block.childs.append(new_block)
                stack.append(new_block)
                cur_block = new_block
                # create caption
                if line:
                    new_block = Block('<caption>')
                    new_block.attributes['style'] = "\"caption-side: bottom;\""
                    new_block.childs.append(line)
                    cur_block.childs.append(new_block)
                new_table = True
                continue

            # table content
            line_orig = line
            if line.startswith('|'):
                if not cur_table_level:
                    fail("Line starts with | but not in table")
                # remove it
                line = line.lstrip('|')
                # create tr
                new_block = Block('<tr>')
                debug("create tr")
                cur_block.childs.append(new_block)
                stack.append(new_block)
                cur_block = new_block
                # create th/td
                new_block = Block('<th>' if new_table else '<td>')
                debug("create th/td")
                cur_block.childs.append(new_block)
                stack.append(new_block)
                cur_block = new_block
            if line.endswith('|'):
                if not cur_table_level:
                    fail("Line end with | but not in table")
                # remove it
                line = line.rstrip('|')
                new_table = False
            if cur_table_level:
                # now work with what is left
                while True:
                    pipe_pos = line.find('|')
                    if pipe_pos == -1:
                        debug(f"put '{line}' in td")
                        cur_block.childs.append(line)
                        break
                    line2 = line[:pipe_pos]
                    debug(f"put '{line2}' in td")
                    cur_block.childs.append(line2)
                    # up
                    debug("end th/td")
                    # end td
                    if stack[-1].name != '<td>' and stack[-1].name != '<th>':
                        fail("Issue with table: closing: expecting2 a td/th on top of stack!")
                    _ = stack.pop()
                    cur_block = stack[-1]
                    if stack[-1].name != '<tr>':
                        fail("Issue with table: closing: expecting3 a tr on top of stack!")
                    # create td
                    new_block = Block('<td>')
                    debug("create td")
                    cur_block.childs.append(new_block)
                    stack.append(new_block)
                    cur_block = new_block
                    # move forward
                    line = line[pipe_pos + len('|'):]
            if line_orig.endswith('|'):
                debug("end td")
                # end td
                if stack[-1].name != '<td>':
                    fail("Issue with table: closing: expecting4 a td on top of stack!")
                _ = stack.pop()
                debug("end tr")
                # end tr
                if stack[-1].name != '<tr>':
                    fail("Issue with table: closing: expecting5 a tr on top of stack!")
                _ = stack.pop()
                cur_block = stack[-1]
            if cur_table_level:
                continue

            # description list
            if line.startswith('(') and line.endswith(')'):
                line = line.lstrip('(').rstrip(')')
                if not within_description:
                    # create dl
                    new_block = Block('<dl>')
                    debug("create dl")
                    cur_block.childs.append(new_block)
                    stack.append(new_block)
                    cur_block = new_block
                    within_description = True
                else:
                    # up
                    if stack[-1].name != '<dd>':
                        fail("Issue with description: closing: expecting5 a dd on top of stack!")
                    _ = stack.pop()
                    cur_block = stack[-1]
                    debug("pop dd")
                # create dt
                new_block = Block('<dt>')
                new_block.attributes['style'] = "\"font-weight: bold;\""
                debug("create dt")
                new_block.childs.append(line)
                cur_block.childs.append(new_block)
                # create dd
                new_block = Block('<dd>')
                debug("create dd")
                cur_block.childs.append(new_block)
                stack.append(new_block)
                cur_block = new_block
                continue
            if within_description:
                cur_block.childs.append(line)
                continue

            # inlined item
            if line.find('*') != -1 or line.find('_') != -1 or line.find('"') != -1 or line.find('+') != -1:
                inline = '*' if line.find('*') != -1 else '_' if line.find('_') != -1 else '"' if line.find('"') != -1 else '+'
                start = line.find(inline)
                end_text = line.find(inline, start + len(inline))
                if end_text == -1:
                    fail("Inline : missing end of text")
                text = line[start + len(inline):end_text]
                before = line[:start]
                after = line[end_text + len(inline):]
                new_block = Block('<strong>' if inline == '*' else '<em>' if inline == '_' else '<q>' if inline == '"' else '<code>')
                new_block.childs.append(text)
                cur_block.childs.append(before)
                cur_block.childs.append(new_block)
                cur_block.childs.append(after)
                continue

            # hyperlink or image
            if line.find('[[') != -1 or line.find('{{') != -1:
                item = '[[' if line.find('[[') != -1 else '{{'
                item2 = ']' if item == '[[' else '}'
                start = line.find(item)
                end_link = line.find(item2)
                if end_link == -1:
                    fail("Hyperlink/image : missing end of link")
                end_text = line.find(item2, end_link + len(item2))
                if end_text == -1:
                    fail("Hyperlink/image : missing end of text")
                link = line[start + len(item):end_link]
                text = line[end_link + len(item2):end_text]
                if not text:
                    text = link
                new_block = Block('<a>' if item == '[[' else '<img>')
                if item == '[[':
                    new_block.attributes['href'] = link
                    new_block.childs.append(text)
                else:
                    new_block.attributes['src'] = f"\"link\""
                    new_block.attributes['alt'] = f"\"text\""
                before = line[:start]
                after = line[end_text + len(item2):]
                cur_block.childs.append(before)
                cur_block.childs.append(new_block)
                cur_block.childs.append(after)
                continue

            # special characters
            for pattern, patter_replace in SUBSTITUTION_TABLE.items():
                line = line.replace(pattern, patter_replace)

            # rest
            cur_block.childs.append(line)

    if len(stack) != 1:
        fail("Issue with main: some blocks were never closed")
    block = stack.pop()

    print(block.html())


def main() -> None:
    """ main """

    # parameters

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help="EZML file")
    args = parser.parse_args()
    file_path = args.input

    # must exist
    if not os.path.isfile(file_path):
        print("ERROR: Seems file {file_path} does not exist !", file=sys.stderr)
        sys.exit(-1)

    # must have extension
    if pathlib.Path(file_path).suffix != EXTENSION_EXPECTED:
        print(f"ERROR: Seems file {file_path} does not have the extension {EXTENSION_EXPECTED} !", file=sys.stderr)
        sys.exit(-1)

    print(f"Parsing file {file_path}...", file=sys.stderr)
    parse_file(file_path)


if __name__ == '__main__':
    main()
