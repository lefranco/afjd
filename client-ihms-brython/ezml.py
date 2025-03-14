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

# what to use for numbering
NUMBERING = "1ai"


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

        cur_block = None
        stack = []
        num_line = 0

        def fail(mess: str) -> None:
            """ fail """
            print(f"ERROR: {mess} line {num_line}")
            #  assert False

        #  def debug(mess: str) -> None:
            #  """ debug """
            #  print(f"DEBUG: {mess} line {num_line}", file=sys.stderr)

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

            # look for inlined item
            found_pos = min((line.find(c) for c in "*_\"+^" if c in line), default=None)

            # none where found
            if found_pos is None:
                line = unescape(line)
                current_block.childs.append(line)
                return

            inline = line[found_pos]
            start = line.find(inline)
            end_text = line.find(inline, start + len(inline))
            if end_text == -1:
                fail(f"Inline : missing end of text for '{inline}' in line='{line}' start={start}")
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
            if after:
                inline_stuff(current_block, after)

        def stack_pop() -> None:
            """ stack_pop """

            nonlocal cur_block

            if not stack:
                fail("poping from empty stack !")
            _ = stack.pop()
            cur_block = stack[-1]

        def stack_push(name: str, child, attributes, must_push: bool, must_update: bool, no_inline: bool = False) -> None:
            """ stack_pop """

            nonlocal cur_block

            new_block = Block(name)
            if child:
                if isinstance(child, str):
                    if no_inline:
                        new_block.childs.append(child)
                    else:
                        inline_stuff(new_block, child)
                else:
                    new_block.childs.append(child)
            if attributes:
                new_block.attributes.update(attributes)

            if cur_block:
                cur_block.childs.append(new_block)

            if must_push:
                stack.append(new_block)

            if must_update:
                cur_block = new_block

        header = True
        within_code = False
        within_description = False
        within_table_header = False
        title = ""
        author = ""
        date_ = ""
        cur_list_level = 0
        cur_chapter_level = 0
        cur_table_level = 0

        # containers
        stack_push('<html>', None, None, True, True)
        stack_push('<body>', None, None, True, True)

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

                    if within_code:
                        stack_push('<br>', None, None, False, False)
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

                    continue

                # comment
                if line.startswith('//'):
                    continue

                line = escape(line)

                # preamble
                if header:
                    if not title:
                        title = line
                        stack_push('<h3>', f"{title}", None, False, False)
                        continue
                    if not author:
                        author = line
                        stack_push('<h4>', f"Auteur : {author}", None, False, False)
                        continue
                    if not date_:
                        date_ = line
                        stack_push('<h4>', f"Date : {date_}", None, False, False)
                        continue

                # special
                if within_code:
                    if line != '</code>':
                        # all is taken as raw
                        cur_block.childs.append(line)
                        stack_push('<br>', None, None, False, False)
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
                    name = f"<h{new_chapter_level + 3}>"
                    stack_push(name, line, None, False, False)
                    continue

                # break line
                if line == '.':
                    stack_push('<br>', None, None, False, False)
                    continue

                # horizontal line
                if line == '_':
                    stack_push('<hr>', None, None, False, False)
                    continue

                # block
                if line.startswith('<'):
                    if line in [f"<{b}>" for b in ('code', 'center', 'blockquote')]:
                        if line == '<code>':
                            within_code = True
                        stack_push(line, None, None, True, True)
                        continue
                    if line in [f"</{b}>" for b in ('code', 'center', 'blockquote')]:
                        if line == '</code>':
                            within_code = False
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
                    if new_list_level > cur_list_level + 1:
                        fail("Issue with (un)ordered list: going too deep too fast")
                    if new_list_level > cur_list_level:
                        # going deeper
                        # create implicit ol
                        name = '<ol>' if start_line.startswith('#') else '<ul>'
                        attributes = {'type': NUMBERING[new_list_level - 1] if name == '<ol>' and new_list_level <= len(NUMBERING) else {}}
                        stack_push(name, None, attributes, True, True)
                        cur_list_level = new_list_level
                        # create li
                        stack_push('<li>', line, None, True, True)
                        continue
                    if new_list_level < cur_list_level:
                        while cur_list_level != new_list_level:
                            # going shallower
                            # go up (quit li)
                            stack_pop()
                            # go up (quit current ul/ol)
                            stack_pop()
                            cur_list_level -= 1
                        # go up (quit upper ul/ol)
                        stack_pop()
                        # create li
                        stack_push('<li>', line, None, True, True)
                        continue
                    # same list continues
                    assert new_list_level == cur_list_level
                    # go up (quit li)
                    stack_pop()
                    # create li
                    stack_push('<li>', line, None, True, True)
                    continue

                # table
                if line.startswith('='):
                    if line == '=':
                        # close table
                        cur_table_level -= 1
                        stack_pop()
                        continue
                    if line.find(' ') == -1:
                        fail("Issue with table: missing space")
                    _, __, line = line.partition(' ')
                    # create table
                    cur_table_level += 1
                    attributes = {'border': '1'}
                    stack_push('<table>', None, attributes, True, True)
                    # create caption
                    if line:
                        attributes = {'style': "caption-side: bottom;"}
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
                    # no continue
                if line.endswith('|'):
                    if not cur_table_level:
                        fail("Line end with | but not in table")
                    # remove it
                    line = line.rstrip('|')
                    # no continue
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
                        # create td/th
                        name = '<th>' if within_table_header else '<td>'
                        stack_push(name, None, None, True, True)
                        # move forward
                        line = line[pipe_pos + len('|'):]
                    # no continue
                if line_orig.endswith('|'):
                    # end td
                    stack_pop()
                    # end tr
                    stack_pop()
                    within_table_header = False
                    # no continue
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
                    attributes = {'style': "font-weight: bold;"}
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
                        # link
                        attributes = {'href': link, 'target': "_blank"}
                        stack_push('<a>', text, attributes, False, False, True)
                    else:
                        # image
                        attributes = {'src': f"{link}", 'alt': f"{text}"}
                        stack_push('<img>', None, attributes, False, False, True)
                    inline_stuff(cur_block, after)
                    continue

                # rest
                inline_stuff(cur_block, line)

        if len(stack) != 2:
            fail("Issue with main: some blocks were never closed")

        if stack[1].name != '<body>':
            fail("Missing <body>")

        if stack[0].name != '<html>':
            fail("Missing <html>")

        self.block = stack[0]
