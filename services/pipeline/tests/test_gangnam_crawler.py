from public_officer_pipeline.crawler.gangnam import GangnamExpenseCrawler


def test_gangnam_crawler_extracts_download_refs() -> None:
    crawler = GangnamExpenseCrawler()

    refs = crawler._parse_list(
        """
        <table>
          <tr class="grid-item">
            <td class="num">9127</td>
            <td class="align-l tit"><a href="javascript:;">2026년 4월 업무추진비 집행내역 공개</a></td>
            <td class="fil">
              <a href="/file/1/get/sample/download.do" title="다운로드">download</a>
            </td>
            <td>지방소득세과</td>
            <td>2026-05-22</td>
          </tr>
        </table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == "https://www.gangnam.go.kr/file/1/get/sample/download.do"
    assert refs[0].department_name == "지방소득세과"
    assert refs[0].file_kind == "xlsx"
