import remem.console as c
from remem.commands import make_cmd, find_commands_by_pattern
from remem.console import select_single_option
import os


def say_hi() -> None:
    print("Hi!")


def say_bye() -> None:
    print("Bye!")


def exit_remem() -> None:
    exit(0)


def clear_screen() -> None:
    os.system('cls')


def show_help() -> None:
    print()
    for c in commands:
        if c.descr:
            print(f'{c.name} - {c.descr}')
        else:
            print(c.name)


commands = [
    make_cmd(say_hi),
    make_cmd(say_bye),
    make_cmd(exit_remem),
    make_cmd(clear_screen),
    make_cmd(show_help),
]

if __name__ == '__main__':
    while True:
        print()
        inp = input(f'{c.prompt(">")} ').strip()
        cmds = find_commands_by_pattern(commands, inp)
        if len(cmds) == 1:
            cmds[0].func()
        elif len(cmds) == 0:
            print('No matches found')
        else:
            print(f'Multiple commands match "{inp}". Please select one:')
            idx = select_single_option([c.name for c in cmds])
            if idx is not None:
                cmds[idx].func()
