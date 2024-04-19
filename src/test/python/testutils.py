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
