import os
import time
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

import requests
import schedule
import RPi.GPIO as GPIO


GPIO.cleanup()

time_pins = [17, 27, 22, 5]
weather_pins = [6, 13, 19, 26]

GPIO.setmode(GPIO.BCM)
GPIO.setup(time_pins, GPIO.OUT)
GPIO.setup(weather_pins, GPIO.OUT)
GPIO.output(time_pins, GPIO.LOW)
GPIO.output(weather_pins, GPIO.LOW)

service_key = os.getenv("KMA_SERVICE_KEY")
if not service_key:
    raise RuntimeError(
        "KMA_SERVICE_KEY 환경변수가 설정되지 않았습니다. "
        "공공데이터포털에서 새 키를 발급한 뒤 환경변수로 설정하세요."
    )

url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
nx = 61
ny = 127
server_url = os.getenv(
    "WEATHER_SERVER_URL",
    "http://192.168.43.93:5000/update_weather_data",
)


def interpret_sky_and_pty(sky, pty):
    if pty == 1:
        return "비옴"
    if pty == 2:
        return "비/눈옴"
    if pty == 3:
        return "눈옴"
    if pty == 5:
        return "빗방울"
    if pty == 6:
        return "빗방울눈날림"
    if pty == 7:
        return "눈날림"
    if pty == 0:
        if sky == 1:
            return "맑음"
        if sky == 3:
            return "구름많음"
        if sky == 4:
            return "흐림"
    return "알 수 없음"


def get_weather():
    now = datetime.now()
    base_date = now.strftime("%Y%m%d")
    base_time = (now - timedelta(minutes=40)).strftime("%H%M")

    params = {
        "serviceKey": service_key,
        "numOfRows": "100",
        "pageNo": "1",
        "dataType": "XML",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    temperature = None
    humidity = None
    sky_value = None
    pty_value = None
    precipitation = None
    snowfall = None

    for item in root.findall(".//item"):
        category_node = item.find("category")
        value_node = item.find("fcstValue")
        if category_node is None or value_node is None:
            continue

        category = category_node.text
        value = value_node.text

        if category == "T1H":
            temperature = value
        elif category == "REH":
            humidity = value
        elif category == "SKY" and value is not None:
            sky_value = int(value)
        elif category == "PTY" and value is not None:
            pty_value = int(value)
        elif category == "RN1":
            precipitation = value
        elif category == "SNO":
            snowfall = value

    final_sky_status = interpret_sky_and_pty(sky_value, pty_value)
    print("노원구 날씨 업데이트를 시작합니다...")
    print(f"현재 시간: {now.strftime('%H%M')}")
    print(f"기온: {temperature if temperature is not None else '데이터 없음'}°C")
    print(f"습도: {humidity if humidity is not None else '데이터 없음'}%")
    print(f"날씨 상태: {final_sky_status}")

    if pty_value in [1, 2]:
        print(f"강수량: {precipitation}mm" if precipitation else "강수량 데이터 없음")
    elif pty_value in [3, 6, 7]:
        print(f"적설량: {snowfall}cm" if snowfall else "적설량 데이터 없음")

    GPIO.output(weather_pins, GPIO.LOW)
    if final_sky_status == "맑음":
        GPIO.output(weather_pins[2], GPIO.HIGH)
    elif final_sky_status == "구름많음":
        GPIO.output(weather_pins[0], GPIO.HIGH)
    elif final_sky_status == "흐림":
        GPIO.output(weather_pins[1], GPIO.HIGH)
    else:
        GPIO.output(weather_pins[3], GPIO.HIGH)

    data = {
        "temperature": temperature,
        "humidity": humidity,
        "weather": final_sky_status,
        "precipitation": precipitation,
        "snowfall": snowfall,
    }

    try:
        post_response = requests.post(server_url, json=data, timeout=15)
        if post_response.status_code == 200:
            print("서버로 데이터 전송 성공:", data)
        else:
            print("서버로 데이터 전송 실패:", post_response.status_code)
    except requests.RequestException as exc:
        print("데이터 전송 중 오류 발생:", exc)


def check_time_signal():
    current_hour = datetime.now().hour

    if 0 <= current_hour < 6:
        time_signal = 1
    elif 6 <= current_hour < 12:
        time_signal = 2
    elif 12 <= current_hour < 18:
        time_signal = 3
    else:
        time_signal = 4

    GPIO.output(time_pins, GPIO.LOW)
    GPIO.output(time_pins[time_signal - 1], GPIO.HIGH)


try:
    get_weather()
    check_time_signal()
    schedule.every(1).minutes.do(get_weather)
    schedule.every(6).hours.do(check_time_signal)

    while True:
        schedule.run_pending()
        time.sleep(1)
finally:
    GPIO.output(time_pins, GPIO.LOW)
    GPIO.output(weather_pins, GPIO.LOW)
    GPIO.cleanup()
