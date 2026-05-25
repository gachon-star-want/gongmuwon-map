from io import BytesIO

from openpyxl import Workbook

from public_officer_pipeline.extractor import extract_spreadsheet_rows


def test_extracts_gangnam_xlsx_rows() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "공개"
    worksheet.append(["2026년 4월 업무추진비 집행내역"])
    worksheet.append(["□ 부서명 : 지방소득세과"])
    worksheet.append([])
    worksheet.append(["연번", "집행일자", "집행시간", "사용자", "장소", "집행 목적", "대상 인원수", "금액", "결제방법", "비목"])
    worksheet.append(
        [
            1,
            "2026-04-30",
            "19:47:37",
            "지방소득세과장",
            "남도사계고운님",
            "세무서 업무 협의",
            6,
            121000,
            "카드결제",
            "시책",
        ]
    )
    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="강남구청")

    assert len(rows) == 1
    assert rows[0].department_name == "지방소득세과"
    assert rows[0].place_text == "남도사계고운님"
    assert rows[0].amount == 121000
    assert rows[0].user_text == "지방소득세과장 6명"


def test_extracts_council_cost_xlsx_header_variants() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "부의장"
    worksheet.append(["부의장 활동비 집행내역(4월)"])
    worksheet.append([])
    worksheet.append(["사용자", "일 자", "시간", "집행처 명", "집행내역", "집행처 주소", "집행방법", "금액", "인원", "비고"])
    worksheet.append(
        [
            "이충현",
            "2026-04-01",
            "12:29",
            "당진아구동태찜탕",
            "의정활동설명 및 민원청취",
            "양천구 등촌로 182",
            "법인카드",
            55000,
            4,
            None,
        ]
    )
    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="강서구의회")

    assert len(rows) == 1
    assert rows[0].place_text == "당진아구동태찜탕 (양천구 등촌로 182)"
    assert rows[0].purpose == "의정활동설명 및 민원청취"
    assert rows[0].payment_method == "법인카드"
    assert rows[0].user_text == "이충현 4명"


def test_extracts_council_cost_xlsx_two_row_headers() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "집행내역"
    worksheet.append(["2026년 4월 의장단 업무추진비 집행내역"])
    worksheet.append(
        [
            "연번",
            "비목",
            "집행부서",
            "사용자",
            "집행일시",
            None,
            "집행금액\n(원)",
            "집행장소",
            None,
            "집행내역",
            "대상\n인원수",
            "결제방법",
        ]
    )
    worksheet.append([None, None, None, None, "일자", "시간", None, "상호명", "주소", None, None, None])
    worksheet.append(
        [
            1,
            "의회운영업무추진비",
            "관악구의회",
            "의장",
            "2026.04.01",
            "13:12",
            19000,
            "만리장성",
            "서울특별시 관악구 관악로 146",
            "의정활동 및 의회운영 관련 업무유대 경비",
            2,
            "신용카드",
        ]
    )
    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="관악구의회")

    assert len(rows) == 1
    assert rows[0].place_text == "만리장성 (서울특별시 관악구 관악로 146)"
    assert rows[0].amount == 19000
    assert rows[0].purpose == "의정활동 및 의회운영 관련 업무유대 경비"
    assert rows[0].user_text == "의장 2명"


def test_extracts_council_cost_xlsx_approval_amount_header() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "지출내역"
    worksheet.append(["2026년 3월 의장단 업무추진비 집행내역"])
    worksheet.append([])
    worksheet.append(["연번", "일자", "시간", "승인금액", "장소", "주소", "내역", "대상인원", "결제방법", "사용자"])
    worksheet.append(
        [
            1,
            "2026-03-04",
            "12:27:40",
            78000,
            "보승회관 구로구청점",
            "서울특별시 구로구 구로중앙로 68",
            "지역 현안 의견청취를 위한 간담회",
            6,
            "카드",
            "정대근",
        ]
    )
    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="구로구의회")

    assert len(rows) == 1
    assert rows[0].amount == 78000
    assert rows[0].place_text == "보승회관 구로구청점 (서울특별시 구로구 구로중앙로 68)"
    assert rows[0].user_text == "정대근 6명"


def test_extracts_council_cost_xlsx_short_merchant_and_party_headers() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "의장"
    worksheet.append(["의회명", "구분", "사용일", "사용일시", "상호", "주소", "집행목적", "사용금액(원)", "인원수", "결제방법"])
    worksheet.append(
        [
            "도봉구의회",
            "의장",
            "2026-01-05",
            "12:22:35",
            "은행골",
            "서울 도봉구 도봉동 635번지",
            "지방의회 운영 방향 등 정책논의 간담회",
            180000,
            9,
            "카드",
        ]
    )
    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="도봉구의회")

    assert len(rows) == 1
    assert rows[0].place_text == "은행골 (서울 도봉구 도봉동 635번지)"
    assert rows[0].amount == 180000
    assert rows[0].user_text == "의장 9명"


def test_extracts_council_cost_xlsx_duplicate_execution_type_headers() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "의장"
    worksheet.append(["의장 업무추진비 집행내역"])
    worksheet.append([])
    worksheet.append(["구분", "사용자", "집행일", "집행유형", "집행구분", "집행대상", "집행인원", "집행액(천원)", "장소", "시간", "집행유형"])
    worksheet.append(
        [
            "의회운영",
            "의장",
            "2026-03-03",
            "업무추진을 위한 각종 회의·간담회·행사·교육",
            "식사",
            "의장, 의원",
            4,
            54000,
            "속초명가",
            "13:28",
            "카드",
        ]
    )
    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="서대문구의회")

    assert len(rows) == 1
    assert rows[0].place_text == "속초명가"
    assert rows[0].purpose == "업무추진을 위한 각종 회의·간담회·행사·교육"
    assert rows[0].amount == 54000
    assert rows[0].payment_method == "카드"
    assert rows[0].expense_category == "의회운영"


def test_extracts_xlsx_with_combined_datetime_and_party_size_aliases() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["연번", "사용자", "일시", "장소", "집행목적", "대상인원수", "금액", "결제", "비목"])
    worksheet.append(
        [
            1,
            "체육정책팀",
            "2026-04-01 12:13:00",
            "추오정남원추어탕",
            "양천마라톤 대회 관련 관계자 간담회 비용 지급",
            6,
            54000,
            "신용카드",
            "시책",
        ]
    )

    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="양천구청")

    assert len(rows) == 1
    assert rows[0].place_text == "추오정남원추어탕"
    assert rows[0].used_at.isoformat() == "2026-04-01T12:13:00"
    assert rows[0].amount == 54000
    assert rows[0].user_text == "체육정책팀 6명"


def test_extracts_xlsx_short_year_datetime_as_2000s_year() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["연번", "사용일시", "장소", "집행목적", "금액", "결제방법"])
    worksheet.append([1, "26.04.30, 13:38", "동트팔팔장어", "간담회", 120000, "카드"])

    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="노원구청")

    assert len(rows) == 1
    assert rows[0].used_at.isoformat() == "2026-04-30T13:38:00"
    assert rows[0].place_text == "동트팔팔장어"


def test_extracts_xlsx_short_year_datetime_first_day_without_dateutil_flip() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["연번", "사용일시", "장소", "집행목적", "금액", "결제방법"])
    worksheet.append([1, "26.04.01, 17:00", "노원어르신행복 주식", "간담회", 90000, "카드"])

    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="노원구청")

    assert len(rows) == 1
    assert rows[0].used_at.isoformat() == "2026-04-01T17:00:00"
    assert rows[0].place_text == "노원어르신행복 주식"


def test_extracts_council_cost_xlsx_approval_date_headers_without_place() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "의원회의"
    worksheet.append(["의장단 집행내역"])
    worksheet.append(["구분", "승인일", "승인시각", "승인금액", "대상인원", "집행내역", "결제방법"])
    worksheet.append(
        [
            "의장",
            "2026-01-02 00:00:00",
            "1970-01-01 11:25:19",
            110000,
            5,
            "더불어민주당 의원 간담회",
            "카드결제",
        ]
    )

    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="노원구의회 의장단")

    assert len(rows) == 1
    assert rows[0].place_text == "더불어민주당 의원 간담회"
    assert rows[0].user_text == "의장 5명"
    assert rows[0].amount == 110000
