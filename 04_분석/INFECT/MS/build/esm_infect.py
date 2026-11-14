# esm_infect.py — 감염성·기생충성 질환 진료 Infectious Diseases 보충자료(단일 파일: Table S1 구성·Appendix A·Table S2-S5·Fig. S1·Appendix B STROBE/RECORD, 2026-11-09).
#  수치는 결과 CSV에서만. 미국식 철자, 표 제목 쌍점 금지. 보충 번호는 본문 첫 인용 순서(content_infect.SUP).
import os, re, json, subprocess, pandas as pd
from docx.shared import Cm
import content_infect as C
from build_id_infect import LABEL, GROUPS, foot_row, read_draft
from build_asap_infect import TX, TITLE as DTITLE
HERE = os.path.dirname(os.path.abspath(__file__)); MSD = os.path.dirname(HERE); OUT = os.path.join(MSD, "out"); B = os.path.dirname(MSD); RS = os.path.join(B, "results_std3")
N = C.N
st = lambda t: f"{t[0]:.3f} ({t[1]:.3f}-{t[2]:.3f})"
J = TX()
def TF(title, header, rows, foot="", fs=8):
    J.page_break(); J.table_fit(title, header, rows, "", fs_max=fs, title_bold=False)
    if foot: foot_row(J, foot, 8, 12)
J.para("<b>Online Resource 1</b>"); J.para(f"Electronic supplementary material for the article \"{DTITLE}\", Applied Spatial Analysis and Policy (author details withheld for anonymous review)")
J.para("Contents. Table S1 (national composition of the chapter); Appendix A (supplementary methods and additional results); Tables S2-S5 (Table S4 in three parts); Fig. S1; Appendix B (STROBE and RECORD checklist).")
assert list(C.SUP.values())[:2] == ["Online Resource 1 (Table S1)", "Online Resource 1 (Appendix A)"]
# ── Table S1: 전국 3단 상병 구성 ──
CP = N["comp"]; cy = [str(y) for y in range(2015, 2025)]
ORDER = [("1+1a Intestinal infections incl. A09 (A00-A09)", "Intestinal (A00-A09)"), ("1a Gastroenteritis and colitis of infectious and unspecified origin (A09)", "  of which A09<sup>a</sup>"),
         ("2 Tuberculosis (A15-A19)", "Tuberculosis (A15-A19)"), ("5 Predominantly sexually transmitted infections (A50-A64)", "Sexual mode (A50-A64)<sup>b</sup>"),
         ("3a Herpes simplex (B00)", "Herpes simplex (B00)"), ("3b Zoster (B02)", "Zoster (B02)"), ("3c Viral warts (B07)", "Viral warts (B07)"), ("4 Viral hepatitis (B15-B19)", "Hepatitis (B15-B19)"),
         ("6 Mycoses (B35-B49)", "Mycoses (B35-B49)"), ("7 Pediculosis, acariasis and other infestations (B85-B89)", "Infestations (B85-B89)"), ("8 Other A00-B99 codes", "Other codes")]
rows = [[lab] + [f"{float(CP.loc[k, y]):.1f}" for y in cy] for k, lab in ORDER]
tot = CP.loc["Code-level patient total (summed, millions)", cy].astype(float)
rows.append(["Summed counts, million"] + [f"{v:.2f}" for v in tot])
grp_sum = sum(CP.loc[k, cy].astype(float) for k, _ in ORDER if k not in ("1a Gastroenteritis and colitis of infectious and unspecified origin (A09)", "1 Intestinal infections (A00-A09)"))
assert ((grp_sum - 100).abs() < 0.3).all(), grp_sum
TF("Table S1. Composition of national counts of people treated for infectious and parasitic diseases by three-character code group, Korea, 2015-2024 (% of summed code-level counts)", ["Code group"] + cy, rows,
   "<sup>a</sup>Gastroenteritis and colitis of infectious and unspecified origin. <sup>b</sup>Infections with a predominantly sexual mode of transmission. Source: National Health Insurance Service big data platform, statistics by three-character code (principal diagnosis), retrieved 9 November 2026. A person treated under two codes in a year is counted under both, so shares refer to summed code-level counts rather than to unique people, and the summed counts exceed the number of unique people treated for the chapter. The platform starts in 2015 and covers National Health Insurance enrollees only, whereas the district outcome also includes Medical Aid beneficiaries; district counts by code are not published.", fs=7)
# ── Appendix A ──
_MT = pd.read_csv(os.path.join(B, "panel_META_INFECT_std3.csv"), encoding="utf-8-sig").set_index("variable")
_imp = lambda v: int(_MT.loc[v, "n_imputed_interp"] + _MT.loc[v, "n_imputed_sgg_mean"] + _MT.loc[v, "n_imputed_year_mean"])
gate = open(os.path.join(B, "data_gate_INFECT_std3_261109.txt"), encoding="utf-8").read(); nwarn = int(re.search(r"경고 (\d+)건", gate).group(1))
zero = re.findall(r"\[전 연도 0인 지역\] (\S+): (\d+)곳", gate)
sex = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(B)), "00_원천", "C_NHIS_3단상병", "INFECT_3char_sex_age5_2015_2024.csv"), encoding="utf-8-sig")
J.page_break(); J.head("Appendix A. Supplementary methods and additional results", 2)
SR = N["screen_row"]
SM = [("Outcome.", "The Regional Medical Care Utilization Statistics of the National Health Insurance Service publish, for each district of residence and year, the number of unique people with at least one claim for each of several major disease groups as the principal diagnosis, including the chapter of infectious and parasitic diseases (A00-B99). The statistics cover National Health Insurance enrollees and Medical Aid beneficiaries. District units that changed during 2011-2024 were aggregated to 229 districts with 2024 boundaries using administrative codes only."),
      ("Expected counts by sex and age.", f"National numbers of people treated by age group came from the national disease-classification tables of the same statistics, published in ten age groups with an open-ended group aged 75 years or older in every year and without sex. These tables count a person in each diagnostic subcategory, so national rates were rescaled to the annual sum of district counts. To split each age group by sex, the male share of summed three-character counts (A00-B99, both care types) in that age group and year was taken from the National Health Insurance big data platform for 2015-2024 ({sex.code.nunique()} codes with data); the 2015 shares were used for 2011-2014. District populations by sex and 5-year age group came from resident registration; the 2023 population of Changwon, which repeated the 2022 value in the source file, was corrected to the published total (1,009,038). Sex- and age-standardized expected counts differed from age-only expected counts by a factor of 0.970-1.012, and both were used in sensitivity analyses."),
      ("Covariates.", "Current smoking, walking practice, and moderate-or-vigorous activity are district age-standardized estimates from the Community Health Survey; the moderate-or-vigorous item was not published for 2018 and that year was interpolated within districts. Suspected diabetes, obesity management needed, and screening uptake come from national general health screening statistics. Long-term care hospitals come from the register of care institutions of the Health Insurance Review and Assessment Service; public swimming pools and public sports facilities from the public sports facility register; public bathhouses from local business licensing data; single-person households from the population and housing census (from 2015); annual mean temperature from inverse-distance-weighted interpolation of weather station records to district centroids. The basic livelihood security recipient rate for 2021-2023 fell to 0.01%-0.12% in 11 cities with administrative wards in the source file, below 20% of each city's 2020-2024 average; these 33 district-years were set to missing and interpolated linearly within districts before standardization. No covariate described exposure through food or water."),
      ("Panel checks before modeling.", f"An automated gate run on the analytic panel reported {nwarn} flags before any covariate model was fitted (Table S3). Most flagged standardized columns whose yearly means were near 0 (a ratio artifact), the post-2020 indicator (constant by design), and real trends. Annual precipitation was dropped because station gaps produced values as low as 146 mm."),
      ("Models.", "Software: R 4.6.0 with R-INLA; Python 3.9 for data preparation and figures. The negative binomial likelihood was chosen because its widely applicable information criterion (WAIC) for the forced-controls model was lower than that of a Poisson model. District effects used the 229-district adjacency graph in which island districts were linked to their nearest mainland neighbors (593 edges); a queen-contiguity graph with 577 edges was used as a sensitivity analysis. Penalized-complexity priors: precision P(1/\u221a\u03c4 > 0.5) = 0.01 for the district, random-walk, and independent year effects, and mixing P(\u03c6 < 0.5) = 2/3. Fixed effects had normal priors with mean 0 and precision 4 (standard deviation 0.5 on the log scale per 1 standard deviation of a covariate), and the intercept had precision 0.001. The parsimonious model in Table S4 contains only the four subset-stable characteristics and the five forced controls."),
      ("Spatial statistics.", "Emerging hot spot analysis used yearly empirical Bayes smoothed standardized treatment ratios (STRs), the Getis-Ord Gi* statistic with a row-standardized weight matrix that includes the district itself on the same adjacency graph (|z| > 1.96 for a hot or cold year), and a Mann-Kendall trend test of yearly z-scores. Persistence used Kendall's W of annual rankings with permutation and Poisson-resampling null distributions."),
      ("Robustness procedures.", "WAIC was computed on the district-year likelihood with the same outcome and offset in every model fitted to the same years, so the space-time models and the principal model are compared on the same scale; models with observation-level effects or different years are not compared by WAIC. Two-way centering subtracted district and year means from each subset-stable characteristic; both components were entered together. Filled values were perturbed 20 times with normal noise scaled to the within-district standard deviation, and the fits were pooled with Rubin's rules.")]
for h, t in SM: J.para(f"<b>{h}</b> {t}")
_tc = N["type_class"]
J.para("<b>Additional results.</b> " + f"In spatial screening with the forced controls only, before covariates were examined, the Moran's I of log STRs from the screening expected counts was {SR['I_raw_std']:.2f} and that of residuals from an urban-rural regression {SR['I_UR_std']:.2f}, with a BYM2 spatial fraction of {SR['phi_forced_std']:.2f}. "
       f"Cold spots comprised {_tc['coldspot']['ward']} urban wards, {_tc['coldspot']['city']} cities, and {_tc['coldspot']['county']} counties. With stricter thresholds of 0.975 and 0.99, there were {N['hot_strict'][0.975][0]} and {N['hot_strict'][0.99][0]} hot spots and {N['hot_strict'][0.975][1]} and {N['hot_strict'][0.99][1]} cold spots. "
       f"The Spearman correlation of residual RRs between windows was {N['win_rr_rho'][1]:.2f} (2011-2015 vs 2016-2019), {N['win_rr_rho'][2]:.2f} (2016-2019 vs 2020-2024), and {N['win_rr_rho'][0]:.2f} (2011-2015 vs 2020-2024). "
       f"E-values for the point estimates (and for the limits closest to 1) were {N['evalue'][C.PSF]['E_point']:.2f} ({N['evalue'][C.PSF]['E_limit']:.2f}) for public sports facilities, {N['evalue'][C.SCR]['E_point']:.2f} ({N['evalue'][C.SCR]['E_limit']:.2f}) for screening uptake, {N['evalue'][C.BL]['E_point']:.2f} ({N['evalue'][C.BL]['E_limit']:.2f}) for the basic livelihood rate, and {N['evalue'][C.SMK]['E_point']:.2f} ({N['evalue'][C.SMK]['E_limit']:.2f}) for smoking. "
       f"Pooled over 20 perturbations of filled values, the rate ratio for single-person households was {N['rubin'][C.SPH]['IRR_pooled']:.3f} ({N['rubin'][C.SPH]['lo']:.3f}-{N['rubin'][C.SPH]['hi']:.3f}). "
       f"In 2024 counts predicted from 2011-2023, the Spearman correlation between observed and predicted counts was {N['oos']['spearman_obs_pred']:.3f}.")
# ── Table S2 ──
DIR = json.load(open(os.path.join(B, "sets_INFECT_std3.json"), encoding="utf-8"))["expected_direction"]
COLV = {v: _MT.loc[v, "source_column"] for v in _MT.index}; dsign = lambda v: DIR[COLV[v]].strip()[0].replace("-", "−")
SRCN = {"screening_suspected_diabetes_share": "Screening", "screening_normalB_obesity_share": "Screening", "current_smoking_rate": "Survey", "long_term_care_hospitals_per_100k": "HIRA",
        "basic_livelihood_rate": "KOSIS", "single_person_household_share": "Census", "annual_mean_temperature": "KMA", "public_baths_per_10k": "Licensing", "public_pools_per_100k": "Register",
        "screening_uptake": "Screening", "walking_practice_rate": "Survey", "moderate_pa_rate": "Survey", "public_sports_facilities_per_100k": "Register",
        "urban_population_share": "KOSIS", "physicians_per_1000": "KOSIS", "sex_ratio": "KOSIS", "fiscal_independence": "KOSIS", "pop80_share": "Registry"}
UNIT = {"screening_suspected_diabetes_share": "%", "screening_normalB_obesity_share": "%", "current_smoking_rate": "%", "long_term_care_hospitals_per_100k": "per 100,000",
        "basic_livelihood_rate": "%", "single_person_household_share": "%", "annual_mean_temperature": "°C", "public_baths_per_10k": "per 10,000", "public_pools_per_100k": "per 100,000",
        "screening_uptake": "%", "walking_practice_rate": "%", "moderate_pa_rate": "%", "public_sports_facilities_per_100k": "per 100,000",
        "urban_population_share": "%", "physicians_per_1000": "per 1,000", "sex_ratio": "ratio", "fiscal_independence": "%", "pop80_share": "%"}
rows = []
for g, vs in GROUPS:
    rows.append(["__H__", g])
    for v in vs:
        m = _MT.loc[v]
        rows.append([f"  {LABEL[v]}", UNIT[v], SRCN[v], f"{int(m.obs_year_min)}-{int(m.obs_year_max)}", ("Forced" if m.role == "forced" else dsign(v)), f"{_imp(v):,}"])
rows += [["__H__", "Negative-control exposures (added one at a time)"]] + [[f"  {lab}", u, src, f"{int(_MT.loc[v, 'obs_year_min'])}-{int(_MT.loc[v, 'obs_year_max'])}", "None", f"{_imp(v):,}"] for v, lab, u, src in (("cpr_awareness_rate", "Resuscitation awareness", "%", "Survey"), ("road_pavement_rate", "Road pavement", "%", "KOSIS"), ("fires_per_10000", "Fires", "per 10,000", "KOSIS"))]
rows += [["__H__", "Comparison outcomes (principal model refitted)"], ["  Treated arthritis", "count", "NHIS", "2011-2024", "–", "0"], ["  Treated stomach cancer", "count", "NHIS", "2011-2024", "–", "0"]]
TF("Table S2. Source, unit, observed years, expected direction, and filled cells for each district characteristic, Korea, 2011-2024", ["Characteristic", "Unit", "Source", "Years", "Direction", "Filled cells"], rows,
   "Survey, Community Health Survey (district age-standardized rates); screening, national general health screening statistics; HIRA, register of care institutions of the Health Insurance Review and Assessment Service; KOSIS, Korean Statistical Information Service local indicators; census, population and housing census; KMA, Korea Meteorological Administration stations interpolated to districts; licensing, local business licensing data; register, public sports facility register; registry, resident registration; NHIS, National Health Insurance Service. Filled cells were interpolated within districts and then filled with district means; the basic livelihood rate additionally had 33 district-years replaced before standardization (Appendix A).")
# ── Table S3: 자료 점검 ──
cnt = lambda tag: len(re.findall(r"\[" + re.escape(tag) + r"\]", gate)); two = re.findall(r"\[연도 간 평균 2배 이상 차이\] (\S+):", gate)
ext = json.load(open(os.path.join(RS, "S41_extreme_flags.json"))); impc = json.load(open(os.path.join(RS, "S41_imputed_cells.json")))
zl = {"long_term_care_hospitals_per_100k_raw": "long-term care hospitals", "public_pools_per_100k_raw": "public pools"}
rows = [["All-zero or missing year", "≥98% of districts", "1 (post-2020 indicator)", "None (by design)"],
        ["Constant within a year", "1 value in a year", "1 (same indicator)", "None (by design)"],
        ["Year explains variance", "Year R² ≥ 0.80", "1 (same indicator)", "None (by design)"],
        ["Zero in every year", "5 to <60%", f"{len(zero)} (" + "; ".join(f"{zl[a]}, {b} districts" for a, b in zero) + ")", "Kept (true zeros)"],
        ["Twofold yearly means", "Max/min ≥ 2", f"{len(two)} (near-zero means, trends)", "Checked; kept"],
        ["Ratio above 100", "Maximum > 100", f"{cnt('비율형인데 100 초과')} (sex ratio)", "Kept (definition)"],
        ["Extreme values", ">5 IQR", f"{sum(ext.values())} cells, {sum(1 for v in ext.values() if v)} covariates", "Refilled in one model"],
        ["Missing cells", "No observation", f"{sum(impc.values()):,} cells, {len(impc)} covariates", "Filled; perturbed"],
        ["Collapsed welfare rate", "<20% of 2020-2024 mean", "33 district-years (11 cities)", "Interpolated"],
        ["Implausible precipitation", "<20% of adjacent years", "3 district-years", "Covariate dropped"],
        ["Duplicated population", "Repeats 2022", "1 (Changwon, 2023)", "Corrected"]]
assert nwarn == 3 + len(two) + cnt("비율형인데 100 초과") + len(zero), (nwarn, len(two))
TF("Table S3. Panel checks before modeling, with rules, thresholds, flags, and actions, Korea, 2011-2024", ["Check", "Threshold", "Flags in this panel", "Action"], rows,
   "Checks were run on the analytic panel of 3,206 district-years before any covariate model was fitted. Near-zero means of standardized columns produce twofold ratios without any change in the raw data.")
# ── Table S4: 사양 ──
PSF, SCR, BL, SMK, POOL, SPH = C.PSF, C.SCR, C.BL, C.SMK, C.POOL, C.SPH
NAMES = [("principal", "Principal model"), ("KH_typeI", "Knorr-Held type I"), ("KH_typeII", "Knorr-Held type II"), ("KH_typeIII", "Knorr-Held type III"), ("KH_typeIV", "Knorr-Held type IV"),
         ("icar_besag", "ICAR district effect"), ("iid_only", "IID district effect"), ("no_spatial", "No district effect"), ("knn3", "3 nearest neighbors"), ("knn4", "4 nearest neighbors"), ("knn5", "5 nearest neighbors"),
         ("pc_phi_flat", "Flat mixing prior"), ("pc_relaxA", "Relaxed priors A"), ("pc_relaxB", "Relaxed priors B"),
         ("B3_smooth_forced", "Smoothed sex ratio"), ("C1_poisson_lognormal", "Poisson, observation effect"), ("C2_rw2_year", "RW2 year effect"), ("C3_ar1_year", "AR1 year effect"), ("C4_sido_year_iid", "Province-by-year effect"), ("D1_spatial_plus", "Spatial+-type adjustment"),
         ("E0_nolag_from2012", "No lag, from 2012"), ("E1_lag1", "Lag 1 year"), ("E0_nolag_from2013", "No lag, from 2013"), ("E2_lag2", "Lag 2 years"), ("F3_extreme_R7", "Extreme values refilled"), ("G1_kchs_ma3", "Survey 3-year averages"), ("H4_odd_years", "Odd years"), ("H4_even_years", "Even years"),
         ("sage", "E by age only"), ("s8", "Coarser age groups in E"), ("s2", "Share aged 80+ omitted"), ("s577", "Queen graph, 577 edges"), ("parsimonious", "Parsimonious model"),
         ("H1_nco_ARTH", "Arthritis (comparison)"), ("H1_nco_GCA", "Stomach cancer (comparison)")]
SS = {**N["s43"], **N["s41"]}; WA = {**N["s43_waic"], **N["s41_waic"]}
for v in ("s577", "s2", "s8", "sage"): SS.update({(v, c): t for c, t in N["sens_main"][v].items()}); WA[v] = float(pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_fit.csv")).WAIC.iloc[0])
SS.update({("parsimonious", c): (r["IRR"], r["lo"], r["hi"], r["cred"]) for c, r in N["s50_pars"].items()}); WA["parsimonious"] = N["s50_moran"]["parsimonious"]["WAIC"]; WA["principal"] = N["waic_main"]
SS.update({("principal", c): (r["IRR"], r["lo"], r["hi"], r["cred"]) for c, r in N["main"].items()})
def cell(a, v): t = SS.get((a, v)); return "–" if t is None else st(t)
HN = {PSF: "Sports facilities", SCR: "Screening uptake", BL: "Basic livelihood", SMK: "Current smoking", POOL: "Swimming pools", SPH: "Single-person households"}
ALT14 = set(N["alt14"]); assert len(ALT14) == 14 and ALT14 <= {a for a, _ in NAMES}, sorted(ALT14 - {a for a, _ in NAMES})
MOR = {"principal": "principal", "parsimonious": "parsimonious", "no_spatial": "no_spatial", "iid_only": "iid_district", "icar_besag": "icar_district", "KH_typeI": "typeI_interaction"}
FOOT4 = "Values are rate ratios (95% credible intervals) per 1 standard deviation, with credibility judged from unrounded bounds; –, not in the model or not computed. For the Spatial+-type model, rate ratios are per 1 standard deviation of the residualized covariate. Models with observation-level effects (Knorr-Held type I and the Poisson model with an observation effect), different years, or different outcomes are not comparable by WAIC, and the WAIC of the first two is not shown. <sup>a</sup>One of the 14 alternative specifications. WAIC, widely applicable information criterion; ICAR, intrinsic conditional autoregressive; IID, independent and identically distributed; RW2, second-order random walk; AR1, first-order autoregressive; E, expected counts."
for part, cols in (("A", [PSF, SCR]), ("B", [BL, SMK]), ("C", [POOL, SPH])):
    rows = [[lab + ("<sup>a</sup>" if a in ALT14 else "")] + ([f"{WA[a]:,.0f}" if a in WA and not a.startswith("H1_") and a not in ("KH_typeI", "C1_poisson_lognormal") else "–", f"{N['s50_moran'][MOR[a]]['resid_moran_I']:.3f}" if a in MOR and MOR[a] in N["s50_moran"] else "–"] if part == "A" else []) + [cell(a, v) for v in cols] for a, lab in NAMES]
    TF(f"Table S4{part.lower()}. Rate ratios per 1 standard deviation across alternative specifications and comparison outcomes, Korea, 2011-2024 (part {part})", ["Specification"] + (["WAIC", "Residual Moran's I"] if part == "A" else []) + [HN[v] for v in cols], rows, FOOT4, fs=7)
# ── Table S5: 권역 ──
REG = [("Capital", "Capital region"), ("Chungcheong", "Chungcheong"), ("Honam", "Honam"), ("Yeongnam", "Yeongnam"), ("Gangwon_Jeju", "Gangwon-Jeju")]
RV = [v for v in (PSF, SCR, BL, SMK) if (v, "Capital") in N["s50_region"]]; assert RV == [PSF, SCR, BL, SMK], RV
rows = [[lab] + [st(N["s50_region"][(v, r)]) for v in RV] for r, lab in REG]
rows.append(["ΔWAIC vs common slope"] + [f"{N['s50_region_dwaic'][v]:+.1f}" for v in RV])
TF("Table S5. Region-specific rate ratios per 1 standard deviation for the subset-stable characteristics, Korea, 2011-2024", ["Region"] + [HN[v] for v in RV], rows,
   "Principal model with each characteristic interacted with five regions (capital region: Seoul, Incheon, Gyeonggi; Chungcheong: Daejeon, Sejong, North and South Chungcheong; Honam: Gwangju, North and South Jeolla; Yeongnam: Busan, Daegu, Ulsan, North and South Gyeongsang; Gangwon-Jeju), one characteristic at a time. ΔWAIC is the difference from the principal model; negative values favor region-specific slopes.")
# ── Fig. S1 ──
J.page_break(); _pp = J.para(""); _pp.add_run().add_picture(os.path.join(HERE, "figs", "ID_FigS1.png"), width=Cm(16))
J.para("<b>Fig. S1 Persistence of the district pattern of care for infectious and parasitic diseases, Korea, 2011-2024.</b> (a) Emerging hot spot analysis (Getis-Ord Gi* with Mann-Kendall trend) of empirical Bayes smoothed standardized treatment ratios; numbers of districts in parentheses. (b) Number of the three windows (2011-2015, 2016-2019, 2020-2024) in which each district was a residual hot or cold spot in the principal model refitted within the window.")
# ── STROBE·RECORD ──
DS = [x[4:].strip() for x in read_draft()["Discussion"] if x.startswith("### ")]; MH = [h for h, _ in C.METHODS]; RH = [h for h, _ in C.RESULTS]
CK = [("Title and abstract", "1; RECORD 1.1-1.3", "Title page; Abstract (data source and geographic level named)"), ("Background/rationale", "2", "Introduction"), ("Objectives", "3", "Introduction, final paragraph"),
      ("Study design", "4", f"Methods, {MH[0]}"), ("Setting", "5", f"Methods, {MH[0]}"),
      ("Participants", "6; RECORD 6.1-6.3", f"Methods, {MH[0]} (district populations; ecological; codes A00-B99)"), ("Variables", "7; RECORD 7.1", f"Methods, {MH[1]}; {MH[2]}; Table S2"),
      ("Data sources/measurement", "8", f"Methods, {MH[0]}; {MH[2]}; Table S2; Appendix A"), ("Bias", "9", f"Methods, {MH[3]}; {MH[4]}; Table S4"), ("Study size", "10", f"Methods, {MH[0]} (all 229 districts)"),
      ("Quantitative variables", "11", f"Methods, {MH[2]}"), ("Statistical methods", "12; RECORD 12.1-12.2", f"Methods, {MH[3]}; {MH[4]}; {MH[5]}; Appendix A (code-only linkage)"),
      ("Participants (flow)", "13; RECORD 13.1", "Not applicable (aggregate district data; no exclusions)"), ("Descriptive data", "14", f"Results, {RH[0]}; Table 1; Table S1"), ("Outcome data", "15", "Table 1; Fig. 1"),
      ("Main results", "16", f"Results, {RH[2]}; Table 2; Figs. 1-2"), ("Other analyses", "17", f"Results, {RH[3]}; {RH[4]}; Tables S4-S5"),
      ("Key results", "18", "Discussion, Principal findings"), ("Limitations", "19; RECORD 19.1", "Discussion, Limitations"), ("Interpretation", "20", "Discussion"), ("Generalizability", "21", "Discussion, Implications and Limitations"),
      ("Funding", "22", "Funding details"), ("Protocol, data, and code access", "RECORD 22.1", "Data availability statement")]
assert "Limitations" in DS and "Implications" in DS and "Principal findings" in DS
J.page_break()
J.table_fit("Appendix B. STROBE and RECORD checklist for this ecological study", ["Item", "No.", "Where reported"], [[a, re.sub(r"(\d)-(\d)", r"\1 to \2", b), re.sub(r"(\d)-(\d)", r"\1 and \2", c).replace("Figs. 1 and 2", "Figures 1 and 2")] for a, b, c in CK], "", fs_max=8, title_bold=False)
foot_row(J, "STROBE, Strengthening the Reporting of Observational Studies in Epidemiology; RECORD, Reporting of studies Conducted using Observational Routinely collected health Data.", 8, 12)
ps = os.path.join(OUT, "ESM_1.docx"); J.doc_title = "Online Resource 1"; J.save(ps)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_infect_esm", "--convert-to", "pdf", "--outdir", OUT, ps], check=True, capture_output=True)
print("saved", os.path.basename(ps))
