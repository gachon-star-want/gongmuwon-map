from __future__ import annotations

from typing import Any

import httpx

KOSIS_DATA_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"


class KosisError(RuntimeError):
    pass


class KosisClient:
    """KOSIS(국가통계포털) OpenAPI 클라이언트.

    가구원수별 가구는 DT_1JC1502(읍면동, org 101). 지역코드 C1 은 SGIS adm_cd 와
    동일한 통계청 코드라 매핑 없이 조인된다(ADR-016).
    """

    def __init__(self, api_key: str | None, *, client: httpx.AsyncClient | None = None) -> None:
        if not api_key:
            raise KosisError("KOSIS_API_KEY is required")
        self._key = api_key
        self._client = client or httpx.AsyncClient(timeout=60.0)
        self._owns_client = client is None

    async def household_by_size(
        self,
        *,
        org_id: str = "101",
        tbl_id: str = "DT_1JC1502",
    ) -> list[dict[str, Any]]:
        """전국 읍면동 가구원수별 가구(최신 1시점). 행: {C1, ITM_ID, DT, ...}."""
        params = {
            "method": "getList",
            "apiKey": self._key,
            "orgId": org_id,
            "tblId": tbl_id,
            "itmId": "T0+T1+T2+T3+T4+T5+T8",  # 계/1/2/3/4/5/6인이상
            "objL1": "ALL",
            "prdSe": "Y",
            "newEstPrdCnt": "1",
            "format": "json",
            "jsonVD": "Y",
        }
        resp = await self._client.get(KOSIS_DATA_URL, params=params)
        try:
            data = resp.json()
        except ValueError as exc:
            raise KosisError(f"non-JSON response: {resp.text[:160]}") from exc
        if isinstance(data, dict):
            # KOSIS 오류는 dict({err, errMsg}) 형태로 반환
            raise KosisError(f"KOSIS error: {data}")
        return data

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
