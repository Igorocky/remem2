import re

from remem.commands import Command
from remem.dao import ListRegisteredDatabases


class Help(Command):
    def __init__(self, all_commands: list[Command]):
        all_commands.append(self)
        self.all_commands = all_commands

    def get_name(self) -> str:
        return 'help'

    def get_description(self) -> str:
        return 'Show help'

    def run(self, user_input: str) -> None:
        for cmd in commands:
            print(f'{cmd.get_name()} - {cmd.get_description()}')


class Exit(Command):
    def get_name(self) -> str:
        return 'exit'

    def get_description(self) -> str:
        return 'Exit from this program'

    def run(self, user_input: str) -> None:
        exit(0)


commands: list[Command] = [
    ListRegisteredDatabases(),
]
help = Help(commands)
commands.append(Exit())

if __name__ == '__main__':
    while True:
        print()
        inp = input().strip()
        cmd = re.split(r'\s', inp)[0].strip()
        for c in commands:
            if cmd == c.get_name():
                c.run(inp)
