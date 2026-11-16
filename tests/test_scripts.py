"""itscseoul.py / seoulfinal.py 동작 테스트 (GPIO·네트워크·API 키 없이)."""
import datetime

import pytest
import requests
from conftest import KEY_ERROR_XML, LAND_OK, ULTRA_OK, FakeDatetime, FakeResponse

WEATHER_PINS = [6, 13, 19, 26]


@pytest.mark.parametrize("now,expected", [
    (datetime.datetime(2026, 11, 16, 0, 10), ("20261115", "2330")),   # 자정 직후: 전날로 넘어감
    (datetime.datetime(2026, 11, 16, 0, 39), ("20261115", "2359")),
    (datetime.datetime(2026, 11, 16, 0, 40), ("20261116", "0000")),
    (datetime.datetime(2026, 11, 16, 14, 17), ("20261116", "1337")),
    (datetime.datetime(2026, 1, 1, 0, 5), ("20251231", "2325")),      # 연도가 바뀌는 경우
])
def test_itscseoul_base_date_and_time(run_script, now, expected):
    namespace, record = run_script("itscseoul.py", [FakeResponse(ULTRA_OK)], ticks=0)
    record["params"].clear()
    FakeDatetime.current = now
    namespace["get_weather"]()
    params = record["params"][-1]
    assert (params["base_date"], params["base_time"]) == expected


def test_itscseoul_loop_survives_request_errors(run_script):
    responses = [requests.ConnectionError("network down"), FakeResponse(b"", 503), FakeResponse(ULTRA_OK)]
    _, record = run_script("itscseoul.py", responses, ticks=3)
    assert record["result"] == "loop-alive", record["text"]
    assert record["text"].count("날씨 조회 실패") == 2
    assert "날씨 상태: 맑음" in record["text"]
    # 맑음 → weather_pins[2] HIGH
    assert (WEATHER_PINS[2], 1) in record["outputs"]


def test_seoulfinal_loop_survives_errors_and_sets_leds(run_script):
    responses = [requests.ConnectionError("network down"), FakeResponse(b"", 503),
                 FakeResponse(KEY_ERROR_XML), FakeResponse(LAND_OK)]
    _, record = run_script("seoulfinal.py", responses, ticks=4)
    assert record["result"] == "exited", record["text"]  # Ctrl+C(KeyboardInterrupt)로 정상 종료
    assert record["text"].count("날씨 조회 실패") == 3
    assert "Sky State: DB01, Rain: 0" in record["text"]
    assert (7, 1) in record["outputs"] and (12, 0) in record["outputs"]
