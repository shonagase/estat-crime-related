"""市区町村・社会・人口統計体系（廃置分合処理済）の取得カタログ。

項目を1つに絞らず、表単位で全 cat01 を取る。
犯罪そのものに加え、実証研究で共変しやすい人口・所得・労働・教育・居住・福祉も含む。
"""

from __future__ import annotations

# 基礎データ（廃置分合処理済）00000202xx / 指標 00000203xx
# A=01 … K=11
TABLES = {
    "0000020201": {
        "field": "A",
        "name": "人口・世帯",
        "kind": "basic",
        "themes": ("population",),
        "why": "総人口・年齢・単独世帯・昼間人口など。犯罪率の分母と都市化の共変量。",
    },
    "0000020203": {
        "field": "C",
        "name": "経済基盤",
        "kind": "basic",
        "themes": ("income", "establishments"),
        "why": "課税対象所得、事業所・従業者。飲食・商業密度の公式値。",
    },
    "0000020204": {
        "field": "D",
        "name": "行政基盤",
        "kind": "basic",
        "themes": ("income", "fiscal"),
        "why": "課税・財政。1人当たり所得の元データ。",
    },
    "0000020205": {
        "field": "E",
        "name": "教育",
        "kind": "basic",
        "themes": ("education",),
        "why": "学校・進学・最終学歴。社会解体理論でよく置く共変量。",
    },
    "0000020206": {
        "field": "F",
        "name": "労働",
        "kind": "basic",
        "themes": ("unemployment", "labor"),
        "why": "労働力・完全失業者・産業別就業者。",
    },
    "0000020207": {
        "field": "G",
        "name": "文化・スポーツ",
        "kind": "basic",
        "themes": ("amenity",),
        "why": "娯楽・集会施設。繁華街・滞在機会の代理。",
    },
    "0000020208": {
        "field": "H",
        "name": "居住",
        "kind": "basic",
        "themes": ("housing",),
        "why": "持ち家・借家・空き家。監視・流動の代理。",
    },
    "0000020210": {
        "field": "J",
        "name": "福祉・社会保障",
        "kind": "basic",
        "themes": ("welfare",),
        "why": "生活保護等。都市化と共変しやすい。原因としては使わない。",
    },
    "0000020211": {
        "field": "K",
        "name": "安全",
        "kind": "basic",
        "themes": ("crime",),
        "why": "刑法犯・窃盗などの件数（犯罪の本体）。",
    },
    "0000020301": {
        "field": "A",
        "name": "人口・世帯（指標）",
        "kind": "indicator",
        "themes": ("population",),
        "why": "高齢化率・単独世帯割合など人口あたり。",
    },
    "0000020303": {
        "field": "C",
        "name": "経済基盤（指標）",
        "kind": "indicator",
        "themes": ("income", "establishments"),
        "why": "産業構成比など。",
    },
    "0000020304": {
        "field": "D",
        "name": "行政基盤（指標）",
        "kind": "indicator",
        "themes": ("income",),
        "why": "納税義務者1人当たり課税対象所得。",
    },
    "0000020305": {
        "field": "E",
        "name": "教育（指標）",
        "kind": "indicator",
        "themes": ("education",),
        "why": "進学率・最終学歴割合。",
    },
    "0000020306": {
        "field": "F",
        "name": "労働（指標）",
        "kind": "indicator",
        "themes": ("unemployment", "labor"),
        "why": "完全失業率・産業別就業者比率。",
    },
    "0000020308": {
        "field": "H",
        "name": "居住（指標）",
        "kind": "indicator",
        "themes": ("housing",),
        "why": "持ち家率など。",
    },
    "0000020310": {
        "field": "J",
        "name": "福祉・社会保障（指標）",
        "kind": "indicator",
        "themes": ("welfare",),
        "why": "保護率など。",
    },
    "0000020311": {
        "field": "K",
        "name": "安全（指標）",
        "kind": "indicator",
        "themes": ("crime",),
        "why": "刑法犯・窃盗の人口あたり、検挙率、罪種構成比。",
    },
}

# ユーザー指定5テーマ（表の全項目）
PROFILE_CORE = (
    "0000020201",  # 人口 基礎
    "0000020203",  # 所得・事業所 基礎
    "0000020205",  # 教育 基礎
    "0000020206",  # 失業・労働 基礎
    "0000020211",  # 犯罪件数 基礎
    "0000020301",  # 人口 指標
    "0000020304",  # 1人当たり所得
    "0000020305",  # 教育 指標
    "0000020306",  # 完全失業率
    "0000020311",  # 犯罪率
)

# 犯罪関連を表単位で網羅（居住・福祉・娯楽・経済指標も）
PROFILE_CRIME_RELATED = PROFILE_CORE + (
    "0000020204",
    "0000020207",
    "0000020208",
    "0000020210",
    "0000020303",
    "0000020308",
    "0000020310",
)

PROFILES = {
    "core": PROFILE_CORE,
    "crime-related": PROFILE_CRIME_RELATED,
}


def resolve_tables(profile: str) -> list[str]:
    if profile not in PROFILES:
        raise ValueError(f"unknown profile: {profile}. choose {list(PROFILES)}")
    # 重複排除・定義順
    seen: set[str] = set()
    out: list[str] = []
    for tid in PROFILES[profile]:
        if tid in TABLES and tid not in seen:
            seen.add(tid)
            out.append(tid)
    return out
