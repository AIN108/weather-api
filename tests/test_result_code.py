"""resultCode 검사 PR 검증용 추가 테스트 (1차 테스트 PR의 conftest.py와 함께 실행)."""
from conftest import LAND_OK, ULTRA_OK, FakeResponse

WEATHER_PINS = [6, 13, 19, 26]
NO_DATA = (b"<response><header><resultCode>03</resultCode><resultMsg>NO_DATA</resultMsg></header>"
           b"<body><items></items></body></response>")
QUOTA = (b"<response><header><resultCode>22</resultCode>"
         b"<resultMsg>LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR</resultMsg></header></response>")
KEY_ERROR_XML = (b"<OpenAPI_ServiceResponse><cmmMsgHeader>"
                 b"<returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg>"
                 b"</cmmMsgHeader></OpenAPI_ServiceResponse>")


def weather_high_outputs(record):
    """날씨 LED를 켠 기록 (시작·종료 시 전체 LOW는 제외)."""
    return [(pin, value) for pin, value in record["outputs"] if pin in WEATHER_PINS and value == 1]


def test_itscseoul_ignores_no_data_response(run_script):
    _, record = run_script("itscseoul.py", [FakeResponse(NO_DATA)], ticks=0)
    assert "기상청 API 오류 응답 (resultCode=03): NO_DATA" in record["text"]
    assert "날씨 상태" not in record["text"]
    assert weather_high_outputs(record) == []  # LED를 '알 수 없음'으로 바꾸지 않음


def test_itscseoul_ignores_service_key_error(run_script):
    _, record = run_script("itscseoul.py", [FakeResponse(KEY_ERROR_XML)], ticks=0)
    assert "SERVICE_KEY_IS_NOT_REGISTERED_ERROR" in record["text"]
    assert weather_high_outputs(record) == []


def test_itscseoul_normal_response_unchanged(run_script):
    _, record = run_script("itscseoul.py", [FakeResponse(ULTRA_OK)], ticks=0)
    assert "날씨 상태: 맑음" in record["text"]
    assert (WEATHER_PINS[2], 1) in record["outputs"]


def test_seoulfinal_reports_result_code_and_recovers(run_script):
    _, record = run_script("seoulfinal.py", [FakeResponse(QUOTA), FakeResponse(LAND_OK)], ticks=2)
    assert "resultCode=22: LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR" in record["text"]
    assert "Sky State: DB01, Rain: 0" in record["text"]
    assert record["result"] == "exited"
