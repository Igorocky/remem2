import sys

sys.path.append('../../main/python')

from remem.dtos import TaskHistRec
from remem.repeat.strategy.buckets import get_bucket_number, parse_buckets_description

from remem.console import parse_idxs

from remem.common import duration_str_to_seconds, seconds_to_duration_str, extract_gaps_from_text, \
    print_table_from_dicts

from unittest import TestCase

from remem.commands import make_cmd_pat, arr_str_matches_pat


class DurationStrToSecondsTest(TestCase):
    def test_duration_str_to_seconds(self) -> None:
        self.assertEqual(duration_str_to_seconds('29s'), 29)
        self.assertEqual(duration_str_to_seconds('1m'), 60)
        self.assertEqual(duration_str_to_seconds('16m'), 16 * 60)
        self.assertEqual(duration_str_to_seconds('1h'), 60 * 60)
        self.assertEqual(duration_str_to_seconds('32h'), 32 * 60 * 60)
        self.assertEqual(duration_str_to_seconds('1d'), 60 * 60 * 24)
        self.assertEqual(duration_str_to_seconds('7d'), 7 * 60 * 60 * 24)


class ArrStrMatchesPatTest(TestCase):
    def test_arr_str_matches_pat(self) -> None:
        self.assertTrue(arr_str_matches_pat(['make', 'new', 'card', 'translate'], make_cmd_pat('mak n car tr')))
        self.assertTrue(arr_str_matches_pat(['make', 'new', 'card', 'translate'], make_cmd_pat('mak car tr')))
        self.assertTrue(arr_str_matches_pat(['make', 'new', 'card', 'translate'], make_cmd_pat('ake car ')))
        self.assertTrue(arr_str_matches_pat(['make', 'new', 'card', 'translate'], make_cmd_pat('ake nsla ')))


class SecondsToDurationStrTest(TestCase):
    def test_seconds_to_duration_str(self) -> None:
        self.assertEqual(seconds_to_duration_str(0), '0s')
        self.assertEqual(seconds_to_duration_str(27), '27s')

        self.assertEqual(seconds_to_duration_str(duration_str_to_seconds('1m') + 8), '1m8s')
        self.assertEqual(
            seconds_to_duration_str(duration_str_to_seconds('8h') + duration_str_to_seconds('13m') + 49), '8h13m')
        self.assertEqual(
            seconds_to_duration_str(duration_str_to_seconds('17d')
                                    + duration_str_to_seconds('9h') + duration_str_to_seconds('25m') + 33), '17d9h')

        self.assertEqual(seconds_to_duration_str(duration_str_to_seconds('1m') + 0), '1m')
        self.assertEqual(
            seconds_to_duration_str(duration_str_to_seconds('8h') + duration_str_to_seconds('0m') + 0), '8h')
        self.assertEqual(
            seconds_to_duration_str(duration_str_to_seconds('17d')
                                    + duration_str_to_seconds('0h') + duration_str_to_seconds('0m') + 0), '17d')


class ParseIdxsTest(TestCase):
    def test_parse_idxs(self) -> None:
        self.assertEqual(parse_idxs(''), [])
        self.assertEqual(parse_idxs('7'), [7])
        self.assertEqual(parse_idxs('7 15'), [7, 15])
        self.assertEqual(parse_idxs('7 15'), [7, 15])
        self.assertEqual(parse_idxs('7 15 20'), [7, 15, 20])
        self.assertEqual(parse_idxs('4-8'), [4, 5, 6, 7, 8])
        self.assertEqual(parse_idxs('1 4-8 10'), [1, 4, 5, 6, 7, 8, 10])
        self.assertEqual(parse_idxs('abc 4'), [])


class ExtractGapsFromTextTest(TestCase):
    def test_extract_gaps_from_text(self) -> None:
        self.assertEqual(None, extract_gaps_from_text('abc def ghi'))
        self.assertEqual(None, extract_gaps_from_text('abc [[def ghi'))
        self.assertEqual((['abc', 'ghi'], ['def'], [''], ['']), extract_gaps_from_text('abc [[def]] ghi'))
        self.assertEqual(
            (['abc', 'ghi', 'mno'], ['def', 'jkl'], ['', '123'], ['', '456']),
            extract_gaps_from_text('abc [[def]] ghi [[jkl|123|456]] mno')
        )
        self.assertEqual(
            (['abc', 'ghi', ''], ['def', 'jkl'], ['', '123'], ['', '456']),
            extract_gaps_from_text('abc [[def]] ghi [[jkl|123|456]]')
        )
        self.assertEqual(
            (['', 'ghi', 'mno'], ['def', 'jkl'], ['', '123'], ['', '456']),
            extract_gaps_from_text('[[def]] ghi [[jkl|123|456]] mno')
        )


class GetBucketNumberTest(TestCase):
    def test_get_bucket_number(self) -> None:
        def make_hist(marks: list[float]) -> list[TaskHistRec]:
            return [TaskHistRec(mark=mark) for mark in marks]

        self.assertEqual(get_bucket_number([], max_num=10), 0)
        self.assertEqual(get_bucket_number(make_hist([0.0]), max_num=10), 0)
        self.assertEqual(get_bucket_number(make_hist([1.0]), max_num=10), 1)
        self.assertEqual(get_bucket_number(make_hist([1.0, 0.0]), max_num=10), 1)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0]), max_num=10), 2)
        self.assertEqual(get_bucket_number(make_hist([0.0, 1.0]), max_num=10), 0)
        self.assertEqual(get_bucket_number(make_hist([1.0, 0.0, 1.0]), max_num=10), 1)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0, 1.0]), max_num=10), 3)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0, 0.0]), max_num=10), 2)
        self.assertEqual(get_bucket_number(make_hist([0.0, 1.0, 1.0, 1.0]), max_num=10), 0)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0, 1.0, 1.0]), max_num=10), 4)
        self.assertEqual(get_bucket_number(make_hist([1.0, 1.0, 1.0, 1.0]), max_num=3), 3)


class PrintTableFromDictsTest(TestCase):
    def test_print_table_from_dicts(self) -> None:
        self.assertEqual(
            """------------------
    id name desc  
------------------
     1 AA   10    
  None BB   ..    
300000 CC   300000
------------------""",
            print_table_from_dicts([
                {'id': 1, 'name': 'AA', 'desc': 10},
                {'id': None, 'name': 'BB', 'desc': '..'},
                {'id': 300000, 'name': 'CC', 'desc': 300000},
            ])
        )


class ParseBucketsDescriptionTest(TestCase):
    def test_parse_buckets_description(self) -> None:
        self.assertEqual(
            ([120, 300, 900, 1800], [4, 3, 2, 1]),
            parse_buckets_description('2m 5m 15m 30m')
        )
        self.assertEqual(
            ([120, 300, 900, 1800], [3, 1, 1, 1]),
            parse_buckets_description('2m,3 5m,1 15m,1 30m,1')
        )
        self.assertEqual(
            ([120, 300, 900, 1800], [10, 3, 2, 4]),
            parse_buckets_description('2m,10 5m 15m 30m,4')
        )
