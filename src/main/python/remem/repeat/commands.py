import dataclasses
import webbrowser
from dataclasses import dataclass
from typing import Callable, Tuple

import remem.repeat.repeat_fill_gaps_card as repeat_fill_gaps_card
import remem.repeat.repeat_translate_card as repeat_translate_card
from remem.app_context import AppCtx
from remem.commands import CollectionOfCommands
from remem.common import first_defined, select_folders
from remem.console import select_multiple_options, select_single_option, clear_screen
from remem.constants import TaskTypes
from remem.dao import insert_task_hist, select_card
from remem.data_commands import edit_card_by_id
from remem.dtos import Task, TaskHistRec
from remem.repeat import TaskContinuation
from remem.repeat.strategy.buckets import repeat_tasks_with_buckets


@dataclass
class TaskTypeForSelectDto:
    task_type_id: int
    lang1_id: int
    lang2_id: int | None
    descr: str = ''


def create_task_type_description(ctx: AppCtx, task_type: TaskTypeForSelectDto) -> str:
    ca = ctx.cache
    if task_type.task_type_id == ca.task_types_si[TaskTypes.translate_12]:
        lang1_id = task_type.lang1_id
        lang2_id = first_defined(task_type.lang2_id, list(ca.lang_is)[0])
        return f'{ca.lang_is[lang1_id]} -> {ca.lang_is[lang2_id]}'
    if task_type.task_type_id == ca.task_types_si[TaskTypes.translate_21]:
        lang1_id = task_type.lang1_id
        lang2_id = first_defined(task_type.lang2_id, list(ca.lang_is)[0])
        return f'{ca.lang_is[lang2_id]} -> {ca.lang_is[lang1_id]}'
    if task_type.task_type_id == ca.task_types_si[TaskTypes.fill_gaps]:
        lang1_id = task_type.lang1_id
        return f'Fill gaps {ca.lang_is[lang1_id]}'
    raise Exception(f'Unexpected task type: {task_type}')


def select_available_task_types(ctx: AppCtx, folder_ids: list[int]) -> list[TaskTypeForSelectDto]:
    available_task_types = [TaskTypeForSelectDto(**r) for r in ctx.database.con.execute(
        f"""
            with recursive folders(id) as (
                select id from FOLDER where {' or '.join(['id = ?'] * len(folder_ids))}
                union all
                select ch.id
                from folders pr inner join FOLDER ch on pr.id = ch.parent_id
            )
            select distinct
                t.task_type_id task_type_id,
                case
                    when t.task_type_id in (1,2) /*lang1->lang2 or lang2->lang1*/ then ct.lang1_id
                    when t.task_type_id = 3 /*fill_gaps*/ then CF.lang_id
                end lang1_id,
                case
                    when t.task_type_id in (1,2) /*lang1->lang2 or lang2->lang1*/ then ct.lang2_id
                end lang2_id
            from folders f
                inner join CARD c on f.id = c.folder_id
                inner join TASK t on c.id = t.card_id
                left join CARD_TRAN CT on c.id = CT.id
                left join CARD_FILL CF on c.id = CF.id
        """,
        folder_ids
    )]
    return [dataclasses.replace(t, descr=create_task_type_description(ctx, t)) for t in available_task_types]


def select_task_ids(ctx: AppCtx, folder_ids: list[int], task_types: list[TaskTypeForSelectDto]) -> list[int]:
    ca = ctx.cache

    def create_folder_ids_condition() -> Tuple[str, dict[str, int]]:
        return (
            ' or '.join([f'id = :folder_id{i}' for i, id in enumerate(folder_ids)]),
            {f'folder_id{i}': id for i, id in enumerate(folder_ids)}
        )

    def create_task_types_condition() -> Tuple[str, dict[str, int]]:
        params = {}
        conditions = []
        for i, t in enumerate(task_types):
            if (t.task_type_id == ca.task_types_si[TaskTypes.translate_12]
                    or t.task_type_id == ca.task_types_si[TaskTypes.translate_21]):
                conditions.append(f"""
                    t.task_type_id = :task_type_id{i} and ct.lang1_id = :lang1_id{i} and ct.lang2_id = :lang2_id{i}
                """)
                params[f'task_type_id{i}'] = t.task_type_id
                params[f'lang1_id{i}'] = t.lang1_id
                params[f'lang2_id{i}'] = first_defined(t.lang2_id, list(ctx.cache.lang_is)[0])
            elif t.task_type_id == ca.task_types_si[TaskTypes.fill_gaps]:
                conditions.append(f"""
                    t.task_type_id = :task_type_id{i} and cf.lang_id = :lang_id{i}
                """)
                params[f'task_type_id{i}'] = t.task_type_id
                params[f'lang_id{i}'] = t.lang1_id
            else:
                raise Exception(f'Unexpected type of task: {t}')

        return (
            ' or '.join(conditions),
            params
        )

    folder_ids_condition, folder_ids_params = create_folder_ids_condition()
    task_types_condition, task_types_params = create_task_types_condition()
    return [r['id'] for r in ctx.database.con.execute(
        f"""
            with recursive folders(id) as (
                select id from FOLDER where {folder_ids_condition}
                union all
                select ch.id
                from folders pr inner join FOLDER ch on pr.id = ch.parent_id
            )
            select t.id
            from folders f
                inner join CARD c on f.id = c.folder_id
                inner join TASK t on c.id = t.card_id
                left join CARD_TRAN CT on c.id = CT.id
                left join CARD_FILL CF on c.id = CF.id
            where {task_types_condition}
        """,
        {**folder_ids_params, **task_types_params}
    )]


def find_in_dictionary(ctx: AppCtx, lang_str: str, dict_idx: int, words: list[str]) -> None:
    c = ctx.console
    dictionaries = ctx.settings.dictionaries
    if lang_str not in dictionaries:
        c.error(f'No dictionary is set for "{lang_str}" language.')
        print()
        c.input('press Enter')
    else:
        dicts_for_lang = dictionaries[lang_str]
        if len(dicts_for_lang) < dict_idx + 1:
            c.error(f'Only {len(dicts_for_lang)} dictionaries are available for "{lang_str}" language, '
                    f'but the #{dict_idx + 1} was requested.')
            print()
            c.input('press Enter')
        else:
            dict_url = dicts_for_lang[dict_idx]
            for word in words:
                webbrowser.open_new_tab(dict_url.replace('{word}', word))


def repeat_task(ctx: AppCtx, task: Task, print_stats: Callable[[], bool]) -> TaskContinuation:
    cache = ctx.cache
    match cache.task_types_is[task.task_type_id]:
        case TaskTypes.translate_12 | TaskTypes.translate_21:
            make_initial_state = repeat_translate_card.make_initial_state
            render_state = repeat_translate_card.render_state
            process_user_input = repeat_translate_card.process_user_input
        case TaskTypes.fill_gaps:
            make_initial_state = repeat_fill_gaps_card.make_initial_state  # type: ignore[assignment]
            render_state = repeat_fill_gaps_card.render_state  # type: ignore[assignment]
            process_user_input = repeat_fill_gaps_card.process_user_input  # type: ignore[assignment]
        case _:
            raise Exception(f'Unexpected type of task: {task}')
    con = ctx.database.con
    card = select_card(con, cache, task.card_id)
    if card is None:
        raise Exception(f'Cannot find a card by id {task.card_id}')
    state = make_initial_state(cache, card, task)
    hist_rec: TaskHistRec | None = None
    while True:
        clear_screen()
        render_state(ctx.console, state)
        state = process_user_input(state, input().strip())
        if state.hist_rec is not None:
            if hist_rec is not None:
                raise Exception('Internal error: hist_rec is not None')
            hist_rec = state.hist_rec
            insert_task_hist(con, hist_rec)
            state.hist_rec = None
        if state.edit_card:
            state.edit_card = False
            edit_card_by_id(ctx, state.task.card_id)
        if state.print_stats:
            state.print_stats = False
            clear_screen()
            if not print_stats():
                return TaskContinuation.EXIT
        if state.find_in_dictionary is not None:
            find_in_dictionary(ctx, *state.find_in_dictionary)
            state.find_in_dictionary = None
        match state.task_continuation:
            case TaskContinuation.CONTINUE_TASK:
                continue
            case act:
                return act


def cmd_repeat_tasks(ctx: AppCtx) -> None:
    c = ctx.console

    selected_folders = select_folders(ctx.database.con, c.mark_prompt('Folder name: '))
    if selected_folders is None:
        c.error('No folders found')
        return
    if len(selected_folders) == 0:
        return
    c.info('\nSelected folders:')
    for f in selected_folders:
        print(f.path)
    print()
    folder_ids = [f.id for f in selected_folders]

    available_task_types = select_available_task_types(ctx, folder_ids)
    if len(available_task_types) == 0:
        c.error('No tasks found in the specified folders')
        return
    available_task_types.sort(key=lambda t: t.descr)
    c.prompt('Select task types:')
    task_type_idxs = select_multiple_options([t.descr for t in available_task_types])
    if len(task_type_idxs) == 0:
        return
    selected_task_types = [available_task_types[i] for i in task_type_idxs]
    c.info('\nSelected task types:')
    for t in selected_task_types:
        print(t.descr)
    print()
    folder_ids = [f.id for f in selected_folders]

    task_ids = select_task_ids(ctx, folder_ids, selected_task_types)
    print(f'{c.mark_info("Number of loaded tasks: ")}{len(task_ids)}\n')

    available_strategies = ['circle', *[f'buckets: {name} {value}' for name, value in ctx.settings.buckets.items()]]
    c.prompt('Select strategy:')
    strategy_idx = select_single_option(available_strategies)
    if strategy_idx is None:
        return
    if strategy_idx == 0:
        raise Exception('The Circle strategy is not implemented yet')
    else:
        repeat_tasks_with_buckets(ctx, task_ids, list(ctx.settings.buckets.values())[strategy_idx - 1], repeat_task)


def add_repeat_commands(ctx: AppCtx, commands: CollectionOfCommands) -> None:
    def add_command(cat: str, name: str, cmd: Callable[[AppCtx], None]) -> None:
        commands.add_command(cat, name, lambda: cmd(ctx))

    add_command('Repeat', 'repeat tasks', cmd_repeat_tasks)
