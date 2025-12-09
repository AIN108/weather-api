import RPi.GPIO as GPIO
import requests
import xmltodict
import time

def get_weather_data():
    url = 'http://apis.data.go.kr/1360000/VilageFcstMsgService/getLandFcst'
    params = {
        'serviceKey': 'H/+1O7x6RzhSsqBmKv5jh9zdkccdPiWXz7GNB1Lkwkrwo4L7EFhthFyPTt27WDbp6LAeSXo9I8fgfxYZuOH2VQ==',
        'pageNo': '1',
        'numOfRows': '1',
        'dataType': 'XML',
        'regId': '11B10101'
    }
    response = requests.get(url, params=params)
    data = xmltodict.parse(response.content)
    return data['response']['body']['items']['item']

# GPIO 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup([7, 8, 11, 12], GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        # 날씨 데이터 가져오기
        item = get_weather_data()

        # 날씨 데이터 추출
        skystate = item['wfCd']  # 날씨 코드
        rain = item['rnYn']      # 강수 여부

        # GPIO에 신호 보내기
        if skystate == 'DB01':  # 맑음
            GPIO.output(7, GPIO.HIGH)
        elif skystate == 'DB03':  # 구름 많음
            GPIO.output(8, GPIO.HIGH)
        elif skystate == 'DB04':  # 흐림
            GPIO.output(11, GPIO.HIGH)

        if rain == '0':  # 강수 없음
            GPIO.output(12, GPIO.LOW)
        else:  # 강수 있음
            GPIO.output(12, GPIO.HIGH)

        print(f"Sky State: {skystate}, Rain: {rain}")

        # 6시간 대기
        time.sleep(10)

except KeyboardInterrupt:
    print("프로그램이 중단되었습니다.")

finally:
    GPIO.cleanup()



