import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


@dataclass
class AppSettings:
    console_colors_info: Tuple[int, int, int] = (0, 0, 255)
    console_colors_success: Tuple[int, int, int] = (0, 255, 0)
    console_colors_hint: Tuple[int, int, int] = (100, 100, 100)
    console_colors_prompt: Tuple[int, int, int] = (26, 138, 59)
    console_colors_error: Tuple[int, int, int] = (255, 0, 0)


app_settings = AppSettings(**json.loads(Path('app-settings.json').read_text('utf-8')))
