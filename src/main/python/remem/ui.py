import tkinter as tk
from ctypes import windll
from dataclasses import dataclass, field
from tkinter import ttk, StringVar, messagebox, BooleanVar
from typing import Callable, Tuple

from remem.common import Try
from remem.dtos import CardTranslate, CardFillGaps, Query

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


@dataclass
class Combobox(Widget):
    values: list[str] = field(default_factory=lambda: [])
    width: int = 10
    var: tk.StringVar | None = None


@dataclass
class Entry(Widget):
    width: int = 10
    var: tk.StringVar | None = None


@dataclass
class Text(Widget):
    width: int = 10
    height: int = 5


@dataclass
class Custom(Widget):
    widget: Callable[[tk.Widget], tk.Widget] = lambda parent: ttk.Label(parent, text='')


@dataclass
class Button(Widget):
    text: str = ''
    cmd: Callable[[], None] | None = None


@dataclass
class Checkbutton(Widget):
    text: str = ''
    var: tk.BooleanVar | None = None


def render_grid(parent: tk.Widget, children: list[list[Widget]], child_pad: Tuple[int, int] = (5, 5)) -> tk.Widget:
    frame = ttk.Frame(parent)
    for row, elems in enumerate(children):
        for col, child in enumerate(elems):
            if isinstance(child, Empty):
                widget = ttk.Label(frame, text='')
            elif isinstance(child, Label):
                widget = ttk.Label(frame, text=child.text)
            elif isinstance(child, Combobox):
                widget = ttk.Combobox(frame, values=child.values, width=child.width)  # type: ignore[assignment]
                if child.var is not None:
                    widget.configure(textvariable=child.var)
            elif isinstance(child, Entry):
                widget = ttk.Entry(frame, width=child.width)  # type: ignore[assignment]
                if child.var is not None:
                    widget.configure(textvariable=child.var)
            elif isinstance(child, Text):
                widget = tk.Text(frame, width=child.width, height=child.height)  # type: ignore[assignment]
            elif isinstance(child, Custom):
                widget = child.widget(frame)  # type: ignore[assignment]
            elif isinstance(child, Button):
                widget = ttk.Button(frame, text=child.text)  # type: ignore[assignment]
                if child.cmd is not None:
                    widget.configure(command=child.cmd)  # type: ignore[call-overload]
            elif isinstance(child, Checkbutton):
                widget = ttk.Checkbutton(frame, text=child.text, offvalue=False,
                                         onvalue=True)  # type: ignore[assignment]
                if child.var is not None:
                    widget.configure(variable=child.var)  # type: ignore[call-overload]
            else:
                raise Exception(f'Unexpected type of widget: {child}')
            widget.grid(row=row, column=col)
            if child.sticky is not None:
                widget.grid_configure(sticky=child.sticky)
    for ch in frame.winfo_children():
        ch.grid_configure(padx=child_pad[0], pady=child_pad[1])
    return frame


def render_add_card_view(
        parent: tk.Widget, langs: list[str],
        card_translate: CardTranslate,
        on_card_tr_save: Callable[[CardTranslate], Try[None]],
        card_fill_gaps: CardFillGaps,
        on_card_fill_save: Callable[[CardFillGaps], Try[None]],
) -> tk.Widget:
    nb = ttk.Notebook(parent)
    card_translate_view = render_card_translate(
        parent=nb, langs=langs, card=card_translate, is_edit=False, on_save=on_card_tr_save,
    )
    card_fill_view = render_card_fill(parent=nb, is_edit=False, on_save=on_card_fill_save)
    nb.add(card_translate_view, text='Translate')
    nb.add(card_fill_view, text='Fill in gaps')
    return nb


def render_card_translate(
        parent: tk.Widget, langs: list[str],
        card: CardTranslate,
        is_edit: bool,
        on_save: Callable[[CardTranslate], Try[None]],
) -> tk.Widget:
    lang1_str = StringVar(value=card.lang1_str)
    readonly1 = BooleanVar(value=card.readonly1)
    text1 = StringVar(value=card.text1)
    tran1 = StringVar(value=card.tran1)
    lang2_str = StringVar(value=card.lang2_str)
    readonly2 = BooleanVar(value=card.readonly2)
    text2 = StringVar(value=card.text2)
    tran2 = StringVar(value=card.tran2)

    def do_save() -> None:
        card.lang1_str = lang1_str.get()
        card.readonly1 = readonly1.get()
        card.text1 = text1.get()
        card.tran1 = tran1.get()
        card.lang2_str = lang2_str.get()
        card.readonly2 = readonly2.get()
        card.text2 = text2.get()
        card.tran2 = tran2.get()
        result = on_save(card)
        if result.is_success() and not is_edit:
            text1.set('')
            tran1.set('')
            text2.set('')
            tran2.set('')
        if result.is_failure():
            messagebox.showerror(message=str(result.ex))

    lang_width = max([len(lang) for lang in langs]) + 2
    return render_grid(parent, [
        [
            Label(text='Language', sticky=tk.W),
            Empty(),
            Label(text='Text', sticky=tk.W),
            Label(text='Transcription', sticky=tk.W),
        ],
        [
            Combobox(values=langs, width=lang_width, var=lang1_str),
            Checkbutton(text='read only', var=readonly1),
            Entry(width=50, var=text1),
            Entry(width=20, var=tran1),
        ],
        [
            Combobox(values=langs, width=lang_width, var=lang2_str),
            Checkbutton(text='read only', var=readonly2),
            Entry(width=50, var=text2),
            Entry(width=20, var=tran2),
        ],
        [
            Empty(),
            Empty(),
            Empty(),
            Button(text='Save' if is_edit else 'Add', sticky=tk.E, cmd=do_save)
        ],
    ])


def render_card_fill(
        parent: tk.Widget, is_edit: bool, on_save: Callable[[CardFillGaps], Try[None]]
) -> tk.Widget:
    return render_grid(parent, [
        [Label(text='Text', sticky=tk.NE), Text(width=100, height=10)],
        [Label(text='Notes', sticky=tk.NE), Text(width=100, height=10)],
        [Empty(), Button(text='Save' if is_edit else 'Add', sticky=tk.E)],
    ])


def render_query(
        parent: tk.Widget, query: Query, is_edit: bool, on_save: Callable[[Query], Try[None]]
) -> tk.Widget:
    name = StringVar(value=query.name)
    text: list[tk.Text] = []

    def create_text(holder: list[tk.Text], paren: tk.Widget, width: int, height: int, value: str) -> tk.Widget:
        holder.append(tk.Text(paren, width=width, height=height))
        holder[0].insert('end', value)
        return holder[0]

    def do_save() -> None:
        query.name = name.get()
        query.text = text[0].get(1.0, 'end')
        result = on_save(query)
        if result.is_success() and not is_edit:
            name.set('')
            text[0].delete(1.0, 'end')
        if result.is_failure():
            messagebox.showerror(message=str(result.ex))

    return render_grid(parent, [
        [
            Label(text='Name', sticky=tk.E),
            Entry(width=125, var=name, sticky=tk.W),
        ],
        [
            Label(text='Query text', sticky=tk.E),
            Custom(widget=lambda p: create_text(text, p, width=100, height=10, value=query.text)),
        ],
        [
            Empty(),
            Button(text='Save' if is_edit else 'Add', sticky=tk.E, cmd=do_save)
        ],
    ])
