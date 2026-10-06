from datetime import datetime, time
from functools import lru_cache
from zoneinfo import ZoneInfo

import exchange_calendars as xcals


SHANGHAI = ZoneInfo("Asia/Shanghai")
NEW_YORK = ZoneInfo("America/New_York")


@lru_cache(maxsize=2)
def _get_calendar(name: str):
    return xcals.get_calendar(name)


def _is_trading_day(calendar_name: str, current: datetime) -> bool | None:
    calendar = _get_calendar(calendar_name)
    session_date = current.date()
    if not calendar.first_session.date() <= session_date <= calendar.last_session.date():
        return None
    return bool(calendar.is_session(session_date))


def get_a_share_market_status(now: datetime | None = None) -> tuple[datetime, str]:
    current = datetime.now(SHANGHAI) if now is None else now
    if current.tzinfo is None:
        current = current.replace(tzinfo=SHANGHAI)
    else:
        current = current.astimezone(SHANGHAI)

    clock = current.time().replace(tzinfo=None)
    is_trading_day = _is_trading_day("XSHG", current)
    if is_trading_day is None:
        status = "交易日历待更新"
    elif not is_trading_day:
        status = "周末休市" if current.weekday() >= 5 else "节假日休市"
    elif clock < time(9, 15):
        status = "盘前"
    elif clock < time(9, 25):
        status = "集合竞价"
    elif clock < time(9, 30):
        status = "待开盘"
    elif time(9, 30) <= clock < time(11, 30) or time(13, 0) <= clock < time(14, 57):
        status = "盘中"
    elif clock < time(13, 0):
        status = "午间休市"
    elif clock < time(15, 0):
        status = "收盘竞价"
    else:
        status = "已收盘"
    return current, status


def get_us_market_status(now: datetime | None = None) -> tuple[datetime, str]:
    current = datetime.now(NEW_YORK) if now is None else now
    if current.tzinfo is None:
        current = current.replace(tzinfo=NEW_YORK)
    else:
        current = current.astimezone(NEW_YORK)

    clock = current.time().replace(tzinfo=None)
    is_trading_day = _is_trading_day("XNYS", current)
    if is_trading_day is None:
        status = "交易日历待更新"
    elif not is_trading_day:
        status = "周末休市" if current.weekday() >= 5 else "节假日休市"
    else:
        close_time = _get_calendar("XNYS").schedule.loc[
            current.date().isoformat(), "close"
        ].tz_convert(NEW_YORK).time().replace(tzinfo=None)
        if clock < time(4, 0):
            status = "未开市"
        elif clock < time(9, 30):
            status = "盘前交易"
        elif clock < close_time:
            status = "盘中"
        elif clock < time(20, 0):
            status = "盘后交易"
        else:
            status = "已收盘"
    return current, status
