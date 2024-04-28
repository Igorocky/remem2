import random
import re
import time
from typing import Callable, Any

from remem.app_context import AppCtx
from remem.common import duration_str_to_seconds, seconds_to_duration_str, print_table_from_dicts
from remem.console import clear_screen
from remem.dao import select_task_hist, select_tasks_with_base_cards_by_ids
from remem.dtos import Task, TaskHistRec
from remem.repeat import TaskContinuation, TaskWithHist, select_random_tasks_from_beginning


def get_bucket_number(hist: list[TaskHistRec], max_num: int) -> int:
    res = 0
    for i, r in enumerate(hist):
        if res >= max_num:
            break
        if r.mark >= 1.0:
            res = res + 1
        else:
            break
    return res


def load_buckets(ctx: AppCtx, task_ids: list[int], num_of_buckets: int) -> list[list[TaskWithHist]]:
    def none_to_zero(i: int | None) -> int:
        return 0 if i is None else i

    db = ctx.database
    hist = select_task_hist(db.con, task_ids, max_num_of_records_per_task=num_of_buckets)
    tasks = [TaskWithHist(
        task=t,
        hist=hist[t.id] if t.id in hist else [],
        last_repeated=none_to_zero(hist[t.id][0].time) if t.id in hist else 0
    ) for t in select_tasks_with_base_cards_by_ids(db.con, task_ids)]
    buckets: list[list[TaskWithHist]] = [[] for _ in range(num_of_buckets)]
    max_bucket_num = num_of_buckets - 1
    for t in tasks:
        buckets[get_bucket_number(t.hist, max_num=max_bucket_num)].append(t)
    return buckets


def select_tasks_to_repeat_from_buckets(buckets: list[list[TaskWithHist]], bucket_delays: list[int]) -> (
        list)[TaskWithHist]:
    all_tasks = [t for b in buckets for t in b]
    folder_last_access = [(t.task.card.folder_id, t.last_repeated) for t in all_tasks]
    random.shuffle(folder_last_access)
    folder_last_access.sort(key=lambda f: f[1])
    preferred_folders = [f[0] for f in folder_last_access]
    curr_time_sec = int(time.time())
    num_of_buckets = len(buckets)
    res: list[TaskWithHist] = []
    for bucket_idx, bucket in enumerate(buckets):
        min_delay_sec = bucket_delays[bucket_idx]
        bucket = [t for t in bucket if curr_time_sec - t.last_repeated >= min_delay_sec]
        if len(bucket) > 0:
            random.shuffle(bucket)
            bucket.sort(key=lambda t: t.last_repeated)
            if bucket_idx == 0:
                bucket.reverse()
            res = res + select_random_tasks_from_beginning(
                sorted_tasks=bucket,
                max_num_of_tasks=num_of_buckets - bucket_idx,
                preferred_folders=preferred_folders
            )
    res.sort(key=lambda t: t.last_repeated)
    return res


def print_stats(ctx: AppCtx, task_ids: list[int], bucket_delays: list[int]) -> bool:
    c = ctx.console
    buckets = load_buckets(ctx, task_ids, num_of_buckets=len(bucket_delays))
    curr_time_sec = int(time.time())
    print(f"{c.mark_info('Bucket delays:')} {' '.join([seconds_to_duration_str(d) for d in bucket_delays])}")
    print()
    print(f"{c.mark_info('Total number of tasks:')} {len(task_ids)}")
    print()
    bucket_counts: list[dict[str, Any]] = []
    for bucket_idx, bucket in enumerate(buckets):
        min_delay_sec = bucket_delays[bucket_idx]
        active = []
        waiting = []
        for t in bucket:
            if curr_time_sec - t.last_repeated >= min_delay_sec:
                active.append(t)
            else:
                waiting.append(t)
        if len(active) == 0 and len(waiting) > 0:
            time_to_wait = min(min_delay_sec - (curr_time_sec - t.last_repeated) for t in waiting)
            time_to_wait_str = seconds_to_duration_str(time_to_wait)
        else:
            time_to_wait_str = ''
        bucket_counts.append({
            'bucket': f'#{bucket_idx}',
            'total': len(bucket),
            'active': len(active),
            'waiting': len(waiting),
            'time_to_wait': time_to_wait_str,
        })
    print(print_table_from_dicts(bucket_counts))
    print()
    return input(c.mark_prompt('Press Enter') + c.mark_hint(' (`e - exit)')).strip() != '`e'


def repeat_tasks_with_buckets(
        ctx: AppCtx,
        task_ids: list[int],
        buckets_descr: str,
        repeat_task: Callable[[AppCtx, Task, Callable[[], bool]], TaskContinuation]
) -> None:
    break_reminder_interval_sec = duration_str_to_seconds(ctx.settings.break_reminder_interval)
    next_break_reminder: int = int(time.time()) + break_reminder_interval_sec

    def remind_about_break_if_needed() -> None:
        nonlocal next_break_reminder
        if next_break_reminder < int(time.time()):
            clear_screen()
            ctx.console.input('TAKE A BREAK')
            clear_screen()
            next_break_reminder = int(time.time()) + break_reminder_interval_sec

    bucket_delays = [duration_str_to_seconds(m.group(1)) for m in re.finditer(r'(\S+)', buckets_descr)]
    num_of_buckets = len(bucket_delays)

    clear_screen()
    if not print_stats(ctx, task_ids, bucket_delays):
        return

    def get_next_tasks_to_repeat() -> list[TaskWithHist]:
        return select_tasks_to_repeat_from_buckets(
            load_buckets(ctx, task_ids, num_of_buckets),
            bucket_delays
        )

    tasks = get_next_tasks_to_repeat()
    act = TaskContinuation.NEXT_TASK
    while act != TaskContinuation.EXIT:
        remind_about_break_if_needed()
        if len(tasks) == 0:
            tasks = get_next_tasks_to_repeat()
            if len(tasks) == 0:
                clear_screen()
                if not print_stats(ctx, task_ids, bucket_delays):
                    return
                continue
        act = repeat_task(
            ctx,
            Task(**{k: v for k, v in tasks.pop(0).task.__dict__.items() if k != 'card'}),
            lambda: print_stats(ctx, task_ids, bucket_delays)
        )
