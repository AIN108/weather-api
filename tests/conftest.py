"""Raspberry Pi 없이 스크립트를 실행하기 위한 도우미.

itscseoul.py·seoulfinal.py는 import 시점에 GPIO를 설정하고 무한 루프에 들어간다. 그래서
RPi.GPIO·schedule을 스텁으로, requests.get을 정해진 응답 목록으로, datetime.now()를 고정 시각으로 바꾼 뒤
스크립트 파일을 exec로 실행하고, 루프는 정해진 횟수 뒤 예외로 빠져나온다.
"""
import contextlib
import datetime as real_datetime
import io
import sys
import types
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]


class StopLoop(BaseException):
    """루프를 끝내기 위한 테스트 전용 예외 (스크립트의 except Exception에 잡히지 않음)."""


class FakeResponse:
    def __init__(self, content=b"", status=200):
        self.content, self.status_code = content, status
        self.text = content.decode("utf-8", "replace")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


class FakeDatetime(real_datetime.datetime):
    current = real_datetime.datetime(2026, 11, 16, 14, 17)

    @classmethod
    def now(cls, tz=None):
        return cls.current


def _fake_gpio(outputs):
    gpio = types.ModuleType("RPi.GPIO")
    for name in ("cleanup", "setmode", "setup", "setwarnings"):
        setattr(gpio, name, lambda *a, **k: None)
    gpio.output = lambda pin, value: outputs.append((pin, value))
    gpio.BCM, gpio.OUT, gpio.LOW, gpio.HIGH = "BCM", "OUT", 0, 1
    rpi = types.ModuleType("RPi")
    rpi.GPIO = gpio
    return rpi, gpio


@pytest.fixture
def run_script(monkeypatch):
    """스크립트를 실행하고 (namespace, 기록) 을 돌려준다.

    responses: requests.get이 차례로 돌려줄 FakeResponse 또는 예외 (마지막 값은 계속 반복)
    ticks: itscseoul의 schedule.run_pending 호출 횟수 / seoulfinal의 time.sleep 허용 횟수
    """

    def _run(name, responses, ticks=3, now=None):
        record = {"outputs": [], "params": [], "stdout": io.StringIO()}
        rpi, gpio = _fake_gpio(record["outputs"])
        monkeypatch.setitem(sys.modules, "RPi", rpi)
        monkeypatch.setitem(sys.modules, "RPi.GPIO", gpio)
        monkeypatch.setenv("KMA_SERVICE_KEY", "dummy-key")
        monkeypatch.setenv("WEATHER_SERVER_URL", "http://127.0.0.1:9/update_weather_data")
        if now is not None:
            FakeDatetime.current = now
        fake_dt = types.ModuleType("datetime")
        fake_dt.__dict__.update(real_datetime.__dict__)
        fake_dt.datetime = FakeDatetime
        monkeypatch.setitem(sys.modules, "datetime", fake_dt)

        queue = list(responses)

        def fake_get(url, params=None, timeout=None):
            record["params"].append(dict(params or {}))
            item = queue.pop(0) if len(queue) > 1 else queue[0]
            if isinstance(item, BaseException):
                raise item
            return item

        monkeypatch.setattr(requests, "get", fake_get)
        monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResponse(b"{}"))

        jobs = []

        class Job:
            def __getattr__(self, _):
                return self

            def do(self, fn):
                jobs.append(fn)

        schedule = types.ModuleType("schedule")
        schedule.every = lambda *a, **k: Job()
        state = {"ticks": 0}

        def run_pending():
            state["ticks"] += 1
            if state["ticks"] > ticks:
                raise StopLoop
            jobs[0]()  # 1분 주기 날씨 작업

        schedule.run_pending = run_pending
        monkeypatch.setitem(sys.modules, "schedule", schedule)

        import time

        sleeps = {"n": 0}

        def fake_sleep(_seconds):
            sleeps["n"] += 1
            if name == "seoulfinal.py" and sleeps["n"] >= ticks:
                raise KeyboardInterrupt  # 사용자 Ctrl+C 흉내

        monkeypatch.setattr(time, "sleep", fake_sleep)

        namespace = {"__name__": "__main__"}
        source = (ROOT / name).read_text(encoding="utf-8")
        with contextlib.redirect_stdout(record["stdout"]):
            try:
                exec(compile(source, str(ROOT / name), "exec"), namespace)
                record["result"] = "exited"
            except StopLoop:
                record["result"] = "loop-alive"
            except BaseException as exc:  # noqa: B036 - 스크립트가 예외로 끝났는지 기록
                record["result"] = f"crashed: {type(exc).__name__}: {exc}"
        record["text"] = record["stdout"].getvalue()
        return namespace, record

    return _run


ULTRA_OK = ("<response><header><resultCode>00</resultCode><resultMsg>NORMAL_SERVICE</resultMsg></header>"
            "<body><items>"
            "<item><category>SKY</category><fcstValue>1</fcstValue></item>"
            "<item><category>PTY</category><fcstValue>0</fcstValue></item>"
            "<item><category>T1H</category><fcstValue>5</fcstValue></item>"
            "<item><category>REH</category><fcstValue>60</fcstValue></item>"
            "</items></body></response>").encode()
LAND_OK = ("<response><header><resultCode>00</resultCode></header><body><items><item>"
           "<wfCd>DB01</wfCd><rnYn>0</rnYn></item></items></body></response>").encode()
KEY_ERROR_XML = (b"<OpenAPI_ServiceResponse><cmmMsgHeader>"
                 b"<returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>"
                 b"<returnReasonCode>30</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>")
