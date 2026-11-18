// 퍼즐 낱말 풀(두 글자 이상)을 JSON으로 내보낸다 — 사전 뜻풀이를 고를 때 쓴다.
// 지금 적힌 뜻(def)과 열쇠(clue)는 사전의 여러 뜻 가운데 맞는 뜻을 고르는 실마리가 된다.
const path = require("path");
const root = path.join(__dirname, "..", "..");
const { PUZZLES, EXTRA_WORDS } = require(path.join(root, "puzzles.js"));
const COMMON = require(path.join(root, "words.js"));

const seen = new Map();
const add = (w) => {
  if ([...w.answer].length >= 2 && !seen.has(w.answer)) seen.set(w.answer, { answer: w.answer, def: w.def || "", clue: w.clue || "" });
};
PUZZLES.forEach((p) => p.words.forEach(add));
EXTRA_WORDS.forEach(add);
COMMON.forEach(add);

process.stdout.write(JSON.stringify([...seen.values()]));
