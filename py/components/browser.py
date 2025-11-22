import tkinter

from tkinter import font as tk_font
from typing import TYPE_CHECKING

from components.layout import HEIGHT, SCROLL_STEP, VSTEP, WIDTH, Layout
from components.url import URL
from components.html_parser import HTMLParser, Element

if TYPE_CHECKING:
    from tkinter import Event


class Browser:
    window: tkinter.Tk
    canvas: tkinter.Canvas
    nodes: Element | None
    display_list: list[tuple[float, float, str, tk_font.Font]]
    scroll: int

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.display_list = []
        self.nodes = None
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
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes).display_list
        self.draw()
