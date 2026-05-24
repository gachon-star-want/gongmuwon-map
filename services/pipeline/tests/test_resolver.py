from pathlib import Path

from public_officer_pipeline.entity import KakaoResolver, normalize_name, natural_key
from public_officer_pipeline.entity.resolver import road_address_part
from public_officer_pipeline.models import PlaceRaw


def test_normalize_name_removes_company_noise() -> None:
    assert normalize_name("주식회사 창고43 시청점") == "창고43시청점"


def test_natural_key_is_stable() -> None:
    assert natural_key("창고43 시청점", "서울특별시 중구 서소문로 120") == natural_key(
        "창고43 시청점", "서울특별시 중구 서소문로 120"
    )


def test_extracts_road_address_part() -> None:
    assert road_address_part("서울특별시 중구 서소문로 120") == "서울 중구"


def test_address_fallback_keeps_coordinates_without_place_match(tmp_path: Path) -> None:
    resolver = KakaoResolver(
        kakao_rest_key="test",
        allow_unmatched_fallback=True,
        cache_path=tmp_path / "cache.db",
    )

    resolved = resolver._from_kakao_address(
        PlaceRaw(name="반가안동국시", address_hint="서울 강남구 광평로46길 5"),
        {
            "address_name": "서울 강남구 수서동 715",
            "road_address": {"address_name": "서울 강남구 광평로46길 5", "x": "127.1000", "y": "37.4800"},
        },
    )

    assert resolved.kakao_place_id is None
    assert resolved.latitude == 37.48
    assert resolved.longitude == 127.1
    assert resolved.road_address_part == "서울 강남구"
