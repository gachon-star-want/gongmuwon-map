import zipfile
from io import BytesIO

from public_officer_pipeline.extractor import extract_hwpx_rows


def _hwpx_bytes(section_xml: str) -> bytes:
    content = BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("mimetype", b"application/hwp+zip")
        archive.writestr("Contents/section0.xml", section_xml.encode("utf-8"))
    return content.getvalue()


def test_extracts_hwpx_table_rows() -> None:
    section_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <hs:sec
      xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"
      xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">
      <hp:p><hp:run><hp:t>(도시주택국 도시계획과)</hp:t></hp:run></hp:p>
      <hp:tbl>
        <hp:tr>
          <hp:tc><hp:cellAddr colAddr="0"/><hp:t>연번</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="1"/><hp:t>사용자</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="2"/><hp:t>사용일자</hp:t><hp:t>(일시)</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="3"/><hp:t>사용장소</hp:t><hp:t>(상호명)</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="4"/><hp:t>집행목적(내역)</hp:t><hp:t>* 사용대상 포함</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="5"/><hp:t>대상</hp:t><hp:t>인원(명)</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="6"/><hp:t>금액(원)</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="7"/><hp:t>결제방법</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="8"/><hp:t>비목</hp:t></hp:tc>
        </hp:tr>
        <hp:tr>
          <hp:tc><hp:cellAddr colAddr="0"/><hp:t>1</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="1"/><hp:t>도시계획과장</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="2"/><hp:t>2026-04-24</hp:t><hp:t>(12:32)</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="3"/><hp:t>지베</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="4"/><hp:t>도시계획위원회 개최에 따른 다과비 지급</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="5"/><hp:t>15</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="6"/><hp:t>142,500</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="7"/><hp:t>카드</hp:t></hp:tc>
          <hp:tc><hp:cellAddr colAddr="8"/><hp:t>부서</hp:t></hp:tc>
        </hp:tr>
      </hp:tbl>
    </hs:sec>
    """

    rows = extract_hwpx_rows(_hwpx_bytes(section_xml), fallback_department="성남시청")

    assert len(rows) == 1
    assert rows[0].department_name == "도시주택국 도시계획과"
    assert rows[0].place_text == "지베"
    assert rows[0].purpose == "도시계획위원회 개최에 따른 다과비 지급"
    assert rows[0].amount == 142500
    assert rows[0].user_text == "도시계획과장 15명"
    assert rows[0].payment_method == "카드"
