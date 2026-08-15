#!/usr/bin/env python3
"""e-Stat から市区町村の犯罪関連統計を表ごと全件取得する。

必要な環境変数:
  ESTAT_APP_ID   https://www.e-stat.go.jp/api/ で発行

例:
  python fetch_estat.py --profile crime-related
  python fetch_estat.py --profile core
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from catalog import TABLES, resolve_tables
from estat_client import fetch_table, save_parquet

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        default="crime-related",
        choices=("core", "crime-related"),
        help="core=人口/所得/教育/労働/犯罪。crime-related=居住・福祉・娯楽も表ごと追加",
    )
    parser.add_argument("--force", action="store_true", help="既存 parquet を取り直す")
    parser.add_argument(
        "--tables",
        nargs="*",
        default=None,
        help="統計表IDを直接指定（省略時は profile）",
    )
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    app_id = os.environ.get("ESTAT_APP_ID", "").strip()
    if not app_id:
        print("ESTAT_APP_ID が未設定です。.env か環境変数に入れてください。", file=sys.stderr)
        print("発行: https://www.e-stat.go.jp/api/", file=sys.stderr)
        return 1

    table_ids = args.tables or resolve_tables(args.profile)
    unknown = [t for t in table_ids if t not in TABLES]
    if unknown:
        print(f"catalog に無い表ID: {unknown}", file=sys.stderr)
        return 1
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "source": "e-Stat API 3.0 / 社会・人口統計体系 00200502",
        "tables": {},
    }

    frames = []
    for tid in table_ids:
        meta = TABLES[tid]
        out_path = RAW / f"{tid}.parquet"
        print(f"\n== {tid} {meta['field']} {meta['name']} ({meta['kind']})")
        print(f"   {meta['why']}")
        if out_path.exists() and not args.force:
            print(f"   skip (exists) {out_path}")
            import pandas as pd

            df = pd.read_parquet(out_path)
        else:
            df = fetch_table(app_id, tid)
            df["field"] = meta["field"]
            df["table_name"] = meta["name"]
            df["kind"] = meta["kind"]
            save_parquet(df, out_path)
            print(f"   saved {len(df):,} rows -> {out_path}")

        manifest["tables"][tid] = {
            **{k: meta[k] for k in ("field", "name", "kind", "why")},
            "rows": int(len(df)),
            "items": int(df["item_code"].nunique()) if len(df) else 0,
            "areas": int(df["area_code"].nunique()) if len(df) else 0,
            "times": int(df["time_code"].nunique()) if len(df) else 0,
            "path": str(out_path.relative_to(ROOT)),
        }
        frames.append(df)

    import pandas as pd

    long_df = pd.concat(frames, ignore_index=True)
    long_path = PROCESSED / "municipal_long.parquet"
    save_parquet(long_df, long_path)

    latest = (
        long_df.sort_values("time_code")
        .groupby(["stats_data_id", "item_code", "area_code"], as_index=False)
        .tail(1)
    )
    latest_path = PROCESSED / "municipal_latest.parquet"
    save_parquet(latest, latest_path)

    man_path = PROCESSED / "manifest.json"
    manifest["long_rows"] = int(len(long_df))
    manifest["latest_rows"] = int(len(latest))
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nlong: {len(long_df):,} -> {long_path}")
    print(f"latest: {len(latest):,} -> {latest_path}")
    print(f"manifest: {man_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
