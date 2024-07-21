from sqlite3 import Connection
from uuid import uuid4

from remem.cache import Cache
from remem.constants import CardTypes
from remem.dao_base import get_last_id
from remem.dtos import CardTranslate, AnyCard, BaseCard, CardFillGaps


def insert_card(con: Connection, cache: Cache, card: AnyCard) -> int:
    assert con.in_transaction

    card.base.ext_id = str(uuid4())
    if isinstance(card, CardTranslate):
        card.base.card_type_id = cache.card_types_si[CardTypes.translate]
    elif isinstance(card, CardFillGaps):
        card.base.card_type_id = cache.card_types_si[CardTypes.fill_gaps]
    else:
        raise Exception(f'Unexpected type of card: {card}')

    con.execute(
        """insert into CARD(ext_id, folder_id, card_type_id) values (:ext_id, :folder_id, :card_type_id)""",
        card.base.__dict__
    )
    card_id = get_last_id(con)
    card.base.id = card_id
    card.id = card_id
    if isinstance(card, CardTranslate):
        con.execute(
            """ insert into CARD_TRAN(id, lang1_id, read_only1, text1, lang2_id, read_only2, text2, notes)
            values (:id, :lang1_id, :read_only1, :text1, :lang2_id, :read_only2, :text2, :notes) """,
            card.__dict__
        )
    elif isinstance(card, CardFillGaps):
        con.execute(
            """ insert into CARD_FILL(id, lang_id, descr, text, notes)
            values (:id, :lang_id, :descr, :text, :notes) """,
            card.__dict__
        )
    else:
        raise Exception(f'Unexpected type of card {card}')
    return card_id


def select_card(con: Connection, cache: Cache, card_id: int) -> AnyCard | None:
    row = con.execute('select * from CARD where id = ?', [card_id]).fetchone()
    if row is None:
        return None
    base_card = BaseCard(**row)
    card_type_code = cache.card_types_is[base_card.card_type_id]
    match card_type_code:
        case CardTypes.translate:
            row = con.execute(""" select * from CARD_TRAN where id = ? """, [card_id]).fetchone()
            return CardTranslate(base=base_card, **row)
        case CardTypes.fill_gaps:
            row = con.execute(""" select * from CARD_FILL where id = ? """, [card_id]).fetchone()
            return CardFillGaps(base=base_card, **row)
        case _:
            raise Exception(f'Unexpected card type: {card_type_code}')


def insert_translate_card(
        con: Connection, cache: Cache,
        folder_id: int,
        lang1_id: int, read_only1: int, text1: str,
        lang2_id: int, read_only2: int, text2: str,
        notes: str,
) -> int:
    return insert_card(
        con,
        cache,
        CardTranslate(
            base=BaseCard(folder_id=folder_id),
            lang1_id=lang1_id,
            read_only1=read_only1,
            text1=text1,
            lang2_id=lang2_id,
            read_only2=read_only2,
            text2=text2,
            notes=notes
        )
    )


def insert_fill_gaps_card(
        con: Connection, cache: Cache,
        folder_id: int,
        lang_id: int, descr: str, text: str, notes: str
) -> int:
    return insert_card(
        con,
        cache,
        CardFillGaps(
            base=BaseCard(folder_id=folder_id),
            lang_id=lang_id,
            descr=descr,
            text=text,
            notes=notes,
        )
    )
