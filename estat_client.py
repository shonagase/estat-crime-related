"""e-Stat API 3.0: 統計表をページングして全セル取得する。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

API = "https://api.e-stat.go.jp/rest/3.0/app/json"
LIMIT = 100_000
SLEEP_SEC = 0.4
MAX_RETRY = 5


class EstatError(RuntimeError):
    pass


def _get(url: str, *, timeout: int = 120) -> dict[str, Any]:
    last: Exception | None = None
    for i in range(MAX_RETRY):
        try:
            res = requests.get(url, timeout=timeout)
            res.raise_for_status()
            data = res.json()
            return data
        except (requests.RequestException, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(1.5 * (i + 1))
    raise EstatError(f"request failed: {url}: {last}") from last


def _status_ok(block: dict[str, Any] | None) -> None:
    if not block:
        raise EstatError("empty RESULT")
    status = block.get("STATUS")
    if str(status) not in {"0"}:
        raise EstatError(json.dumps(block, ensure_ascii=False))


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def fetch_meta(app_id: str, stats_data_id: str) -> dict[str, dict[str, dict[str, str]]]:
    """CLASS_OBJ id -> {code: {name, unit}}"""
    url = (
        f"{API}/getMetaInfo?appId={app_id}&lang=J"
        f"&statsDataId={stats_data_id}"
    )
    data = _get(url)
    _status_ok(data.get("GET_META_INFO", {}).get("RESULT"))
    objs = _as_list(
        data.get("GET_META_INFO", {})
        .get("METADATA_INF", {})
        .get("CLASS_INF", {})
        .get("CLASS_OBJ")
    )
    out: dict[str, dict[str, dict[str, str]]] = {}
    for obj in objs:
        oid = str(obj.get("@id") or "")
        mapping: dict[str, dict[str, str]] = {}
        for cls in _as_list(obj.get("CLASS")):
            code = str(cls.get("@code") or "")
            mapping[code] = {
                "name": str(cls.get("@name") or ""),
                "unit": str(cls.get("@unit") or ""),
                "level": str(cls.get("@level") or ""),
            }
        out[oid] = mapping
    return out


def fetch_table(app_id: str, stats_data_id: str) -> pd.DataFrame:
    meta = fetch_meta(app_id, stats_data_id)
    cat01 = meta.get("cat01", {})
    area = meta.get("area", {})
    time_map = meta.get("time", {})

    rows: list[dict[str, Any]] = []
    start = 1
    total = None
    while True:
        url = (
            f"{API}/getStatsData?appId={app_id}&lang=J"
            f"&statsDataId={stats_data_id}"
            f"&metaGetFlg=N&cntGetFlg=N&sectionHeaderFlg=1"
            f"&limit={LIMIT}&startPosition={start}"
        )
        data = _get(url)
        block = data.get("GET_STATS_DATA", {})
        _status_ok(block.get("RESULT"))
        info = block.get("STATISTICAL_DATA", {}).get("RESULT_INF", {})
        if total is None:
            total = int(info.get("TOTAL_NUMBER") or 0)
            print(f"  {stats_data_id}: total={total:,} cells")

        values = _as_list(
            block.get("STATISTICAL_DATA", {}).get("DATA_INF", {}).get("VALUE")
        )
        for v in values:
            code = str(v.get("@cat01") or "")
            area_code = str(v.get("@area") or "")
            time_code = str(v.get("@time") or "")
            raw = v.get("$")
            num = pd.to_numeric(str(raw).replace(",", ""), errors="coerce")
            cat = cat01.get(code, {})
            ar = area.get(area_code, {})
            tm = time_map.get(time_code, {})
            rows.append(
                {
                    "stats_data_id": stats_data_id,
                    "item_code": code,
                    "item_name": cat.get("name", ""),
                    "unit": v.get("@unit") or cat.get("unit") or "",
                    "area_code": area_code,
                    "area_name": ar.get("name", ""),
                    "time_code": time_code,
                    "time_name": tm.get("name", ""),
                    "value": num,
                }
            )

        to_n = int(info.get("TO_NUMBER") or start + len(values) - 1)
        next_key = info.get("NEXT_KEY")
        print(f"  fetched {to_n:,}/{total:,}")
        if not next_key:
            break
        start = int(next_key)
        time.sleep(SLEEP_SEC)

    return pd.DataFrame(rows)


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
