import re
from dataclasses import dataclass
from typing import Callable, Pattern, Optional
from unittest import TestCase


class Command:
    def get_name(self) -> str:
        return 'this is an abstract method'

    def get_description(self) -> str:
        return 'this is an abstract method'

    def run(self, user_input: str) -> None:
        pass


@dataclass
class Cmd:
    name: str
    name_arr: list[str]
    descr: Optional[str]
    func: Callable[[], None]


def make_cmd(func: Callable[[], None]) -> Cmd:
    return Cmd(
        name=func.__name__,
        name_arr=re.split('_', func.__name__),
        descr=func.__doc__,
        func=func
    )


@dataclass
class CmdSubPat:
    text: str
    pat: Pattern[str]


@dataclass
class CmdPat:
    parts: list[CmdSubPat]


def make_cmd_pat(text: str) -> CmdPat:
    return CmdPat(
        [CmdSubPat(text=s, pat=re.compile(r'.*' + s.replace('-', '.*') + '.*'))
         for s in re.split(r'\s+', text) if s.strip() != '']
    )


def cmd_matches_pat(cmd: Cmd, pat: CmdPat) -> bool:
    def go(name_idx: int, pat_idx: int) -> bool:
        if pat_idx >= len(pat.parts):
            return True
        elif name_idx >= len(cmd.name_arr):
            return False
        elif pat.parts[pat_idx].pat.match(cmd.name_arr[name_idx]):
            return go(name_idx + 1, pat_idx + 1)
        else:
            return go(name_idx + 1, pat_idx)

    return go(0, 0)


class CmdMatchesPatTest(TestCase):
    def test_cmd_matches_pat(self) -> None:
        self.assertTrue(cmd_matches_pat(
            Cmd(name='', name_arr=['make', 'new', 'card', 'translate'], descr='', func=lambda: None),
            make_cmd_pat('mak n car tr')
        ))
        self.assertTrue(cmd_matches_pat(
            Cmd(name='', name_arr=['make', 'new', 'card', 'translate'], descr='', func=lambda: None),
            make_cmd_pat('mak car tr')
        ))
        self.assertTrue(cmd_matches_pat(
            Cmd(name='', name_arr=['make', 'new', 'card', 'translate'], descr='', func=lambda: None),
            make_cmd_pat('mak car ')
        ))


def find_commands_by_pattern(cmds: list[Cmd], pat_text: str) -> list[Cmd]:
    pat = make_cmd_pat(pat_text)
    return [cmd for cmd in cmds if cmd_matches_pat(cmd, pat)]
