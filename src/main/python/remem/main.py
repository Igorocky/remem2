import sys

sys.path.append('src/main/python')

from remem.app_context import AppCtx
from remem.cache import Cache
from remem.app_settings import load_app_settings
from remem.commands import CollectionOfCommands
from remem.console import Console, select_single_option
from remem.data_commands import add_data_commands
from remem.database import Database


def exit_remem() -> None:
    exit(0)


def show_help(cmds: CollectionOfCommands, c: Console) -> None:
    c.info("List of available commands:")
    for name, descr in cmds.list_commands():
        if descr == '':
            print(name)
        else:
            print(f'{name} - {descr}')


def main() -> None:
    settings_path = 'app-settings.toml'
    if len(sys.argv) > 1:
        settings_path = sys.argv[1].strip()
    app_settings = load_app_settings(settings_path)
    c = Console(app_settings=app_settings)
    database = Database(app_settings=app_settings, c=c)
    cache = Cache(database)
    ctx = AppCtx(c, database, cache)
    commands = CollectionOfCommands()
    commands.add_command('exit remem', lambda: exit(0))
    commands.add_command('show help', lambda: show_help(commands, c))
    add_data_commands(ctx, commands)

    while True:
        try:
            print()
            inp = c.input('> ').strip()
            cmds = commands.find_commands_by_pattern(inp)
            if len(cmds) == 1:
                print()
                cmds[0].func()
            elif len(cmds) == 0:
                c.error(f'No matches found for "{inp}"')
            else:
                c.prompt(f'Multiple commands match "{inp}". Please select one:')
                idx = select_single_option([c.name for c in cmds])
                if idx is not None:
                    print()
                    cmds[idx].func()
        except Exception as ex:
            c.print_last_exception_info(ex)


if __name__ == '__main__':
    main()
