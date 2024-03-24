from typing import Optional, Tuple

from remem.appsettings import AppSettings
from remem.commands import split_by_space, arr_str_matches_pat, make_cmd_pat


def add_color(color_rgb: Tuple[int, int, int], text: str) -> str:
    return f'\033[38;2;{color_rgb[0]};{color_rgb[1]};{color_rgb[2]}m{text}\033[0m'


def select_single_option(options: list[str]) -> Optional[int]:
    def print_options() -> None:
        print()
        print('0. Cancel')
        for i, o in enumerate(options):
            print(f'{i + 1}. {o}')

    while True:
        print_options()
        try:
            inp = input()
            if len(inp) == 0:
                continue
            if inp[0].isdigit():
                idx = int(inp)
            else:
                pat = make_cmd_pat(inp)
                options_as_arr = [split_by_space(o) for o in options]
                matched_idxs = [i for i,o in enumerate(options_as_arr) if arr_str_matches_pat(o,pat)]
                if len(matched_idxs) != 1:
                    continue
                idx = matched_idxs[0]+1

            if 0 <= idx <= len(options):
                if idx == 0:
                    return None
                else:
                    return idx - 1
        except ValueError:
            pass


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

    def error(self, text: str) -> None:
        print(self.mark_error(text))

    def success(self, text: str) -> None:
        print(self.mark_success(text))

    def prompt(self, text: str) -> None:
        print(self.mark_prompt(text))

    def info(self, text: str) -> None:
        print(self.mark_info(text))
