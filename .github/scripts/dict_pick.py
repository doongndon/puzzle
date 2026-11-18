"""candidates.json에서 낱말마다 뜻풀이 하나를 골라 dict.js를 만든다.

내려받기가 없어 어디서나 돌릴 수 있다 (후보 모으기는 dict_fetch.py).
쓰는 법: python dict_pick.py 낱말목록.json candidates.json picks.json dict.js [--review]

고르는 법
  1. picks.json에 적힌 낱말은 그대로 따른다.
     "낱말": "글귀"  → 뜻풀이나 원어(한자 등)에 그 글귀가 든 뜻을 쓴다
     "낱말": null    → 사전 뜻이 퍼즐에 맞지 않으니 낱말을 빼 버린다
  2. 아니면 퍼즐에 적힌 뜻·열쇠와 가장 닮은 뜻을 고르되, 쉬운 한국어기초사전(k)을 먼저 쓴다.
     우리말샘(u) 뜻이 확실히 더 닮았을 때만 우리말샘을 쓴다.
  3. 긴 뜻풀이는 앞 문장들만 남긴다 (대략 LIMIT자 안).
"""
import json
import re
import sys

LIMIT = 120        # 긴 뜻풀이는 이 길이 안에서 문장 단위로 줄인다
U_MARGIN = 0.12    # 우리말샘 뜻이 이만큼 더 닮아야 기초사전 대신 쓴다
LEVEL_RANK = {"초급": 1, "중급": 2, "고급": 3}

# 뜻을 가르는 데 도움이 안 되는 흔한 글자 (토씨·씨끝 등)
STOP = set("이가을를은는의에서로와과도만고며면하한할함해다것수등및또그더잘인있없되된때")


def tokens(s):
    words = [w for w in (re.sub(r"[^가-힣]", "", x) for x in s.split()) if w]
    uni = {c for w in words for c in w if c not in STOP}
    bi = {w[i:i + 2] for w in words for i in range(len(w) - 1)}
    return uni, bi


def dice(a, b):
    return 2 * len(a & b) / (len(a) + len(b)) if a and b else 0.0


def recall(a, b):
    return len(a & b) / len(a) if a else 0.0


def similarity(mine, theirs):
    mu, mb = tokens(mine)
    tu, tb = tokens(theirs)
    return 0.35 * dice(mu, tu) + 0.35 * dice(mb, tb) + 0.3 * recall(mb, tb)


NOTE = re.compile(r"\s*⇒.*$")                       # "⇒규범 표기는 ‘…’이다." 같은 덧붙임
SELF_REF = "‘{}’"                                   # "‘딸기’의 열매."처럼 낱말 자신을 가리키는 뜻
CROSS_REF = re.compile(r"^\(.*\)\s*→|^→")              # "(파래, 파래서)→ 파랗다" 같은 활용형 안내


def trim(d):
    d = NOTE.sub("", d).strip().replace("<", "〈").replace(">", "〉")   # 화면에서 HTML 태그로 읽히지 않게
    parts = re.split(r"(?<=[.?!])\s+", d)
    out = parts[0]
    for p in parts[1:]:
        if len(out) + 1 + len(p) > LIMIT:
            break
        out += " " + p
    return out


def score(word, mine, c):
    s = similarity(mine, c["def"])
    if c["src"] == "u":
        if SELF_REF.format(word) in c["def"]:
            s -= 0.10
        if c["field"]:
            s -= 0.03
    s += 0.02 if c["pos"] == "명사" else 0.0
    return s


def main():
    WORDS_JSON, CANDS_JSON, PICKS_JSON, OUT_JS = sys.argv[1:5]
    REVIEW = "--review" in sys.argv[5:]
    words = json.load(open(WORDS_JSON, encoding="utf-8"))
    data = json.load(open(CANDS_JSON, encoding="utf-8"))
    names = data["_fields"]
    picks = json.load(open(PICKS_JSON, encoding="utf-8")) if PICKS_JSON != "-" else {}
    picks = {k: v for k, v in picks.items() if not k.startswith("_")}

    result, notes = {}, {"missing": [], "excluded": [], "unfetched": [], "pick_miss": [], "nonstd": [],
                         "low": [], "switched": []}
    for w in words:
        word = w["answer"]
        mine = f'{w["def"]} {w["clue"]}'
        if word not in data["words"]:
            notes["unfetched"].append(word)
            continue
        cands = [dict(zip(["src", "pos", "def", "origin", "field", "cat", "region", "level", "head"], row))
                 for row in data["words"][word]]
        cands = [c for c in cands if not CROSS_REF.search(c["def"])]
        if not cands:
            notes["missing"].append(word)
            continue
        level = min((c["level"] for c in cands if c["level"] in LEVEL_RANK),
                    key=lambda lv: LEVEL_RANK[lv], default="")
        for c in cands:
            c["score"] = score(word, mine, c)

        rule = picks.get(word, "")
        if word in picks and rule is None:
            notes["excluded"].append(word)
            continue
        if rule:
            chosen = [c for c in cands if rule in c["def"] or rule in c["origin"]]
            if not chosen:
                notes["pick_miss"].append(f"{word}: '{rule}'")
            best = max(chosen or cands, key=lambda c: c["score"])
        else:
            k = [c for c in cands if c["src"] == "k"]
            u = [c for c in cands if c["src"] == "u"]
            bk = max(k, key=lambda c: c["score"]) if k else None
            bu = max(u, key=lambda c: c["score"]) if u else None
            best = bk if bk and (not bu or bu["score"] - bk["score"] < U_MARGIN) else bu
            if bk and best is bu:
                notes["switched"].append((word, bk, bu))
            ranked = sorted(cands, key=lambda c: -c["score"])
            if best["score"] < 0.15 or (len(ranked) > 1 and ranked[0]["score"] - ranked[1]["score"] < 0.03):
                notes["low"].append((word, mine, best, ranked))
        if NOTE.search(best["def"]):
            notes["nonstd"].append(f"{word}: {NOTE.search(best['def']).group(0).strip()}")
        result[word] = [trim(best["def"]), best["src"], best["pos"], level]

    by_src = {}
    for v in result.values():
        by_src[v[1]] = by_src.get(v[1], 0) + 1
    made = data.get("_made", "")
    header = (
        "/* ================================================================\n"
        "   국립국어원 사전에서 가져온 뜻풀이 — 자동으로 만든 파일이니 손대지 마세요\n"
        "   (.github/workflows/dict-build.yml 이 .github/dict/의 후보에서 고릅니다)\n"
        "   출처: 국립국어원 한국어기초사전(k), 국립국어원 우리말샘(u)\n"
        "         Hugging Face 공개 사본 hac541309/basic_korean_dict, hac541309/woori_spring_dict\n"
        "   라이선스: CC BY-SA 2.0 KR — 이 파일도 같은 조건으로 나눕니다.\n"
        "   긴 뜻풀이는 앞 문장만 남기고, 규범 표기 안내(⇒…)는 뺐습니다.\n"
        f"   사전 자료 받은 날: {made} · 낱말 {len(result)}개\n"
        "   [뜻풀이, 출처, 품사, 한국어기초사전 어휘 등급]\n"
        "   ================================================================ */\n"
    )
    body = ",\n".join(f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}"
                      for k, v in sorted(result.items()))
    with open(OUT_JS, "w", encoding="utf-8") as out:
        out.write(header + "const DICT_DEFS = {\n" + body + "\n};\n\n"
                  "if (typeof module !== \"undefined\" && module.exports) module.exports = DICT_DEFS;\n")

    print(f"낱말 {len(words)}개 → 뜻풀이 {len(result)}개 (기초사전 {by_src.get('k', 0)}, 우리말샘 {by_src.get('u', 0)})")
    for key, label in [("missing", "사전에 없음"), ("excluded", "picks.json에서 뺌"),
                       ("unfetched", "후보를 아직 안 모음"), ("pick_miss", "picks.json 글귀를 못 찾음"),
                       ("nonstd", "규범 표기 안내가 붙은 낱말")]:
        if notes[key]:
            print(f"{label} {len(notes[key])}개: {', '.join(notes[key])}")
    if REVIEW:
        print(f"\n기초사전 대신 우리말샘을 쓴 {len(notes['switched'])}개:")
        for word, bk, bu in notes["switched"]:
            print(f"  {word}  k {bk['score']:.2f} {bk['def'][:40]} | u {bu['score']:.2f} {bu['def'][:50]}")
        print(f"\n덜 확실한 {len(notes['low'])}개:")
        for word, mine, best, ranked in notes["low"]:
            print(f"■ {word} — 지금: {mine[:60]}")
            for c in ranked[:5]:
                mark = "▶" if c is best else " "
                extra = " ".join(x for x in [c["origin"], c["field"], c["cat"], c["region"]] if x)
                print(f"   {mark} {c['score']:.2f} [{c['src']}/{c['pos']}] {extra} | {c['def'][:70]}")


if __name__ == "__main__":
    main()
