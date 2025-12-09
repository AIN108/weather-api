import requests
import schedule
import time
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import RPi.GPIO as GPIO

# GPIO 경고 무시

GPIO.cleanup()

# GPIO 핀 설정
time_pins = [17, 27, 22, 5]  # 시간대별 출력 핀 (각 시간대에 해당하는 핀 번호)
weather_pins = [6, 13, 19, 26]  # 날씨 상태별 출력 핀 (구름 많음, 흐림, 맑음, 그 외)


# GPIO 초기화
GPIO.setmode(GPIO.BCM)
GPIO.setup(time_pins, GPIO.OUT)
GPIO.setup(weather_pins, GPIO.OUT)



# 모든 핀을 LOW로 초기화
GPIO.output(time_pins, GPIO.LOW)
GPIO.output(weather_pins, GPIO.LOW)

# 기상청 API 정보
service_key = "H/+1O7x6RzhSsqBmKv5jh9zdkccdPiWXz7GNB1Lkwkrwo4L7EFhthFyPTt27WDbp6LAeSXo9I8fgfxYZuOH2VQ=="
url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"

# 노원구 좌표 (서울시 노원구)
nx = 61
ny = 127

# 서버 URL
server_url = "http://192.168.43.93:5000/update_weather_data"  # 서버의 IP와 포트를 설정하세요.

def interpret_sky_and_pty(sky, pty):
    if pty == 1:  # 비
        return "비옴"
    elif pty == 2:  # 비/눈
        return "비/눈옴"
    elif pty == 3:  # 눈
        return "눈옴"
    elif pty == 5:  # 빗방울
        return "빗방울"
    elif pty == 6:  # 빗방울눈날림
        return "빗방울눈날림"
    elif pty == 7:  # 눈날림
        return "눈날림"
    elif pty == 0:  # 강수 없음
        if sky == 1:
            return "맑음"
        elif sky == 3:
            return "구름많음"
        elif sky == 4:
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

    response = requests.get(url, params=params)
    root = ET.fromstring(response.content)

    temperature = None
    humidity = None
    sky_value = None
    pty_value = None
    precipitation = None
    snowfall = None

    for item in root.findall(".//item"):
        category = item.find('category').text
        value = item.find('fcstValue').text

        if category == 'T1H':  # 기온
            temperature = value
        elif category == 'REH':  # 습도
            humidity = value
        elif category == 'SKY':  # 하늘상태
            sky_value = int(value)
        elif category == 'PTY':  # 강수형태
            pty_value = int(value)
        elif category == 'RN1':  # 1시간 강수량
            precipitation = value
        elif category == 'SNO':  # 1시간 적설량
            snowfall = value

    # 날씨 상태 해석 및 출력
    final_sky_status = interpret_sky_and_pty(sky_value, pty_value)
    print("노원구 날씨 업데이트를 시작합니다...")
    print(f"현재 시간: {now.strftime('%H%M')}")
    print(f"기온: {temperature if temperature is not None else '데이터 없음'}°C")
    print(f"습도: {humidity if humidity is not None else '데이터 없음'}%")
    print(f"날씨 상태: {final_sky_status}")

    # 강수량 또는 적설량 출력
    if pty_value in [1, 2]:  # 비 또는 비/눈
        print(f"강수량: {precipitation}mm" if precipitation else "강수량 데이터 없음")
    elif pty_value in [3, 6, 7]:  # 눈 또는 눈날림
        print(f"적설량: {snowfall}cm" if snowfall else "적설량 데이터 없음")

    # GPIO 제어
    GPIO.output(weather_pins, GPIO.LOW)
    if final_sky_status is not None:
        if final_sky_status == "맑음":
            GPIO.out
            put(weather_pins[2], GPIO.HIGH)
        elif final_sky_status == "구름많음":
            GPIO.output(weather_pins[0], GPIO.HIGH)
        elif final_sky_status == "흐림":
            GPIO.output(weather_pins[1], GPIO.HIGH)
        else:  # 비 또는 눈
            GPIO.output(weather_pins[3], GPIO.HIGH)

    # 데이터 송신
    data = {
        "temperature": temperature,
        "humidity": humidity,
        "weather": final_sky_status,
        "precipitation": precipitation,
        "snowfall": snowfall
    }

    try:
        response = requests.post(server_url, json=data)
        if response.status_code == 200:
            print("서버로 데이터 전송 성공:", data)
        else:
            print("서버로 데이터 전송 실패:", response.status_code)
    except Exception as e:
        print("데이터 전송 중 오류 발생:", e)

def check_time_signal():
    now = datetime.now()
    current_hour = now.hour

    if 0 <= current_hour < 6:
        time_signal = 1
    elif 6 <= current_hour < 12:
        time_signal = 2
    elif 12 <= current_hour < 18:
        time_signal = 3
    elif 18 <= current_hour < 24:
        time_signal = 4
    else:
        time_signal = None

    GPIO.output(time_pins, GPIO.LOW)
    if time_signal is not None:
        GPIO.output(time_pins[time_signal - 1], GPIO.HIGH)

# 첫 실행 시 바로 실행
get_weather()
check_time_signal()

# 1분마다 날씨 체크
schedule.every(1).minutes.do(get_weather)
# 6시간마다 시간대 체크
schedule.every(6).hours.do(check_time_signal)

while True:
    schedule.run_pending()
    time.sleep(1)
    

