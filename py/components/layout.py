from typing import Literal
from tkinter import font as tk_font

from components.html_parser import Element, Text
from utils.fonts import get_font

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

    def __init__(self, nodes: Element):
        self.line = []
        self.display_list = []
        self.weight, self.style = 'normal', 'roman'
        self.recurse(nodes)
        self.flush()

    def open_tag(self, tag: str):
        if tag == 'i':
            self.style = 'italic'
        elif tag == 'b':
            self.weight = 'bold'
        elif tag == 'small':
            self.size -= 2
        elif tag == 'big':
            self.size += 4
        elif tag == 'br':
            self.flush()
        elif tag == 'p':
            self.flush()

    def close_tag(self, tag: str):
        if tag == 'i':
            self.style = 'roman'
        elif tag == 'b':
            self.weight = 'normal'
        elif tag == 'small':
            self.size += 2
        elif tag == 'big':
            self.size -= 4
        elif tag == 'br':
            self.flush()
        elif tag == 'p':
            self.flush()
            # if you want to add a paragraph gap, uncomment the following line
            self.cursor_y += VSTEP

    def recurse(self, tree: Element | Text):
        if isinstance(tree, Text):
            for word in tree.text.split():
                self.word(word)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

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
