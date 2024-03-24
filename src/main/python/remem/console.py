from typing import Optional, Tuple

from remem.appsettings import AppSettings


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
            idx = int(input())
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

    def error(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_error, text)

    def success(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_success, text)

    def info(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_info, text)

    def hint(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_hint, text)

    def prompt(self, text: str) -> str:
        return add_color(self._app_settings.console_colors_prompt, text)
