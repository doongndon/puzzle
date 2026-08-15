# 낱말풀이 마당 — 한글 가로세로 퍼즐

광고 없이 즐기는 한국 전통 분위기의 한글 가로세로 낱말 퍼즐입니다.
한지 질감과 궁서체, 단청 빛깔로 꾸민 정적 웹앱으로, 서버나 외부 의존성 없이
브라우저만 있으면 어디서든 동작합니다.

## 실행 방법

`index.html`을 브라우저로 열기만 하면 됩니다.

```bash
# 그냥 파일을 열거나
open index.html

# 간단한 로컬 서버로 열어도 됩니다
python3 -m http.server 8000
# → http://localhost:8000
```

## 놀이 방법

처음에는 낱말의 뜻(열쇠)을 알려주지 않습니다. 판에 드문드문 밝혀진
글자를 실마리 삼아, 아래 **글자 보따리**에서 글자를 골라 빈 칸을 채웁니다.

1. **마당 고르기** — 스물한 개의 고정 마당(나라와 얼 / 맛과 살림 / 놀이와 자연 /
   계절과 하늘 / 옛이야기와 풍류 / 사자성어 / 바다와 물고기 / 새와 들짐승 /
   나무와 풀꽃 / 몸과 마음 / 집과 세간 / 옷과 꾸밈 / 하늘과 날씨 / 고을과 명승 /
   나라 역사 / 배움과 글 / 장터와 살림살이 / 소리와 가락 / 잔치와 예절 /
   속담 속 낱말 / 사자성어 둘)과 **랜덤 마당** 가운데 하나를 고릅니다.
   랜덤 마당은 275개 낱말 풀에서 뽑아 11×11 판을 즉석에서 짜 주며,'새 판 뽑기'를 누를 때마다 새로운 판이 나옵니다.
   **난이도**(하수·중수·고수)도 고를 수 있으며, 난이도마다 진행이 따로 저장됩니다.
2. **빈 칸 고르기** — 낱말판의 빈 칸을 누릅니다. 가로·세로가 겹치는 칸은
   다시 누르면 방향이 바뀝니다.
3. **글자 채우기** — 글자 보따리에서 알맞은 글자를 누르면 칸에 놓입니다.
   틀린 글자는 놓이지 않고 헛짚기로 기록됩니다.
4. **뜻풀이 보기** — 낱말을 완성하면 그 낱말이 열립니다. 완성한 낱말의 칸이나
   낱말 목록을 누르면 두루마리에 사전 뜻풀이가 펼쳐지고,
   표준국어대사전으로 바로 가는 길도 열립니다.

## 보물 주머니 (아이템)

| 아이템 | 개수 (하수/중수/고수) | 효과 |
|---|---|---|
| 힌트 | 5 / 3 / 2개 | 고른 빈 칸의 글자를 밝혀 줍니다 |
| 뜻보기 | 5 / 3 / 2개 | 고른 낱말의 사전 뜻풀이를 미리 보여 줍니다 |

## 난이도

| 난이도 | 처음에 밝혀 두는 글자 | 특징 |
|---|---|---|
| 하수 | 절반쯤 | 낱말마다 최소 한 글자 공개 |
| 중수 | 3분의 1쯤 | 낱말마다 최소 한 글자 공개 |
| 고수 | 5분의 1쯤 | 통째로 숨은 낱말도 있음 |

## 특징

- **광고 없음** — 광고, 추적, 외부 스크립트가 전혀 없습니다.
- **전통 UI** — 한지 질감, 궁서체(미지원 환경에서는 명조체), 단청 띠, 낙관 도장.
- **진행 저장** — 풀이 상태와 남은 아이템이 브라우저(localStorage)에 저장됩니다.
- **반응형** — 휴대폰, 태블릿, 컴퓨터 화면 모두에 맞춰집니다.

## 파일 구성

```
index.html   앱 본체 (화면, 양식, 동작 전부 포함)
puzzles.js   퍼즐 데이터 (고정 마당 21개 + 랜덤 전용 낱말, 전체 풀 275개)
```

새 퍼즐을 만들려면 `puzzles.js`에 마당을 추가하면 됩니다. 각 낱말은
방향(`across`/`down`), 시작 칸(`row`, `col`), 정답, 열쇠(`clue`),
뜻풀이(`def`)로 이루어집니다.

  # Word-of-the-word puzzle yard — Hangul horizontal and vertical puzzles

This is a Korean word puzzle with a traditional Korean atmosphere, enjoyed without advertisements.
A static web app decorated with Hanji texture, Gungseo font, and the colors of Dancheong, without server or external dependence.
It works anywhere with just a browser.

## How to Execute

All you need to do is open `index.html` in your browser.

```bash
# Just open the file or
open index.html

# You can open it with a simple local server
python3 -m http.server 8000
# → http://localhost:8000
```

## Playing Methods

At first, they don't tell you the meaning (key) of the word. The sporadically revealed information on the plate.
Using the letters as a clue, fill in the blanks by selecting a letter from the **letter bundle** below.

1. **Choosing the Yard** — Six fixed Yards (Nation and Spirit / Taste and Living / Play and Nature /
Choose one between the seasons and the sky / old tales and elegance / idioms) and **random yard**.
The random yard is made by weaving 11x11 boards on the spot from a pool of 150 words, and...
Every time you click 'Draw a new board,' a new board appears.
**Difficulty levels** (sewer, intermediate, and advanced) can also be selected, and progress is saved separately for each difficulty level.
2. **Fill the blank** — Press the blank on the word board. The spaces where the width and height overlap are...
If you press it again, the direction changes.
3. **Filling** — If you press the appropriate letter from the letter bundle, it will be placed in the space.
Incorrect letters are not placed and are recorded as false errors.
4. **View the meaning** — When a word is completed, that word opens. The space of the completed word or...
When you click on the word list, a dictionary definition unfolds on the scroll, and...
Direct access to the Standard Korean Language Dictionary is also open.

## Treasure Pouch (Item)

| Item | Number (low/medium/expert) | Effect |
|---|---|---|
| Hint | 5 / 3 / 2 | Illuminate the letters in the selected blanks |
| View the meaning | 5 / 3 / 2 | Shows the dictionary definitions of selected words in advance |

## Difficulty

| Difficulty | The initial characters to be revealed | Features |
|---|---|---|
| Amateur | About half | Reveal at least one character for each word |
| Intermediate | About one-third | At least one character is disclosed for each word |
| Master | About 1/5 | There are also hidden words entirely |

## Features

- **No Advertisement** — There are no ads, tracking, or external scripts at all.
- **Traditional UI** — Hanji texture, Gungseo font (in unsupported environments, Myeongjo font), Dancheong belt, and seal seal.
- **Save progress** — The solved status and remaining items are saved in the browser (localStorage).
- **Responsive** — It is tailored to all screens on mobile phones, tablets, and computers.

## File Configuration

```
Index.html app body (including screen, format, and operation)
puzzles.js puzzle data (6 fixed yards, 95 words + 55 random-only = 150)
```

To create a new puzzle, you can add a yard to `puzzles.js`. Each word is...
Direction (`across`/`down`), start box (`row`, `col`), answer, key (`clue`),
It consists of meaning interpretation (`def`).


