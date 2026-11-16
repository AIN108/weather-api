"""시간대 LED(check_time_signal)가 0·6·12·18시 경계에서 늦지 않게 바뀌는지 검사한다."""
import datetime

import pytest
from conftest import ULTRA_OK, FakeDatetime, FakeResponse

TIME_PINS = [17, 27, 22, 5]
SECONDS = {"seconds": 1, "second": 1, "minutes": 60, "minute": 60, "hours": 3600, "hour": 3600}


def test_time_signal_job_runs_often_enough_to_follow_boundaries(run_script):
    _, record = run_script("itscseoul.py", [FakeResponse(ULTRA_OK)], ticks=0)
    jobs = [(n, unit) for n, unit, name in record["schedule"] if name == "check_time_signal"]
    assert len(jobs) == 1, record["schedule"]
    n, unit = jobs[0]
    # 6시간 주기면 05:59에 시작했을 때 11:59까지 '0~6시' LED가 켜져 있다. 경계 뒤 1분 안에 바뀌어야 한다.
    assert n * SECONDS[unit] <= 60, jobs[0]


@pytest.mark.parametrize("hour,pin", [(5, TIME_PINS[0]), (6, TIME_PINS[1]), (12, TIME_PINS[2]), (18, TIME_PINS[3])])
def test_time_signal_picks_slot_for_current_hour(run_script, hour, pin):
    namespace, record = run_script("itscseoul.py", [FakeResponse(ULTRA_OK)], ticks=0)
    record["outputs"].clear()
    FakeDatetime.current = datetime.datetime(2026, 11, 16, hour, 0)
    namespace["check_time_signal"]()
    assert record["outputs"][-1] == (pin, 1)
