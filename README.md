# weather-api
# 🌤️ Seoul Weather API

기상청 공공 API를 활용한 서울 날씨 정보 조회 프로젝트입니다.

## 📋 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 목적 | 서울 지역 실시간 날씨 정보 조회 |
| 데이터 소스 | 기상청 단기예보 API |
| 언어 | Python |

## 📂 프로젝트 구조

```
weather-api/
├── seoul.py          # 서울 날씨 기본 조회
├── itscseoul.py      # 서울과기대 지역 날씨 조회
└── seoulfinal.py     # 최종 버전 (통합)
```

## 🛠️ 기술 스택

- **언어**: Python 3.x
- **API**: 기상청 공공데이터 API
- **라이브러리**: requests, json

## 🚀 실행 방법

### 1. 필수 라이브러리 설치

```bash
pip install requests
```

### 2. API 키 발급

1. [공공데이터포털](https://www.data.go.kr) 접속
2. 회원가입 후 "기상청_단기예보" 검색
3. API 키 발급

### 3. 실행

```bash
python seoulfinal.py
```

## 📊 제공 정보

- 🌡️ 현재 기온
- 💧 습도
- 🌧️ 강수 확률
- 💨 풍속/풍향
- ☁️ 하늘 상태 (맑음/흐림/비 등)

## 📍 지원 지역

- 서울 전역
- 서울과학기술대학교 (노원구)

## 💡 활용 예시

```python
# 날씨 정보 조회
from seoulfinal import get_weather

weather = get_weather("서울")
print(f"현재 기온: {weather['temp']}°C")
print(f"하늘 상태: {weather['sky']}")
```

## 🔗 API 참고

- [기상청 단기예보 API](https://www.data.go.kr/data/15084084/openapi.do)
- [공공데이터포털](https://www.data.go.kr)

##  개발자

- GitHub: [@AIN108](https://github.com/AIN108)

