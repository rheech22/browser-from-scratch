class Element:
    tag: str
    children: list['Element | Text']
    parent: 'Element | None'
    attributes: dict[str, str]

    def __init__(self, tag: str, attributes: dict[str, str], parent: 'Element | None'):
        self.tag = tag
        self.children = []
        self.parent = parent
        self.attributes = attributes


class Text:
    text: str
    children: list[Element]
    parent: Element

    def __init__(self, text: str, parent: Element):
        self.text = text
        self.children = []
        self.parent = parent


class HTMLParser:
    body: str
    unfinished: list[Element]
    SELF_CLOSING_TAGS: list[str] = [
        'area',
        'base',
        'br',
        'col',
        'embed',
        'hr',
        'img',
        'input',
        'link',
        'meta',
        'param',
        'source',
        'track',
        'wbr',
    ]
    HEAD_TAGS: list[str] = [
        'base',
        'basefont',
        'bgsound',
        'noscript',
        'link',
        'meta',
        'script',
        'style',
        'title',
    ]

    def __init__(self, body: str):
        self.body = body
        self.unfinished = []

    def parse(self):
        text = ''
        in_tag = False
        for c in self.body:
            if c == '<':
                if in_tag:
                    text = ''
                else:
                    in_tag = True
                if text:
                    self.add_text(text)
                    text = ''
            elif c == '>':
                in_tag = False
                self.add_tag(text)
                text = ''
            else:
                text += c
        if not in_tag and text:
            self.add_text(text)
        return self.finish()

    def add_text(self, text: str):
        if text.isspace():
            return
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)

    def add_tag(self, tag: str):
        tag, attributes = self.get_attributes(tag)

        if tag.startswith('!'):
            return

        self.implicit_tags(tag)

        if tag.startswith('/'):
            if len(self.unfinished) > 1:
                node = self.unfinished.pop()
                parent = self.unfinished[-1]
                parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)

    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()

    def get_attributes(self, text: str):
        parts = text.split()
        tag = parts[0].casefold()
        attributes: dict[str, str] = {}
        for attrpair in parts[1:]:
            if '=' in attrpair:
                key, value = attrpair.split('=', 1)
                attributes[key.casefold()] = value
                if len(value) > 2 and value[0] in ['"', "'"]:
                    value = value[1:-1]
            else:
                attributes[attrpair.casefold()] = ''
        return tag, attributes

    def implicit_tags(self, tag: str | None):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != 'html':
                self.add_tag('html')
            elif open_tags == ['html'] and tag not in ['head', 'body', '/html']:
                if tag in self.HEAD_TAGS:
                    self.add_tag('head')
                else:
                    self.add_tag('body')
            elif (
                open_tags == ['html', 'head'] and tag not in ['/head'] + self.HEAD_TAGS
            ):
                self.add_tag('/head')
            else:
                break
