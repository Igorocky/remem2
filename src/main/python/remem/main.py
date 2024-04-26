import sys

sys.path.append('src/main/python')

from remem.repeat.commands import add_repeat_commands
from remem.app_context import init_app_context
from remem.commands import CollectionOfCommands, Cmd
from remem.console import Console, select_single_option
from remem.data_commands import add_data_commands


def exit_remem() -> None:
    exit(0)


def show_help(all_commands: CollectionOfCommands, c: Console) -> None:
    def print_commands(cmds: list[Cmd], prefix: str) -> None:
        for cmd in cmds:
            if cmd.descr == '':
                print(prefix + cmd.name)
            else:
                print(prefix + f'{cmd.name} - {cmd.descr}')

    c.info("List of available commands:")
    commands_by_cats = all_commands.list_commands()
    print_commands(commands_by_cats.no_cat, prefix='')
    for cat, cmds in commands_by_cats.by_cat.items():
        print(f'[{cat}]')
        print_commands(cmds, prefix='    ')


def main() -> None:
    settings_path = 'app-settings.toml'
    if len(sys.argv) > 1:
        settings_path = sys.argv[1].strip()
    ctx = init_app_context(settings_path)
    c = ctx.console
    commands = CollectionOfCommands()
    commands.add_command('', 'show help', lambda: show_help(commands, c))
    commands.add_command('', 'exit remem', lambda: exit(0))
    add_repeat_commands(ctx, commands)
    add_data_commands(ctx, commands)
    delim = '─' * ctx.settings.screen_width

    while True:
        try:
            print(delim)
            inp = c.input('> ').strip()
            cmds = commands.find_commands_by_pattern(inp)
            if len(cmds) == 0:
                c.error(f'No matches found for "{inp}"')
            else:
                cmds.sort(key=lambda cmd:len(cmd.name_arr))
                print(c.mark_info('Command: ') + cmds[0].name)
                print()
                cmds[0].func()
        except Exception as ex:
            c.print_last_exception_info(ex)


if __name__ == '__main__':
    main()
