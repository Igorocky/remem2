from dataclasses import dataclass

from remem.app_settings import load_app_settings, AppSettings
from remem.cache import Cache
from remem.console import Console
from remem.database import Database


@dataclass
class AppCtx:
    settings: AppSettings
    console: Console
    database: Database
    cache: Cache


def init_app_context(settings_path: str | None = None, app_settings: AppSettings | None = None) -> AppCtx:
    if settings_path is not None:
        app_settings = load_app_settings(settings_path)
    else:
        assert app_settings is not None
    c = Console(app_settings=app_settings)
    database = Database(app_settings=app_settings, c=c)
    cache = Cache(database)
    return AppCtx(settings=app_settings, console=c, database=database, cache=cache)
