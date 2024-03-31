from dataclasses import dataclass


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
    read_only1: bool = False
    text1: str = ''
    tran1: str = ''
    lang2_id: int = -1
    lang2_str: str = ''
    read_only2: bool = False
    text2: str = ''
    tran2: str = ''


@dataclass
class CardFillGaps(Card):
    text: str = ''
    notes: str = ''
