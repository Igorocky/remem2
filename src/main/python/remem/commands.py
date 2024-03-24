import re
from dataclasses import dataclass
from typing import Callable, Pattern, Tuple
from unittest import TestCase


@dataclass
class Cmd:
    name: str
    name_arr: list[str]
    descr: str
    func: Callable[[str | None], None]


def make_cmd(name: str, func: Callable[[str | None], None], descr: str = "") -> Cmd:
    return Cmd(
        name=name,
        name_arr=[p.strip() for p in re.split(r'\s+', name) if p.strip() != ''],
        descr=descr,
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
            Cmd(name='', name_arr=['make', 'new', 'card', 'translate'], descr='', func=lambda _: None),
            make_cmd_pat('mak n car tr')
        ))
        self.assertTrue(cmd_matches_pat(
            Cmd(name='', name_arr=['make', 'new', 'card', 'translate'], descr='', func=lambda _: None),
            make_cmd_pat('mak car tr')
        ))
        self.assertTrue(cmd_matches_pat(
            Cmd(name='', name_arr=['make', 'new', 'card', 'translate'], descr='', func=lambda _: None),
            make_cmd_pat('mak car ')
        ))


class CollectionOfCommands:
    def __init__(self) -> None:
        self._commands: list[Cmd] = []

    def add_command(self, name: str, func: Callable[[str | None], None], descr: str = "") -> None:
        self._commands.append(make_cmd(name, func, descr))
        self._commands.sort(key=lambda c: c.name)

    def find_commands_by_pattern(self, pat_text: str) -> list[Cmd]:
        pat = make_cmd_pat(pat_text)
        return [cmd for cmd in self._commands if cmd_matches_pat(cmd, pat)]

    def list_commands(self) -> list[Tuple[str, str]]:
        return [(c.name, c.descr) for c in self._commands]
