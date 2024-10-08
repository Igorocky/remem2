import tkinter as tk
from ctypes import windll
from dataclasses import dataclass, field
from tkinter import ttk, StringVar, messagebox, IntVar
from typing import Callable, Tuple

from remem.cache import Cache
from remem.common import Try
from remem.dtos import CardTranslate, CardFillGaps, Query, AnyCard

windll.shcore.SetProcessDpiAwareness(1)


@dataclass
class Widget:
    sticky: str | None = None
    colspan: int = 1
    rowspan: int = 1


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
    holder: list[tk.Text] = field(default_factory=lambda: [])
    init_value: str = ''
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
    var: tk.IntVar | None = None


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
                widget.insert('end', child.init_value)  # type: ignore[attr-defined]
                child.holder.append(widget)  # type: ignore[arg-type]
            elif isinstance(child, Custom):
                widget = child.widget(frame)  # type: ignore[assignment]
            elif isinstance(child, Button):
                widget = ttk.Button(frame, text=child.text)  # type: ignore[assignment]
                if child.cmd is not None:
                    widget.configure(command=child.cmd)  # type: ignore[call-overload]
            elif isinstance(child, Checkbutton):
                widget = ttk.Checkbutton(frame, text=child.text, offvalue=0, onvalue=1)  # type: ignore[assignment]
                if child.var is not None:
                    widget.configure(variable=child.var)  # type: ignore[call-overload]
            else:
                raise Exception(f'Unexpected type of widget: {child}')
            widget.grid(row=row, column=col, columnspan=child.colspan, rowspan=child.rowspan)
            if child.sticky is not None:
                widget.grid_configure(sticky=child.sticky)
    for ch in frame.winfo_children():
        ch.grid_configure(padx=child_pad[0], pady=child_pad[1])
    return frame


def open_dialog(title: str, render: Callable[[tk.Widget, Callable[[], None]], tk.Widget]) -> None:
    root = tk.Tk()

    def close_dialog() -> None:
        root.destroy()

    root.title(title)
    root_frame = ttk.Frame(root)
    root_frame.grid()
    render(root_frame, close_dialog).grid()
    root.mainloop()


def render_add_card_view(
        cache: Cache,
        parent: tk.Widget,
        on_card_save: Callable[[AnyCard], Try[None]],
) -> tk.Widget:
    nb = ttk.Notebook(parent)
    nb.add(render_card_translate(cache, parent=nb, is_edit=False, on_save=on_card_save), text='Translate')
    nb.add(render_card_fill(cache, parent=nb, is_edit=False, on_save=on_card_save), text='Fill in gaps')
    return nb


def render_card_translate(
        cache: Cache,
        parent: tk.Widget,
        is_edit: bool,
        on_save: Callable[[CardTranslate], Try[None]],
        card: CardTranslate | None = None,
) -> tk.Widget:
    if card is None:
        card = CardTranslate(
            lang1_id=cache.get_card_tran_lang1_id(),
            lang2_id=cache.get_card_tran_lang2_id(),
            read_only1=cache.get_card_tran_read_only1(),
            read_only2=cache.get_card_tran_read_only2(),
        )

    lang1_str = StringVar(value=cache.lang_is[card.lang1_id])
    read_only1 = IntVar(value=card.read_only1)
    text1: list[tk.Text] = []
    lang2_str = StringVar(value=cache.lang_is[card.lang2_id])
    read_only2 = IntVar(value=card.read_only2)
    text2: list[tk.Text] = []
    notes: list[tk.Text] = []

    def do_save() -> None:
        card.lang1_id = cache.lang_si[lang1_str.get()]
        card.read_only1 = read_only1.get()
        card.text1 = text1[0].get(1.0, 'end').strip()
        card.lang2_id = cache.lang_si[lang2_str.get()]
        card.read_only2 = read_only2.get()
        card.text2 = text2[0].get(1.0, 'end').strip()
        card.notes = notes[0].get(1.0, 'end').strip()
        result = on_save(card)
        if result.is_success() and not is_edit:
            text1[0].delete(1.0, 'end')
            text2[0].delete(1.0, 'end')
            notes[0].delete(1.0, 'end')
        if result.is_failure():
            messagebox.showerror(message=str(result.ex))

    langs = list(cache.lang_si)
    lang_width = max([len(lang) for lang in langs]) + 2
    return render_grid(parent, [
        [
            Label(text='Language', sticky=tk.W),
            Empty(),
            Label(text='Text', sticky=tk.W),
        ],
        [
            Combobox(values=langs, width=lang_width, var=lang1_str, sticky=tk.NW),
            Checkbutton(text='read only', var=read_only1, sticky=tk.NW),
            Text(width=100, height=5, init_value=card.text1, holder=text1, sticky=tk.NW),
        ],
        [
            Combobox(values=langs, width=lang_width, var=lang2_str, sticky=tk.NW),
            Checkbutton(text='read only', var=read_only2, sticky=tk.NW),
            Text(width=100, height=5, init_value=card.text2, holder=text2, sticky=tk.NW),
        ],
        [
            Label(text='Notes', sticky=tk.NW),
            Empty(),
            Empty(),
        ],
        [
            Text(width=118, height=5, init_value=card.notes, holder=notes, colspan=3, sticky=tk.NW),
        ],
        [
            Empty(),
            Empty(),
            Button(text='Save' if is_edit else 'Add', sticky=tk.E, cmd=do_save)
        ],
    ])


def render_card_fill(
        cache: Cache,
        parent: tk.Widget,
        is_edit: bool,
        on_save: Callable[[CardFillGaps], Try[None]],
        card: CardFillGaps | None = None,
) -> tk.Widget:
    if card is None:
        card = CardFillGaps(lang_id=cache.get_card_fill_lang_id())
    lang_str = StringVar(value=cache.lang_is[card.lang_id])
    descr: list[tk.Text] = []
    text: list[tk.Text] = []
    notes: list[tk.Text] = []

    def do_save() -> None:
        card.lang_id = cache.lang_si[lang_str.get()]
        card.descr = descr[0].get(1.0, 'end').strip()
        card.text = text[0].get(1.0, 'end').strip()
        card.notes = notes[0].get(1.0, 'end').strip()
        result = on_save(card)
        if result.is_success() and not is_edit:
            descr[0].delete(1.0, 'end')
            text[0].delete(1.0, 'end')
            notes[0].delete(1.0, 'end')
        if result.is_failure():
            messagebox.showerror(message=str(result.ex))

    langs = list(cache.lang_si)
    lang_width = max([len(lang) for lang in langs]) + 2
    return render_grid(parent, [
        [Label(text='Language', sticky=tk.E), Combobox(values=langs, width=lang_width, var=lang_str, sticky=tk.W)],
        [Label(text='Description', sticky=tk.NE), Text(width=100, height=5, init_value=card.descr, holder=descr)],
        [Empty(), Label(text='format: [[word|translation|transcription]] or [[answer|hint|note]]', sticky=tk.NW)],
        [Label(text='Text', sticky=tk.NE), Text(width=100, height=5, init_value=card.text, holder=text)],
        [Label(text='Notes', sticky=tk.NE), Text(width=100, height=5, init_value=card.notes, holder=notes)],
        [Empty(), Button(text='Save' if is_edit else 'Add', sticky=tk.E, cmd=do_save)],
    ])


def render_query(
        parent: tk.Widget,
        is_edit: bool,
        on_save: Callable[[Query], Try[None]],
        query: Query | None = None
) -> tk.Widget:
    query = Query() if query is None else query
    name = StringVar(value=query.name)
    text: list[tk.Text] = []

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
            Text(width=100, height=10, init_value=query.text, holder=text),
        ],
        [
            Empty(),
            Button(text='Save' if is_edit else 'Add', sticky=tk.E, cmd=do_save)
        ],
    ])
