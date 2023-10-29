#!/usr/bin/env python3


"""
EZML parser

Reads and EZML file and convertit into a tree of Block / str
that matches the DOM

"""


# DEBUG mode
DEBUG = False


# character to escape
ESCAPER_CHAR = '\\'


class Block:
    """ Block """

    @staticmethod
    def terminator(name: str) -> str:
        """ terminator """
        return name.replace('<', '</')

    def __init__(self, name: str) -> None:
        if DEBUG:
            print(f"DEBUG: make {name}")
        self.name = name
        self.attributes = {}
        self.childs = []


class Ezml:
    """ Ezml object """

    def __init__(self, parsed_file: str) -> None:
        """ parse_file """

        cur_block = Block('<body>')
        stack = []
        num_line = 0

        def fail(mess: str) -> None:
            """ fail """
            print(f"ERROR: {mess} line {num_line}")

        #  def debug(mess: str) -> None:
            #  """ debug """
            #  print(f"DEBUG: {mess} line {num_line}", file=sys.stderr)

        # slash means escape
        def unescape(text: str) -> str:
            """ replaces 'ESCAPER'+ ascii code of char by 'ESCAPER' + char """

            result = ''
            while True:
                bpos = text.find(ESCAPER_CHAR)
                if bpos == -1:
                    result += text
                    return result
                result += text[:bpos]
                text = text[bpos + len(ESCAPER_CHAR):]
                if not text:
                    fail("Escape no character unescape'ing")
                escaped = 0
                while text and text[0].isdigit():
                    escaped *= 10
                    escaped += int(text[0])
                    text = text[1:]
                result += f"{chr(escaped)}"

        # slash means escape
        def escape(text: str) -> str:
            """ replaces 'ESCAPER'+ char by 'ESCAPER' + ascii code of char """

            result = ''
            while True:
                bpos = text.find(ESCAPER_CHAR)
                if bpos == -1:
                    result += text
                    return result
                result += text[:bpos]
                text = text[bpos + len(ESCAPER_CHAR):]
                if not text:
                    fail("Escape no character escape'ing")
                escaped = text[0]
                result += f"{ESCAPER_CHAR}{ord(escaped)}"
                text = text[len(escaped):]

        def inline_stuff(current_block: Block, line: str) -> None:
            """ inline_stuff """

            # inlined item
            if not (line.find('*') != -1 or line.find('_') != -1 or line.find('"') != -1 or line.find('+') != -1 or line.find('^') != -1):
                if line:
                    line = unescape(line)
                    current_block.childs.append(line)
                return

            inline = '*' if line.find('*') != -1 else '_' if line.find('_') != -1 else '"' if line.find('"') != -1 else '+' if line.find('+') != -1 else '^'
            start = line.find(inline)
            end_text = line.find(inline, start + len(inline))
            if end_text == -1:
                fail("Inline : missing end of text")
            inlined_text = line[start + len(inline):end_text]

            before = line[:start]
            after = line[end_text + len(inline):]

            # add before
            before = unescape(before)
            current_block.childs.append(before)

            name = '<strong>' if inline == '*' else '<em>' if inline == '_' else '<q>' if inline == '"' else '<code>' if inline == '+' else '<sup>'
            inline_new_block = Block(name)

            # recurse on inside
            inline_stuff(inline_new_block, inlined_text)

            current_block.childs.append(inline_new_block)

            # recurse on after
            inline_stuff(current_block, after)

        def stack_pop() -> None:
            """ stack_pop """

            nonlocal cur_block

            if not stack:
                fail("poping from empty stack !")
            _ = stack.pop()
            cur_block = stack[-1]

        def stack_push(name: str, child, attributes, must_push: bool, must_update: bool) -> None:
            """ stack_pop """

            nonlocal cur_block

            new_block = Block(name)
            if child:
                if isinstance(child, str):
                    inline_stuff(new_block, child)
                else:
                    new_block.childs.append(child)
            if attributes:
                new_block.attributes.update(attributes)

            cur_block.childs.append(new_block)

            if must_push:
                stack.append(new_block)

            if must_update:
                cur_block = new_block

        header = True
        within_code = False
        within_description = False
        within_table_header = False
        prev_line_empty = False
        title = ""
        author = ""
        date_ = ""
        cur_list_level = 0
        cur_chapter_level = 0
        cur_table_level = 0
        stack.append(cur_block)

        with open(parsed_file, encoding='utf-8') as file_ptr:

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
                        while cur_block.name in ('<li>', '<ol>', '<ul>'):
                            stack_pop()
                        cur_list_level = 0
                        continue

                    # description list terminator
                    if cur_block.name == '<dd>':
                        while cur_block.name in ('<dd>', '<dl>'):
                            stack_pop()
                        within_description = False
                        continue

                    # actual empty line
                    if prev_line_empty:
                        stack_push('<br>', None, None, False, False)
                        continue

                    prev_line_empty = True
                    continue

                # so line was not empty
                prev_line_empty = False

                # comment
                if line.startswith('//'):
                    continue

                line = escape(line)

                # preamble
                if header:
                    if not title:
                        title = line
                        stack_push('<h2>', f"{title}", None, False, False)
                        continue
                    if not author:
                        author = line
                        stack_push('<h3>', f"Auteur : {author}", None, False, False)
                        continue
                    if not date_:
                        date_ = line
                        stack_push('<h3>', f"Date : {date_}", None, False, False)
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
                    name = f"<h{new_chapter_level + 2}>"
                    stack_push(name, line, None, False, False)
                    continue

                # horizontal line
                if line == '_':
                    stack_push('<hr>', None, None, False, False)
                    continue

                # block
                if line.startswith('<'):
                    if line in [f"<{b}>" for b in ('center', 'code', 'blockquote')]:
                        if line == '<code>':
                            within_code = True
                        stack_push(line, None, None, True, True)
                        continue
                    if line in [f"</{b}>" for b in ('center', 'code', 'blockquote')]:
                        if line == '</code>':
                            within_code = False
                        if not stack:
                            fail("Issue with block: end but no start")
                        stack_pop()
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
                        name = '<ol>' if start_line.startswith('#') else '<ul>'
                        stack_push(name, None, None, True, True)
                        cur_list_level = new_list_level
                        # create li
                        stack_push('<li>', line, None, True, True)
                        continue
                    # up
                    if new_list_level < cur_list_level:
                        # go up
                        stack_pop()
                        # go up
                        stack_pop()
                        cur_list_level = new_list_level
                        # create li
                        stack_push('<li>', line, None, True, True)
                        continue
                    # same list continues
                    assert new_list_level == cur_list_level
                    # go up
                    stack_pop()
                    # create li
                    stack_push('<li>', line, None, True, True)
                    continue

                # table
                if line.startswith('='):
                    # close table
                    if line == '=':
                        cur_table_level -= 1
                        stack_pop()
                        continue
                    cur_table_level += 1
                    if line.find(' ') == -1:
                        fail("Issue with table: missing space")
                    _, __, line = line.partition(' ')
                    # create table
                    attributes = {'border': '1'}
                    stack_push('<table>', None, attributes, True, True)
                    # create caption
                    if line:
                        attributes = {'style': "\"caption-side: bottom;\""}
                        stack_push('<caption>', line, attributes, False, False)
                    within_table_header = True
                    continue

                # table content
                line_orig = line
                if line.startswith('|'):
                    if not cur_table_level:
                        fail("Line starts with | but not in table")
                    # remove it
                    line = line.lstrip('|')
                    # create tr
                    stack_push('<tr>', None, None, True, True)
                    # create th/td
                    name = '<th>' if within_table_header else '<td>'
                    stack_push(name, None, None, True, True)
                if line.endswith('|'):
                    if not cur_table_level:
                        fail("Line end with | but not in table")
                    # remove it
                    line = line.rstrip('|')
                if cur_table_level:
                    # now work with what is left
                    while True:
                        pipe_pos = line.find('|')
                        if pipe_pos == -1:
                            inline_stuff(cur_block, line)
                            break
                        line2 = line[:pipe_pos]
                        inline_stuff(cur_block, line2)
                        # up
                        # end td
                        stack_pop()
                        if stack[-1].name != '<tr>':
                            fail("Issue with table: closing: expecting3 a tr on top of stack!")
                        # create td/th
                        name = '<th>' if within_table_header else '<td>'
                        stack_push(name, None, None, True, True)
                        # move forward
                        line = line[pipe_pos + len('|'):]
                if line_orig.endswith('|'):
                    # end td
                    stack_pop()
                    # end tr
                    stack_pop()
                    within_table_header = False
                if cur_table_level:
                    continue

                # description list
                if line.startswith('(') and line.endswith(')'):
                    line = line.lstrip('(').rstrip(')')
                    if not within_description:
                        # create dl
                        stack_push('<dl>', None, None, True, True)
                        within_description = True
                    else:
                        # up
                        stack_pop()
                    # create dt
                    attributes = {'style': "\"font-weight: bold;\""}
                    stack_push('<dt>', line, attributes, False, False)
                    # create dd
                    stack_push('<dd>', None, None, True, True)
                    continue
                if within_description:
                    inline_stuff(cur_block, line)
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
                    before = line[:start]
                    after = line[end_text + len(item2):]
                    inline_stuff(cur_block, before)
                    if item == '[[':
                        attributes = {'href': link, 'target': "\"_blank\""}
                        stack_push('<a>', text, attributes, False, False)
                    else:
                        attributes = {'src': f"\"{link}\"", 'alt': f"\"{text}\""}
                        stack_push('<img>', None, None, False, False)
                    inline_stuff(cur_block, after)
                    continue

                # rest
                inline_stuff(cur_block, line)

        if len(stack) != 1:
            fail("Issue with main: some blocks were never closed")

        self.block = stack[-1]
