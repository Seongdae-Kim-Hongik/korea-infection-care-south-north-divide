#!/usr/bin/env python3
# 99I — 감염병 진료(A00-B99) 공간 선별 std3·성×연령(2026-11-09). 99L_screen_lca_std3.py 복제, E = E_sexage(성×연령 10구간). 99_screen_cancers.py 복제, 지표·분류 규칙 동일(98_screen_std.py, 결과 전 고정). 바뀐 것은 입력만:
#  rho_old 용 65+ 비율(older_adult_share_raw)은 v1 패널 panel_LCA.csv 에서 가져옴(서술용, 분류에 안 씀)
import os, sys, importlib.util, numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); AN = os.path.join(ROOT, "04_분석")
src = open(os.path.join(HERE, "98_screen_std.py"), encoding="utf-8").read(); src = src[:src.index("SCR = pd.read_csv")]
g = {"__file__": os.path.join(HERE, "98_screen_std.py")}; exec(compile(src, "98head", "exec"), g)
read_graph, clusters, moran, classify, failed = g["read_graph"], g["clusters"], g["moran"], g["classify"], g["failed"]
TAGS = ["INFECT"]; KO = {"INFECT": "감염병"}
rows = []
for T in TAGS:
    D = os.path.join(AN, T); rng = np.random.default_rng(20261019)
    pan = pd.read_csv(f"{D}/panel_{T}_std3.csv", encoding="utf-8-sig", usecols=lambda c: c in ("year", "fbd_region", "cases", "E", "population", "area_m2", "urban_population_share_raw"))
    o65 = pd.read_csv(f"{D}/panel_{T}.csv", encoding="utf-8-sig", usecols=["year", "fbd_region", "older_adult_share_raw"])
    pan = pan.merge(o65, on=["year", "fbd_region"], how="left", validate="one_to_one")
    es = pd.read_csv(os.path.join(ROOT, "02_패널", f"{T}_Estd2.csv"), encoding="utf-8-sig").rename(columns={"E_std": "E_std_v1", "E_std2": "E_age2", "E_sexage": "E_std"})
    pan = pan.merge(es[["year", "fbd_region", "E_std"]], on=["year", "fbd_region"], how="left", validate="one_to_one"); assert pan.E_std.notna().all() and np.allclose(pan.E, pan.E_std)
    nb = read_graph(f"{D}/results/nb_{T}.graph")
    rr = pd.read_csv(f"{D}/results_screen/forced_std3_RR.csv"); hy = pd.read_csv(f"{D}/results_screen/forced_std3_hyper.csv")
    g0 = pan.groupby("fbd_region").agg(cases=("cases", "sum"), E_std=("E_std", "sum"), pop=("population", "mean"), km2=("area_m2", lambda x: x.mean() / 1e6),
                                        urban=("urban_population_share_raw", "mean"), old=("older_adult_share_raw", "mean"))
    g0 = rr[["area", "fbd_region"]].merge(g0, left_on="fbd_region", right_index=True, how="inner").sort_values("area").dropna(subset=["urban", "pop", "km2"]); g0 = g0[g0.cases > 0]
    idx = {a: i for i, a in enumerate(g0.area.values)}; W = np.zeros((len(g0), len(g0)))
    for a, i in idx.items():
        nbs = [idx[b] for b in nb.get(a, []) if b in idx]
        if nbs: W[i, nbs] = 1 / len(nbs)
    dens = np.log(g0["pop"] / g0["km2"]).values; u = g0.urban.values; X = np.column_stack([np.ones(len(g0)), u, u ** 2, dens, dens ** 2])
    sir = (g0.cases / g0.E_std).values; y = np.log(sir)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None); res = y - X @ beta; r2 = 1 - res.var() / y.var()
    I_raw, _ = moran(y, W, rng); I_ur, p_ur = moran(res, W, rng)
    ratio = float(np.percentile(sir, 90) / np.percentile(sir, 10)); rho = float(spearmanr(sir, g0.old.values).correlation)
    imin = []
    for yr, d in pan.groupby("year"):
        d = d.set_index("fbd_region").reindex(g0.fbd_region); k = d.cases.notna().values & (d.E_std > 0).values
        Wk = W[np.ix_(k, k)].copy(); rs = Wk.sum(1); Wk[rs > 0] = Wk[rs > 0] / rs[rs > 0, None]
        imin.append(moran(np.log((d.cases.values[k] + 0.5) / d.E_std.values[k]), Wk)[0])
    e1 = pan[pan.year <= 2015].groupby("fbd_region")[["cases", "E_std"]].sum(); e2 = pan[pan.year >= 2020].groupby("fbd_region")[["cases", "E_std"]].sum()
    cm = e1.index.intersection(e2.index); pers = float(spearmanr((e1.cases / e1.E_std)[cm], (e2.cases / e2.E_std)[cm]).correlation)
    hot = rr.loc[rr["class"] == "hotspot", "area"].tolist(); cold = rr.loc[rr["class"] == "coldspot", "area"].tolist(); hc = clusters(hot, nb)
    phi = float(hy[hy.hyperpar.str.startswith("Phi")]["mean"].iloc[0]); rl = float(np.corrcoef(dens, y)[0, 1])
    big = rr.set_index("area").loc[hc[0], "fbd_region"].tolist() if hc else []
    rows.append(dict(TAG=T, 질환=KO[T], n_sgg=len(g0), cases_14y=int(pan.cases.sum()), rho_old_std=round(rho, 3), P90P10_std=round(ratio, 3), I_raw_std=round(I_raw, 3), I_min_year_std=round(min(imin), 3),
                     persistence_std=round(pers, 3), R2_UR_std=round(r2, 3), I_UR_std=round(I_ur, 3), P_UR_std=p_ur, r_logdens_std=round(rl, 3), phi_forced_std=round(phi, 3),
                     hot_std=len(hot), cold_std=len(cold), largest_hot_std=len(hc[0]) if hc else 0, hot_core_std="; ".join(big[:8]),
                     track_std=classify(I_raw, r2, I_ur, p_ur, phi, ratio), fail_std=failed(I_ur, p_ur, phi, ratio),
                     방향_std="도시 높음" if rl > 0.2 else "농촌 높음" if rl < -0.2 else "도농 차 작음"))
O = pd.DataFrame(rows); O.insert(2, "판", "std3 성×연령(11/9)"); O.to_csv(os.path.join(AN, "00_공간선별_감염병std3_261109.csv"), index=False, encoding="utf-8-sig")
OLD = pd.read_csv(os.path.join(AN, "00_공간선별_std재판정_261019.csv")); OLD = OLD[OLD.TAG == "INFECT"]; assert len(OLD) == 1
cols = ["질환", "track_std", "I_raw_std", "I_min_year_std", "persistence_std", "P90P10_std", "R2_UR_std", "I_UR_std", "phi_forced_std", "largest_hot_std", "방향_std"]
ALL = pd.concat([O[cols].assign(묶음="std3 성×연령(11/9, 신규)"), OLD[cols].assign(묶음="std 10/19(연령 8구간)")])
dif = {c: O[c].iat[0] - OLD[c].iat[0] for c in cols[2:-1]}
L = ["# 공간 선별 — 감염성·기생충성 질환 진료(A00-B99) std3, 성×연령 간접표준화 기준 (2026-11-09)", "",
     "스크립트 `01_스크립트/99I_fetch_infect_sexage.py`(3단 성×5세) · `99I_screen_infect_std3_prep.py`(E_sexage·패널) · `98_fit_forced_v.R INFECT std3`(강제통제 BYM2) · `99I_screen_infect_std3.py`(지표·분류). 지표·분류 규칙은 98과 같다(결과 전 고정).",
     "std3 = 창원 2023 인구 1,009,038 교정(ST_FBDZIP 교정 사본) · 성(2)×연령 세분 10구간(0-9 … 60-64·65-69·70-74·75+; 298분류 연령별 인원을 3단 상병 A00-B99 성별 비율로 나눔, 2011-14는 2015 비율) · 강제통제 요양기관·도시인구·성비·재정자주도·80세 이상 인구 비율(65+ 제외). 전국 진료 원자료의 최상위 구간이 전 연도 75세 이상이라 75+ 내부는 표준화하지 못하고 80+ 비율 강제통제로 보정한다.", "",
     "| 묶음 | 질환 | 트랙 | 원자료 Moran | 연도별 최소 | 순위 지속 | P90/P10 | 도농 R² | 보정 후 Moran | phi | 최대 핫스팟 덩어리 | 방향 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for r in ALL.itertuples():
    L.append(f"| {r.묶음} | {r.질환} | {r.track_std} | {r.I_raw_std:.2f} | {r.I_min_year_std:.2f} | {r.persistence_std:.2f} | {r.P90P10_std:.2f} | {r.R2_UR_std:.2f} | {r.I_UR_std:.2f} | {r.phi_forced_std:.2f} | {r.largest_hot_std} | {r.방향_std} |")
L.append("| 차이(std3 − 10/19) | 감염병 | " + ("같음" if O.track_std.iat[0] == OLD.track_std.iat[0] else f"{OLD.track_std.iat[0]} → {O.track_std.iat[0]}") + " | " + " | ".join(f"{dif[c]:+.2f}" if c != "largest_hot_std" else f"{int(dif[c]):+d}" for c in cols[2:-1]) + " | " + ("같음" if O.방향_std.iat[0] == OLD.방향_std.iat[0] else f"{OLD.방향_std.iat[0]} → {O.방향_std.iat[0]}") + " |")
r = O.iloc[0]
L += ["", f"핫스팟 {r.hot_std}곳 · 콜드스팟 {r.cold_std}곳 · 보정 후 Moran P {r.P_UR_std} · SIR–65+ 비율 Spearman {r.rho_old_std:.2f} (10/19 {OLD.rho_old_std.iat[0]:.2f})",
      f"공간형 미충족 항목: std3 {r.fail_std} (10/19 {OLD.fail_std.iat[0]})",
      f"핫스팟 핵심 지역(최대 덩어리 앞 8곳): std3: {r.hot_core_std} / 10/19: {OLD.hot_core_std.iat[0]}"]
open(os.path.join(AN, "00_공간선별_감염병std3_261109.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
