"""KOSIS OpenAPI 공용 모듈. 키는 ~/.kosis_key 한 줄.
- stat_list(parentListId): 통계목록 트리
- table_meta(orgId, tblId): 분류·항목·시점 메타
- fetch_table(orgId, tblId, start, end, prdSe='Y'): 전체 분류 ALL 로 받아 long 형식 DataFrame
문서: https://kosis.kr/openapi/
"""
import os, sys, json, time, urllib.request, urllib.parse
import pandas as pd

KEYFILE = os.path.expanduser("~/.kosis_key")
BASE = "https://kosis.kr/openapi"

def key():
    if not os.path.exists(KEYFILE):
        sys.exit(f"KOSIS 인증키 파일이 없음: {KEYFILE} (kosis.kr 마이페이지 → OpenAPI 인증키를 한 줄로 저장)")
    return open(KEYFILE, encoding="utf-8").read().strip()

def _get(url, params, retries=4):
    q = urllib.parse.urlencode({**params, "apiKey": key()})
    for t in range(retries):
        try:
            with urllib.request.urlopen(url + "?" + q, timeout=180) as r:
                txt = r.read().decode("utf-8")
            j = json.loads(txt)
            if isinstance(j, dict) and "err" in j:
                raise RuntimeError(f"KOSIS err {j.get('err')}: {j.get('errMsg')}")
            return j
        except Exception as e:
            if t == retries - 1:
                raise
            time.sleep(3 * (t + 1))

def stat_list(parentListId="", vwCd="MT_ZTITLE"):
    return _get(BASE + "/statisticsList.do", {"method": "getList", "vwCd": vwCd, "parentListId": parentListId, "format": "json", "jsonVD": "Y"})

def table_meta(orgId, tblId, what="ITM"):
    # what: TBL(표 설명), ORG, PRD(시점), ITM(항목), CMMT(주석), ALL
    return _get(BASE + "/statisticsData.do", {"method": "getMeta", "type": what, "orgId": orgId, "tblId": tblId, "format": "json", "jsonVD": "Y"})

def fetch_table(orgId, tblId, startPrdDe, endPrdDe, prdSe="Y", itmId="ALL", levels=None):
    """분류 축 수를 모르면 objL1=ALL 부터 시작해 '필수 파라미터' 오류가 나면 objL2..objL8 을 차례로 ALL 로 늘려 재시도."""
    last = None
    for n in ([levels] if levels else range(1, 9)):
        p = {"method": "getList", "orgId": orgId, "tblId": tblId, "itmId": itmId, "prdSe": prdSe,
             "startPrdDe": startPrdDe, "endPrdDe": endPrdDe, "format": "json", "jsonVD": "Y"}
        for i in range(1, 9):
            p[f"objL{i}"] = "ALL" if i <= n else ""
        try:
            j = _get(BASE + "/Param/statisticsParameterData.do", p, retries=2)
            df = pd.DataFrame(j); df.attrs["levels"] = n
            return df
        except Exception as e:
            last = e
            msg = str(e)
            # 분류 축 부족(필수 objL 누락)일 때만 축을 늘려 재시도, 그 외는 바로 올림
            if "objL" in msg or "필수" in msg or "err 30" in msg or "err 20" in msg:
                time.sleep(0.5); continue
            raise
    raise last

if __name__ == "__main__":
    # 사용 예: python3 kosis_api.py 177 DT_DIA_DOCTOR 2008 2025
    orgId, tblId, s, e = sys.argv[1:5]
    df = fetch_table(orgId, tblId, s, e)
    print(df.shape); print(df.head())


def _is_too_big(e):
    m = str(e)
    return "40,000" in m or "40000" in m or "err 31" in m

def meta_codes(orgId, tblId):
    """getMeta type=ITM 결과를 (항목 코드 목록, 분류별 코드 목록 dict) 로 나눈다."""
    j = table_meta(orgId, tblId, "ITM")
    items = [x["ITM_ID"] for x in j if x.get("OBJ_ID") == "ITEM"]
    objs = {}
    for x in j:
        if x.get("OBJ_ID") != "ITEM":
            objs.setdefault(x["OBJ_ID"], []).append(x["ITM_ID"])
    return items, objs

def fetch_table_safe(orgId, tblId, y0, y1, levels=None, _meta=None):
    """40,000셀 한도를 넘으면 ① 연도 1개씩 → ② 항목별 → ③ 첫 분류 코드별로 쪼개어 받아 합친다."""
    try:
        return fetch_table(orgId, tblId, str(y0), str(y1), levels=levels)
    except Exception as e:
        if not _is_too_big(e):
            raise
    if y0 != y1:
        parts = [fetch_table_safe(orgId, tblId, y, y, levels, _meta) for y in range(int(y0), int(y1) + 1)]
        parts = [p for p in parts if len(p)]
        return pd.concat(parts) if parts else pd.DataFrame()
    items, objs = _meta or meta_codes(orgId, tblId)
    parts = []
    for it in items:
        try:
            df = fetch_table(orgId, tblId, str(y0), str(y1), itmId=it, levels=levels)
            levels = df.attrs.get("levels", levels)
            parts.append(df); time.sleep(0.8); continue
        except Exception as e:
            if not _is_too_big(e):
                raise
        # ③ 첫 분류 코드별
        obj1 = list(objs.keys())[0]
        for code in objs[obj1]:
            n = levels or len(objs)
            p = {"method": "getList", "orgId": orgId, "tblId": tblId, "itmId": it, "prdSe": "Y",
                 "startPrdDe": str(y0), "endPrdDe": str(y1), "format": "json", "jsonVD": "Y"}
            for i in range(1, 9):
                p[f"objL{i}"] = (code if i == 1 else "ALL") if i <= n else ""
            try:
                parts.append(pd.DataFrame(_get(BASE + "/Param/statisticsParameterData.do", p, retries=2)))
            except Exception as e:
                if "err 30" not in str(e): raise
            time.sleep(0.8)
    parts = [p for p in parts if len(p)]
    return pd.concat(parts) if parts else pd.DataFrame()


def fetch_split(orgId, tblId, y0, y1, prdSe="Y"):
    """단일 시점(또는 짧은 구간)에서 40,000셀을 넘는 표: 항목별 → 분류축(코드 수가 가장 적은 축부터)별로 쪼개 받는다."""
    items, objs = meta_codes(orgId, tblId)
    axes = list(objs.keys()); n = len(axes)
    def call(itm, fixed):
        p = {"method": "getList", "orgId": orgId, "tblId": tblId, "itmId": itm, "prdSe": prdSe,
             "startPrdDe": str(y0), "endPrdDe": str(y1), "format": "json", "jsonVD": "Y"}
        for i in range(1, 9):
            p[f"objL{i}"] = (fixed.get(i, "ALL") if i <= n else "")
        return pd.DataFrame(_get(BASE + "/Param/statisticsParameterData.do", p, retries=2))
    out = []
    for itm in items:
        try:
            out.append(call(itm, {})); time.sleep(0.8); continue
        except Exception as e:
            if "err 30" in str(e): continue
            if not _is_too_big(e): raise
        # 축을 하나씩 고정(코드 수 적은 축부터) — 2축까지 중첩
        order = sorted(range(1, n + 1), key=lambda i: len(objs[axes[i - 1]]))
        done = False
        for ai in order:
            try:
                for code in objs[axes[ai - 1]]:
                    try: out.append(call(itm, {ai: code}))
                    except Exception as e:
                        if "err 30" in str(e): continue
                        raise
                    time.sleep(0.8)
                done = True; break
            except Exception as e:
                if not _is_too_big(e): raise
        if not done:
            a1, a2 = order[0], order[1]
            for c1 in objs[axes[a1 - 1]]:
                for c2 in objs[axes[a2 - 1]]:
                    try: out.append(call(itm, {a1: c1, a2: c2}))
                    except Exception as e:
                        if "err 30" in str(e): continue
                        raise
                    time.sleep(0.8)
    out = [o for o in out if len(o)]
    return pd.concat(out) if out else pd.DataFrame()
