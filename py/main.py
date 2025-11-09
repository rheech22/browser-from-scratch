import socket
import ssl
import tkinter

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Event


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


def lex(body: str):
    text = ''
    in_tag = False
    for c in body:
        if c == '<':
            in_tag = True
        elif c == '>':
            in_tag = False
        elif not in_tag:
            text += c
    return text


HSTEP, VSTEP = 10, 18
WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100


def layout(text: str):
    display_list: list[tuple[int, int, str]] = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


class Browser:
    window: tkinter.Tk
    canvas: tkinter.Canvas
    display_list: list[tuple[int, int, str]]
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
        for x, y, c in self.display_list:
            # the two branches below make the canvas scroll faster,
            # even if it might not look like it.
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            _ = self.canvas.create_text(x, y - self.scroll, text=c)

    def load(self, url: str):
        body = URL(url).request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()


if __name__ == '__main__':
    import sys

    Browser().load(sys.argv[1])
    tkinter.mainloop()
