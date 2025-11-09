import socket
import ssl
import tkinter

from tkinter import font as tk_font
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from tkinter import Event


# url
class URL:
    scheme: str
    host: str
    path: str
    port: int

    def __init__(self, url: str):
        self.scheme, url = url.split('://', 1)
        assert self.scheme in ['http', 'https']
        if '/' not in url:
            url += '/'
        self.host, url = url.split('/', 1)
        self.path = '/' + url
        if self.scheme == 'http':
            self.port = 80
        elif self.scheme == 'https':
            self.port = 443
        if ':' in self.host:
            self.host, port = self.host.split(':')
            self.port = int(port)

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        s.connect((self.host, self.port))
        if self.scheme == 'https':
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        request = 'GET {} HTTP/1.0\r\n'.format(self.path)
        request += 'Host: {}\r\n'.format(self.host)
        request += '\r\n'

        _ = s.send(request.encode('utf-8'))

        response = s.makefile('r', encoding='utf-8', newline='\r\n')
        statusline = response.readline()
        _version, _status, _explanation = statusline.split(' ', 2)
        response_headers = {}

        while True:
            line = response.readline()
            if line == '\r\n':
                break
            header, value = line.split(': ', 1)
            response_headers[header.casefold()] = value.strip()

        assert 'transfer-encoding' not in response_headers
        assert 'content-encoding' not in response_headers

        body = response.read()
        s.close()
        return body


# text
class Text:
    text: str

    def __init__(self, text: str):
        self.text = text


# tag
class Tag:
    tag: str

    def __init__(self, tag: str):
        self.tag = tag


# helpers
def lex(body: str):
    out: list[Text | Tag] = []
    buffer = ''
    in_tag = False
    for c in body:
        if c == '<':
            if in_tag:
                buffer = ''
            else:
                in_tag = True

            if buffer:
                out.append(Text(buffer))
                buffer = ''
        elif c == '>':
            in_tag = False
            out.append(Tag(buffer))
            buffer = ''
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out


FONT: dict[
    tuple[
        int,
        Literal['normal', 'bold'],
        Literal['roman', 'italic'],
    ],
    tuple[
        tk_font.Font,
        tkinter.Label,
    ],
] = {}


def get_font(
    size: int,
    weight: Literal['normal', 'bold'],
    style: Literal['roman', 'italic'],
):
    key = (size, weight, style)

    if key not in FONT:
        font = tk_font.Font(
            size=size,
            weight=weight,
            slant=style,
        )
        label = tkinter.Label(font=font)
        FONT[key] = (font, label)
    return FONT[key][0]


# layout
HSTEP, VSTEP = 13, 18
WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100


class Layout:
    # layout state
    line: list[tuple[float, str, tk_font.Font]]
    display_list: list[tuple[float, float, str, tk_font.Font]]
    cursor_x: float = HSTEP
    cursor_y: float = VSTEP
    # font state
    size: int = 12
    weight: Literal['normal', 'bold']
    style: Literal['roman', 'italic']

    def __init__(self, tokens: list[Text | Tag]):
        self.line = []
        self.display_list = []
        self.weight, self.style = 'normal', 'roman'
        for token in tokens:
            self.token(token)
        self.flush()

    def token(self, token: Text | Tag):
        if isinstance(token, Text):
            for word in token.text.split():
                self.word(word)
        elif token.tag == 'i':
            self.style = 'italic'
        elif token.tag == '/i':
            self.style = 'roman'
        elif token.tag == 'b':
            self.weight = 'bold'
        elif token.tag == '/b':
            self.weight = 'normal'
        elif token.tag == 'small':
            self.size -= 2
        elif token.tag == '/small':
            self.size += 2
        elif token.tag == 'big':
            self.size += 4
        elif token.tag == '/big':
            self.size -= 4
        elif token.tag == 'br':
            self.flush()
        elif token.tag == 'p':
            self.flush()
        elif token.tag == '/p':
            self.flush()
            # if you want to add a paragraph gap, uncomment the following line
            # self.cursor_y += VSTEP

    def flush(self):
        if not self.line:
            return
        metrics = [font.metrics() for _x, _word, font in self.line]
        max_ascent = max([metric['ascent'] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics('ascent')
            self.display_list.append((x, y, word, font))
        max_descent = max([metric['descent'] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []

    def word(self, word: str):
        font = get_font(self.size, self.weight, self.style)

        w = font.measure(word)

        if self.cursor_x + w >= WIDTH - HSTEP:
            self.flush()

        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(' ')


# browser
class Browser:
    window: tkinter.Tk
    canvas: tkinter.Canvas
    display_list: list[tuple[float, float, str, tk_font.Font]]
    scroll: int

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.display_list = []
        self.scroll = 0
        _ = self.window.bind('<Down>', self.scroll_down)
        _ = self.window.bind('<Up>', self.scroll_up)

    def scroll_down(self, _: 'Event'):
        self.scroll += SCROLL_STEP
        self.draw()

    def scroll_up(self, _: 'Event'):
        self.scroll -= SCROLL_STEP
        self.draw()

    def draw(self):
        self.canvas.delete('all')
        for x, y, c, font in self.display_list:
            # the two branches below make the canvas scroll faster,
            # even if it might not look like it.
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            _ = self.canvas.create_text(
                x, y - self.scroll, text=c, font=font, anchor='nw'
            )

    def load(self, url: str):
        body = URL(url).request()
        tokens = lex(body)
        self.display_list = Layout(tokens).display_list
        self.draw()


# main
if __name__ == '__main__':
    import sys

    Browser().load(sys.argv[1])
    tkinter.mainloop()
