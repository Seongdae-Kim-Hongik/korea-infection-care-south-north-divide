#!/usr/bin/env python3
# 99I — 감염병 진료(INFECT, A00-B99): 전국 3단 상병 성별×5세 진료실인원 수집(NHIS 빅데이터 플랫폼 공개 화면, 로그인 없음)
#  출처: https://nhiss.nhis.or.kr/lp/f/a/300/lpfa300m05.do (주상병 3단 성별/연령 5세 구간별 현황), 2015-2024
#  산출: 00_원천/C_NHIS_3단상병/INFECT_3char_sex_age5_2015_2024.csv (code, name, year, sex, age, patients) + raw json
#  용도: ① 전국 3단 상병 구성표(방법·보충) ② 298분류 연령별 진료실인원을 성별로 나누는 연령대별 남성 비율(성×연령 간접표준화)
import json, time, os, re, sys, urllib.request, urllib.parse, http.cookiejar
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "00_원천", "C_NHIS_3단상병")
B = "https://nhiss.nhis.or.kr/lp/f/a/300/"
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)); op.addheaders = [("User-Agent", "Mozilla/5.0 (research data retrieval)")]
op.open(B + "lpfa300m05.do").read()
def q(code, y0, y1):
    d = urllib.parse.urlencode(dict(dissCd=code, dissNm="", rmetYyyyStr=y0, rmetYyyyEnd=y1, typeCd="A5", subject="", unit="")).encode()
    r = urllib.request.Request(B + "selectLpfa300m05List.do", data=d, headers={"X-Requested-With": "XMLHttpRequest"})
    for k in range(4):
        try: return json.loads(op.open(r, timeout=60).read())
        except Exception as e: time.sleep(5 * (k + 1)); err = e
    raise err
codes = [f"{l}{n:02d}" for l in "AB" for n in range(100)]
raw = {}; rows = []
rawf = os.path.join(OUT, "INFECT_3char_sex_age5_raw.json")
if os.path.exists(rawf): raw = json.load(open(rawf))
for c in codes:
    for y0, y1 in ((2015, 2019), (2020, 2024)):
        key = f"{c}_{y0}"
        if key not in raw:
            raw[key] = q(c, y0, y1); time.sleep(0.4)
        js = raw[key]; yrs = [str(y) for y in range(y0, y1 + 1)]
        for r in js.get("dataList", []):
            if not r.get("col2") or not r.get("col3"): continue
            for i, y in enumerate(yrs):
                v = r.get(f"col{4 + 4 * i}")
                rows.append((c, r.get("col1"), int(y), r["col2"], r["col3"], float(str(v).replace(",", "")) if v not in (None, "", "-") else 0.0))
    if c.endswith("9") : json.dump(raw, open(rawf, "w"), ensure_ascii=False); print(c, len(rows), flush=True)
json.dump(raw, open(rawf, "w"), ensure_ascii=False)
D = pd.DataFrame(rows, columns=["code", "name", "year", "sex", "age", "patients"])
D.to_csv(os.path.join(OUT, "INFECT_3char_sex_age5_2015_2024.csv"), index=False, encoding="utf-8-sig")
print("codes with data", D.code.nunique(), "rows", len(D), "sexes", sorted(D.sex.unique()), "ages", D.age.nunique())
