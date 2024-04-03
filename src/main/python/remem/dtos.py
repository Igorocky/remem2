from dataclasses import dataclass


@dataclass
class Folder:
    id: int
    parent_id: int | None
    name: str


@dataclass
class Query:
    id: int = -1
    name: str = ''
    text: str = ''


@dataclass
class Task:
    id: int = -1
    card_id: int = -1
    task_type_id: int = -1
    task_type_code: str = ''


@dataclass
class Card:
    id: int = -1
    ext_id: str = ''
    folder_id: int = -1
    card_type_id: int = -1
    crt_time: int = -1


@dataclass
class CardTranslate(Card):
    lang1_id: int = -1
    lang1_str: str = ''
    readonly1: bool = False
    text1: str = ''
    tran1: str = ''
    lang2_id: int = -1
    lang2_str: str = ''
    readonly2: bool = False
    text2: str = ''
    tran2: str = ''


@dataclass
class CardFillGaps(Card):
    lang_id: int = -1
    lang_str: str = ''
    text: str = ''
    notes: str = ''
