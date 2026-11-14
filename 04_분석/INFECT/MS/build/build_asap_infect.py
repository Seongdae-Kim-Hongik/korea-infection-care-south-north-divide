# build_asap_infect.py — 감염성·기생충성 질환 진료(INFECT) Applied Spatial Analysis and Policy(Springer) 원고 조립(2026-11-14).
#  표 아라비아 번호·제목, 그림 캡션 "Fig. 1"(볼드)·끝 마침표 없음·패널 소문자, 보충은 "Online Resource". 미국식 철자 유지.
import os, re, json, subprocess, unicodedata
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Cm
from jkms_engine import JKMS
import content_infect as C
from build_id_infect import read_draft, pandoc_cites, strip, KEYS, REFS, table1, table2, put_table, foot_row, FIGCAP, IRB, CONTRIB, FUNDING, ORCID, AFFIL, ADDRESS, LABEL, GROUPS
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; TITLE = C.TITLE
_zf = os.path.join(OUT, "zenodo_doi.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "[ZENODO DOI]"
REPO = "korea-infection-care-south-north-divide"; GITHUB = f"https://github.com/Seongdae-Kim-Hongik/{REPO}"
AI_TITLE = "Use of generative AI"
AI_STATEMENT = "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. The author reviewed and edited all output and takes full responsibility for the content of this publication."
COI = "The author has no relevant financial or non-financial interests to disclose."
FUNDING_S = "No funding was received for conducting this study."
CONSENT = "Not applicable. Only published aggregate statistics were used, and the institutional review board waived informed consent."
IRB_ANON = "The institutional review board of the author's institution approved the study and its continuing review and waived informed consent because only published aggregate statistics were used (approval details are given on the separate title page to preserve anonymity)."
def data_statement(anon=False):
    if anon: return "All source data are publicly available from the statistics cited in the Methods. The analysis code and the scripts that generate every number, table, and figure are publicly archived in a code repository with a persistent identifier; the link is given on the separate title page to preserve anonymity during review. The processed district-year analytic data are available on reasonable request."
    return f"All source data are publicly available from the statistics cited in the Methods. The analysis code and the scripts that generate every number, table, and figure are publicly archived on Zenodo (https://doi.org/{ZENODO}) and GitHub ({GITHUB}). The processed district-year analytic data are available from the author on reasonable request."

def surname(a): return re.sub(r"\s+[A-ZÀ-Ý]{1,4}$", "", a.strip())
def initials(a):
    m = re.search(r"\s([A-ZÀ-Ý]{1,4})$", a.strip()); return " ".join(f"{c}." for c in m.group(1)) if m else ""
def is_group(a): return not re.search(r"\s[A-ZÀ-Ý]{1,4}$", a.strip())
def auths(k): r = REFS[k]; return [r["authors"]] if r["type"] == "web" else r["authors"]
def _first_sur(k): a = auths(k)[0]; return a if is_group(a) else surname(a)
def base_label(k):
    s = [a if is_group(a) else surname(a) for a in auths(k)]
    if not is_group(auths(k)[0]) and len({auths(j)[0] for j in KEYS if _first_sur(j) == s[0]}) > 1: s[0] = f"{initials(auths(k)[0])} {s[0]}"
    return s[0] if len(s) == 1 else (f"{s[0]} & {s[1]}" if len(s) == 2 else f"{s[0]} et al.")
def fold(x): return "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c)).lower().replace(" ", "")
def list_sortkey(k):
    a = auths(k); return (fold(_first_sur(k)), fold(a[0]), len(a) if len(a) <= 2 else 3, tuple(fold(x) for x in a[1:]) if len(a) <= 2 else (), int(REFS[k]["year"]), REFS[k]["title"].lower())
SUFFIX = {}; _grp = {}
for k in KEYS: _grp.setdefault((tuple(auths(k)) if len(auths(k)) <= 2 else auths(k)[0], int(REFS[k]["year"])), []).append(k)
for ks in _grp.values():
    if len(ks) > 1:
        for i, k in enumerate(sorted(ks, key=lambda k: REFS[k]["title"].lower())): SUFFIX[k] = "abcdefgh"[i]
def year_str(k): return f"{REFS[k]['year']}{SUFFIX.get(k, '')}"
JFIX = {"Lancet (London, England)": "The Lancet", "BMJ (Clinical research ed.)": "BMJ", "PLoS medicine": "PLOS Medicine", "Sports medicine (Auckland, N.Z.)": "Sports Medicine",
        "The Lancet. Public health": "The Lancet Public Health", "The Lancet. Infectious diseases": "The Lancet Infectious Diseases", "Dermatology (Basel, Switzerland)": "Dermatology",
        "Epidemiology (Cambridge, Mass.)": "Epidemiology", "Health policy (Amsterdam, Netherlands)": "Health Policy", "JAMA dermatology": "JAMA Dermatology", "BMC public health": "BMC Public Health",
        "Euro surveillance : bulletin Europeen sur les maladies transmissibles = European communicable disease bulletin": "Eurosurveillance",
        "Clinical infectious diseases : an official publication of the Infectious Diseases Society of America": "Clinical Infectious Diseases",
        "Perspectives on psychological science : a journal of the Association for Psychological Science": "Perspectives on Psychological Science",
        "Human vaccines & immunotherapeutics": "Human Vaccines & Immunotherapeutics", "Acta dermato-venereologica": "Acta Dermato-Venereologica"}
ABBR = {"Polit Sci Res Methods": "Political Science Research and Methods", "Ann Inst Stat Math": "Annals of the Institute of Statistical Mathematics", "Geogr Anal": "Geographical Analysis",
        "The American Statistician": "The American Statistician", "Econometrica": "Econometrica", "J R Stat Soc Series B Stat Methodol": "Journal of the Royal Statistical Society: Series B (Statistical Methodology)",
        "Stat Sci": "Statistical Science", "Biometrika": "Biometrika"}
SMALL = {"of", "and", "the", "in", "for", "on", "a", "an", "to", "&", "de"}
def jtitle(r):
    j = ABBR.get(r["journal"]) or r.get("journal_full") or r["journal"]
    if j in JFIX: return JFIX[j]
    if r["journal"] in ABBR: return j
    if j.startswith("The ") and not j.startswith(("The Lancet", "The American Statistician")): j = j[4:]
    j = re.sub(r"\s*[:=].*$", "", j)
    out = []
    for i, x in enumerate(j.split()):
        if i and x.lower() in SMALL: out.append(x.lower())
        else: out.append("-".join(y[:1].upper() + y[1:] for y in x.split("-")))
    return " ".join(out)
ACR = {"COVID-19", "US", "UK", "WHO", "INLA", "BMI", "GBD", "Korea", "Korean", "Koreans", "Europe", "European", "Japan", "Japanese", "Asia", "Asian", "Bayesian", "Laplace", "Poisson", "Gaussian", "Dutch", "Danish",
       "England", "Scotland", "Italy", "Italian", "China", "Chinese", "Taiwan", "Canada", "Australia", "Germany", "German", "Swiss", "Spain", "Spanish", "Brazil", "Mann-Kendall", "Kendall", "Moran", "Getis", "Ord",
       "Besag", "York", "Mollié", "Knorr-Held", "E-value", "E-Value", "STROBE", "RECORD", "Hodgkin", "Haddon",
       "Jeolla", "Gyeongsang", "Gangwon", "Seoul", "Busan", "Nilsson's", "Iran", "Pennsylvania", "UK-based", "Indonesian", "New", "Zealand", "Swedish", "Sweden", "Norway", "Finnish", "American", "Americans", "British", "Hispanic", "Greek", "Turkish", "Thailand", "Thai", "Vietnam"}
PHRASES = ("UK Clinical Practice Research Datalink", "UK Biobank", "South Korea", "North America", "New Zealand", "Global Burden of Disease Study", "Community Health Survey", "Medical Aid", "National Health Insurance Service", "National Health Insurance", "Republic of Korea")
def sentence(t):   # APA 문장형 제목: 첫 글자·쌍점 뒤·고유명사·약어만 대문자
    out = []; cap = True
    for w in t.split(" "):
        core = re.sub(r"^[^\w]+|[^\w']+$", "", w)
        keep = core in ACR or any(any(c.isupper() for c in q[1:]) for q in core.split("-")) or any(q in ACR for q in core.split("-"))
        out.append(w if keep else (w[:1].upper() + w[1:].lower() if cap else w.lower()))
        cap = w.endswith((":", "?", "."))
    t2 = " ".join(out)
    for ph in PHRASES: t2 = re.sub(re.escape(ph), ph, t2, flags=re.I)
    return t2
def apa_author(a): return a if is_group(a) else f"{surname(a)}, {initials(a)}"
def ref(k):   # APA 7: Surname, I. I., & Surname, I. (Year). Title. Journal, vol(issue), pages. https://doi.org/...
    r = REFS[k]
    if r["type"] == "web":
        if "[Computer software]" in r["title"]: return f"{r['authors']}. ({year_str(k)}). <i>{r['title'].split(' (Version')[0]}</i> (Version{r['title'].split(' (Version')[1]}. {r['url']}"
        import datetime as _dt; acc = _dt.datetime.strptime(r["accessed"], "%d %B %Y"); acc = f"{acc:%B} {acc.day}, {acc.year}"
        return f"{r['authors']}. ({year_str(k)}). <i>{r['title']}</i> [Data set; in Korean]. Retrieved {acc}, from {r['url']}"
    au = [apa_author(a) for a in r["authors"]]
    if len(au) > 20: au = au[:19] + ["…", au[-1]]
    if len(au) == 1 and is_group(r["authors"][0]): au = [au[0] + "."]
    a = au[0] if len(au) == 1 else (f"{au[0]}, & {au[1]}" if len(au) == 2 else (", ".join(au[:-1]) + ", & " + au[-1] if "…" not in au else ", ".join(au[:19]) + ", … " + au[-1]))
    t = sentence(r["title"].rstrip(".")); t = t if t.endswith(("?", "!")) else t + "."
    s = f"{a} ({year_str(k)}). {t} <i>{jtitle(r)}</i>"
    s = s.replace(".. (", ". (", 1)
    vol = str(r.get("vol", "")).strip(); iss = str(r.get("issue", "")).strip(); pg = str(r.get("pages", "")).strip().rstrip(".")
    m = re.match(r"^(\d+)\s*Suppl\s*(\d+)$", vol)
    if m: s += f", <i>{m.group(1)}</i>(Suppl. {m.group(2)})"
    elif vol: s += f", <i>{vol}</i>" + (f"({iss})" if iss and "Suppl" not in iss else "")
    if pg: s += f", {pg.replace('-', chr(8211))}"
    s += "."
    if r.get("doi"): s += f" https://doi.org/{r['doi']}"
    return s

class TX(JKMS):
    raw = False; table_bold = False
    def __init__(self, cite="ay"):
        super().__init__(cite=cite)
    def aylabel(self, k): return ((fold(base_label(k)), int(REFS[k]["year"]), SUFFIX.get(k, "")), base_label(k), year_str(k))
    def _ay(self, tok):   # (Surname, Year; Surname & Surname, Year; Surname et al., Year, Year)
        keys = [k.strip() for k in tok[2:-2].split(",") if k.strip()]
        for k in keys: self.cite_num(k)
        labs = sorted((self.aylabel(k) for k in keys), key=lambda x: x[0]); out = []
        for sk, lab, yr in labs:
            if out and out[-1][0] == lab: out[-1][1].append(yr)
            else: out.append([lab, [yr]])
        return "(" + "; ".join(f"{l}, {', '.join(y)}" for l, y in out) + ")"
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)
            text = re.sub(r"(\{\{[^}]+\}\})", lambda m: self._ay(m.group(1)), text)
        return super()._emit(p, text, sz, bold, italic)

def ANON(t):   # 본문 익명화
    t = t.replace(IRB, IRB_ANON)
    assert "Hongik" not in t and "7002340" not in t, t[:80]
    return t
METHODS_H = [h for h, _ in C.METHODS]; RESULTS_H = [h for h, _ in C.RESULTS]
def numbered(D):
    disc = [x[4:].strip() for x in D["Discussion"] if x.startswith("### ") and not x.startswith("### Conclusions")]
    return disc
def build(bw=0, aw=0):
    D = read_draft(); J = TX()
    J.para(f"<b>{TITLE}</b>")
    J.head("Abstract", 1)
    for p in D["Abstract"]: J.para(p)
    J.para(f"<b>Keywords</b> {C.KEYWORDS}", before=6)
    J.page_break(); J.counting = True
    J.head("1 Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("2 Data and Methods", 1)
    for i, (h, p) in enumerate(C.METHODS, 1): J.head(f"2.{i} {h}", 2); J.para(ANON(pandoc_cites(p)), indent=True)
    J.head("3 Results", 1)
    for i, (h, p) in enumerate(C.RESULTS, 1): J.head(f"3.{i} {h}", 2); J.para(pandoc_cites(p), indent=True)
    J.head("4 Discussion", 1); i = 0; concl = False
    for p in D["Discussion"]:
        if p.startswith("### Conclusions"): J.head("5 Conclusions", 1); concl = True; continue
        if p.startswith("### "): i += 1; J.head(f"4.{i} {p[4:].strip()}", 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.counting = False
    J.head("Statements and Declarations", 1)
    J.para("<b>Competing interests</b> " + "Disclosed on the separate title page.")
    J.para("<b>Ethics approval</b> " + IRB_ANON)
    J.para("<b>Data availability</b> " + data_statement(anon=True))
    assert sorted(set(J.cites)) == KEYS, (set(J.cites) ^ set(KEYS))
    J.page_break(); J.head("References", 1); rl = []
    for k in sorted(set(J.cites), key=list_sortkey):
        s_ = ref(k); rl.append(s_); p = J.para(s_); p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.first_line_indent = Cm(-1.0)
    J.page_break(); put_table(J, table1())
    J.page_break(); put_table(J, table2(), fs=8)
    J.page_break(); J.head("Figure captions", 1)
    for k in sorted(FIGCAP):   # ASAP: 그림은 본문 파일 안에(캡션 아래 그림), 고해상도 TIFF는 별도 업로드
        J.para(f"<b>Fig. {k}</b> {FIGCAP[k].rstrip('.')}")
        J.doc.add_paragraph().add_run().add_picture(os.path.join(HERE, "figs", f"ID_Fig{k}.png"), width=Cm(16))
    return J, rl, D

def fix_orphans(path, heads, max_iter=10):   # 쪽 끝 고아 제목 → 그 제목 앞에 쪽 나눔. 바로 앞 문단도 제목이면 그 앞(제목 묶음 통째로)
    from docx import Document
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_infect_asap", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pages = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f"); orphan = None
        for pg in pages:
            ls = [re.sub(r"^\d+\s+", "", l.strip()) for l in pg.split("\n") if l.strip()]; ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads: orphan = ls[-1]; break
        if orphan is None: return
        d = Document(path); P = d.paragraphs
        i = next(k for k, p in enumerate(P) if p.text.strip() == orphan)
        while i > 0 and P[i - 1].text.strip() in heads: i -= 1
        p = P[i]; r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); p._p.insert(1 if p._p.pPr is not None else 0, r)
        d.save(path); print("orphan fixed:", p.text.strip())

def docx_bw(path):
    from docx import Document
    t = "\n".join(x.text for x in Document(path).paragraphs)
    return len(t[t.find("\n1 Introduction\n"):t.find("\nStatements and Declarations\n")].split())

if __name__ == "__main__":
    p = os.path.join(OUT, "Manuscript.docx"); D = read_draft()
    aw = sum(len(strip(x).split()) for x in D["Abstract"]); assert 150 <= aw <= 250, aw
    J, rl, D = build(); J.doc_title = "Manuscript"; J.save(p); bw = docx_bw(p)
    J, rl, D = build(bw, aw); J.doc_title = "Manuscript"; J.save(p); assert docx_bw(p) == bw
    from docx import Document
    heads = {x.text.strip() for x in Document(p).paragraphs if re.match(r"^(\d(\.\d+)? |Abstract$|References$|Figure captions$|Statements and Declarations$)", x.text.strip())}
    fix_orphans(p, heads)
    tot = len("\n".join(x.text for x in Document(p).paragraphs).split())
    open(os.path.join(OUT, "wordcount_asap.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\nrefs={len(KEYS)}\ntables=2\nfigures=2\ntitle_words={len(TITLE.split())}\ntotal_words={tot}\n")
    print(f"body {bw} | abstract {aw} | refs {len(KEYS)} | total {tot} | title words {len(TITLE.split())}")
