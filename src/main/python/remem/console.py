import os
import re
import traceback
from typing import Tuple

from remem.app_settings import AppSettings


def add_color(color_rgb: Tuple[int, int, int], text: str) -> str:
    return f'\033[38;2;{color_rgb[0]};{color_rgb[1]};{color_rgb[2]}m{text}\033[0m'


def parse_idxs(inp: str) -> list[int]:
    if not re.match(r'^[\d\s-]+$', inp):
        return []
    groups = [m.group(1) for m in re.finditer(r'(\S+)', inp)]
    res = []
    for grp in groups:
        if re.match(r'^\d+$', grp):
            res.append(int(grp))
        else:
            start, end = grp.split('-')
            res.extend(range(int(start), int(end) + 1))
    return res


def _select_options(options: list[str], single: bool) -> list[int]:
    filt: list[str] = []

    def option_matches_filter(opt: str, flt: list[str]) -> bool:
        return all([f in opt.lower() for f in flt])

    def print_options(filtered_options: list[Tuple[int, str]]) -> None:
        for i, o in filtered_options:
            print(f'{i}. {o}')
        print('` - Cancel')
        if not single:
            print('`` - Select all')

    while True:
        filtered_options = [(i + 1, o) for i, o in enumerate(options) if option_matches_filter(o, filt)]
        print_options(filtered_options)
        inp = input().strip()
        if inp == '`':
            return []
        if inp == '``' and not single:
            return [i - 1 for i, _ in filtered_options]
        if inp == '':
            if len(filtered_options) == 1:
                return [filtered_options[0][0] - 1]
            else:
                filt = []
            continue
        selected_idxs = parse_idxs(inp)
        if len(selected_idxs) > 0:
            return [i - 1 for i, _ in filtered_options if i in selected_idxs]
        filt = [m.group(1).lower() for m in re.finditer(r'(\S+)', inp)]
        print()


def select_single_option(options: list[str]) -> int | None:
    idxs = _select_options(options, single=True)
    if len(idxs) == 0:
        return None
    return idxs[0]


def select_multiple_options(options: list[str]) -> list[int]:
    return _select_options(options, single=False)


def clear_screen() -> None:
    os.system('cls')


class Console:
    def __init__(self, app_settings: AppSettings) -> None:
        self._app_settings = app_settings

    def mark_error(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_error, text)

    def mark_success(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_success, text)

    def mark_info(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_info, text)

    def mark_hint(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_hint, text)

    def mark_prompt(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_prompt, text)

    def input(self, prompt: str) -> str:
        print(self.mark_prompt(prompt), end='')
        return input()

    def print(self, text: str = '', end: str = '\n') -> None:
        print(text, end=end)

    def error(self, text: str) -> None:
        self.print(self.mark_error(text))

    def success(self, text: str) -> None:
        self.print(self.mark_success(text))

    def prompt(self, text: str) -> None:
        self.print(self.mark_prompt(text))

    def info(self, text: str) -> None:
        self.print(self.mark_info(text))

    def hint(self, text: str) -> None:
        self.print(self.mark_hint(text))

    def print_last_exception_info(self, ex: Exception) -> None:
        self.error(str(ex))
        if self._app_settings.print_stack_traces_for_exceptions:
            self.print(traceback.format_exc())

    def ask_to_press_enter(self) -> None:
        self.input('Press Enter')
