import tkinter as tk
from ctypes import windll
from dataclasses import dataclass, field
from tkinter import ttk
from typing import Callable, Tuple

from remem.dtos import CardTranslate

windll.shcore.SetProcessDpiAwareness(1)


@dataclass
class Widget:
    sticky: str | None = None


@dataclass
class Empty(Widget):
    pass


@dataclass
class Label(Widget):
    text: str = ''
    sticky = None


@dataclass
class Combobox(Widget):
    values: list[str] = field(default_factory=lambda: [])
    sticky = None
    width: int = 10


@dataclass
class Entry(Widget):
    sticky = None
    width: int = 10


@dataclass
class Button(Widget):
    text: str = ''


def render_grid(parent: tk.Widget, children: list[list[Widget]], child_pad: Tuple[int, int] = (5, 5)) -> tk.Widget:
    frame = ttk.Frame(parent)
    for row, elems in enumerate(children):
        for col, child in enumerate(elems):
            if isinstance(child, Label):
                widget = ttk.Label(frame, text=child.text)
            elif isinstance(child, Combobox):
                widget = ttk.Combobox(frame, values=child.values, width=child.width)  # type: ignore[assignment]
            elif isinstance(child, Entry):
                widget = ttk.Entry(frame, width=child.width)  # type: ignore[assignment]
            elif isinstance(child, Button):
                widget = ttk.Button(frame, text=child.text)  # type: ignore[assignment]
            elif isinstance(child, Empty):
                widget = ttk.Label(frame, text='')
            else:
                raise Exception(f'Unexpected type of widget: {child}')
            widget.grid(row=row, column=col)
            if child.sticky is not None:
                widget.grid_configure(sticky=child.sticky)
    for ch in frame.winfo_children():
        ch.grid_configure(padx=child_pad[0], pady=child_pad[1])
    return frame


def render_card_add_view(
        parent: tk.Widget, langs: list[str],
        on_card_tr_save: Callable[[CardTranslate], Tuple[bool, str]],
) -> tk.Widget:
    frame = ttk.Frame(parent)
    nb = ttk.Notebook(frame)
    nb.grid(row=0, column=0)
    card_translate_view = render_card_translate_edit_view(nb, langs, False, on_card_tr_save)
    nb.add(card_translate_view, text='Translate')
    for child in nb.winfo_children():
        child.grid(row=0, column=0)
    return frame


def render_card_translate_edit_view(
        parent: tk.Widget, langs: list[str], is_edit: bool, on_save: Callable[[CardTranslate], Tuple[bool, str]]
) -> tk.Widget:
    return render_grid(parent, [
        [Label(text='Language', sticky=tk.W), Label(text='Text', sticky=tk.W),
         Label(text='Transcription', sticky=tk.W)],
        [Combobox(values=langs, width=6), Entry(width=50), Entry(width=20)],
        [Combobox(values=langs, width=6), Entry(width=50), Entry(width=20)],
        [Empty(), Empty(), Button(text='Save' if is_edit else 'Add', sticky=tk.E)],
    ])
