import os
from io import StringIO

from bs4 import BeautifulSoup
import requests
import RPi.GPIO as GPIO


def return_print(*message):
    io = StringIO()
    print(*message, file=io, end="")
    return io.getvalue()


def get_service_key():
    service_key = os.getenv("KMA_SERVICE_KEY")
    if not service_key:
        raise RuntimeError(
            "KMA_SERVICE_KEY 환경변수가 설정되지 않았습니다. "
            "공공데이터포털에서 새 키를 발급한 뒤 환경변수로 설정하세요."
        )
    return service_key


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([7, 8, 11, 12], GPIO.OUT, initial=GPIO.LOW)

url = "https://apis.data.go.kr/1360000/VilageFcstMsgService/getLandFcst"
params = {
    "serviceKey": get_service_key(),
    "pageNo": "1",
    "numOfRows": "1",
    "dataType": "XML",
    "regId": "11B10101",
}

try:
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    items = soup.find_all("item")

    for item in items:
        skystate = item.find("wfcd")
        rain = item.find("rnyn")
        when = return_print(skystate, rain)
        print(type(skystate), type(rain))
        print(when)
finally:
    GPIO.cleanup()
