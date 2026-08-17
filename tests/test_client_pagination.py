"""Pagination and plan-chunking tests (no live API)."""

from __future__ import annotations

from eighty6_repro.client import Eighty6Client, Page, mask_key


def test_mask_key_never_prints_full_token() -> None:
    assert "secret" not in mask_key("e86_" + "secret" + "token")
    assert mask_key("") == "(missing)"


def test_year_chunks_basic_is_one_year() -> None:
    client = Eighty6Client(api_key="", api_base="https://www.eighty6data.com/api", plan="basic")
    try:
        assert client.max_rows == 1000
        assert client.year_chunks(2014, 2016) == [(2014, 2014), (2015, 2015), (2016, 2016)]
    finally:
        client.close()


def test_year_chunks_pro_spans_decade() -> None:
    client = Eighty6Client(api_key="", api_base="https://www.eighty6data.com/api", plan="pro")
    try:
        assert client.max_rows == 10_000
        chunks = client.year_chunks(2014, 2025)
        assert chunks[0] == (2014, 2023)
        assert chunks[-1][1] == 2025
        assert all(b - a + 1 <= 10 for a, b in chunks)
    finally:
        client.close()


def test_page_dataclass() -> None:
    page = Page(data=[{"year": 2024}], total=12, limit=10, offset=0, has_more=True)
    assert page.has_more
    assert page.total == 12
