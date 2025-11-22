import tkinter

from typing import Literal
from tkinter import font as tk_font

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
