import re
import sqlite3
from dataclasses import dataclass, field

from remem.database import dict_factory

tmp_dir_path = '../../../../../../../temp'


@dataclass
class IrregVerb:
    descr: str
    text: str
    notes: str
    form: int
    verb: str
    examples: list[str] = field(default_factory=lambda: [])


@dataclass
class Word:
    text: str
    examples: list[str]


def load_irreg_verbs(db_file: str) -> list[IrregVerb]:
    con = sqlite3.connect(db_file)
    con.row_factory = dict_factory
    res = []
    for r in con.execute("""
        select descr, text, notes 
        from CARD_FILL
        where text == ''
        order by descr, notes
    """):
        notes: str = r['notes']
        parts = notes.split(' ')
        form = int(parts[0])
        verb = parts[form]
        res.append(IrregVerb(descr=r['descr'], text=r['text'], notes=notes, form=form, verb=verb))
    return res


def load_sentences() -> list[str]:
    sentences = set()
    with open(f'{tmp_dir_path}/irreg-verbs/rus.txt', 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.split('\t')
            sentences.add(parts[0])
    return list(sentences)


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


def print_verb(verb: IrregVerb) -> str:
    res = [
        f'd\t{verb.descr}',
        f'n\t\t{verb.notes}',
        f'f\t\t{verb.form}',
        f'v\t\t{verb.verb}',
    ]
    for example in verb.examples:
        res.append(f'e\t\t\t{example}')
    return '\n'.join(res)


def main() -> None:
    verbs = load_irreg_verbs(db_file='')
    print(f'{len(verbs)=}')
    words = load_words()
    print(f'{len(words)=}')
    for i, verb in enumerate(verbs):
        progress = i / len(verbs)
        print(f'{progress=}')
        if verb.verb in words:
            verb.examples = words[verb.verb].examples
    pct = len([1 for v in verbs if len(v.examples) > 0]) / len(verbs)
    print(f'{pct=}')
    with open(f'{tmp_dir_path}/irreg-verbs/verbs-with-examples.txt', 'w', encoding='utf-8') as file:
        file.writelines([print_verb(v) + '\n\n' for v in verbs if len(v.examples) > 0])


if __name__ == '__main__':
    main()
