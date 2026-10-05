from datetime import datetime, time
from zoneinfo import ZoneInfo


SHANGHAI = ZoneInfo("Asia/Shanghai")
NEW_YORK = ZoneInfo("America/New_York")


def get_a_share_market_status(now: datetime | None = None) -> tuple[datetime, str]:
    current = datetime.now(SHANGHAI) if now is None else now
    if current.tzinfo is None:
        current = current.replace(tzinfo=SHANGHAI)
    else:
        current = current.astimezone(SHANGHAI)

    clock = current.time().replace(tzinfo=None)
    if current.weekday() >= 5:
        status = "周末休市"
    elif time(9, 30) <= clock < time(11, 30) or time(13, 0) <= clock < time(15, 0):
        status = "开盘中"
    elif clock < time(9, 30):
        status = "盘前"
    elif clock < time(13, 0):
        status = "午间休市"
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
    if current.weekday() >= 5:
        status = "周末休市"
    elif time(9, 30) <= clock < time(16, 0):
        status = "开盘中"
    elif clock < time(9, 30):
        status = "盘前"
    else:
        status = "已收盘"
    return current, status
