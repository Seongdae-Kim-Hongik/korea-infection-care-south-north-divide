#!/usr/bin/env python3
# 99I — 감염성·기생충성 질환 진료(A00-B99, 건보 진료실인원 "전염병(AB)") 공간 선별 std3·성×연령 준비(2026-11-09). 99L_screen_lca_std3_prep.py 복제.
#  ★성×연령: 298분류 전국 연령별 진료실인원(성별 없음)을 3단 상병(A00-B99) 전국 성별×5세 합의 연령대별 남성 비율로 나눔(00_원천/C_NHIS_3단상병, 99I_fetch). 2011-14는 2015 비율.
#  E_sexage = Σ_s,a 시군구 성·연령 인구(패널 offset × FBD 성·연령 비율) × 전국 성·연령 율 → 주 E. E_std2(연령만)은 비교용.
# (원 머리말) 99_screen_cancers_prep.py(11/5 std) 복제 + 39_build_Estd_fine.py 세분 E + 시리즈 std3 규칙.
#  std3(진료 자료판, PLAYBOOK §3-B 8·CRC/HCC config_*_std3.json과 같은 정의):
#   ① 인구: 창원 2023 = 1,009,038 교정(패널 population·offset, ST_FBDZIP 교정 사본의 시군구 5세 인구)
#   ② 연령 구간: 39의 세분 10구간 0-9 … 50-59·60-64·65-69·70-74·75+ (전국 진료 원자료 최상위가 전 연도 75세 이상 → 75+ 내부 표준화 불가)
#  rate[y,a] = 전국 감염병(A00-B99) 진료실인원 / Σ_d (패널 offset × FBD 연령 비율) ; E_std2 = Σ_a 분모 × rate, 연도별 ΣE = Σcases 재척도
#  산출(기존 파일 덮어쓰지 않음): 02_패널/INFECT_Estd2.csv, 02_패널/INFECT_national_agerates_std2.csv,
#  사용: ST_FBDZIP=$ST_FBDZIP_CORRECTED python3 99L_screen_lca_std3_prep.py
import os, sys, re, json, shutil, importlib.util, unicodedata
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석")
assert os.environ.get("ST_FBDZIP"), "ST_FBDZIP(창원 2023 교정 인구 폴더)를 지정"
def _load(nm, f):
    s = importlib.util.spec_from_file_location(nm, os.path.join(HERE, f)); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
m38 = _load("m38", "38_build_Estd_all.py"); cw = _load("cw", "40_region_crosswalk.py")
NFC = lambda s: unicodedata.normalize("NFC", str(s))
assert os.path.abspath(m38.FBDZIP) == os.path.abspath(os.environ["ST_FBDZIP"])
TAG, KO = "INFECT", "감염병"; CHANGWON = dict(year=2023, fbd_region="경상남도창원시", population=1009038)
AGES2 = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-64", "65-69", "70-74", "75+"]
def fine_bin(lo):
    lo = int(lo)
    if lo < 60: return AGES2[lo // 10]
    if lo < 65: return "60-64"
    if lo < 70: return "65-69"
    if lo < 75: return "70-74"
    return "75+"
m38.m36.age10 = fine_bin
for p in [os.path.join(ROOT, "02_패널", f"{TAG}_Estd2.csv"), os.path.join(AN, TAG, f"panel_{TAG}_std3.csv"), os.path.join(AN, TAG, f"config_{TAG}_std3.json")]:
    assert not os.path.exists(p), f"덮어쓰기 금지: {p}"

# ── 코드·전국 연령별 진료실인원(10구간) ──
M = pd.read_csv(os.path.join(AN, "00_298코드_질환매핑.csv"), encoding="utf-8-sig")
CODES = M[(M.TAG == TAG) & (M["포함"].astype(str) == "True")].code298.astype(int).tolist(); assert len(CODES) >= 15, CODES; print("[99I] 298 코드", CODES)
ko_, kdiff = m38.kosis_codes(CODES)
L = pd.DataFrame(ko_ + m38.excel_codes(CODES), columns=["year", "code", "age", "patients"]).groupby(["year", "code", "age"], as_index=False).patients.sum()
A = L[L.age != "TOTAL"]; TT = L[L.age == "TOTAL"].set_index(["year", "code"]).patients
assert sorted(A.year.unique()) == list(range(2011, 2025))
for y in range(2011, 2025): assert set(A[A.year == y].age) == set(AGES2), (y, sorted(set(A[A.year == y].age)))
chk = A.groupby(["year", "code"]).patients.sum(); assert ((chk - TT).abs() <= np.maximum(20, 1e-3 * TT)).all()
print(f"[99I] 코드 {CODES} · 14년 모두 세분 10구간 확보(최상위 75+) · KOSIS 연령 합-총계 차이 {kdiff if kdiff else '없음'}")

base = pd.read_csv(os.path.join(AN, "PERIO", "panel_PERIO_std3.csv"), encoding="utf-8-sig"); base["fbd_region"] = base.fbd_region.map(NFC); base["key"] = base.key.map(NFC)
MA = pd.read_parquet(os.path.join(ROOT, "02_패널", "MASTER_시군구_연도_wide.parquet"), columns=["year", "fbd_region", f"nhis__{KO}__진료실인원수"])
MA["fbd_region"] = MA.fbd_region.map(NFC); MA = MA[MA.year.between(2011, 2024)]
P = base.drop(columns=["cases", "E", "E_crude", "SIR", "offset"]).merge(MA.rename(columns={f"nhis__{KO}__진료실인원수": "cases"}), on=["year", "fbd_region"], how="left", validate="one_to_one")
assert P.cases.notna().all() and len(P) == 3206, P.cases.isna().sum()
cwm = (P.year == CHANGWON["year"]) & (P.fbd_region == NFC(CHANGWON["fbd_region"])); assert cwm.sum() == 1 and P.loc[cwm, "population"].iat[0] == CHANGWON["population"]
v1 = pd.read_csv(os.path.join(AN, TAG, f"panel_{TAG}.csv"), encoding="utf-8-sig", usecols=["year", "fbd_region", "cases"]); v1["fbd_region"] = v1.fbd_region.map(NFC)
assert (P.merge(v1, on=["year", "fbd_region"], suffixes=("", "_v1")).eval("cases == cases_v1")).all()   # 11/5 판과 cases 동일
P["offset"] = P.population
nat = P.groupby("year").apply(lambda d: d.cases.sum() / d.offset.sum(), include_groups=False); P["E_crude"] = P.offset * P.year.map(nat)

# ── 시군구 5세 인구(ST_FBDZIP, 39 매칭 규칙 그대로) ──
PKEYS = set(P.key); SIDO_HDR = {k for k in cw.SIDO_STD if len(k) >= 3 and (k.endswith("시") or k.endswith("도"))}
FIVE = [f"{lo}-{lo+4}세" for lo in range(0, 75, 5)]; OLD = ["75-79세", "80-84세", "85-89세", "90-94세", "95-99세", "100세 이상"]
EXTRA = {("충청북도", "청원군"): "충청북도|청주시"}; rows = []
for y in range(2011, 2025):
    d = pd.read_csv(os.path.join(m38.FBDZIP, f"{y}.csv"), encoding="cp949", dtype=str)
    d["행정구역별"] = d["행정구역별"].map(NFC).str.strip(); d["연령별"] = d["연령별"].map(NFC).str.strip(); d["v"] = pd.to_numeric(d["전체"].str.replace(",", ""), errors="coerce"); d["vf"] = pd.to_numeric(d["여자"].str.replace(",", ""), errors="coerce"); d["vm"] = pd.to_numeric(d["남자"].str.replace(",", ""), errors="coerce")
    sido = None; city = None; blocks = (d["행정구역별"] != d["행정구역별"].shift()).cumsum()
    for _, g in d.groupby(blocks, sort=False):
        nm = g["행정구역별"].iat[0]
        if nm == "전국": continue
        if nm in SIDO_HDR:
            sido = nm; city = None
            if nm != "세종특별자치시": continue
            g = g.drop_duplicates("연령별")
        sg = nm.split("-")[-1]
        if sg.endswith("시"): city = sg
        elif sg.endswith("구") and city is not None and cw.sido_std(sido) not in ("서울시", "부산시", "대구시", "인천시", "광주시", "대전시", "울산시"): continue
        else: city = None
        a = g.set_index("연령별")["v"]; tot = a.get("계", np.nan)
        if pd.isna(tot): continue
        f = a.reindex(FIVE); o = a.reindex(OLD); assert f.notna().all() and o.notna().all(), (y, nm)
        r = {"year": y, "tot": tot}
        for lo in range(0, 60, 10): r[AGES2[lo // 10]] = f[f"{lo}-{lo+4}세"] + f[f"{lo+5}-{lo+9}세"]
        r["60-64"] = f["60-64세"]; r["65-69"] = f["65-69세"]; r["70-74"] = f["70-74세"]; r["75+"] = tot - f.sum()
        assert abs(r["75+"] - o.sum()) < 0.5, (y, nm)
        key = EXTRA.get((cw.sido_std(sido), sg), cw.make_key(sido, sg))
        if key not in PKEYS and key.endswith("군") and key[:-1] + "시" in PKEYS: key = key[:-1] + "시"
        for sx, col in (("F", "vf"), ("M", "vm")):
            b = g.set_index("연령별")[col]; ff = b.reindex(FIVE); tt = b.get("계", np.nan); assert ff.notna().all() and pd.notna(tt), (y, nm, sx)
            for lo in range(0, 60, 10): r[sx + AGES2[lo // 10]] = ff[f"{lo}-{lo+4}세"] + ff[f"{lo+5}-{lo+9}세"]
            r[sx + "60-64"] = ff["60-64세"]; r[sx + "65-69"] = ff["65-69세"]; r[sx + "70-74"] = ff["70-74세"]; r[sx + "75+"] = tt - ff.sum()
        r["key"] = NFC(key); rows.append(r)
SB = [s + b for s in "FM" for b in AGES2]
G = pd.DataFrame(rows).groupby(["year", "key"], as_index=False)[["tot"] + AGES2 + SB].sum()
assert (((G[["F" + b for b in AGES2]].values + G[["M" + b for b in AGES2]].values) - G[AGES2].values).__abs__() <= 2).all(), "성별 합 ≠ 전체"
X = P[["year", "key", "fbd_region", "offset", "cases"]].merge(G, on=["year", "key"], how="left", validate="one_to_one"); assert X.tot.notna().all(), X[X.tot.isna()][["year", "key"]]
ratio = X.tot / X.offset; assert ((ratio - 1).abs() <= 0.01).all(), X[(ratio - 1).abs() > 0.01][["year", "key"]]
print(f"[99I] 창원 2023 FBD 계 {int(X.loc[(X.year == 2023) & (X.fbd_region == NFC(CHANGWON['fbd_region'])), 'tot'].iat[0]):,} / 패널 {CHANGWON['population']:,} · 총인구 비 {ratio.min():.4f}~{ratio.max():.4f}")

# ── rate·E_std2 ──
DEN = pd.DataFrame({b: X.offset * X[b] / X.tot for b in AGES2}); DEN["year"] = X.year.values
num = A.groupby(["year", "age"]).patients.sum().unstack()[AGES2]; den = DEN.groupby("year")[AGES2].sum(); rate = num / den
e = (DEN[AGES2].values * rate.loc[X.year.values].values).sum(axis=1)
X["E_std2"] = e * X.groupby("year").cases.transform("sum") / pd.Series(e, index=X.index).groupby(X.year).transform("sum")
assert (X.groupby("year").E_std2.sum() - X.groupby("year").cases.sum()).abs().max() < 1e-6 * X.cases.sum()
# ── 성×연령: 3단 상병 성별×5세 합 → 연령대별 남성 비율 ──
C3 = pd.read_csv(os.path.join(ROOT, "00_원천", "C_NHIS_3단상병", "INFECT_3char_sex_age5_2015_2024.csv"), encoding="utf-8-sig")
def bin3(s):
    s = str(s).replace(" ", "")
    if s in ("계", "합계", "전체"): return "TOTAL"
    n = re.findall(r"\d+", s); return fine_bin(int(n[0])) if n else None
C3["band"] = C3.age.map(bin3); C3 = C3[C3.band.notna() & (C3.band != "TOTAL") & C3.sex.isin(["남", "여", "남자", "여자", "남성", "여성"])]
C3["sx"] = C3.sex.str[0].map({"남": "M", "여": "F"})
SH = C3.groupby(["year", "band", "sx"]).patients.sum().unstack("sx"); SH = (SH["M"] / (SH["M"] + SH["F"])).unstack("band")[AGES2]
for y in range(2011, 2015): SH.loc[y] = SH.loc[2015]
SH = SH.sort_index(); assert list(SH.index) == list(range(2011, 2025)) and SH.notna().all().all()
print("[99I] 연령대별 남성 비율(3단 합, 2015/2024):", {b: (round(SH.loc[2015, b], 3), round(SH.loc[2024, b], 3)) for b in AGES2})
DENs = {s: pd.DataFrame({b: X.offset * X[s + b] / X.tot for b in AGES2}) for s in "FM"}
erow = np.zeros(len(X))
for s, frac in (("M", SH), ("F", 1 - SH)):
    nums = num * frac.loc[num.index, AGES2]; dens = DENs[s].assign(year=X.year.values).groupby("year")[AGES2].sum(); rs = nums / dens
    erow += (DENs[s][AGES2].values * rs.loc[X.year.values].values).sum(axis=1)
    rs.stack().rename("rate").reset_index().assign(sex=s).to_csv(os.path.join(ROOT, "02_패널", f"{TAG}_national_sexagerates_{s}.csv"), index=False, encoding="utf-8-sig")
X["E_sexage"] = erow * X.groupby("year").cases.transform("sum") / pd.Series(erow, index=X.index).groupby(X.year).transform("sum")
print(f"[99I] E_sexage/E_std2 {(X.E_sexage / X.E_std2).min():.3f}~{(X.E_sexage / X.E_std2).max():.3f}")
P = P.merge(X[["year", "fbd_region", "E_std2", "E_sexage"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
OLDE = pd.read_csv(os.path.join(ROOT, "02_패널", f"{TAG}_Estd.csv"), encoding="utf-8-sig"); OLDE["fbd_region"] = OLDE.fbd_region.map(NFC)
P = P.merge(OLDE[["year", "fbd_region", "E_std"]], on=["year", "fbd_region"], how="left", validate="one_to_one"); assert P.E_std.notna().all()
out = P[["year", "fbd_region", "E_sexage", "E_std2", "E_std"]].assign(SIR_crude=P.cases / P.E_crude, SIR_std=P.cases / P.E_std, SIR_std2=P.cases / P.E_std2, SIR_sexage=P.cases / P.E_sexage, pop80_share_raw=P.pop80_share_raw)
out.to_csv(os.path.join(ROOT, "02_패널", f"{TAG}_Estd2.csv"), index=False, encoding="utf-8-sig")
rate.stack().rename("rate").reset_index().to_csv(os.path.join(ROOT, "02_패널", f"{TAG}_national_agerates_std2.csv"), index=False, encoding="utf-8-sig")
P["E"] = P.E_sexage; P["SIR"] = P.cases / P.E
P.drop(columns=["E_std2", "E_std", "E_sexage"]).to_csv(os.path.join(AN, TAG, f"panel_{TAG}_std3.csv"), index=False, encoding="utf-8-sig")
cfg = json.load(open(os.path.join(AN, "PERIO", "config_PERIO_std3.json"), encoding="utf-8")); cfg["tag"] = TAG
json.dump(cfg, open(os.path.join(AN, TAG, f"config_{TAG}_std3.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"[99I] forced(std3) = {cfg['forced']}")
print(f"[99I] 14년 진료 {int(P.cases.sum()):,} · E_std2/E_std {(P.E / P.E_std).min():.3f}~{(P.E / P.E_std).max():.3f} · 창원 2023 E_std2 {P.loc[cwm.values, 'E'].iat[0]:.1f} (11/5 E_std {P.loc[cwm.values, 'E_std'].iat[0]:.1f})")
print("[99I] 2024 연령별 율(천 명당):", {k: round(v * 1e3, 2) for k, v in rate.loc[2024].items()})
print("[99I] 저장: 02_패널/INFECT_Estd2.csv(E_sexage 주) · 04_분석/INFECT/panel_INFECT_std3.csv(E = E_sexage) · config_INFECT_std3.json")
