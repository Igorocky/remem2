import tkinter as tk
from ctypes import windll
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable, Tuple

from remem.dtos import CardTranslate

windll.shcore.SetProcessDpiAwareness(1)

# @dataclass
# class Label:
#     text


def render_card_add_view(
        parent: tk.Widget, langs: list[str],
        on_card_tr_save: Callable[[CardTranslate], Tuple[bool,str]],
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
        parent: tk.Widget, langs: list[str], is_edit: bool, on_save: Callable[[CardTranslate], Tuple[bool,str]]
) -> tk.Widget:
    frame = ttk.Frame(parent)
    ttk.Label(frame, text='Language').grid(row=0, column=0, sticky=tk.W)
    ttk.Label(frame, text='Text').grid(row=0, column=1, sticky=tk.W)
    ttk.Label(frame, text='Transcription').grid(row=0, column=2, sticky=tk.W)
    ttk.Combobox(frame, values=langs, width=6).grid(row=1, column=0, sticky=tk.W)
    ttk.Entry(frame, width=50).grid(row=1, column=1, sticky=tk.W)
    ttk.Entry(frame, width=20).grid(row=1, column=2, sticky=tk.W)
    ttk.Combobox(frame, values=langs, width=6).grid(row=2, column=0, sticky=tk.W)
    ttk.Entry(frame, width=50).grid(row=2, column=1, sticky=tk.W)
    ttk.Entry(frame, width=20).grid(row=2, column=2, sticky=tk.W)
    ttk.Button(frame, text='Save' if is_edit else 'Add').grid(row=3, column=2, sticky=tk.E)
    for child in frame.winfo_children():
        child.grid_configure(padx=5, pady=5)
    return frame
