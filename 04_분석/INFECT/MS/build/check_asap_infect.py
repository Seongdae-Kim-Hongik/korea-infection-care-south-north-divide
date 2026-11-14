# check_asap_infect.py — INFECT Applied Spatial Analysis and Policy(Springer) 검사기(2026-11-14). 규정 > 플레이북(3선 표·네모·지문·익명) > 문체·수치. FAIL 0이면 PASS.
import os, re, json, subprocess, zipfile
from docx import Document
from docx.oxml.ns import qn
from PIL import Image
import content_infect as C
from build_asap_infect import read_draft, TITLE, ORCID, KEYS, REFS, AI_STATEMENT, AI_TITLE, GITHUB, ZENODO, CONTRIB, IRB, COI, FUNDING_S, base_label, year_str, list_sortkey
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out")
N = C.N; R = []
def ok(c, m): R.append(("ok  " if c else "FAIL") + " " + m)
W = dict(l.split("=") for l in open(os.path.join(OUT, "wordcount_asap.txt")).read().split())
D = read_draft(); AB = D["Abstract"]; ab = " ".join(AB)
MSF, TPF, ESF, CLF = "Manuscript.docx", "Title_Page.docx", "ESM_1.docx", "Cover_Letter.docx"
for f in (MSF, TPF, ESF, CLF, "Figures/Fig1.tif", "Figures/Fig2.tif"): ok(os.path.exists(os.path.join(OUT, f)), f"파일 {f}")
# 1. ASAP 규정(00_저널가이드/ASAP_submission_guidelines_261114.md)
ok(int(W["total_words"]) <= 8000, f"원고 전체 {W['total_words']}단어 ≤ 8,000(참고문헌·표 포함)")
aw = sum(len(re.sub(r"<[^>]+>|\s*\[@[^\]]+\]", "", p).split()) for p in AB); ok(150 <= aw <= 250 and aw == int(W["abstract_words"]), f"초록 {aw}단어 150-250")
ok(len(AB) == 1 and not re.search(r"<b>", ab), "초록 비구조 한 문단")
ok(not re.search(r"\[@", ab) and not re.search(r"\b(SD|STR|CrI|BYM2|WAIC|RR|ICD|IRR)\b", ab), "초록에 인용·정의 안 된 약어 없음")
ok("2011" in ab and "2024" in ab, "초록에 자료 기간")
KW = [k.strip() for k in C.KEYWORDS.split(";")]; ok(4 <= len(KW) <= 6, f"키워드 {len(KW)}개(4-6)")
ok(":" not in TITLE and "229" not in TITLE and "standardi" not in TITLE.lower() and not re.search(r"\b[A-Z]{2,}\b", TITLE) and len(TITLE.split()) <= 22, "제목 쌍점·약어·시리즈 틀 없음")
d = Document(os.path.join(OUT, MSF)); _ps = [p.text.strip() for p in d.paragraphs]; _dx = "\n".join(_ps)
ok("Statements and Declarations" not in _dx and "Data availability" not in _dx, "원고에 선언문 블록 없음(포털 칸에만)")
heads = [p for p in _ps if re.match(r"^\d+(\.\d+)* [A-Z]", p) and len(p) < 90]
ok(heads[:2] == ["1 Introduction", "2 Data and Methods"] and all(h.count(".") <= 2 for h in heads) and "5 Conclusions" in heads, f"십진 제목 3단계 이하({len(heads)}개)")
ok(len(d.tables) == 2, "표 2")
ok(zipfile.ZipFile(os.path.join(OUT, MSF)).read("word/document.xml").decode().count("<w:drawing") == 2, "그림 2개 본문 파일 안(캡션 아래)")
ok(all(re.fullmatch(r"Fig\. \d [^\n]*[^.]", p) for p in _ps if p.startswith("Fig. ")) and sum(p.startswith("Fig. ") for p in _ps) == 2, "그림 캡션 'Fig. n'·끝 마침표 없음")
for k in (1, 2):
    im = Image.open(os.path.join(OUT, "Figures", f"Fig{k}.tif")); dpi = round(im.info.get("dpi", (0, 0))[0])
    ok(im.mode == "RGB" and dpi >= 600 and getattr(im, "n_frames", 1) == 1, f"Fig{k}.tif RGB·{dpi} dpi(복합 그림 ≥600)·폭 {im.size[0]}px")
# 2. 이중 익명
sup = "\n".join(p.text for p in Document(os.path.join(OUT, ESF)).paragraphs) + "\n" + "\n".join(c.text for t in Document(os.path.join(OUT, ESF)).tables for r in t.rows for c in r.cells)
ID = r"Seongdae|Hongik|7002340|" + "www" + "wrte" + r"|kimsd|" + ORCID + r"|zenodo|github|Seongdae-Kim|Wausan|Mapo"
for nm, tx in (("원고", _dx + "\n" + "\n".join(c.text for t in d.tables for r in t.rows for c in r.cells)), ("보충", sup)):
    hit = re.findall(ID, tx, re.I); ok(not hit, f"{nm} 저자 식별 정보 없음 {hit[:3]}")
for f in (MSF, ESF):
    core = zipfile.ZipFile(os.path.join(OUT, f)).read("docProps/core.xml").decode()
    ok("<dc:creator></dc:creator>" in core or "<dc:creator/>" in core, f"{f} 작성자 메타 비움")
tp = "\n".join(p.text for p in Document(os.path.join(OUT, TPF)).paragraphs)
for t in ("Seongdae Kim", "kimsd@hongik.ac.kr", ORCID, "Hongik University", "Statements and Declarations", "Funding", "Competing interests", "Ethics approval", "Consent to participate", "Data availability", "Code availability", "Author contributions", AI_TITLE, "7002340-202611-HR-040", f"https://doi.org/{ZENODO}", GITHUB):
    ok(t in tp, f"제목면 '{t[:40]}'")
ok(AI_STATEMENT in tp and IRB in tp and FUNDING_S in tp and COI in tp, "제목면 AI·IRB·연구비·이해충돌 정본 문장")
ok(AI_STATEMENT == "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. The author reviewed and edited all output and takes full responsibility for the content of this publication.", "AI 고지 정본(번역·첨삭만)")
i0, i1 = _ps.index("References"), next(i for i, p in enumerate(_ps) if p.startswith("Table 1. "))
refl = [p for p in _ps[i0 + 1:i1] if p]
ok(len(refl) == len(KEYS) == int(W["refs"]), f"참고문헌 {len(refl)}편")
exp = [k for k in sorted(KEYS, key=list_sortkey)]
import unicodedata as _u
_fk = ["".join(c for c in _u.normalize("NFKD", r.split(",")[0].split(".")[0]) if not _u.combining(c)).lower().replace(" ", "") for r in refl]
ok(_fk == sorted(_fk), f"참고문헌 첫 저자 알파벳순 {[ (a,b) for a,b in zip(_fk,_fk[1:]) if a>b][:2]}")
body = re.sub(r"\s+", " ", _dx[_dx.find("\n1 Introduction\n"):_dx.find("\nReferences\n")])
cites = re.findall(r"\(([^()]*?\d{4}[a-h]?(?:, \d{4}[a-h]?)*(?:; [^()]*?\d{4}[a-h]?(?:, \d{4}[a-h]?)*)*)\)", body)
labs = set()
for g in cites:
    for part in g.split("; "):
        m = re.match(r"^(.+?), (\d{4}[a-h]?(?:, \d{4}[a-h]?)*)$", part.strip())
        if m:
            for y in m.group(2).split(", "): labs.add((m.group(1), y))
want = {(base_label(k), year_str(k)) for k in KEYS}
ok(want <= labs, f"참고문헌마다 본문 인용 있음(미인용 {sorted(want - labs)[:3]})")
ok(not [x for x in labs if x not in want and not re.match(r"^(\d|ICD|A00|C00|Chapter)", x[0])], f"본문 인용마다 참고문헌 있음 {[x for x in labs if x not in want][:3]}")
ok(not re.search(r"\[\d+(?:[,\-–]\s*\d+)*\]", body), "번호 인용 잔재 없음")
ok(not re.search(r"\[(@|web:)", _dx) and "{{" not in _dx, "미해결 인용 없음")
refs = "\n".join(refl)
ok(not re.search(r"github|zenodo", refs, re.I), "참고문헌에 GitHub·Zenodo 없음")
ok(all(("https://doi.org/" in l or "http" in l or int(re.search(r"\((\d{4})[a-h]?\)", l).group(1)) < 2000) for l in refl), "참고문헌마다 DOI 링크·URL(2000년 이전 DOI 없는 문헌 예외)")
ok(not re.search(r"doi:", refs), "DOI는 https://doi.org/ 형식")
# 4. 표·문서 위생
for nm, f in (("원고", MSF), ("보충", ESF), ("제목면", TPF), ("커버", CLF)):
    dd = Document(os.path.join(OUT, f))
    for i, t in enumerate(dd.tables):
        tpr = t._tbl.tblPr; b = tpr.find(qn("w:tblBorders"))
        ok(b is not None and all(b.find(qn(f"w:{s}")).get(qn("w:val")) == "nil" for s in ("insideV", "insideH", "left", "right")), f"{nm} 표{i+1} 3선")
        _rows = [row for k_, row in enumerate(t.rows) if k_ > 0 and len({id(c._tc) for c in row.cells}) > 1]
        bad = [r.text for row in _rows for c in row.cells for p in c.paragraphs for r in p.runs if r.bold and r.text.strip()]
        ok(not bad, f"{nm} 표{i+1} 데이터 칸 볼드 없음 {bad[:2]}")
        ok(not [c.text for r in t.rows for c in r.cells if re.fullmatch(r"[\d.()\- ]+\*+", c.text.strip())], f"{nm} 표{i+1} 유의성 별표 없음")
    x = subprocess.run(["unzip", "-p", os.path.join(OUT, f), "word/*.xml"], capture_output=True, text=True).stdout
    ok(len(re.findall(r"<w:keepNext[ />]|<w:keepLines[ />]|<w:pageBreakBefore[ />]", x)) == 0, f"{nm} Word 검은 네모 0건")
    zz = zipfile.ZipFile(os.path.join(OUT, f)); core = zz.read("docProps/core.xml").decode(); app = zz.read("docProps/app.xml").decode()
    ok("2013-12-23" not in core and not any(n.startswith("customXml/") for n in zz.namelist()) and "<Words>0<" not in app, f"{nm} python-docx 지문 없음")
# 5. 문체
ok(not re.search(r"\b(we|our|us|We|Our)\b", body), "1인칭 없음")
cov = subprocess.run(["pdftotext", os.path.join(OUT, CLF.replace(".docx", ".pdf")), "-"], capture_output=True, text=True).stdout
alltxt = _dx + sup + cov + tp
ok("—" not in alltxt and not re.search(r"[가-힣]", alltxt), "em-dash·한글 없음")
ok(not re.search(r"\bsignifican", _dx + sup, re.I), "'significant' 없음")
UK = r"\b(\w*(standardis|harmonis|summaris|characteris(?=e|ed|ing|ation)|categoris|minimis|randomis|generalis|normalis|prioritis|organis|utilis)\w*|analys(e|ed|ing)|modelled|modelling|centre(s|d)?|neighbour\w*|behaviour\w*|ageing|colour|favour\w*|labelled|grey|programme)\b"
uk = sorted(set(m.group(0) for m in re.finditer(UK, body + " " + sup + " " + cov))); ok(not uk, f"영국식 철자 없음(본문·보충·커버) {uk}")
ok("−" in body, "마이너스 U+2212")
disc = _dx[_dx.find("\n4 Discussion\n"):_dx.find("\nReferences\n")]
disc_nc = re.sub(r"\([^()]*\d{4}[a-h]?\)", "", disc).replace("COVID-19", "COVID"); disc_nc = re.sub(r"\n\d(\.\d+)? [^\n]+", "\n", disc_nc)
_dn = re.findall(r".{15}\d.{8}", disc_nc)[:3]; ok(not _dn, f"고찰·결론에 숫자 없음 {_dn}")
for k, lab in C.SUP.items():
    inner = lab.split("(")[1].rstrip(")")
    ok(lab in body and inner in sup, f"'{lab}' 본문 인용·보충 존재")
ok("Appendix B. STROBE and RECORD checklist" in sup and "Online Resource 1, Appendix B" in body, "STROBE 점검표 보충 Appendix B·본문 인용")
_fb = [l.strip() for l in open(os.path.join(HERE, "_forbidden_terms.txt"), encoding="utf-8") if l.strip()] + ["previously submitted", "resubmi"]
_hit = re.findall("|".join(_fb), _dx[:_dx.find("\nReferences\n")] + sup + cov, re.I); ok(not _hit, f"이전 호·이전 투고 흔적 없음 {_hit[:3]}")
ok("[ZENODO DOI]" not in tp and "[ZENODO DOI]" not in cov and re.fullmatch(r"10\.5281/zenodo\.\d+", ZENODO or ""), "Zenodo DOI 채움(투고 전 게이트)")
open(os.path.join(OUT, "check_asap.txt"), "w").write("\n".join(R)); nf = sum(r.startswith("FAIL") for r in R)
print("\n".join(r for r in R if r.startswith("FAIL")) or "", f"\n{len(R)} checks, FAIL {nf}", "PASS" if nf == 0 else "")
