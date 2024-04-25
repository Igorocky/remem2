import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple


@dataclass
class AppSettings:
    database_file: str = 'databases/remem.sqlite'
    database_backup_dir: str | None = None
    buckets: dict[str, str] = field(default_factory=lambda: {
        'short': '2m 5m 15m 30m',
        'long': '1d 7d 30d',
    })
    dictionaries: dict[str, dict[str, str]] = field(default_factory=lambda: {
        'ENG': {
            'Cambridge': 'https://dictionary.cambridge.org/dictionary/english/{word}'
        }
    })
    screen_width: int = 120

    console_colors_info: Tuple[int, int, int] = (30, 144, 255)
    console_colors_success: Tuple[int, int, int] = (26, 138, 59)
    console_colors_hint: Tuple[int, int, int] = (100, 100, 100)
    console_colors_prompt: Tuple[int, int, int] = (0, 0, 255)
    console_colors_error: Tuple[int, int, int] = (255, 0, 0)
    print_stack_traces_for_exceptions: bool = True
    database_schema_script_path: str = 'src/main/resources/schema_v1.sql'


def load_app_settings(path: str) -> AppSettings:
    return AppSettings(**tomllib.loads(Path(path).read_text('utf-8')))
