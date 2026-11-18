"""국립국어원 사전 공개 사본에서 퍼즐 낱말의 뜻풀이 후보를 모두 모아 candidates.json에 담는다.

쓰는 사전 (Hugging Face에 공개된 사본, 원본 라이선스 CC BY-SA 2.0 KR):
  k  한국어기초사전  hac541309/basic_korean_dict   — 쉬운 뜻풀이, 어휘 등급
  u  우리말샘        hac541309/woori_spring_dict   — 표준국어대사전 뜻풀이를 포함한 큰 사전

쓰는 법: python dict_fetch.py 낱말목록.json 내려받을폴더 candidates.json [--all]
  candidates.json에 이미 있는 낱말은 다시 찾지 않는다(--all이면 모두 새로 찾는다).
  새로 찾을 낱말이 없으면 사전을 내려받지도 않는다.
  뜻 고르기는 dict_pick.py가 한다 (내려받기가 필요 없어 어디서나 돌릴 수 있다).
"""
import html
import json
import os
import re
import sys
import urllib.request
from datetime import date

SOURCES = [
    ("k", "hac541309/basic_korean_dict"),
    ("u", "hac541309/woori_spring_dict"),
]
FIELDS = ["출처", "품사", "뜻풀이", "원어", "전문 분야", "범주", "지역", "어휘 등급", "표제어"]

# 한 줄 안의 "이름: 값, 이름: 값, …"을 가르는 데 쓰는 이름들
KEYS = [
    "어휘", "표제어", "구성 단위", "구분", "고유어 여부", "원어·어종", "원어", "발음", "활용",
    "품사", "뜻풀이", "문법", "범주", "용례", "관련 어휘", "관련어", "전문 분야",
    "다중 매체(멀티미디어) 정보", "다중 매체 정보", "멀티미디어", "어휘 등급", "의미 범주",
    "주제 및 상황 범주", "의미 참고", "파생어", "의미 문형", "의미 문법", "공통 문법",
    "주표제어", "부표제어", "규범 정보", "어원", "지역", "수어 정보", "역사 정보", "참고 정보",
    "로마자 표기", "검색용 이형태", "속담", "관용구", "참고 어휘", "대역어",
]
BOUNDARY = re.compile(
    ", (?=(?:" + "|".join(re.escape(k) for k in KEYS) + r"|[가-힣]+어 대역어(?: 뜻풀이)?): )"
)
HEAD = re.compile(r"^(?:어휘|표제어): (.*?), (?:구성 단위|구분): ")
SKIP_POS = ("접사", "어미", "조사")
SKIP_CATEGORY = ("옛말", "북한어", "방언", "지역어")


def norm(h):
    h = re.sub(r"(?:\(\d+\)|\d+)$", "", h.strip())
    return re.sub(r"[-^\s]", "", h)


def fields(text):
    out = {}
    for seg in BOUNDARY.split(text):
        key, sep, val = seg.partition(": ")
        if sep and key not in out:
            out[key] = val.strip()
    return out


def clean(d):
    return re.sub(r"\s+", " ", html.unescape(d or "")).strip()


def download(repo, data_dir):
    req = urllib.request.Request(f"https://huggingface.co/api/datasets/{repo}",
                                 headers={"User-Agent": "puzzle-dict-build"})
    with urllib.request.urlopen(req, timeout=120) as r:
        info = json.loads(r.read())
    paths = []
    for f in [s["rfilename"] for s in info.get("siblings", []) if s["rfilename"].endswith(".parquet")]:
        dest = os.path.join(data_dir, repo.replace("/", "_") + "_" + os.path.basename(f))
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


def collect(todo, data_dir):
    import pyarrow.parquet as pq

    found = {w: [] for w in todo}
    for code, repo in SOURCES:
        rows = 0
        for path in download(repo, data_dir):
            for batch in pq.ParquetFile(path).iter_batches(batch_size=50000, columns=["text"]):
                for text in batch.column(0).to_pylist():
                    rows += 1
                    m = HEAD.match(text or "")
                    if not m:
                        continue
                    head = norm(m.group(1))
                    if head not in found:
                        continue
                    f = fields(text)
                    if (f.get("구성 단위") or f.get("구분") or "") != "단어":
                        continue
                    pos = (f.get("품사") or "").strip("「」")
                    if any(p in pos for p in SKIP_POS):
                        continue
                    cat = f.get("범주") or ""
                    if any(c in cat for c in SKIP_CATEGORY):
                        continue
                    d = clean(f.get("뜻풀이"))
                    if not d:
                        continue
                    row = [code, pos, d[:500], clean(f.get("원어·어종") or f.get("원어")),
                           clean(f.get("전문 분야")), cat, clean(f.get("지역")),
                           clean(f.get("어휘 등급")), m.group(1).strip()]
                    if not any(r[0] == code and r[2] == row[2] for r in found[head]):
                        found[head].append(row)
        print(f"{repo}: {rows:,}줄 훑음", flush=True)
    return found


def main():
    words_json, data_dir, out_path = sys.argv[1:4]
    every = "--all" in sys.argv[4:]
    pool = [w["answer"] for w in json.load(open(words_json, encoding="utf-8"))]

    known, made = {}, date.today().isoformat()
    if os.path.exists(out_path) and not every:
        old = json.load(open(out_path, encoding="utf-8"))
        known, made = old.get("words", {}), old.get("_made", made)
    todo = [w for w in pool if w not in known]
    if todo:
        print(f"사전에서 새로 찾을 낱말 {len(todo)}개", flush=True)
        os.makedirs(data_dir, exist_ok=True)
        known.update(collect(todo, data_dir))
        made = date.today().isoformat()
        missing = [w for w in todo if not known[w]]
        print(f"찾음 {len(todo) - len(missing)}개, 못 찾음 {len(missing)}개: {', '.join(missing)}")
    else:
        print("새로 찾을 낱말 없음 — 사전을 내려받지 않음")

    lines = [
        "{",
        '"_about": "국립국어원 한국어기초사전(k)·우리말샘(u) 공개 사본(Hugging Face hac541309/basic_korean_dict, '
        'hac541309/woori_spring_dict)에서 모은 뜻풀이 후보. 라이선스 CC BY-SA 2.0 KR. '
        '.github/workflows/dict-build.yml이 만들며, 못 찾은 낱말은 빈 목록으로 남긴다.",',
        f'"_fields": {json.dumps(FIELDS, ensure_ascii=False)},',
        f'"_made": "{made}",',
        '"words": {',
        ",\n".join(f"{json.dumps(w, ensure_ascii=False)}: {json.dumps(known[w], ensure_ascii=False)}"
                   for w in sorted(set(pool))),
        "}}",
    ]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as out:
        out.write("\n".join(lines) + "\n")


main()
