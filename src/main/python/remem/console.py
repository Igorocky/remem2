import re
import traceback
from typing import Optional, Tuple

from remem.app_settings import AppSettings


def add_color(color_rgb: Tuple[int, int, int], text: str) -> str:
    return f'\033[38;2;{color_rgb[0]};{color_rgb[1]};{color_rgb[2]}m{text}\033[0m'


def select_single_option(options: list[str]) -> Optional[int]:
    filt: list[str] = []

    def option_matches_filter(opt: str, flt: list[str]) -> bool:
        return all([f.lower() in opt.lower() for f in flt])

    def print_options() -> None:
        if len(filt) == 0:
            print('0. Cancel')
        for i, o in enumerate(options):
            if option_matches_filter(o, filt):
                print(f'{i + 1}. {o}')

    while True:
        print_options()
        try:
            inp = input()
            if len(inp) == 0:
                filtered_option_idxs = [i for i, o in enumerate(options) if option_matches_filter(o, filt)]
                if len(filtered_option_idxs) == 1:
                    return filtered_option_idxs[0]
                else:
                    filt = []
            if re.match(r'\d+', inp):
                filt = []
                idx = int(inp)
                if 0 <= idx <= len(options):
                    if idx == 0:
                        return None
                    else:
                        return idx - 1
            else:
                filt = [m.group(1) for m in re.finditer(r'(\S+)', inp)]
            print()
        except ValueError:
            print()
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

    def hint(self, text: str) -> None:
        print(self.mark_hint(text))

    def print_last_exception_info(self, ex: Exception) -> None:
        self.error(str(ex))
        if self._app_settings.print_stack_traces_for_exceptions:
            print(traceback.format_exc())
