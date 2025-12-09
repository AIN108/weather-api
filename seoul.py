from bs4 import BeautifulSoup
from random import *
from io import StringIO
import requests
import RPi.GPIO as GPIO
#import xmltodict
import json
import serial
import pyfirmata

def return_print(*massage):
    io = StringIO()
    print(*massage, file=io, end="")
    return io.getvalue()

#a = {맑음: "DB01", 구름많음: "DB03", 흐림: "DB04" }
#b = {강수없음: "0", 비: "1", 비/눈: "2", 눈: "3", 소나기 : "4"}

#DB01 = a
#DB03 = b
#DB04 = c

#list1 = list(DB01, DB03, DB04)
#list2 = list(0,1,2,3,4,5,6)
GPIO.setwarnings (False)
GPIO.setmode(GPIO.BCM)

GPIO.setup([7,8,11,12], GPIO.OUT, initial=GPIO.LOW)

url = 'http://apis.data.go.kr/1360000/VilageFcstMsgService/getLandFcst'
params ={'serviceKey' : 'H/+1O7x6RzhSsqBmKv5jh9zdkccdPiWXz7GNB1Lkwkrwo4L7EFhthFyPTt27WDbp6LAeSXo9I8fgfxYZuOH2VQ==',
          'pageNo' : '1', 'numOfRows' : '1', 'dataType' : 'XML', 'regId' : '11B10101' }

response = requests.get(url, params=params)
soup = BeautifulSoup(response.text,"lxml")
items = soup.find_all("item")

'''tag = soup.find_all("item")
type(tag)
<class 'bs4.element.Tag'>'''

for item in items:
    skystate = item.find('wfcd')
    #list1.append(skystate)
    rain = item.find('rnYn')
    #list2.append(rain)

    when = return_print(skystate,rain)
    print(type(skystate),type(rain))
    print(when)

"""
ser = serial.Serial('/dev/ttyACM0', 115200)
ser.open()
ser.write(str.encode("Hello"))
ser.close()

while rain != None:
    continue

if list1[0]  DB01:
    GPIO.output(7, True)
    GPIO.output(8, 0)
    GPIO.output(11, 0
    GPIO.output(12, 0)
elif list1[0] == DB03 or DB04:
    GPIO.output(7, 0)
    GPIO.output(8, True)
    GPIO.output(11, 0)
    GPIO.output(12, 0)
elif list2[0] == 1 or 4:
    GPIO.output(7, 0)
    GPIO.output(8, 0)
    GPIO.output(11, True)
    GPIO.output(12, 0)
elif list2[0] == 2 or 3:
    GPIO.output(7, 0)
    GPIO.output(8, 0)
    GPIO.output(11, 0)
    GPIO.output(12, True)
    """


