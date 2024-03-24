import os
import sys

from remem.appsettings import load_app_settings
from remem.commands import CollectionOfCommands
from remem.console import Console, select_single_option
from remem.database import Database


def say_hi() -> None:
    print("Hi!")


def say_bye() -> None:
    print("Bye!")


def exit_remem() -> None:
    exit(0)


def clear_screen() -> None:
    os.system('cls')


def show_help(cmds: CollectionOfCommands) -> None:
    print()
    for name, descr in cmds.list_commands():
        if descr == '':
            print(name)
        else:
            print(f'{name} - {descr}')


def main() -> None:
    settings_path = 'app-settings.json'
    if len(sys.argv) > 1:
        settings_path = sys.argv[1].strip()
    app_settings = load_app_settings(settings_path)
    c = Console(app_settings=app_settings)
    database = Database(file_path=app_settings.database_file)
    commands = CollectionOfCommands()
    commands.add_command('say hi', say_hi)
    commands.add_command('exit remem', lambda: exit(0))
    commands.add_command('show help', lambda: show_help(commands))

    while True:
        print()
        inp = input(f'{c.prompt(">")} ').strip()
        cmds = commands.find_commands_by_pattern(inp)
        if len(cmds) == 1:
            print()
            cmds[0].func()
        elif len(cmds) == 0:
            print(f'No matches found for "{inp}"')
        else:
            print(f'Multiple commands match "{inp}". Please select one:')
            idx = select_single_option([c.name for c in cmds])
            if idx is not None:
                print()
                cmds[idx].func()


if __name__ == '__main__':
    main()
