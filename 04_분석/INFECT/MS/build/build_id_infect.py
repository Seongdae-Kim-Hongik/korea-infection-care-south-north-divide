# build_id_infect.py — analysis/manuscript script for the study of care for infectious and parasitic diseases across Korean districts, 2011-2024.
#  규정(44_감염병진료시공간_ID/00_저널가이드/Infectious_Diseases_투고규정_요약_261109.md): Research Article, 구조화 초록 250(Background/Objectives/Methods/Results/Conclusion),
#  키워드 5-7, 단어 제한 없음(단어 수 표기), 단일 익명(본문 1쪽 제목면), 순서 = 제목면·초록·키워드·본문·감사·선언·참고문헌·표(각 쪽)·그림 범례 목록, 그림 별도 파일,
#  Funding details·Disclosure statement·Declaration of generative AI use·Data availability statement, 형식 자유(Vancouver 유지), 미국식 철자.
import os, re, json, subprocess
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Cm
from jkms_engine import JKMS
# (LC 미국식: british.brit 사용 안 함)
import content_infect as C
brit = lambda t: t
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_infect.json"), encoding="utf-8"))
DRAFT = os.path.join(MS, "draft", "01_manuscript.md")
_zf = os.path.join(OUT, "zenodo_doi.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "[ZENODO DOI]"
REPO = "infectious-disease-care-districts-korea"; GITHUB = f"https://github.com/Seongdae-Kim-Hongik/{REPO}"
TITLE = C.TITLE; ORCID = "0000-0002-1525-0091"
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
AI_TITLE = "Declaration of generative AI use"
AI_STATEMENT = "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. The author reviewed and edited all output and takes full responsibility for the content of this publication."
IRB = "The Institutional Review Board of Hongik University approved the study on November 4, 2025 (7002340-202511-HR-012) and its continuing review on November 3, 2026 (7002340-202611-HR-040), and waived informed consent because only published aggregate statistics were used."
FUNDING = "No funding was obtained for this study."
CONTRIB = "Seongdae Kim: Conceptualization, Methodology, Software, Formal analysis, Data curation, Visualization, Writing – original draft, Writing – review & editing."
COI = "The author reports there are no competing interests to declare."
def data_statement(): return f"All source data are publicly available from the statistics cited in the Methods. The analysis code and the scripts that generate every number, table and figure are archived on Zenodo (https://doi.org/{ZENODO}); the files are restricted during peer review, are accessible to editors and reviewers through a private link provided with the submission, and will be made public on acceptance together with a public GitHub repository. The processed district-year analytic data are available from the author on reasonable request."

def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def pandoc_cites(t): return re.sub(r"\s*\[(@[^\]]+)\]", lambda m: " {{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)
def strip(t): return re.sub(r"\{\{[^}]+\}\}|<[^>]+>", "", re.sub(r"\s*\[@[^\]]+\]", "", t))
def all_keys():
    src = open(os.path.join(HERE, "content_infect.py"), encoding="utf-8").read() + open(DRAFT, encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
    return sorted(k for k in {k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")} if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k))
KEYS = all_keys()

KEEP = {"CT", "EGFR", "NSCLC", "Non-Small", "Asian", "Italy", "North-Eastern", "Hodgkin's", "European", "IARC", "National", "Lung", "Cancer", "Screening", "Program", "Health", "Insurance", "System", "Information", "Database", "Service", "Korea", "Korean", "Bayesian", "United", "States", "US", "U.S.", "Gaussian", "Laplace", "Poisson", "Japan", "Japanese", "Taiwan", "China", "Chinese", "England", "Australia", "Brazilian", "Canada", "Canadian", "Pennsylvania", "Georgia",
        "Alabama", "North", "Carolina", "Asia-Pacific", "Asia", "Pacific", "Nilsson's", "E-Value", "Haddon", "Shanghai", "Iran", "Latin", "America", "UK", "Canada", "British", "Columbia", "Nonmetropolitan", "STROBE", "Statement", "Kanagawa", "Tokyo", "DC"}
def sent(t):
    w = t.split(" "); caps = sum(1 for x in w[1:] if x[:1].isupper())
    if len(w) < 4 or caps < 0.5 * (len(w) - 1): return t
    out = [w[0]]
    for x in w[1:]:
        core = x.strip("(),:;.?")
        keep = core in KEEP or core.isupper() or any(c.isdigit() for c in core) or out[-1].endswith((":", "?")) or (core.split("-")[0] in KEEP)
        if not keep: x = x[:1].lower() + x[1:]
        x = "-".join([x.split("-")[0]] + [y if (y in KEEP or y.isupper()) else y[:1].lower() + y[1:] for y in x.split("-")[1:]])
        out.append(x)
    t2 = " ".join(out)
    for ph in ("Global Burden of Disease Study", "Community Health Survey", "E-value", "Nilsson's Power Model"): t2 = re.sub(re.escape(ph), ph, t2, flags=re.I)
    return t2.replace("E-Value", "E-value")
def ref(k):
    r = REFS[k]
    if r["type"] == "web": return f"{r['authors']}. {r['title']} [Internet]. {r.get('year', '')} [cited {r['accessed']}]. Available from: {r['url']}"
    au = r["authors"]; a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:6]) + ", et al"
    t = sent(r["title"].rstrip(".")); t = t if t.endswith(("?", "!")) else t + "."
    vol = str(r.get("vol", "")).strip(); iss = str(r.get("issue", "")).strip(); pg = str(r.get("pages", "")).strip().rstrip(".")
    s_ = f"{a}. {t} {r['journal']}. {r['year']}"
    if vol: s_ += f";{vol}" + (f"({iss})" if iss else "")
    if pg: s_ += f":{pg}"
    return s_ + "." + (f" doi:{r['doi']}" if r.get("doi") else "")

class TX(JKMS):
    raw = False; table_bold = False   # 표 데이터 셀 볼드 금지(시리즈 규칙)
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = brit(text); text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)   # brit = 항등(미국식), 음수는 U+2212
        return super()._emit(p, text, sz, bold, italic)
    def head(self, text, level=1):   # LC: 번호 절(1. Introduction / 2.1. ...)은 build()가 번호를 붙여 넘김
        return super().head(text, level)

TAB1_COV = [("pop80_share", "Population aged 80 years or older, %"), ("urban_population_share", "Urban population share, %"),
            ("screening_suspected_diabetes_share", "Suspected diabetes at screening, %"), ("screening_normalB_obesity_share", "Obesity management needed at screening, %"),
            ("current_smoking_rate", "Current smoking, %"), ("long_term_care_hospitals_per_100k", "Long-term care hospitals per 100,000"),
            ("basic_livelihood_rate", "Basic livelihood security recipients, %"), ("single_person_household_share", "Single-person households, %"),
            ("annual_mean_temperature", "Annual mean temperature, °C"), ("public_baths_per_10k", "Public bathhouses per 10,000"), ("public_pools_per_100k", "Public swimming pools per 100,000"),
            ("screening_uptake", "General health screening uptake, %"), ("walking_practice_rate", "Walking practice, %"), ("moderate_pa_rate", "Moderate-or-vigorous activity, %"),
            ("public_sports_facilities_per_100k", "Public sports facilities per 100,000")]
def table1():
    T = N["T1"]; cols = ["W1_2011-15", "W2_2016-19", "W3_2020-24", "2011-2024"]
    rows = [["__H__", "People treated for infectious and parasitic diseases"],
            ["  District-years, n"] + [f"{T[c]['n']:,}" for c in cols],
            ["  Treated person-years, million<sup>a</sup>"] + [f"{T[c]['cases']/1e6:.1f}" for c in cols],
            ["  Population person-years, million"] + [f"{T[c]['py']/1e6:.1f}" for c in cols],
            ["  Crude rate per 100,000"] + [f"{T[c]['crude']:,.0f}" for c in cols],
            ["  Sex- and age-standardized rate per 100,000<sup>b</sup>"] + [f"{T[c]['asr']:,.0f}" for c in cols],
            ["  District STR, median<sup>c</sup>"] + [f"{T[c]['sir_med']:.2f}" for c in cols],
            ["  District STR, 10th-90th percentile<sup>c</sup>"] + [f"{T[c]['sir_p10']:.2f}-{T[c]['sir_p90']:.2f}" for c in cols],
            ["__H__", "District characteristics, mean (standard deviation)"]]
    for v, lab in TAB1_COV:
        mx = max(abs(T[c]['cov'][v][0]) for c in cols); dp = 0 if mx >= 100 else (2 if mx < 1 else 1)
        rows.append([f"  {lab}"] + [f"{T[c]['cov'][v][0]:,.{dp}f} ({T[c]['cov'][v][1]:,.{dp}f})" for c in cols])
    foot = (f"<sup>a</sup>Unique people treated in a year with a disease in Chapter I (A00-B99) of the International Classification of Diseases, 10th revision, as the principal diagnosis, summed over years. "
            f"<sup>b</sup>Direct standardization to the 2015 national population by sex and ten age groups (to 75 years or older); window values are means of annual rates ({N['asr_2011']:,.0f} in 2011 and {N['asr_2024']:,.0f} in 2024). "
            "<sup>c</sup>Observed over sex- and age-standardized expected counts summed over the window. STR, standardized treatment ratio.")
    return ("Table 1. People treated for infectious and parasitic diseases and district characteristics by calendar window, 3,206 district-years in Korea, 2011-2024", ["Characteristic", "2011-2015", "2016-2019", "2020-2024", "2011-2024"], rows, foot)

GROUPS = [("Host susceptibility", ["screening_suspected_diabetes_share", "screening_normalB_obesity_share", "current_smoking_rate", "long_term_care_hospitals_per_100k"]),
          ("Socioeconomic position", ["basic_livelihood_rate", "single_person_household_share"]),
          ("Skin and mucosal exposure", ["annual_mean_temperature", "public_baths_per_10k", "public_pools_per_100k"]),
          ("Care-seeking", ["screening_uptake"]),
          ("Physical activity", ["walking_practice_rate", "moderate_pa_rate", "public_sports_facilities_per_100k"]),
          ("Forced controls", ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"])]
LABEL = {"screening_suspected_diabetes_share": "Suspected diabetes", "screening_normalB_obesity_share": "Obesity management needed",
         "current_smoking_rate": "Current smoking", "long_term_care_hospitals_per_100k": "Long-term care hospitals",
         "basic_livelihood_rate": "Basic livelihood recipients", "single_person_household_share": "Single-person households",
         "annual_mean_temperature": "Annual mean temperature", "public_baths_per_10k": "Public bathhouses", "public_pools_per_100k": "Public swimming pools",
         "screening_uptake": "Health screening uptake", "walking_practice_rate": "Walking practice", "moderate_pa_rate": "Moderate-or-vigorous activity",
         "public_sports_facilities_per_100k": "Public sports facilities",
         "urban_population_share": "Urban population share", "physicians_per_1000": "Physicians per 1,000", "sex_ratio": "Sex ratio", "fiscal_independence": "Fiscal autonomy", "pop80_share": "Aged 80 years or older"}
from decimal import Decimal, ROUND_HALF_UP
_pct = lambda f: str(int(Decimal(str(round(100 * f, 6))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
def table2():
    rows = []; assert sum(len(v) for g, v in GROUPS[:-1]) == N["n_hyp"] and set(LABEL) == set(N["main"])
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v); k1 = N["s43"][("KH_typeI", v)]; k4 = N["s43"][("KH_typeIV", v)]
            rows.append([f"  {LABEL[v]}", f"{m['IRR']:.3f} ({m['lo']:.3f}-{m['hi']:.3f})", _pct(mv["cred_frac"]) if mv else "–",
                         f"{k1[0]:.3f} ({k1[1]:.3f}-{k1[2]:.3f})", f"{k4[0]:.3f} ({k4[1]:.3f}-{k4[2]:.3f})"])
    foot = (f"RR, rate ratio per 1 standard deviation; CrI, credible interval. Units as in Table 1. Credibility was judged from unrounded interval bounds. Principal model, negative binomial with a Besag-York-Mollié 2 district effect and random-walk and independent year effects (n={N['n_rows']:,} district-years); all 13 district characteristics and five forced controls were included together. "
            f"<sup>a</sup>Share of the 200 covariate-subset fits containing the characteristic in which the CrI excluded 1 (credible), in either direction; –, forced into every fit. "
            f"<sup>b</sup>Principal model plus a Knorr-Held space-time interaction: type I (independent district-year effects, which act as observation-level effects, so its widely applicable information criterion is not compared) and type IV (district-specific time trends structured in space and time; widely applicable information criterion {abs(N['s43_waic']['KH_typeIV'] - N['waic_main']):,.0f} lower than the principal model).")
    return ("Table 2. District characteristics and sex- and age-standardized treatment for infectious and parasitic diseases in Korea, 2011-2024, in the principal and space-time interaction models",
            ["Characteristic", "Principal RR\n(95% CrI)", "Subsets, %<sup>a</sup>", "Type I RR\n(95% CrI)<sup>b</sup>", "Type IV RR\n(95% CrI)<sup>b</sup>"], rows, foot)

FIGCAP = {
 1: "Residual geography, trend, and composition of care for infectious and parasitic diseases in Korea. (a) Residual spatial rate ratio by district in 2011-2024, the exponentiated posterior mean of the Besag-York-Mollié 2 district effect from the principal model, that is, the district treatment ratio not explained by sex, age, the 13 characteristics, the forced controls, or year effects; hot and cold spots have a posterior probability of a residual rate ratio above 1 greater than 0.95 or less than 0.05. Province boundaries are drawn. (b) Crude and directly sex- and age-standardized rates of people treated per 100,000, 2011-2024. (c) Shares of national code-level counts by diagnostic group, 2015-2024, from three-character code statistics; a person treated under two codes is counted under both. STIs, infections with a predominantly sexual mode of transmission.",
 2: "Rate ratios per 1 standard deviation with 95% credible intervals for public sports facilities, general health screening uptake, basic livelihood security recipients, and current smoking, the four subset-stable characteristics, Korea, 2011-2024. Estimates are shown from the principal model; the principal model with province-by-year effects and with Knorr-Held type I and IV space-time interactions; the between-district and within-district components; and the principal model refitted to people treated for arthritis and for stomach cancer as comparison outcomes.",
}
def foot_row(J, text, sz=9, ls=15):
    from docx.enum.text import WD_LINE_SPACING
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs=9):
    c = J.counting; J.counting = False; J.table_fit(t[0], t[1], t[2], "", fs_max=fs, title_bold=False); foot_row(J, t[3], 8); J.counting = c

def build(bw=0, aw=0):
    D = read_draft(); J = TX(cite="bracket")
    J.para(f"<b>{TITLE}</b>")
    J.para("Seongdae Kim", before=6)
    J.para(AFFIL)
    J.para(f"<b>Corresponding author:</b> Seongdae Kim, {ADDRESS}. E-mail: kimsd@hongik.ac.kr. ORCID: {ORCID}", before=6)
    J.para(f"<b>Word count:</b> abstract {aw} words; main text {bw:,} words. <b>Tables and figures:</b> 2 tables and 2 figures. <b>Supplementary material:</b> 1 file.", before=6)
    J.head("Abstract", 1)
    for p in D["Abstract"]: J.para(p)
    J.para(f"<b>Keywords:</b> {C.KEYWORDS}", before=6)
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("Materials and methods", 1)
    for h, p in C.METHODS: J.head(h, 2); J.para(pandoc_cites(p), indent=True)
    J.head("Results", 1)
    for h, p in C.RESULTS: J.head(h, 2); J.para(pandoc_cites(p), indent=True)
    J.head("Discussion", 1)
    for p in D["Discussion"]:
        if p.startswith("### Conclusions"): J.head("Conclusions", 1); continue
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.counting = False
    J.head("Acknowledgments", 1); J.para("None.")
    J.head("Ethics approval", 1); J.para(IRB)
    J.head("Author contributions", 1); J.raw = True; J.para(CONTRIB); J.raw = False
    J.head("Funding details", 1); J.para(FUNDING)
    J.head("Disclosure statement", 1); J.para(COI)
    J.head(AI_TITLE, 1); J.para(AI_STATEMENT)
    J.head("Data availability statement", 1); J.para(data_statement())
    assert sorted(J.cites) == KEYS, (set(J.cites) ^ set(KEYS))
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for i, k in enumerate(J.cites, 1): s_ = f"{i}. " + ref(k); rl.append(s_); J.para(s_)
    J.raw = False
    J.page_break(); put_table(J, table1())
    J.page_break(); put_table(J, table2(), fs=8)
    J.page_break(); J.head("Figure captions", 1)
    for k in sorted(FIGCAP): J.para(f"<b>Figure {k}.</b> {FIGCAP[k]}")
    return J, rl, D

def docx_bw(path):   # 본문 단어 수: Introduction ~ Conclusions 끝(Acknowledgments 직전)
    from docx import Document
    t = "\n".join(x.text for x in Document(path).paragraphs)
    return len(t[t.find("\nIntroduction\n"):t.find("\nAcknowledgments\n")].split())
def fix_orphans(path, heads, max_iter=8):
    from docx import Document
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_infect_id", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pages = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f"); orphan = None
        for pg in pages:
            ls = [re.sub(r"^\d+\s+", "", l.strip()) for l in pg.split("\n") if l.strip()]; ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads: orphan = ls[-1]; break
        if orphan is None: return
        d = Document(path)
        for p in d.paragraphs:
            if p.text.strip() == orphan:
                r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); p._p.insert(1 if p._p.pPr is not None else 0, r); break
        d.save(path); print("orphan fixed:", orphan)

