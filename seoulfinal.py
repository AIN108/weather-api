import os
import time

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
    header = data.get("response", {}).get("header", {})
    if header.get("resultCode") != "00":
        raise ValueError(f"기상청 API 오류: {header.get('resultCode')} {header.get('resultMsg')}")
    item = data["response"]["body"]["items"]["item"]
    return item[0] if isinstance(item, list) else item


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([7, 8, 11, 12], GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        try:
            item = get_weather_data()
        except (requests.RequestException, ValueError, KeyError) as exc:
            print("날씨 조회 실패:", exc)
            time.sleep(60)
            continue

        skystate = item["wfCd"]
        rain = item["rnYn"]

        GPIO.output([7, 8, 11], GPIO.LOW)
        if skystate == "DB01":
            GPIO.output(7, GPIO.HIGH)
        elif skystate == "DB03":
            GPIO.output(8, GPIO.HIGH)
        elif skystate == "DB04":
            GPIO.output(11, GPIO.HIGH)

        GPIO.output(12, GPIO.LOW if rain == "0" else GPIO.HIGH)

        print(f"Sky State: {skystate}, Rain: {rain}")
        # 육상예보는 하루 3회 발표되므로 10분 간격이면 충분하다(일일 호출 한도 보호).
        time.sleep(600)

except KeyboardInterrupt:
    print("프로그램이 중단되었습니다.")
finally:
    GPIO.cleanup()
