import os
import time
from xml.parsers.expat import ExpatError

import requests
import RPi.GPIO as GPIO
import xmltodict


def get_service_key():
    service_key = os.getenv("KMA_SERVICE_KEY")
    if not service_key:
        raise RuntimeError(
            "KMA_SERVICE_KEY 환경변수가 설정되지 않았습니다. "
            "공공데이터포털에서 새 키를 발급한 뒤 환경변수로 설정하세요."
        )
    return service_key


def get_weather_data():
    url = "https://apis.data.go.kr/1360000/VilageFcstMsgService/getLandFcst"
    params = {
        "serviceKey": get_service_key(),
        "pageNo": "1",
        "numOfRows": "1",
        "dataType": "XML",
        "regId": "11B10101",
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = xmltodict.parse(response.content)
    header = (data.get("response") or {}).get("header") or {}
    result_code = header.get("resultCode")
    if result_code is not None and result_code != "00":
        # 오류 응답(트래픽 초과·NO_DATA 등)은 본문이 없거나 비어 있다. 원인 코드를 그대로 보여 준다.
        raise KmaApiError(f"resultCode={result_code}: {header.get('resultMsg')}")
    return data["response"]["body"]["items"]["item"]


class KmaApiError(Exception):
    """기상청 API가 정상(00)이 아닌 resultCode를 돌려준 경우."""


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([7, 8, 11, 12], GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        try:
            item = get_weather_data()
            skystate = item["wfCd"]
            rain = item["rnYn"]
        except (requests.RequestException, ExpatError, KeyError, TypeError, KmaApiError) as exc:
            # 네트워크 오류·오류 응답(body 없음) 한 번으로 종료하지 않고 LED 상태를 유지한 채 재시도한다.
            print("날씨 조회 실패, 10초 후 다시 시도합니다:", exc)
            time.sleep(10)
            continue

        GPIO.output([7, 8, 11], GPIO.LOW)
        if skystate == "DB01":
            GPIO.output(7, GPIO.HIGH)
        elif skystate == "DB03":
            GPIO.output(8, GPIO.HIGH)
        elif skystate == "DB04":
            GPIO.output(11, GPIO.HIGH)

        GPIO.output(12, GPIO.LOW if rain == "0" else GPIO.HIGH)

        print(f"Sky State: {skystate}, Rain: {rain}")
        time.sleep(10)

except KeyboardInterrupt:
    print("프로그램이 중단되었습니다.")
finally:
    GPIO.cleanup()
