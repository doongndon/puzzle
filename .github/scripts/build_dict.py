"""퍼즐 낱말의 뜻풀이를 국립국어원 사전 공개 사본에서 뽑아 dict.js로 만든다.

쓰는 사전 (Hugging Face에 공개된 사본, 원본 라이선스 CC BY-SA 2.0 KR):
  k  한국어기초사전  hac541309/basic_korean_dict   — 쉬운 뜻풀이, 어휘 등급
  u  우리말샘        hac541309/woori_spring_dict   — 표준국어대사전 뜻풀이를 포함한 큰 사전

뜻이 여럿인 낱말은 퍼즐에 지금 적힌 뜻과 가장 가까운 뜻을 고른다.
쓰는 법: python build_dict.py 낱말목록.json 내려받을폴더 dict.js
"""
import json
import os
import re
import sys
import urllib.request
from datetime import date

import pyarrow.parquet as pq

WORDS_JSON, DATA_DIR, OUT_JS = sys.argv[1], sys.argv[2], sys.argv[3]

SOURCES = [
    ("k", "hac541309/basic_korean_dict", "국립국어원 한국어기초사전"),
    ("u", "hac541309/woori_spring_dict", "국립국어원 우리말샘"),
]

# 한 줄 안의 "이름: 값, 이름: 값, …"을 가르는 데 쓰는 이름들
KEYS = [
    "어휘", "표제어", "구성 단위", "구분", "고유어 여부", "원어·어종", "원어", "발음", "활용",
    "품사", "뜻풀이", "문법", "범주", "용례", "관련 어휘", "관련어", "전문 분야",
    "다중 매체(멀티미디어) 정보", "다중 매체 정보", "멀티미디어", "어휘 등급", "의미 범주",
    "주제 및 상황 범주", "의미 참고", "파생어", "의미 문형", "의미 문법", "공통 문법",
    "주표제어", "부표제어", "규범 정보", "어원", "지역", "수어 정보", "역사 정보", "참고 정보",
    "로마자 표기", "검색용 이형태", "속담", "관용구", "참고 어휘",
]
BOUNDARY = re.compile(
    ", (?=(?:" + "|".join(re.escape(k) for k in KEYS) + r"|[가-힣]+어 대역어(?: 뜻풀이)?): )"
)
HEAD = re.compile(r"^(?:어휘|표제어): (.*?), (?:구성 단위|구분): ")
SKIP_CATEGORY = ("옛말", "북한어", "방언", "지역어")
SKIP_POS = ("접사", "어미", "조사")


def norm(h):
    h = re.sub(r"\(\d+\)$", "", h.strip())
    return re.sub(r"[-^\s]", "", h)


def fields(text):
    out = {}
    for seg in BOUNDARY.split(text):
        key, sep, val = seg.partition(": ")
        if sep and key not in out:
            out[key] = val.strip()
    return out


# 뜻을 가르는 데 도움이 안 되는 흔한 글자 (토씨·씨끝 등)
STOP = set("이가을를은는의에서로와과도만고며면하한할함해다것수등및또그더잘인있없되된때")


def bigrams(s):
    s = re.sub(r"[^가-힣]", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)} or ({s} if s else set())


def dice(A, B):
    return 2 * len(A & B) / (len(A) + len(B)) if A and B else 0.0


def similarity(a, b):
    """글자 겹침과 두 글자 묶음 겹침을 함께 본다 (0~1)."""
    uni_a = {c for c in a if "가" <= c <= "힣" and c not in STOP}
    uni_b = {c for c in b if "가" <= c <= "힣" and c not in STOP}
    return 0.5 * dice(uni_a, uni_b) + 0.5 * dice(bigrams(a), bigrams(b))


def clean_def(d):
    d = re.sub(r"\s+", " ", d).strip()
    return d


def download(repo):
    req = urllib.request.Request(f"https://huggingface.co/api/datasets/{repo}",
                                 headers={"User-Agent": "puzzle-dict-build"})
    with urllib.request.urlopen(req, timeout=120) as r:
        info = json.loads(r.read())
    paths = []
    for f in [s["rfilename"] for s in info.get("siblings", []) if s["rfilename"].endswith(".parquet")]:
        dest = os.path.join(DATA_DIR, repo.replace("/", "_") + "_" + os.path.basename(f))
        if not os.path.exists(dest):
            url = f"https://huggingface.co/datasets/{repo}/resolve/main/{f}"
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "puzzle-dict-build"}),
                                        timeout=600) as r, open(dest, "wb") as out:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
        paths.append(dest)
    return paths


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    words = json.load(open(WORDS_JSON, encoding="utf-8"))
    ours = {w["answer"]: w["def"] for w in words}
    cands = {a: [] for a in ours}          # 낱말 → 후보 뜻풀이들
    level = {}                             # 낱말 → 한국어기초사전 어휘 등급
    odd = []                               # 뜻풀이 안에 이름표가 끼어든 듯한 것 (점검용)

    for code, repo, label in SOURCES:
        files = download(repo)
        rows = 0
        for path in files:
            for batch in pq.ParquetFile(path).iter_batches(batch_size=50000, columns=["text"]):
                for text in batch.column(0).to_pylist():
                    rows += 1
                    if not text:
                        continue
                    m = HEAD.match(text)
                    if not m:
                        continue
                    head = norm(m.group(1))
                    if head not in ours:
                        continue
                    f = fields(text)
                    unit = f.get("구성 단위") or f.get("구분") or ""
                    if unit != "단어":
                        continue
                    pos = (f.get("품사") or "").strip("「」")
                    if any(p in pos for p in SKIP_POS):
                        continue
                    cat = f.get("범주") or ""
                    if any(c in cat for c in SKIP_CATEGORY):
                        continue
                    d = clean_def(f.get("뜻풀이") or "")
                    if not d:
                        continue
                    if re.search(r", [가-힣·() ]{1,12}: ", d) and len(odd) < 20:
                        odd.append((head, d[:120]))
                    if code == "k" and f.get("어휘 등급"):
                        lv = f["어휘 등급"]
                        rank = {"초급": 1, "중급": 2, "고급": 3}.get(lv, 9)
                        if head not in level or rank < {"초급": 1, "중급": 2, "고급": 3}.get(level[head], 9):
                            level[head] = lv
                    cands[head].append({"def": d, "src": code, "pos": pos})
        print(f"{label}: {rows:,}줄 훑음", flush=True)

    result, scored = {}, []
    for word, our_def in ours.items():
        best, best_score = None, -1.0
        for c in cands[word]:
            s = similarity(our_def, c["def"])
            s += 0.03 if c["src"] == "k" else 0.0     # 비슷하면 쉬운 뜻풀이를 먼저
            s += 0.02 if c["pos"] == "명사" else 0.0
            if s > best_score:
                best, best_score = c, s
        if best:
            result[word] = [best["def"], best["src"], best["pos"], level.get(word, "")]
            scored.append((best_score, word, our_def, best["def"], best["src"]))

    missing = [w for w in ours if w not in result]
    by_src = {}
    for v in result.values():
        by_src[v[1]] = by_src.get(v[1], 0) + 1

    header = (
        "/* ================================================================\n"
        "   국립국어원 사전에서 가져온 뜻풀이 — 자동으로 만든 파일이니 손대지 마세요\n"
        "   (.github/workflows/dict-build.yml 이 만듭니다)\n"
        "   출처: 국립국어원 한국어기초사전(k), 국립국어원 우리말샘(u)\n"
        "         Hugging Face 공개 사본 hac541309/basic_korean_dict, hac541309/woori_spring_dict\n"
        "   라이선스: CC BY-SA 2.0 KR — 이 파일도 같은 조건으로 나눕니다.\n"
        f"   만든 날: {date.today().isoformat()} · 낱말 {len(result)}개\n"
        "   [뜻풀이, 출처, 품사, 한국어기초사전 어휘 등급]\n"
        "   ================================================================ */\n"
    )
    body = ",\n".join(f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}"
                      for k, v in sorted(result.items()))
    with open(OUT_JS, "w", encoding="utf-8") as out:
        out.write(header + "const DICT_DEFS = {\n" + body + "\n};\n\n"
                  "if (typeof module !== \"undefined\" && module.exports) module.exports = DICT_DEFS;\n")

    print(f"\n낱말 {len(ours)}개 중 사전에서 찾음 {len(result)}개 (기초사전 {by_src.get('k', 0)}, 우리말샘 {by_src.get('u', 0)})")
    print(f"못 찾음 {len(missing)}개: {', '.join(missing)}")
    print(f"어휘 등급: " + json.dumps({lv: list(level.values()).count(lv) for lv in set(level.values())}, ensure_ascii=False))
    print("\n지금 뜻과 가장 덜 닮은 40개 (뜻 고르기 점검용):")
    for s, w, mine, theirs, src in sorted(scored)[:40]:
        print(f"  {s:.2f} {w} [{src}]  지금: {mine[:40]} | 사전: {theirs[:60]}")
    if odd:
        print("\n뜻풀이에 이름표가 끼어든 듯한 것:")
        for h, d in odd:
            print("  ", h, "|", d)


main()
