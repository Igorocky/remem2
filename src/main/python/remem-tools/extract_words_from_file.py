import re
from pathlib import Path

from tika import parser  # type: ignore[import-untyped]

tmp_dir = ""
src_file = ""
text_file = f'{tmp_dir}/tmp_text.txt'
dst_file = f'{tmp_dir}/word_counts.txt'


def convert_src_file_to_text(file_in: str, file_out: str) -> None:
    parsed = parser.from_file(file_in, service='text')
    content = parsed["content"]
    with open(file_out, 'w', encoding='utf-8') as fout:
        fout.write(content)


def sanitize_word(w: str) -> str:
    return w.strip('"\',.!?').lower()


def split_text_to_words(text: str) -> dict[str, int]:
    words = [sanitize_word(w) for w in re.split(r'\W+', text)]
    counts = {}
    for w in words:
        if w not in counts:
            counts[w] = 1
        else:
            counts[w] += 1
    return counts


def print_word_counts(counts: dict[str, int], dst_file: str) -> None:
    grp_by_count: dict[int, list[str]] = {}
    for w, c in counts.items():
        if c not in grp_by_count:
            grp_by_count[c] = []
        grp_by_count[c].append(w)
    for c in grp_by_count:
        grp_by_count[c].sort()
    sorted_counts = sorted(grp_by_count.keys())
    sorted_counts.reverse()
    with open(dst_file, 'w', encoding='utf-8') as file:
        for c in sorted_counts:
            for w in grp_by_count[c]:
                file.write(f'{c} {w}\n')


def main() -> None:
    # convert_src_file_to_text(src_file, text_file)
    print_word_counts(
        split_text_to_words(Path(text_file).read_text('utf-8')),
        dst_file
    )


if __name__ == '__main__':
    main()
