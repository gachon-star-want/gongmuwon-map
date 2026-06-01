from pathlib import Path

from public_officer_pipeline.entity import (
    DefaultPlaceResolutionPolicy,
    KakaoResolver,
    classify_large_chain_brand,
    is_valid_place_name,
    normalize_name,
    natural_key,
    road_address_part,
)
from public_officer_pipeline.models import PlaceRaw


def test_normalize_name_removes_company_noise() -> None:
    assert normalize_name("주식회사 창고43 시청점") == "창고43시청점"


def test_natural_key_is_stable() -> None:
    assert natural_key("창고43 시청점", "서울특별시 중구 서소문로 120") == natural_key(
        "창고43 시청점", "서울특별시 중구 서소문로 120"
    )


def test_road_address_part_handles_regional_formats() -> None:
    assert road_address_part("서울특별시 중구 서소문로 120") == "서울 중구"
    assert road_address_part("경기도 수원시 팔달구 ...") == "경기 수원시"
    assert road_address_part("인천광역시 강화군 ...") == "인천 강화군"


def test_choose_best_prefers_fd6_category() -> None:
    policy = DefaultPlaceResolutionPolicy()

    place = PlaceRaw(name="반가안동국시", address_hint="서울 중구")
    documents = [
        {"id": "1", "category_group_code": "AT4", "place_name": "후보"},
        {"id": "2", "category_group_code": "FD6", "place_name": "식당"},
        {"id": "3", "category_group_code": "FD6", "place_name": "다른"},
    ]

    best = policy.choose_best_kakao_document(place, documents)
    assert best == documents[1]


def test_cache_hit_and_ttl_refresh_behavior(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.db"
    resolver = KakaoResolver(
        kakao_rest_key="test",
        allow_unmatched_fallback=True,
        cache_path=cache_path,
    )
    place = PlaceRaw(name="반가안동국시", address_hint="서울 중구 서소문로")
    cache_key = f"{place.name}|{place.address_hint or ''}"

    assert resolver._cache_get(cache_key) is None
    payload = (
        resolver.policy.fallback(place, latitude=37.5665, longitude=126.978).model_dump_json()
    )
    resolver._cache_set(cache_key, payload)
    assert resolver._cache_get(cache_key) == payload

    base_time = resolver._now_ts()
    resolver._now_ts = lambda: base_time + 60 * 60 * 24 * 8
    assert resolver._cache_get(cache_key) is None


def test_policy_uses_fallback_key_with_coordinates_when_address_coordinates_exist() -> None:
    place = PlaceRaw(name="반가안동국시", address_hint="서울 중구 서소문로 120")
    first = natural_key(place.name, place.address_hint, 37.5665, 126.978)
    second = natural_key(place.name, place.address_hint, 37.5665, 126.978)
    assert first == second


def test_placeholder_place_names_are_not_valid_place_candidates() -> None:
    for value in ("", "-", "unknown", "none", "N/A", "정보 없음", "미상", "해당없음", "없음", "장소 없음", "불명"):
        assert is_valid_place_name(value) is False

    assert is_valid_place_name("반가안동국시") is True


def test_policy_classifies_large_national_chain_candidates() -> None:
    assert classify_large_chain_brand("스타벅스 코리아") == "스타벅스"
    assert classify_large_chain_brand("파리바게뜨 종로구청점") == "파리바게뜨"
    assert classify_large_chain_brand("동네식당") is None


def test_kakao_document_sets_public_exposure_flags() -> None:
    policy = DefaultPlaceResolutionPolicy()
    resolved = policy.from_kakao_document(
        PlaceRaw(name="스타벅스 코리아", address_hint="서울 중구"),
        {
            "id": "chain-1",
            "place_name": "스타벅스 코리아",
            "category_group_code": "FD6",
            "category_name": "음식점 > 카페",
            "road_address_name": "서울특별시 중구 세종대로 1",
            "x": "126.978",
            "y": "37.5665",
        },
    )

    assert resolved.valid_place is True
    assert resolved.is_restaurant_like is True
    assert resolved.is_chain is True
    assert resolved.is_large_chain is True
    assert resolved.chain_brand == "스타벅스"
    assert resolved.chain_scale == "대형전국체인"


def test_non_food_kakao_document_is_not_restaurant_like() -> None:
    policy = DefaultPlaceResolutionPolicy()
    resolved = policy.from_kakao_document(
        PlaceRaw(name="문구점", address_hint="서울 중구"),
        {
            "id": "store-1",
            "place_name": "문구점",
            "category_group_code": "CS2",
            "category_name": "소매 > 문구",
            "road_address_name": "서울특별시 중구 세종대로 1",
        },
    )

    assert resolved.valid_place is True
    assert resolved.is_restaurant_like is False
