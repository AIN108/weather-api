# Seoul Weather API

기상청 공공데이터 API를 활용해 서울/노원구 날씨 정보를 조회하고 Raspberry Pi GPIO 또는 로컬 서버 연동을 실험한 프로젝트입니다.

## 프로젝트 구조

```text
weather-api/
├── seoul.py
├── itscseoul.py
├── seoulfinal.py
├── LICENSE
└── README.md
```

## API 키 설정

공공데이터 API 키는 소스 코드에 직접 넣지 않습니다. 공공데이터포털에서 키를 발급한 뒤 `KMA_SERVICE_KEY` 환경변수로 설정합니다.

Linux / Raspberry Pi:

```bash
export KMA_SERVICE_KEY='YOUR_NEW_SERVICE_KEY'
```

Windows PowerShell:

```powershell
$env:KMA_SERVICE_KEY='YOUR_NEW_SERVICE_KEY'
```

`itscseoul.py`에서 날씨 데이터를 보낼 서버 주소를 바꾸려면 선택적으로 `WEATHER_SERVER_URL`도 설정할 수 있습니다.

```bash
export WEATHER_SERVER_URL='http://127.0.0.1:5000/update_weather_data'
```

> 보안 주의: 과거 커밋에는 API 키가 하드코딩된 이력이 있습니다. Git 히스토리에서 문자열을 지우는 것만으로 이미 노출된 키가 안전해지는 것은 아니므로, 기존 키는 폐기/재발급하는 것이 필요합니다.

## 주요 의존성

스크립트별로 필요한 패키지가 다릅니다. 대표적으로 다음 패키지를 사용합니다.

```bash
pip install requests beautifulsoup4 lxml xmltodict schedule
```

Raspberry Pi에서는 `RPi.GPIO` 설치/지원 여부를 사용 중인 Raspberry Pi OS 환경에 맞게 확인해야 합니다.

## 실행

```bash
python seoulfinal.py
```

또는:

```bash
python itscseoul.py
```

## 데이터 출처

- 기상청 단기예보/육상예보 API
- 공공데이터포털: https://www.data.go.kr
- API 예시: https://www.data.go.kr/data/15084084/openapi.do

기상청 API 데이터는 이 저장소의 MIT License와 별개로 공공데이터포털 및 제공기관의 이용 조건을 따릅니다.

## 라이선스

AIN108이 작성한 이 저장소의 소스 코드는 MIT License로 배포합니다. 자세한 내용은 `LICENSE`를 참고하십시오. 외부 API 데이터와 Python 라이브러리는 각각의 별도 이용 조건 및 라이선스를 따릅니다.

## 개발자

- GitHub: [@AIN108](https://github.com/AIN108)
