from typing import Optional


def add_color(r: int, g: int, b: int, text: str) -> str:
    return f'\033[38;2;{r};{g};{b}m{text}\033[0m'


def error(text: str) -> str:
    return add_color(255, 0, 0, text)


def success(text: str) -> str:
    return add_color(0, 255, 0, text)


def info(text: str) -> str:
    return add_color(0, 0, 255, text)


def hint(text: str) -> str:
    return add_color(0, 0, 255, text)


def select_single_option(options: list[str]) -> Optional[int]:
    def print_options() -> None:
        print()
        for i, o in enumerate(options):
            print(f'{i + 1}. {o}')
        print(f'{len(options) + 1}. Cancel')

    while True:
        print_options()
        try:
            idx = int(input()) - 1
            if 0 <= idx <= len(options):
                if idx == len(options):
                    return None
                else:
                    return idx
        except ValueError:
            pass
