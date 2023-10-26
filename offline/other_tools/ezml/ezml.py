#!/usr/bin/env python3


"""
EZML parser

"""

import argparse
import os
import sys
import pathlib
import typing


# extension of files to scan
EXTENSION_EXPECTED = ".ezml"


class Block:
    """ Block """

    @staticmethod
    def terminator(name: str) -> str:
        """ terminator """
        return name.replace('<', '</')

    def __init__(self, name: str) -> None:
        print(f"DEBUG: make {name}", file=sys.stderr)
        self.name = name
        self.attributes: typing.Dict[str, str] = {}
        self.childs:typing.List[typing.Union[str, 'Block']] = []

    def html(self, level: int = 0) -> str:
        """ HTML output for checking """

        # HTML
        name = self.name.rstrip('>').lstrip('<')
        if self.attributes:
            name += ' ' + ' '.join([f"{k}={v}" for k, v in self.attributes.items()])
        text = ' ' * level + f"<{name}>"
        text += '\n'
        if self.childs:
            childs_str = '\n'.join([c if isinstance(c, str) else c.html(level + 1) for c in self.childs])
            text += childs_str
            text += '\n'
        terminator_str = Block.terminator(self.name)
        text += ' ' * level + terminator_str
        return text


def parse_file(parsed_file: str) -> None:
    """ parse_file """

    def fail(mess: str) -> None:
        """ fail """
        print(f"ERROR: {mess} line {num_line}")
        sys.exit(1)

    def debug(mess: str) -> None:
        """ debug """
        print(f"DEBUG: {mess} line {num_line}", file=sys.stderr)

    with open(parsed_file, encoding='utf-8') as file_ptr:

        header = True
        title = ""
        author = ""
        date_ = ""
        stack = []
        cur_list_level = 0
        cur_chapter_level = 0
        cur_block = Block('<body>')
        stack.append(cur_block)

        for num, line in enumerate(file_ptr.readlines()):

            # line number
            num_line = num + 1

            # strip ending '\n'
            line = line.rstrip()

            # empty line
            if not line:

                if not title:
                    fail("Missing title!")
                if header:
                    header = False
                    continue

                # close ol/ul
                if cur_block.name == '<li>':
                    while cur_block.name in ('<li>', '<ol>', '<ul>'):
                        _ = stack.pop()
                        cur_block = stack[-1]
                    cur_list_level = 0
                    continue

                new_block = Block('<br>')
                cur_block.childs.append(new_block)
                continue

            # comment
            if line.startswith('//'):
                continue

            # preamble
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

            # chapters
            if line.startswith('$'):
                start_line, _, line2 = line.partition(' ')
                if not all(c == start_line[0] for c in start_line):
                    fail("Issue with chapter: not homogeneous")
                new_chapter_level = len(start_line)
                if abs(new_chapter_level - cur_chapter_level) > 1:
                    fail("Issue with chapter: level not same/incremented/decremented")
                cur_chapter_level = new_chapter_level
                new_block = Block(f"<h{new_chapter_level + 2}>")
                new_block.childs.append(line2)
                cur_block.childs.append(new_block)
                continue

            # horizontal line
            if line == '+':
                new_block = Block('<hr>')
                cur_block.childs.append(new_block)
                continue

            # block
            if line.startswith('<'):
                if line in [f"<{b}>" for b in ('center', 'code', 'quotation')]:
                    new_block = Block(line)
                    cur_block.childs.append(new_block)
                    stack.append(new_block)
                    cur_block = new_block
                    continue
                if line in [f"</{b}>" for b in ('center', 'code', 'quotation')]:
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
                start_line, _, line2 = line.partition(' ')
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
                    new_block.childs.append(line2)
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
                    new_block.childs.append(line2)
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
                new_block.childs.append(line2)
                cur_block.childs.append(new_block)
                stack.append(new_block)
                cur_block = new_block
                continue

            # table
            if line.startswith('='):
                # close table
                if line == '=':
                    if not stack:
                        fail("Issue with table: closing: end but no start")
                    _ = stack.pop()
                    cur_block = stack[-1]
                    continue
                if line.find(' ') == -1:
                    fail("Issue with table: missing space")
                _, __, line2 = line.partition(' ')
                # create table
                new_block = Block('<table>')
                new_block.attributes['border'] = '1'
                cur_block.childs.append(new_block)
                stack.append(new_block)
                cur_block = new_block
                # create caption
                new_block = Block('<caption>')
                new_block.childs.append(line2)
                cur_block.childs.append(new_block)
                new_table = True
                continue
            # new row
            if line.find('|') != -1:
                # create tr/th
                new_block = Block('<tr>')
                cur_block.childs.append(new_block)
                stack.append(new_block)
                cur_block = new_block
                # check same number of columns
                if new_table:
                    expected_colums = line.count('|')
                else:
                    if line.count('|') != expected_colums:
                        fail("Issue with table: not same number of columns")
                # put in tr
                for line2 in line.split('|'):
                    new_block = Block('<th>' if new_table else '<td>')
                    new_block.childs.append(line2)
                    cur_block.childs.append(new_block)
                new_table = False
                # up
                _ = stack.pop()
                cur_block = stack[-1]
                continue

            # inlined item
            if line.find('*') != -1 or line.find('_') != -1 or line.find('"') != -1:
                inline = '*' if line.find('*') != -1 else '_' if line.find('_') != -1 else '"'
                start = line.find(inline)
                end_text = line.find(inline, start + len(inline))
                if end_text == -1:
                    fail("Inline : missing end of text")
                text = line[start + len(inline):end_text]
                before = line[:start]
                after = line[end_text + len(inline):]
                new_block = Block('<b>' if inline == '*' else '<em>' if inline == '_' else '<q>')
                new_block.childs.append(text)
                cur_block.childs.append(before)
                cur_block.childs.append(new_block)
                cur_block.childs.append(after)
                continue

            # hyperlink
            if line.find('[[') != -1:
                start = line.find('[[')
                end_link = line.find(']')
                if end_link == -1:
                    fail("Hyperlink : missing end of link")
                end_text = line.find(']', end_link + len(']'))
                if end_text == -1:
                    fail("Hyperlink : missing end of text")
                link = line[start + len('[['):end_link]
                text = line[end_link + len(']'):end_text]
                new_block = Block('<a>')
                new_block.childs.append(text)
                new_block.attributes['href'] = link
                before = line[:start]
                after = line[end_text + len(']'):]
                cur_block.childs.append(before)
                cur_block.childs.append(new_block)
                cur_block.childs.append(after)
                continue

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
