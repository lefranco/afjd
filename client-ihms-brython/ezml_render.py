""" ezml_render """

# pylint: disable=pointless-statement, expression-not-assigned


import ezml


class MyEzml(ezml.Ezml):
    """ MyEzml """

    def render(self, panel):
        """ render """

        def render_block(block) -> None:

            # HTML
            name = block.name.rstrip('>').lstrip('<')

            if name == 'h2':
                item = html.H2()
            else:
                assert False, f"Unhandled HTML item : {name}"


            if block.attributes:
                name += ' ' + ' '.join([f"{k}={v}" for k, v in block.attributes.items()])
            if block.childs:
                text = f"<{name}>"
                childs_str = ''.join([c if isinstance(c, str) else render_block(c) for c in block.childs])
                text += childs_str
                terminator_str = ezml.Block.terminator(block.name)
                text += terminator_str
            else:
                text = f"<{name} />"
            return text

        # return render_block(self.block)

