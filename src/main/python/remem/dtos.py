from dataclasses import dataclass


@dataclass
class Language:
    id: int
    ext_id: str
    name: str


@dataclass
class Folder:
    id: int = -1
    parent_id: int | None = -1
    name: str = ''


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
class BaseCard:
    id: int = -1
    ext_id: str = ''
    folder_id: int = -1
    card_type_id: int = -1
    crt_time: int = -1


@dataclass
class CardTranslate:
    base: BaseCard = BaseCard()
    id: int = -1
    lang1_id: int = -1
    read_only1: int = 0
    text1: str = ''
    tran1: str = ''
    lang2_id: int = -1
    read_only2: int = 0
    text2: str = ''
    tran2: str = ''


@dataclass
class CardFillGaps:
    base: BaseCard = BaseCard()
    id: int = -1
    lang_id: int = -1
    text: str = ''
    notes: str = ''


AnyCard = CardTranslate | CardFillGaps
