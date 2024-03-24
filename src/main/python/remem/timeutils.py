import datetime
import time


def unix_epoch_sec_now() -> int:
    now = datetime.datetime.now()
    return int(time.mktime(now.timetuple()))


def unix_epoch_sec_to_str(unix_epoch_sec: int) -> str:
    return str(datetime.datetime.fromtimestamp(unix_epoch_sec))
