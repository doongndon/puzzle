// 퍼즐 낱말 풀(두 글자 이상)을 JSON으로 내보낸다 — 사전 뜻풀이를 뽑을 때 쓴다.
const path = require("path");
const root = path.join(__dirname, "..", "..");
const { PUZZLES, EXTRA_WORDS } = require(path.join(root, "puzzles.js"));
const COMMON = require(path.join(root, "words.js"));

const seen = new Map();
const add = (answer, def) => {
  if ([...answer].length >= 2 && !seen.has(answer)) seen.set(answer, def || "");
};
PUZZLES.forEach((p) => p.words.forEach((w) => add(w.answer, w.def)));
EXTRA_WORDS.forEach((w) => add(w.answer, w.def));
COMMON.forEach((w) => add(w.answer, w.def));

process.stdout.write(JSON.stringify([...seen].map(([answer, def]) => ({ answer, def }))));
