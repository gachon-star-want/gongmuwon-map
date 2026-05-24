from public_officer_pipeline.normalizer import mask_user_text


def test_elected_official_can_keep_representative() -> None:
    result = mask_user_text("홍길동 시장 외 5명", fallback_department="시장실")

    assert result["representative"] == "홍길동"
    assert result["rank_label"] == "시장"
    assert result["party_size"] == 6


def test_appointed_official_name_is_not_kept() -> None:
    result = mask_user_text("박철수 국장(총무국) 외 2명", fallback_department="총무국")

    assert result["representative"] is None
    assert result["rank_label"] == "국장"
    assert result["party_size"] == 3


def test_staff_group_is_department_only() -> None:
    result = mask_user_text("총무과 직원 7명", fallback_department="총무과")

    assert result["representative"] is None
    assert result["rank_label"] == "5급 이하"
    assert result["department_name"] == "총무과 외"


def test_elected_rank_without_name_keeps_rank_only() -> None:
    result = mask_user_text("구의원 12명", fallback_department="구의회사무국")

    assert result["representative"] is None
    assert result["rank_label"] == "구의원"
    assert result["party_size"] == 12
