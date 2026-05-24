from public_officer_pipeline.entity import normalize_name, natural_key
from public_officer_pipeline.entity.resolver import road_address_part


def test_normalize_name_removes_company_noise() -> None:
    assert normalize_name("주식회사 창고43 시청점") == "창고43시청점"


def test_natural_key_is_stable() -> None:
    assert natural_key("창고43 시청점", "서울특별시 중구 서소문로 120") == natural_key(
        "창고43 시청점", "서울특별시 중구 서소문로 120"
    )


def test_extracts_road_address_part() -> None:
    assert road_address_part("서울특별시 중구 서소문로 120") == "서울 중구"
