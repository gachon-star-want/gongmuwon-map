from pathlib import Path
import pytest

from public_officer_pipeline.entity import (
    DefaultPlaceResolutionPolicy,
    KakaoResolver,
    classify_large_chain_brand,
    is_valid_place_name,
    normalize_name,
    natural_key,
    road_address_part,
)
from public_officer_pipeline.models import PlaceRaw, Agency, GovTier


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


@pytest.mark.asyncio
async def test_cache_hit_and_ttl_refresh_behavior(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.db"
    resolver = KakaoResolver(
        kakao_rest_key="test",
        allow_unmatched_fallback=True,
        cache_path=cache_path,
    )
    try:
        place = PlaceRaw(name="반가안동국시", address_hint="서울 중구 서소문로")
        cache_key = f"{place.name}|{place.address_hint or ''}"

        assert await resolver._cache_get(cache_key) is None
        payload = (
            resolver.policy.fallback(place, latitude=37.5665, longitude=126.978).model_dump_json()
        )
        await resolver._cache_set(cache_key, payload)
        assert await resolver._cache_get(cache_key) == payload

        base_time = resolver._now_ts()
        resolver._now_ts = lambda: base_time + 60 * 60 * 24 * 8
        assert await resolver._cache_get(cache_key) is None
    finally:
        await resolver.close()


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
    assert classify_large_chain_brand("뚜레쥬르 은평구청점") == "뚜레쥬르"
    assert classify_large_chain_brand("BBQ치킨 길동역점") == "BBQ"
    assert classify_large_chain_brand("BHC치킨 명동점") == "BHC"
    assert classify_large_chain_brand("교촌치킨 염창점") == "교촌치킨"
    assert classify_large_chain_brand("네네치킨 앤 봉구스밥버거 부안점") == "네네치킨"
    assert classify_large_chain_brand("굽네치킨 여주점") == "굽네치킨"
    assert classify_large_chain_brand("아웃백스테이크하우스 미아점") == "아웃백"
    assert classify_large_chain_brand("도미노피자 역삼점") == "도미노피자"
    assert classify_large_chain_brand("본죽 등촌역점") == "본죽"
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


def test_policy_validate_candidate_distance_rejection() -> None:
    from uuid import UUID
    policy = DefaultPlaceResolutionPolicy()
    
    # 서울특별시청 is at 37.566824, 126.978652
    agency = Agency(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name="서울특별시청",
        gov_tier=GovTier.REGIONAL,
    )
    
    # 1. Close candidate (e.g., 5km away, within 50km)
    # Let's say coordinates: 37.56, 126.97 (about 1km away)
    place = PlaceRaw(name="식당")
    doc_close = {
        "place_name": "식당",
        "x": "126.97",
        "y": "37.56",
    }
    assert policy.validate_candidate(place, doc_close, agency=agency) is True
    
    # 2. Far candidate (> 50km away, e.g. Busan: 35.1796, 129.0756)
    doc_far = {
        "place_name": "식당",
        "x": "129.0756",
        "y": "35.1796",
    }
    assert policy.validate_candidate(place, doc_far, agency=agency) is False
    
    # 3. Exception: Agency is national/constitutional
    national_agency = Agency(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name="서울특별시청",
        gov_tier=GovTier.NATIONAL,
    )
    assert policy.validate_candidate(place, doc_far, agency=national_agency) is True
    
    # 4. Large chain candidate is no longer exempt from distance check
    chain_doc_far = {
        "place_name": "스타벅스 부산점",
        "x": "129.0756",
        "y": "35.1796",
    }
    assert policy.validate_candidate(place, chain_doc_far, agency=agency) is False


@pytest.mark.asyncio
async def test_resolver_resolve_uses_coordinates_and_falls_back(tmp_path: Path) -> None:
    from unittest.mock import AsyncMock, MagicMock, patch
    from uuid import UUID
    
    resolver = KakaoResolver(
        kakao_rest_key="mock_key",
        allow_unmatched_fallback=True,
        cache_path=tmp_path / "test_cache.db",
    )
    
    agency = Agency(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        name="서울특별시청",
        gov_tier=GovTier.REGIONAL,
    )
    
    place = PlaceRaw(name="반가안동국시")
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response_address = MagicMock()
        mock_response_address.json.return_value = {"documents": []}
        
        mock_response_kakao_coords = MagicMock()
        mock_response_kakao_coords.json.return_value = {"documents": []}
        
        mock_response_kakao_fallback = MagicMock()
        mock_response_kakao_fallback.json.return_value = {
            "documents": [
                {
                    "id": "123",
                    "place_name": "반가안동국시",
                    "category_group_code": "FD6",
                    "x": "126.978",
                    "y": "37.5665",
                }
            ]
        }
        
        def get_side_effect(url, **kwargs):
            params = kwargs.get("params", {})
            if "address.json" in url:
                return mock_response_address
            elif "keyword.json" in url:
                if "x" in params:
                    return mock_response_kakao_coords
                else:
                    return mock_response_kakao_fallback
            return MagicMock()
            
        mock_get.side_effect = get_side_effect
        
        resolved = await resolver.resolve(place, agency=agency)
        
        assert resolved.matched is True
        assert resolved.kakao_place_id == "123"
        
        coords_call_found = False
        fallback_call_found = False
        for call in mock_get.call_args_list:
            args, kwargs = call
            url = args[0]
            params = kwargs.get("params", {})
            if "keyword.json" in url:
                if "x" in params and "y" in params and params.get("radius") == 20000:
                    coords_call_found = True
                    assert float(params["y"]) == 37.56682420267543
                    assert float(params["x"]) == 126.978652258823
                elif "x" not in params:
                    fallback_call_found = True
                    
        assert coords_call_found is True
        assert fallback_call_found is True

    await resolver.close()


def test_policy_validate_candidate_name_similarity() -> None:
    policy = DefaultPlaceResolutionPolicy()

    # 1. Matches with common Korean characters should be accepted
    place = PlaceRaw(name="반가안동국시")
    doc_match = {"place_name": "반가안동국시 시청점"}
    assert policy.validate_candidate(place, doc_match) is True

    # 2. Matches with disjoint Korean characters should be rejected
    doc_disjoint = {"place_name": "스타벅스 시청점"}
    assert policy.validate_candidate(place, doc_disjoint) is False

    # 3. Matches without Korean characters in one of the names should be accepted (pass-through)
    doc_english = {"place_name": "McDonalds"}
    assert policy.validate_candidate(place, doc_english) is True
