from remem.app_settings import AppSettings
from remem.console import Console
from remem.constants import CardTypes, TaskTypes


class CacheMock:
    def __init__(self) -> None:
        self.lang_si: dict[str, int] = {}
        self.lang_is: dict[int, str] = {}
        for i, s in enumerate(['PL', 'EN']):
            lang_id = i
            lang_name = s
            self.lang_si[lang_name] = lang_id
            self.lang_is[lang_id] = lang_name

        self.card_types_si: dict[str, int] = {}
        self.card_types_is: dict[int, str] = {}
        for i, s in enumerate([CardTypes.translate, CardTypes.fill_gaps]):
            type_id = i
            type_code = s
            self.card_types_si[type_code] = type_id
            self.card_types_is[type_id] = type_code

        self.task_types_si: dict[str, int] = {}
        self.task_types_is: dict[int, str] = {}
        for i, s in enumerate([TaskTypes.translate_12, TaskTypes.translate_21, TaskTypes.fill_gaps]):
            task_type_id = i
            task_type_code = s
            self.task_types_si[task_type_code] = task_type_id
            self.task_types_is[task_type_id] = task_type_code


class ConsoleMock:
    def __init__(self, app_settings: AppSettings) -> None:
        self._c = Console(app_settings)
        self._app_settings = app_settings
        self.text = ''

    def reset(self) -> None:
        self.text = ''

    def mark_error(self, text: str) -> str:
        return self._c.mark_error(text)

    def mark_success(self, text: str) -> str:
        return self._c.mark_success(text)

    def mark_info(self, text: str) -> str:
        return self._c.mark_info(text)

    def mark_hint(self, text: str) -> str:
        return self._c.mark_hint(text)

    def mark_prompt(self, text: str) -> str:
        return self._c.mark_prompt(text)

    def input(self, prompt: str) -> str:
        raise Exception('Not implemented')

    def print(self, text: str = '', end: str = '\n') -> None:
        self.text += text + end

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
        raise Exception('Not implemented')

    def ask_to_press_enter(self) -> None:
        raise Exception('Not implemented')
