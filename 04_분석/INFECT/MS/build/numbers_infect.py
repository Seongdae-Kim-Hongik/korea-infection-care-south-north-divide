# numbers_infect.py — 감염성·기생충성 질환 진료(INFECT, A00-B99) 원고의 모든 수치를 결과 CSV에서 읽는다(2026-11-09, numbers_lca 복제). 기억·손입력 금지, assert로 정합 확인.
#  사용: from numbers_infect import load; N = load()
import os, re, glob, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
ROOT = os.path.dirname(os.path.dirname(B)); PAN = os.path.join(ROOT, "02_패널")
WIN = [("W1_2011-15", 2011, 2015), ("W2_2016-19", 2016, 2019), ("W3_2020-24", 2020, 2024)]
rd = lambda f, **k: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", **k)
ROB = ["current_smoking_rate", "basic_livelihood_rate", "screening_uptake", "public_sports_facilities_per_100k"]
REV = ["current_smoking_rate", "basic_livelihood_rate"]   # 역방향(결과 요약 5절)
CAP = ("서울", "경기", "인천")
COV_T1 = ["pop80_share", "urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "screening_suspected_diabetes_share", "screening_normalB_obesity_share", "current_smoking_rate", "long_term_care_hospitals_per_100k", "basic_livelihood_rate", "single_person_household_share", "annual_mean_temperature", "public_baths_per_10k", "public_pools_per_100k", "screening_uptake", "walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k"]
SHP = os.environ.get("ST_SHP", os.path.join(HERE, "..", "..", "..", "..", "data", "boundary", "final.shp"))

def load():
    N = {}
    P = pd.read_csv(os.path.join(B, "panel_INFECT_std3.csv")); N["n_rows"] = len(P); N["n_districts"] = P.fbd_region.nunique()
    assert (N["n_rows"], N["n_districts"]) == (3206, 229)
    N["cases_total"] = int(P.cases.sum()); N["py"] = float(P.offset.sum())
    y = P.groupby("year")[["cases", "offset"]].sum(); N["cases_2011"], N["cases_2024"] = int(y.cases[2011]), int(y.cases[2024])
    N["crude_2011"], N["crude_2024"] = 1e5 * y.cases[2011] / y.offset[2011], 1e5 * y.cases[2024] / y.offset[2024]
    # 직접 성·연령 표준화율(2015 전국 주민등록 인구 성×10구간; 3단 합 기반 전국 율을 연도별 시군구 합계에 맞게 재척도)
    AG = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-64", "65-69", "70-74", "75+"]
    def natpop(yr):
        d = pd.read_csv(os.path.join(os.environ["ST_FBDZIP_CORRECTED"], f"{yr}.csv"), encoding="cp949", dtype=str); d = d[d["행정구역별"].str.strip() == "전국"]
        out = {}
        for sx, col in (("M", "남자"), ("F", "여자")):
            v = d.set_index(d["연령별"].str.strip())[col].str.replace(",", "").replace("-", "0").astype(float); tot = v["계"]; f = {k: v[k] for k in v.index if re.fullmatch(r"\d+-\d+세", k)}
            for lo in range(0, 60, 10): out[(sx, AG[lo // 10])] = f[f"{lo}-{lo+4}세"] + f[f"{lo+5}-{lo+9}세"]
            out[(sx, "60-64")], out[(sx, "65-69")], out[(sx, "70-74")] = f["60-64세"], f["65-69세"], f["70-74세"]; out[(sx, "75+")] = tot - sum(f[f"{l}-{l+4}세"] for l in range(0, 75, 5))
        return out
    R = pd.concat([pd.read_csv(os.path.join(PAN, f"INFECT_national_sexagerates_{x}.csv")) for x in "MF"]).set_index(["year", "sex", "age"]).rate
    W15 = natpop(2015); wt = sum(W15.values()); asr = {}
    for yr in range(2011, 2025):
        pp = natpop(yr); k = y.cases[yr] / sum(R[(yr, sx, a)] * pp[(sx, a)] for sx in "MF" for a in AG)
        asr[yr] = 1e5 * sum(R[(yr, sx, a)] * k * W15[(sx, a)] for sx in "MF" for a in AG) / wt
    N["asr"] = asr; N["asr_2011"], N["asr_2024"] = asr[2011], asr[2024]; N["asr_ratio"] = asr[2024] / asr[2011]
    N["asr_2019"], N["asr_2020"] = asr[2019], asr[2020]
    T1 = {}
    for wn, a, b in WIN + [("2011-2024", 2011, 2024)]:
        q = P[(P.year >= a) & (P.year <= b)]; sir = q.groupby("fbd_region").apply(lambda d: d.cases.sum() / d.E.sum(), include_groups=False)
        T1[wn] = dict(n=len(q), cases=int(q.cases.sum()), py=float(q.offset.sum()), crude=1e5 * q.cases.sum() / q.offset.sum(),
                      asr=np.mean([asr[t] for t in range(a, b + 1)]), sir_p10=sir.quantile(.1), sir_p90=sir.quantile(.9), sir_med=sir.median(),
                      cov={v: (q[f"{v}_raw"].mean(), q[f"{v}_raw"].std()) for v in COV_T1})
    N["T1"] = T1
    # 공간
    s6m = rd("S6_moran_year.csv"); N["moran_year_min"], N["moran_year_max"] = s6m.moran_I.min(), s6m.moran_I.max()
    r8 = rd("S8_residual_moran.csv").set_index("quantity"); N["moran_pooled"] = r8.loc["observed_logSIR_pooled", "moran_I"]
    N["moran_resid"] = r8.loc["pearson_residual_area_mean", "moran_I"]; N["moran_resid_p"] = r8.loc["pearson_residual_area_mean", "p_perm"]
    N["moran_y"] = s6m.set_index("year").moran_I.to_dict()
    h = rd("S3_main_hyper.csv"); ph = h[h.hyperpar.str.startswith("Phi")].iloc[0]; N["phi"] = (ph["mean"], ph["X0.025quant"], ph["X0.975quant"])
    s6 = rd("S6_spatial_RR.csv"); N["rr_min"], N["rr_max"] = s6.RR.min(), s6.RR.max()
    N["n_hot"], N["n_cold"] = int((s6["class"] == "hotspot").sum()), int((s6["class"] == "coldspot").sum())
    N["hot_strict"] = {t: (int((s6.P_gt1 > t).sum()), int((s6.P_gt1 < 1 - t).sum())) for t in (0.975, 0.99)}   # review(11/6): 느슨한 기준 우려 → 엄격 기준 병기
    sido = s6.fbd_region.str.extract(r"^(\S+?(?:도|시))")[0]
    N["hot_by_sido"] = s6[s6["class"] == "hotspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["cold_by_sido"] = s6[s6["class"] == "coldspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["hot_capital"] = int(((s6["class"] == "hotspot") & s6.fbd_region.str.startswith(CAP)).sum())
    N["cold_capital"] = int(((s6["class"] == "coldspot") & s6.fbd_region.str.startswith(CAP)).sum())
    typ = s6.fbd_region.map(lambda r: "county" if r.endswith("군") else ("ward" if r.endswith("구") else "city"))
    N["type_class"] = pd.crosstab(typ, s6["class"]).to_dict(); N["n_type"] = typ.value_counts().to_dict()
    wm = rd("S4b_window_spatialRR.csv"); N["win_hot"] = wm[wm["class"] == "hotspot"].groupby("window").size().to_dict()
    N["win_cold"] = wm[wm["class"] == "coldspot"].groupby("window").size().to_dict()
    hs = {w: set(wm[(wm.window == w) & (wm["class"] == "hotspot")].fbd_region) for w in wm.window.unique()}; N["hot_all_windows"] = len(set.intersection(*hs.values()))
    _pv = wm.pivot_table(index="fbd_region", columns="window", values="RR").corr(method="spearman"); N["win_rr_rho"] = (float(_pv.loc["W1_2011-15", "W3_2020-24"]), float(_pv.loc["W1_2011-15", "W2_2016-19"]), float(_pv.loc["W2_2016-19", "W3_2020-24"]))
    pe = rd("S12_persistence.csv").set_index("set"); N["kendall_W"] = pe.loc["2011-2024", "kendall_W"]
    N["kendall_W_1119"], N["kendall_W_2024"] = pe.loc["2011-2019", "kendall_W"], pe.loc["2020-2024", "kendall_W"]
    eh = rd("S11_ehsa_summary.csv").set_index("category").n.to_dict(); N["ehsa"] = eh
    # 주모형·다중우주
    m3 = rd("S3_main_IRR.csv").set_index("cov"); N["main"] = m3[["IRR", "lo", "hi", "cred", "role", "label_en", "P_gt1"]].to_dict("index")
    N["n_hyp"] = int((m3.role == "hypothesis").sum()); N["n_cred_hyp"] = int(((m3.role == "hypothesis") & m3.cred).sum())
    s7 = rd("S7_multiverse_summary.csv").set_index("cov"); N["mv"] = s7[["n_specs", "cred_frac", "sign_agree", "robust"]].to_dict("index")
    N["n_robust"] = int(s7.robust.sum()); assert set(s7.index[s7.robust]) == set(ROB), s7.index[s7.robust].tolist()
    hb = open(os.path.join(B, "HM_best_INFECT_std3.txt")).read(); N["waic_forced"] = float(hb.split("ref_forced_only_WAIC=")[1].split()[0])
    N["waic_main"] = float(hb.split("S1_narrative_full(")[1].split(",")[0])
    nc = rd("S3_negcontrol.csv").set_index("cov"); N["negctl"] = nc[["IRR", "lo", "hi", "cred"]].to_dict("index")
    wi = rd("S4_window_IRR.csv"); N["win_irr"] = {(r.cov, r.window): (r.IRR, r.lo, r.hi, r.cred) for r in wi.itertuples()}
    S43 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S43_part_*.csv"))]); N["s43"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S43.itertuples()}
    N["s43_waic"] = S43.groupby("analysis").WAIC.first().to_dict()
    T9 = rd("S9_typeI_IRR.csv"); N["s43"].update({("KH_typeI", r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in T9.itertuples()}); N["s43_waic"]["KH_typeI"] = float(T9.WAIC.iloc[0])
    S41 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S41_part_*.csv"))]); N["s41"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S41.itertuples()}
    N["s41_waic"] = S41.groupby("analysis").WAIC.first().to_dict()
    ALT = sorted({a for a in S41.analysis.unique() if not a.startswith(("F1_", "F2_", "G2_", "H1_", "bw_"))}); N["alt14"] = ALT
    N["ret14"] = {}
    for v in ROB:
        sg = N["main"][v]["IRR"] > 1; rr = [N["s41"][(a, v)] for a in ALT if (a, v) in N["s41"]]
        N["ret14"][v] = (sum(1 for t in rr if t[3] and (t[0] > 1) == sg), len(rr))
    N["c1_robust_kept"] = int(S41[S41.analysis == "C1_poisson_lognormal"].robust_kept.iloc[0])
    N["bw"] = {(r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in S41[S41.analysis == "bw_twoway"].itertuples()}
    N["retention"] = rd("S41_retention_by_cov.csv").set_index("cov").to_dict("index"); N["rubin"] = rd("S41_noise_rubin.csv").set_index("cov").to_dict("index")
    N["evalue"] = rd("S41_evalues.csv").set_index("cov").to_dict("index"); N["oos"] = rd("S41_oos2024.csv").iloc[0].to_dict()
    N["ppc"] = rd("S42_ppc.csv").iloc[0].to_dict(); N["varpart"] = rd("S42_variance_partition.csv").set_index("component").to_dict("index")
    N["nco"] = {(r.analysis.replace("H1_nco_", ""), r.cov): (r.IRR, r.lo, r.hi, r.cred) for r in rd("S41_nco_detail.csv").itertuples()}
    # 사전지정 E·그래프 민감도(주모형만)
    # 남북 기울기 검정: 시군구 중심점 북쪽 좌표와 잔차 RR·보정 없는 EB 평활 STR의 Spearman 상관, 잔차 RR과 EB STR의 상관
    import geopandas as gpd; from scipy.stats import spearmanr
    G = gpd.read_file(SHP); G["cd"] = G.sigungu_cd.astype(str); G["y"] = G.centroid.y
    s6i = s6.set_index(s6.sigungu_cd.astype(str)); ehi = rd("S11_ehsa.csv"); ehi = ehi.set_index(ehi.sigungu_cd.astype(str))
    G["rr"] = G.cd.map(s6i.RR); G["eb"] = G.cd.map(ehi.ebSIR_mean); assert G[["rr", "eb"]].notna().all().all()
    N["lat_rr"] = spearmanr(G.y, G.rr).correlation; N["lat_eb"] = spearmanr(G.y, G.eb).correlation; N["rr_eb"] = spearmanr(G.rr, G.eb).correlation
    # 박탈 기울기: 보정 없는 EB STR·잔차 RR과 시군구 평균 의료급여 1종·수검률·흡연율의 Spearman 상관
    s6r = s6.set_index("fbd_region"); ehr = rd("S11_ehsa.csv").set_index("fbd_region"); Pm2 = P.groupby("fbd_region")[[f"{v}_raw" for v in COV_T1 if f"{v}_raw" in P.columns]].mean()
    for k, v in (("eb_bl", "basic_livelihood_rate"), ("eb_scr", "screening_uptake"), ("eb_smk", "current_smoking_rate"), ("eb_p80", "pop80_share"), ("eb_urb", "urban_population_share"), ("eb_tmp", "annual_mean_temperature"), ("eb_dm", "screening_suspected_diabetes_share"), ("eb_psf", "public_sports_facilities_per_100k")):
        N[k] = spearmanr(Pm2[f"{v}_raw"], ehr.ebSIR_mean.reindex(Pm2.index)).correlation
    N["rr_bl"] = spearmanr(Pm2.basic_livelihood_rate_raw, s6r.RR.reindex(Pm2.index)).correlation
    cv = rd("S5_covid.csv"); N["covid_main"] = tuple(cv[cv.term == "post_main"][["IRR", "lo", "hi", "cred"]].iloc[0]); N["covid_nint"] = int(cv[(cv.term == "var_x_post") & cv.cred].shape[0]); N["covid_int_cov"] = cv[(cv.term == "var_x_post") & cv.cred]["cov"].tolist()
    import unicodedata as _u
    _wm = wm.assign(r=wm.fbd_region.map(lambda x: _u.normalize("NFC", x))); _sd = lambda x: re.match(r"^(\S+?(?:도|시))", x).group(1)
    for cls, key in (("hotspot", "persist_hot_by_sido"), ("coldspot", "persist_cold_by_sido")):
        k3 = _wm[_wm["class"] == cls].groupby("r").size(); idx = k3[k3 == 3].index
        N[key] = pd.Series([_sd(x) for x in idx]).value_counts().to_dict()
    nc3 = {w: set(wm[(wm.window == w) & (wm["class"] == "coldspot")].fbd_region) for w in wm.window.unique()}; N["cold_all_windows"] = len(set.intersection(*nc3.values()))
    N["sens_main"] = {}
    for v in ["s577", "s2", "s8", "sage"]:
        m = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")).set_index("cov"); N["sens_main"][v] = {c: (m.loc[c, "IRR"], m.loc[c, "lo"], m.loc[c, "hi"], bool(m.loc[c, "cred"])) for c in m.index}
    # 심사 선제(88k review, 2026-11-06)
    N["s50_moran"] = rd("S50_resid_moran_by_spec.csv").set_index("spec").to_dict("index")
    N["s50_pars"] = rd("S50_parsimonious.csv").set_index("cov").to_dict("index")
    rs = rd("S50_region_slopes.csv"); N["s50_region"] = {(r.covariate, r.region): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in rs.itertuples()}
    N["s50_region_dwaic"] = rs.groupby("covariate").dWAIC_vs_common.first().to_dict()
    ac = rd("S50_access_sensitivity.csv").set_index("cov"); N["s50_access"] = {c: (ac.loc[c, "IRR"], ac.loc[c, "lo"], ac.loc[c, "hi"], bool(ac.loc[c, "cred"])) for c in ac.index}
    # 결과 열람 뒤 추가한 기술 분석: 연도별 경험적 베이즈 평활 STR의 상대 격차
    from scipy.stats import kendalltau
    eb = rd("S12c_yearly_EB_SIR.csv"); g = eb.groupby("year").ebSIR
    gap = pd.DataFrame({"p10": g.quantile(.1), "p90": g.quantile(.9), "sdlog": g.apply(lambda s: float(np.log(s).std()))}); gap["ratio"] = gap.p90 / gap.p10
    gap["abs"] = (gap.p90 - gap.p10) * pd.Series(asr)   # 10만 명당 절대 격차 = (P90−P10 SMR) × 전국 직접표준화율
    N["gap"] = gap.to_dict("index"); kt = kendalltau(gap.index, gap.ratio); N["gap_tau"] = (float(kt.statistic), float(kt.pvalue))
    ks = kendalltau(gap.index, gap.sdlog); N["gap_sd_tau"] = (float(ks.statistic), float(ks.pvalue)); ka = kendalltau(gap.index, gap["abs"]); N["gap_abs_tau"] = (float(ka.statistic), float(ka.pvalue))
    N["win_rr_ratio"] = wm.groupby("window").RR.apply(lambda s: float(s.quantile(.9) / s.quantile(.1))).to_dict()
    # 역방향 변수의 지역 내·간 성분 SD(원 단위)
    _p = P.copy(); N["within_sd"] = {}; N["between_sd"] = {}
    for v in ROB:
        x = _p[f"{v}_raw"]; mi = _p.groupby("fbd_region")[f"{v}_raw"].transform("mean"); mt = _p.groupby("year")[f"{v}_raw"].transform("mean")
        N["within_sd"][v] = float((x - mi - mt + x.mean()).std()); N["between_sd"][v] = float(mi.std())
    N["pit"] = (float(N["ppc"]["coverage50"]), float(N["ppc"]["pit_ks_p"]))
    lo = rd("S41_leaveout_ranges.csv"); N["leaveout"] = {(r.set, r.cov): (r.n, r.n_cred_same_sign) for r in lo.itertuples() if not str(r.cov).startswith("__")}
    N["s41_retention"] = rd("S41_retention_by_cov.csv").set_index("cov").to_dict("index")
    sc = pd.read_csv(os.path.join(B, "..", "00_공간선별_감염병std3_261109.csv")); N["screen_row"] = sc[sc.TAG == "INFECT"].iloc[0].to_dict()
    cp = pd.read_csv(os.path.join(B, "composition_3char_2015_2024.csv"), index_col=0); N["comp"] = cp
    N["covid_terms"] = {(r.term, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in cv.itertuples()}
    N["s5_waic"] = float(cv.WAIC.iloc[0])
    N["rev_n_cred_main"] = sum(1 for v in REV if N["main"][v]["cred"]); assert N["rev_n_cred_main"] == 2
    N["crude_y"] = (1e5 * y.cases / y.offset).to_dict()
    return N

if __name__ == "__main__":
    N = load()
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in N.items() if not isinstance(v, (dict, list, pd.DataFrame))})
    print("hot_by_sido", N["hot_by_sido"]); print("cold_by_sido", N["cold_by_sido"]); print("ehsa", N["ehsa"]); print("win_hot", N["win_hot"])
    print("T1", {k: {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk != "cov"} for k, v in N["T1"].items()})
    print("KH WAIC", {k: v for k, v in N["s43_waic"].items() if "KH" in k}, "ppc", {k: N["ppc"][k] for k in ["coverage95", "coverage50", "pit_ks_p"]})
