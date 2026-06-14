from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

DEFAULT_HOST = "https://sgisapi.mods.go.kr/OpenAPI3"


class SgisError(RuntimeError):
    pass


class SgisClient:
    """국가데이터처 SGIS OpenAPI3 클라이언트 (토큰 캐시 + 재시도).

    지역코드는 통계청 고유 adm_cd(시도2/시군구5/읍면동8)로, KOSIS와 동일하다(ADR-016).
    """

    def __init__(
        self,
        service_id: str | None,
        api_key: str | None,
        *,
        host: str = DEFAULT_HOST,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not service_id or not api_key:
            raise SgisError("SGIS_SERVICE_ID / SGIS_API_KEY are required")
        self._sid = service_id
        self._sec = api_key
        self._host = host.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._owns_client = client is None
        self._token: str | None = None
        self._token_exp = 0.0

    async def _ensure_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_exp - 60:
            return self._token
        resp = await self._client.get(
            f"{self._host}/auth/authentication.json",
            params={"consumer_key": self._sid, "consumer_secret": self._sec},
        )
        data = resp.json()
        if str(data.get("errCd")) != "0":
            raise SgisError(f"auth failed: errCd={data.get('errCd')} {data.get('errMsg')}")
        result = data.get("result") or {}
        token = result.get("accessToken")
        if not token:
            raise SgisError("auth returned no accessToken")
        self._token = token
        try:
            # accessTimeout 은 만료 시각(epoch ms)
            self._token_exp = float(result.get("accessTimeout", 0)) / 1000.0
        except (TypeError, ValueError):
            self._token_exp = now + 4 * 3600
        if self._token_exp <= now:
            self._token_exp = now + 4 * 3600
        return token

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        last: Exception | None = None
        for attempt in range(3):
            token = await self._ensure_token()
            params["accessToken"] = token
            try:
                resp = await self._client.get(f"{self._host}/{path}", params=params)
            except httpx.HTTPError as exc:
                last = exc
                await asyncio.sleep(1.0 * (2 ** attempt))
                continue
            try:
                data = resp.json()
            except ValueError as exc:
                raise SgisError(f"{path}: non-JSON response {resp.text[:160]}") from exc
            err = str(data.get("errCd")) if isinstance(data, dict) else None
            if err in ("0", "-100"):  # 0=success, -100=no result
                return data
            # 토큰 만료/기타 → 토큰 폐기 후 재시도
            self._token = None
            last = SgisError(f"{path}: errCd={err} {data.get('errMsg') if isinstance(data, dict) else ''}")
            await asyncio.sleep(0.5 * (2 ** attempt))
        raise last or SgisError(f"{path}: request failed")

    async def stage(self, cd: str | None = None) -> list[dict[str, Any]]:
        """행정구역 트리. cd 없으면 시도, cd=시도면 시군구, cd=시군구면 읍면동."""
        data = await self._get("addr/stage.json", **({"cd": cd} if cd else {}))
        return data.get("result") or []

    async def population(self, adm_cd: str, year: str, *, low_search: str = "1") -> list[dict[str, Any]]:
        data = await self._get("stats/population.json", year=year, adm_cd=adm_cd, low_search=low_search)
        return data.get("result") or []

    async def themamap(
        self,
        ctgr: str,
        stat_thema_map_id: str,
        adm_cd: str,
        year: str,
        *,
        region_div: str = "3",
    ) -> dict[str, float]:
        """통계주제도 데이터 → {adm_cd: value}. region_div 3=읍면동."""
        data = await self._get(
            f"themamap/{ctgr}/data.json",
            stat_thema_map_id=stat_thema_map_id,
            adm_cd=adm_cd,
            year=year,
            region_div=region_div,
        )
        result = data.get("result") or {}
        result_data = result.get("resultData") or []
        rows = result_data[0].get("data") if result_data else []
        out: dict[str, float] = {}
        for row in rows or []:
            cd = row.get("adm_cd")
            val = row.get("value")
            if cd is None or val in (None, ""):
                continue
            try:
                out[cd] = float(val)
            except (TypeError, ValueError):
                continue
        return out

    async def boundary(self, adm_cd: str, year: str, *, low_search: str = "1") -> dict[str, Any]:
        """행정경계 GeoJSON FeatureCollection (UTM-K / EPSG:5179). caller가 features 유무로 판단."""
        token = await self._ensure_token()
        resp = await self._client.get(
            f"{self._host}/boundary/hadmarea.geojson",
            params={"accessToken": token, "year": year, "adm_cd": adm_cd, "low_search": low_search},
        )
        try:
            return resp.json()
        except ValueError as exc:
            raise SgisError(f"boundary: non-JSON response {resp.text[:160]}") from exc

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
