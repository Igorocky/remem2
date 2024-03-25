from dataclasses import dataclass


@dataclass
class CardTranslate:
    lang1:str
    text1:str
    tran1:str
    lang2:str
    text2:str
    tran2:str