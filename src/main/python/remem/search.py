import dataclasses
from dataclasses import dataclass

from remem.app_context import AppCtx
from remem.common import select_folders
from remem.console import Console, clear_screen
from remem.database import Database
from remem.dtos import FolderWithPathDto


@dataclass
class SearchState:
    c: Console
    db: Database
    dir: FolderWithPathDto | None = None
    text: str | None = None


def make_initial_state(c: Console, db: Database) -> SearchState:
    return SearchState(c=c, db=db)


def render_state(c: Console, state: SearchState) -> None:
    c.print('1. Text')
    c.print('None' if state.text is None else state.text)

    c.print()
    c.print('2. Folder')
    c.print('None' if state.dir is None else state.dir.path)

    c.print()


def process_user_input(
        state: SearchState,
        user_input: str
) -> SearchState:
    c = state.c
    if user_input == '1':
        c.print()
        new_text = c.input('Enter text to search for: ').strip().lower()
        return dataclasses.replace(state, text=None if len(new_text) == 0 else new_text)
    elif user_input == '2':
        c.print()
        selected_folders = select_folders(c, state.db.con, 'Folder name: ', single=True)
        if selected_folders is None:
            return state
        else:
            return dataclasses.replace(state, dir=None if len(selected_folders) == 0 else selected_folders[0])
    else:
        return state


def cmd_search_cards(ctx: AppCtx) -> None:
    c, db = ctx.console, ctx.database
    state = make_initial_state(c, db)
    clear_screen()
    render_state(c, state)
    prompt = 'Press Enter to search or select a parameter number to change it: '
    user_input = c.input(prompt).strip()
    while user_input != '':
        state = process_user_input(state, user_input)
        clear_screen()
        render_state(c, state)
        user_input = c.input(prompt).strip()
    clear_screen()
    print(f'Search results for text={state.text} dir={state.dir.path if state.dir is not None else "None"}')
