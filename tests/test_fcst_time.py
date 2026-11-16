"""초단기예보의 여러 예보 시각(fcstTime) 중 가장 이른 시각 값을 쓰는지 검사한다."""
from conftest import FakeResponse

WEATHER_PINS = [6, 13, 19, 26]


def item(category, value, time, date="20261116"):
    return (f"<item><category>{category}</category><fcstDate>{date}</fcstDate>"
            f"<fcstTime>{time}</fcstTime><fcstValue>{value}</fcstValue></item>")


def response(*items):
    return ("<response><header><resultCode>00</resultCode><resultMsg>NORMAL_SERVICE</resultMsg></header>"
            "<body><items>" + "".join(items) + "</items></body></response>").encode()


def test_uses_earliest_forecast_time_regardless_of_order(run_script):
    # 실제 응답처럼 시각별 값이 섞여 오고, 가장 늦은 시각이 마지막에 오는 경우
    body = response(
        item("T1H", "5", "1500"), item("T1H", "9", "1700"), item("T1H", "7", "1600"),
        item("REH", "60", "1500"), item("REH", "40", "1700"),
        item("SKY", "1", "1500"), item("SKY", "4", "1700"),
        item("PTY", "0", "1500"), item("PTY", "1", "1700"),
    )
    _, record = run_script("itscseoul.py", [FakeResponse(body)], ticks=0)
    assert "기온: 5°C" in record["text"]
    assert "습도: 60%" in record["text"]
    assert "날씨 상태: 맑음" in record["text"]  # 17시의 비(PTY=1)가 아니라 15시 값


def test_earliest_across_date_boundary(run_script):
    body = response(item("T1H", "-1", "0000", date="20261117"), item("T1H", "2", "2330", date="20261116"))
    _, record = run_script("itscseoul.py", [FakeResponse(body)], ticks=0)
    assert "기온: 2°C" in record["text"]
