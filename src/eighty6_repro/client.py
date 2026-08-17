"""eighty6 QCEW HTTP client: Bearer auth, pagination, 429, plan date chunking.

Production surface verified 2026-08-17:

- Account / key creation: https://www.eighty6data.com
- Working API base: https://www.eighty6data.com/api  (GET /health → healthy)
- OpenAPI: https://www.eighty6data.com/api/openapi.json
- Direct host api.eighty6data.com was not serving /health on that date

Every live QCEW row in this package comes from GET /v1/qcew/employment.
The API accepts one industry_code, area_fips, and agglvl_code per request.
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx

from eighty6_repro.config import DEFAULT_API_BASE, PLAN_LIMITS, USER_AGENT


class Eighty6APIError(RuntimeError):
    """HTTP or plan-limit error from the eighty6 API."""


@dataclass(frozen=True)
class Page:
    data: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
    has_more: bool


def load_settings(
    *,
    api_key: str | None = None,
    api_base: str | None = None,
    plan: str | None = None,
) -> tuple[str, str, str]:
    """Read key / base / plan from arguments or the environment.

    Loads a local `.env` if python-dotenv is available. Never prints the key.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    key = api_key if api_key is not None else os.environ.get("E86_API_KEY", "")
    base = (api_base or os.environ.get("E86_API_BASE") or DEFAULT_API_BASE).rstrip("/")
    chosen = (plan or os.environ.get("E86_PLAN") or "pro").strip().lower()
    if chosen not in PLAN_LIMITS:
        raise Eighty6APIError(f"Unknown E86_PLAN={chosen!r}; use basic or pro")
    return key, base, chosen


class Eighty6Client:
    """Thin client for GET /v1/qcew/employment."""

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        plan: str | None = None,
        *,
        timeout: float = 60.0,
        max_retries: int = 6,
    ) -> None:
        key, base, chosen = load_settings(api_key=api_key, api_base=api_base, plan=plan)
        self.api_key = key
        self.api_base = base
        self.plan = chosen
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url=base,
            timeout=timeout,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                **({"Authorization": f"Bearer {key}"} if key else {}),
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Eighty6Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def max_rows(self) -> int:
        return PLAN_LIMITS[self.plan]["max_rows"]

    @property
    def max_year_span(self) -> int:
        """Inclusive calendar-year span allowed by the plan date-range cap."""
        days = PLAN_LIMITS[self.plan]["max_date_range_days"]
        return 1 if days <= 365 else max(1, days // 365)

    def health(self) -> dict[str, Any]:
        r = self._request("GET", "/health")
        return r.json()

    def fetch_page(
        self,
        *,
        year: int | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        qtr: int | None = None,
        area_fips: str | None = None,
        industry_code: str | None = None,
        ownership_code: str | None = None,
        agglvl_code: str | None = None,
        size_code: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> Page:
        params: dict[str, Any] = {"offset": offset}
        if year is not None:
            params["year"] = year
        if start_year is not None:
            params["start_year"] = start_year
        if end_year is not None:
            params["end_year"] = end_year
        if qtr is not None:
            params["qtr"] = qtr
        if area_fips:
            params["area_fips"] = area_fips
        if industry_code:
            params["industry_code"] = industry_code
        if ownership_code:
            params["ownership_code"] = ownership_code
        if agglvl_code:
            params["agglvl_code"] = agglvl_code
        if size_code:
            params["size_code"] = size_code
        params["limit"] = min(limit or self.max_rows, self.max_rows)

        r = self._request("GET", "/v1/qcew/employment", params=params)
        body = r.json()
        return Page(
            data=list(body.get("data") or []),
            total=int(body.get("total") or 0),
            limit=int(body.get("limit") or params["limit"]),
            offset=int(body.get("offset") or offset),
            has_more=bool(body.get("has_more")),
        )

    def iter_pages(self, **kwargs: Any) -> Iterator[Page]:
        """Yield pages until has_more is false."""
        offset = int(kwargs.pop("offset", 0))
        while True:
            page = self.fetch_page(offset=offset, **kwargs)
            yield page
            if not page.has_more:
                return
            offset = page.offset + page.limit

    def iter_all_rows(self, **kwargs: Any) -> Iterator[dict[str, Any]]:
        for page in self.iter_pages(**kwargs):
            yield from page.data

    def year_chunks(self, start_year: int, end_year: int) -> list[tuple[int, int]]:
        """Split an inclusive year range so each chunk fits the plan date cap."""
        span = self.max_year_span
        chunks: list[tuple[int, int]] = []
        y = start_year
        while y <= end_year:
            chunks.append((y, min(y + span - 1, end_year)))
            y += span
        return chunks

    def _request(
        self, method: str, path: str, *, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                r = self._client.request(method, path, params=params)
            except httpx.HTTPError as exc:
                last_exc = exc
                time.sleep(min(2**attempt, 30))
                continue
            if r.status_code == 429:
                wait = _retry_after_seconds(r, default=min(2**attempt, 30))
                time.sleep(wait)
                continue
            if r.status_code >= 500:
                time.sleep(min(2**attempt, 30))
                last_exc = Eighty6APIError(f"{r.status_code} {path}")
                continue
            if r.status_code >= 400:
                detail = _safe_detail(r)
                raise Eighty6APIError(f"{r.status_code} {path}: {detail}")
            return r
        raise Eighty6APIError(f"exhausted retries for {path}: {last_exc}")


def _retry_after_seconds(r: httpx.Response, default: float) -> float:
    raw = r.headers.get("Retry-After")
    if not raw:
        return default
    try:
        return max(float(raw), 0.5)
    except ValueError:
        return default


def _safe_detail(r: httpx.Response) -> str:
    try:
        body = r.json()
        return str(body.get("detail", body))[:400]
    except Exception:
        return (r.text or r.reason_phrase)[:400]


def mask_key(key: str) -> str:
    """Show only prefix and last four characters."""
    if not key:
        return "(missing)"
    if len(key) <= 8:
        return key[:4] + "…"
    return f"{key[:4]}…{key[-4:]}"
