#!/usr/bin/env python3
# 99c_extra_canonical_pool_infect.py — 감염성·기생충성 질환 진료(INFECT, A00-B99) 가설 풀 추가 열(2026-11-09). 99c_mets 방식 복제.
#  ① 정본 basic_livelihood_recipient_rate(수급률): 2021-23 값 < 같은 시군구 2020·2024 평균의 20% → 결측 → 시군구 안 선형 보간(일반구 시 10곳 30칸 + 창원 3칸 명시, 33칸)
#  ② 정본 lic_public_baths_per10k(목욕장업 영업 인허가, 인구 1만 명당) — 공용 습윤 환경(족부 백선·사마귀 전파)
#  ③ 기온·강수(연평균, 기상 관측소 IDW 보간, 00_원천/climate_annual_IDW_229x2011_2024.csv ← FBD_SpatioTemporal/data_cache/climate_covariates_IDW.rds)
#     결합: 기후 region 이름 → 정본 대응표 region(=sigungu_cd 1:1) 집합 일치 assert 후 코드표 경유(이름 임의 결합 아님, 229/229 완전 일치만 허용)
#  출력 02_패널/EXT_canonical_pool_INFECT_261109.csv
import os, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, ".."))
ZD = os.environ.get("ST_CANON", os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/통합자료_261030"))
PAN = os.path.join(ROOT, "02_패널")
C = pd.read_csv(os.path.join(ZD, "01_공변량_229x2011_2024.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
K = pd.read_csv(os.path.join(ZD, "00_시군구_229_대응표.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str}); assert K.sigungu_cd.is_unique and len(K) == 229
K.loc[K.sigungu_cd == "37310", "region"] = "대구시군위군"; K["region"] = K.region.map(NFC)
C = C.drop(columns=["region"]).merge(K[["sigungu_cd", "region"]], on="sigungu_cd", how="left", validate="many_to_one"); assert C.region.notna().all()
out = pd.DataFrame({"year": C.year, "sigungu_cd": C.sigungu_cd, "fbd_region": C.region.map(NFC),
                    "basic_livelihood_rate": C.basic_livelihood_recipient_rate.astype(float),
                    "public_baths_per10k": C.lic_public_baths_per10k.astype(float)})
out = out[(out.year >= 2011) & (out.year <= 2024)].copy()
ref = out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean()
bad = out.year.isin([2021, 2022, 2023]) & ((out.basic_livelihood_rate < 0.2 * out.fbd_region.map(ref)) | (out.fbd_region == NFC("경상남도창원시")))
print("[99c-infect] 수급률 결함 칸", int(bad.sum()), sorted(out.loc[bad, "fbd_region"].unique()))
assert int(bad.sum()) == 33 and out.loc[bad, "fbd_region"].nunique() == 11, int(bad.sum())
out.loc[bad, "basic_livelihood_rate"] = np.nan
out = out.sort_values(["fbd_region", "year"])
out["basic_livelihood_rate"] = out.groupby("fbd_region").basic_livelihood_rate.transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
# ③ 기후
W = pd.read_csv(os.path.join(ROOT, "00_원천", "climate_annual_IDW_229x2011_2024.csv"), encoding="utf-8"); W["region"] = W.region.map(NFC)
W.loc[W.region == NFC("인천시미추홀구"), "region"] = NFC("인천시남구")
miss = set(W.region) ^ set(K.region); print("[99c-infect] 기후 이름-대응표 불일치", sorted(miss))
assert not miss, miss
W = W.merge(K[["region", "sigungu_cd"]], on="region", how="left", validate="many_to_one")
out = out.merge(W[["year", "sigungu_cd", "temp_annual", "precip_annual"]], on=["year", "sigungu_cd"], how="left", validate="one_to_one")
assert out.groupby("fbd_region").year.nunique().eq(14).all() and out.fbd_region.nunique() == 229 and not out.duplicated(["year", "fbd_region"]).any() and out.notna().all().all(), out.isna().sum()
# 데이터 게이트 보조: 이웃 연도 평균 대비 20% 미만·5배 초과 칸
for c in ["public_baths_per10k", "temp_annual", "precip_annual", "basic_livelihood_rate"]:
    s = out.sort_values(["fbd_region", "year"]).groupby("fbd_region")[c]; nb = (s.shift(1) + s.shift(-1)) / 2
    v = out.sort_values(["fbd_region", "year"])[c]; k = ((v < 0.2 * nb) | (v > 5 * nb)) & nb.notna()
    print(f"[99c-infect] {c}: 이웃 연도 대비 20%↓·5배↑ 칸 {int(k.sum())} · 범위 {v.min():.2f}~{v.max():.2f}")
fp = os.path.join(PAN, "EXT_canonical_pool_INFECT_261109.csv"); out[["year", "fbd_region", "basic_livelihood_rate", "public_baths_per10k", "temp_annual", "precip_annual"]].to_csv(fp, index=False, encoding="utf-8-sig")
print(f"[99c-infect] 저장 {fp} {out.shape}")
