import re
import sqlite3
from dataclasses import dataclass, field

tmp_dir_path = '../../../../../../../temp'


@dataclass
class IrregVerb:
    tran: str
    text: str
    form: int
    examples: list[str] = field(default_factory=lambda: [])


@dataclass
class Word:
    text: str
    examples: list[str]


def load_irreg_verbs() -> list[IrregVerb]:
    con = sqlite3.connect(f'{tmp_dir_path}/irreg-verbs/remem__2024_04_16__19_02_09.sqlite')
    con.row_factory = sqlite3.Row
    res = []
    for r in con.execute("""
        select ct.text1, ct.text2 
        from CARD c left join main.CARD_TRAN ct on c.id = ct.id
        where c.folder_id = 2
    """):
        tran = r['text1']
        forms = r['text2'].split(' ')
        for i, form in enumerate(forms):
            res.append(IrregVerb(tran=tran, text=form, form=i + 1))
    return res


def load_sentences() -> list[str]:
    sentences = []
    with open(f'{tmp_dir_path}/irreg-verbs/rus.txt', 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.split('\t')
            sentences.append(parts[0])
    return sentences


def sanitize_word(w: str) -> str:
    return w.strip('"\',.!?').lower()


def contains_digits(w: str) -> bool:
    return bool(re.search(r'\d', w))


def load_words() -> dict[str, Word]:
    words = {}
    for s in load_sentences():
        for w in s.split(' '):
            if not contains_digits(w):
                word_str = sanitize_word(w)
                if word_str not in words:
                    words[word_str] = Word(text=word_str, examples=[])
                words[word_str].examples.append(s)
    return words


def main() -> None:
    verbs = load_irreg_verbs()
    print(f'{len(verbs)=}')
    words = load_words()
    print(f'{len(words)=}')
    for i, verb in enumerate(verbs):
        progress = i / len(verbs)
        print(f'{progress=}')
        if verb.text in words:
            verb.examples = words[verb.text].examples
    pct = len([1 for v in verbs if len(v.examples) > 0]) / len(verbs)
    print(f'{pct=}')
    with open(f'{tmp_dir_path}/irreg-verbs/examples.txt', 'w', encoding='utf-8') as file:
        file.writelines([str(v) + '\n' for v in verbs])
    with open(f'{tmp_dir_path}/irreg-verbs/verbs-without-examples.txt', 'w', encoding='utf-8') as file:
        file.writelines([str(v) + '\n' for v in verbs if len(v.examples) == 0])


if __name__ == '__main__':
    main()
