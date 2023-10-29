""" ezml_render """

# pylint: disable=pointless-statement, expression-not-assigned

from browser import html  # pylint: disable=import-error

import ezml


class MyEzml(ezml.Ezml):
    """ MyEzml """

    def render(self, panel):
        """ render """

        def render_block(panel, block) -> None:

            def make_panel(name):
                if name == 'h2':
                    return html.H2()
                assert False, f"name ??? {name}"
                return None

            for child in block.childs:

                # strs are just inserted
                if isinstance(child, str):
                    panel <= child
                    continue

                # now we have a block
                name = child.name.rstrip('>').lstrip('<')
                print(f"{name=}")

                sub_panel = make_panel(name)
                # TODO : attributes
                render_block(sub_panel, child)
                panel <= sub_panel

        cur_block = self.block
        assert cur_block.name == '<html>'

        cur_block = self.block.childs[0]
        assert cur_block.name == '<body>'

        render_block(panel, cur_block)
