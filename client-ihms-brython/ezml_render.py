""" ezml_render """

# pylint: disable=pointless-statement, expression-not-assigned


import browser  # pylint: disable=import-error

import ezml


class MyEzml(ezml.Ezml):
    """ MyEzml """

    def render(self, panel):
        """ render """

        def render_block(panel, block) -> None:
            """ render_block """

            for child in block.childs:

                # strs are just inserted
                if isinstance(child, str):
                    panel <= child
                    continue

                # now we have a block
                name = child.name.rstrip('>').lstrip('<')

                try:
                    # 'h2' --> browser.html.H2()
                    sub_panel = getattr(browser.html, name.upper())()
                except:  # noqa: E722 pylint: disable=bare-except
                    print("ERROR : html  for element name {name}")

                # attributes
                for key, value in child.attributes.items():
                    sub_panel.attrs[key] = value

                render_block(sub_panel, child)
                panel <= sub_panel

        # skip html
        cur_block = self.block
        assert cur_block.name == '<html>'

        # skip body
        cur_block = self.block.childs[0]
        assert cur_block.name == '<body>'

        render_block(panel, cur_block)
