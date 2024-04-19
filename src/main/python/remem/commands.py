import re
from dataclasses import dataclass
from typing import Callable, Pattern
from unittest import TestCase


@dataclass
class Cmd:
    cat: str
    name: str
    name_arr: list[str]
    descr: str
    func: Callable[[], None]


def split_by_space(s: str) -> list[str]:
    return [p.strip() for p in re.split(r'\s+', s) if p.strip() != '']


def make_cmd(cat: str, name: str, func: Callable[[], None], descr: str = "") -> Cmd:
    return Cmd(
        cat=cat,
        name=name,
        name_arr=split_by_space(name),
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


def arr_str_matches_pat(arr: list[str], pat: CmdPat) -> bool:
    def go(name_idx: int, pat_idx: int) -> bool:
        if pat_idx >= len(pat.parts):
            return True
        elif name_idx >= len(arr):
            return False
        elif pat.parts[pat_idx].pat.match(arr[name_idx]):
            return go(name_idx + 1, pat_idx + 1)
        else:
            return go(name_idx + 1, pat_idx)

    return go(0, 0)




def cmd_matches_pat(cmd: Cmd, pat: CmdPat) -> bool:
    return arr_str_matches_pat(cmd.name_arr, pat)


@dataclass
class CategorizedListOfCommands:
    no_cat: list[Cmd]
    by_cat: dict[str, list[Cmd]]


class CollectionOfCommands:
    def __init__(self) -> None:
        self._commands: list[Cmd] = []

    def add_command(self, cat: str, name: str, func: Callable[[], None], descr: str = "") -> None:
        self._commands.append(make_cmd(cat, name, func, descr))

    def find_commands_by_pattern(self, pat_text: str) -> list[Cmd]:
        pat = make_cmd_pat(pat_text)
        return [cmd for cmd in self._commands if cmd_matches_pat(cmd, pat)]

    def list_commands(self) -> CategorizedListOfCommands:
        by_cat: dict[str, list[Cmd]] = {}
        for c in self._commands:
            if c.cat != '':
                if c.cat not in by_cat:
                    by_cat[c.cat] = []
                by_cat[c.cat].append(c)

        return CategorizedListOfCommands(
            no_cat=[c for c in self._commands if c.cat == ''],
            by_cat=by_cat
        )
