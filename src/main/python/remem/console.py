from typing import Optional

from remem.appsettings import app_settings


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


def prompt(text: str) -> str:
    color = app_settings.console_colors_prompt
    return add_color(color[0], color[1], color[2], text)


def select_single_option(options: list[str]) -> Optional[int]:
    def print_options() -> None:
        print()
        print('0. Cancel')
        for i, o in enumerate(options):
            print(f'{i + 1}. {o}')

    while True:
        print_options()
        try:
            idx = int(input())
            if 0 <= idx <= len(options):
                if idx == 0:
                    return None
                else:
                    return idx - 1
        except ValueError:
            pass
