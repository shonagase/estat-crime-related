# 市区町村 犯罪関連統計（e-Stat）

社会・人口統計体系の **表を項目単位で絞らず全件取得** し、リポジトリには **最新年断面だけ** を残します。

## リポジトリに載るもの

- `data/processed/municipal_latest.parquet` … 項目×市区町村の最新年のみ
- `data/processed/manifest.json` … 取得メタ

`data/raw/` と全年の `municipal_long.parquet` は Actions 上の作業用で、コミットしません。

## GitHub Actions

1. リポジトリ **Settings → Secrets and variables → Actions** に `ESTAT_APP_ID` を追加  
   （[e-Stat API](https://www.e-stat.go.jp/api/) で発行。くらし立地と同じ ID で可）
2. Actions タブで **Fetch e-Stat municipal latest** を手動実行（または毎月1日に自動）

## ローカル実行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # ESTAT_APP_ID を記入（.env はコミットしない）
python fetch_estat.py --profile crime-related
```

## 取得範囲（`--profile crime-related`）

| テーマ | 基礎（件数） | 指標（率） |
|---|---|---|
| 犯罪 | `0000020211` | `0000020311` |
| 人口 | `0000020201` | `0000020301` |
| 所得・事業所 | `0000020203` | `0000020303` / `0000020304` |
| 教育 | `0000020205` | `0000020305` |
| 失業・労働 | `0000020206` | `0000020306` |
| 居住 | `0000020208` | `0000020308` |
| 福祉 | `0000020210` | `0000020310` |
| 文化・スポーツ | `0000020207` | — |
| 行政基盤 | `0000020204` | — |

出典: 総務省 社会・人口統計体系（e-Stat）。政府の公式見解ではない加工データです。

## 相関分析（設計）

- [`analysis/DESIGN.md`](analysis/DESIGN.md) … 単位・Y・事業所ファミリーを含む X・手順
- [`analysis/item_dictionary.csv`](analysis/item_dictionary.csv) … コード辞書（Tier A1 に飲食・小売・娯楽・製造業など）
