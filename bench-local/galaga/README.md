# Galaga coding test

A practical software-engineering test for the Strata quants: write a faithful, single-file browser Galaga from one
prompt ([prompt.md](prompt.md)), with no follow-up turns and no chance to run the code. Measured 2026-10-02 on the
5800X / 96 GB DDR4 / RTX 4090 box, engine 0.1.36, each quant on its config in the repo root (262K, KV streaming).

## Method

1. **Generate** (`gen.py`): one server start per quant, 2 thinking settings x 2 seeds = 4 games per quant.
   - `off`: `reasoning_effort: none`, temperature 0.7, top_p 0.8, top_k 20 (Qwen's non-thinking sampling).
   - `medium`: `reasoning_effort: medium`, `reasoning_budget_tokens: 16384`, temperature 0.6, top_p 0.95, top_k 20.
   - `max_tokens` 49,152; seeds 1 and 2.
2. **Play-test** (`playtest.py`): headless Chrome (Playwright, the installed Chrome), 8 checks: loads without
   errors, canvas, title drawn, idle animation, starts on Enter, the fighter moves, no exception in a 90 s bot run
   (sweeps left/right, taps fire), still animating at the end. Screenshots in `play/<run>/`.
3. **Blind review** (`blind.py`, [rubric.md](rubric.md)): each game copied to `review/<letter>/` under a shuffled
   letter; one independent reviewer per game scored 38 rubric items 0/1/2 (max 76) from the code and the play-test,
   with line-number evidence, and listed bugs as severe/minor. The key is `review-key.json`.
4. `results.py` joins everything into `results.json`.

## Results

| run | score /76 | play checks /8 | severe bugs | verdict | out tokens | time | tok/s |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| IQ3_XXS off s1 | 0 | 2 | 2 | not playable (repetition loop, truncated) | 49,152 | 4.4 min | 185 |
| IQ3_XXS off s2 | 35 | 5 | 6 | not playable (TypeError every frame, frozen on READY) | 18,855 | 2.1 min | 150 |
| IQ3_XXS medium s1 | **64** | 8 | 0 | **playable with flaws** | 27,983 | 4.0 min | 117 |
| IQ3_XXS medium s2 | 36 | 2 | 2 | not playable (syntax error) | 27,137 | 3.9 min | 117 |
| IQ3_S off s1 | 46 | 8 | 4 | barely playable | 12,442 | 1.9 min | 109 |
| IQ3_S off s2 | 18 | 1 | 10 | not playable (crash at load) | 17,389 | 2.4 min | 121 |
| IQ3_S medium s1 | 36 | 3 | 6 | not playable (assignment to const, first frame) | 28,155 | 4.7 min | 100 |
| IQ3_S medium s2 | 41 | 6 | 3 | not playable (crash on first frame after Enter) | 27,029 | 4.3 min | 104 |
| UD-Q4_K_XL off s1 | 24 | 7 | 5 | not playable (no enemies, stuck on STAGE 1 CLEAR) | 13,512 | 4.5 min | 50 |
| UD-Q4_K_XL off s2 | 44 | 8 | 3 | barely playable (fly-in stalls, no dives) | 15,999 | 4.9 min | 54 |
| UD-Q4_K_XL medium s1 | 32 | 1 | 5 | not playable (syntax error) | 28,536 | 10.6 min | 45 |
| UD-Q4_K_XL medium s2 | **71** | 8 | 2 | **playable with flaws** (soft-locks at stage 3) | 31,203 | 11.0 min | 48 |

tok/s = output tokens / request time (the medium runs' `/metrics` decode rate only covers the part after the
thinking budget closed the thinking, so it reads 250-330 and is not used).

| | IQ3_XXS | IQ3_S | UD-Q4_K_XL |
| --- | ---: | ---: | ---: |
| mean score /76 (4 runs) | 33.8 | 35.2 | 42.8 |
| best run | 64 | 46 | 71 |
| playable games (plays well / with flaws) | 1 of 4 | 0 of 4 | 1 of 4 |
| reached gameplay without an exception | 1 of 4 | 1 of 4 | 3 of 4 |
| time for one medium-thinking game | ~4 min | ~4.5 min | ~11 min |

| thinking | mean score | playable |
| --- | ---: | ---: |
| off (6 runs) | 27.8 (33.4 without the looped run) | 0 of 6 |
| medium (6 runs) | 46.7 | 2 of 6 |

## Baseline: Claude Sonnet 5.5 (`gen_claude.py`)

Same prompt and 49,152-token cap, through the Anthropic API, 4 runs. Sonnet 5.5 takes no temperature or seed and
cannot turn thinking fully off, so the arms are `off` = `thinking: between_tools`, effort high (its default), and
`medium` = adaptive thinking, effort medium; the two runs per arm are plain repeats. No refusal fallback.

| run | finish | out tokens | of which thinking | time | html lines | score /76 | play checks | verdict |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| off r1 | stop | 29,170 | 0 | 2.7 min | 1,341 | **72** | 8 | **plays well** (0 severe, 10 minor bugs) |
| off r2 | length | 49,152 | 49,152 | 7.1 min | 0 | - | - | no code: all thinking |
| medium r1 | length | 49,152 | 49,152 | 6.7 min | 0 | - | - | no code: all thinking |
| medium r2 | length | 49,152 | 42,852 | 6.4 min | 213 | - | - | code cut off at the cap |

- **The one finished game is the best of the whole test**, and the only one rated "plays well": the formation flies in
  on curved paths, dives return to their slots, the tractor beam captures and the rescue docks into a dual fighter,
  and the Challenging Stage ends and pays its bonus (verified in the code, lines 1064-1105). Its misses: the captured
  fighter never fires (E6) and a lot of dead code (A4).
- **3 of 4 runs produced no game, because of the cap, not bad code.** Sonnet 5.5 spent 43-49K thinking tokens on this
  prompt at effort `medium` and also with `between_tools`, which did not stop it from thinking before its answer.
  The Strata runs were protected from this by a hard 16K thinking budget. No reruns at a larger cap were made.
- So this baseline is **one game**: it shows one-shot "plays well" is reachable on this prompt, which the Strata
  quants did not reach in 12 tries (best: 71/76 but soft-locks at stage 3), but n=1 cannot give a rate. Scored by the
  same blind rubric, though its reviewer saw a 13th letter added after the others.
- Cost: about $5 for 8 API responses; the first 4 were lost to a crash in `gen_claude.py` (fixed: it now saves
  each raw response before any parsing, as `out/*.raw.json`).

## Human play-test (2026-10-03)

The user played the two playable Strata games by hand. **IQ3_XXS medium s1 is the best complete game: played to stage 6
before dying**, so it gets through its stage-3 Challenging Stage cleanly. UD-Q4 medium s2 has bad entry paths: enemies
jump around instead of flying in.

That reverses the rubric's order (71 vs 64), for two reasons the rubric cannot see:

- **Motion quality.** Reviewers read code and still screenshots. UD-Q4 s2's entry code is a Catmull-Rom spline and
  scored full marks (D5); the jumping only shows when it runs. IQ3_XXS s1's reviewer flagged a double division that
  makes entries ~3x slower than intended, which probably makes them look deliberate rather than broken.
- **Additive scoring.** A soft-lock at stage 3 (UD-Q4 s2) costs a few of 76 points. Ranking should gate on
  playability first (does it play through several stages), then use the rubric to order what passes.

**The Sonnet 5.5 game is the most faithful of all**, by the user's hand play: enemy movement and fighter capture work
the way the arcade does, and the gaps are minor. IQ3_XXS medium s1 is closer to the real game on movement than the
other Strata games but not fully right. The Sonnet game got through its Challenging Stage; 25 hits paid no end bonus.
That follows `prompt.md` exactly (100 per hit during the stage, 1,000 only per whole wave of 8, lines 698 and
1101-1102), so the gap is in the spec, which simplified the arcade's hits-based end bonus, not in the model.

Hand-play order: **Sonnet 5.5 off r1 > IQ3_XXS medium s1 > UD-Q4_K_XL medium s2.**

## IQ3_XXS with a 32K thinking cap: xhigh vs medium (2026-10-03)

Same prompt, sampling (0.6 / 0.95 / 20) and seeds as the `medium` arm, with `reasoning_budget_tokens` 32,768 instead of
16,384 and `max_tokens` 81,920. Strata runs `xhigh` the same as `high` (2026-09-28 notes). Arms `xhigh32k` and
`medium32k` in `gen.py`; all four scored blind (letters N-Q) with the rest.

| run | score /76 | play checks | severe bugs | verdict | out tokens | time |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| xhigh 32K s1 | 67 | 8 | 1 | playable with flaws (Boss hangs after a capture, no more dives that stage) | 50,383 | 7.3 min |
| xhigh 32K s2 | **72** | 8 | 1 | playable with flaws (challenge waves move twice per step, hard to hit) | 50,881 | 7.3 min |
| medium 32K s1 | 70 | 8 | 0 | playable with flaws | 44,467 | 5.8 min |
| medium 32K s2 | 51 | 8 | 3 | not playable (player `y` never set: the ship is invisible and cannot fire or die) | 44,077 | 6.1 min |
| *medium 16K s1 / s2* | *64 / 36* | *8 / 2* | *0 / 2* | *playable / not playable* | *~27,500* | *~4 min* |
| *off s1 / s2* | *0 / 35* | *2 / 5* | *2 / 6* | *not playable* | | *2-4 min* |

- **The bigger cap is the effect, more than the effort level.** At 32K, 3 of 4 games are playable, against 1 of 2 at
  16K medium and 0 of 2 with thinking off. Every run, at both levels, used its full 32K thinking budget, as every
  16K run used its 16K. None of the 32K games crashed: their failures are logic bugs, not syntax or load errors.
- **xhigh: 2 of 2 playable (67, 72); medium 32K: 1 of 2 (70, 51).** xhigh looks at least as good, but 2 runs each
  cannot separate them. No runaway thinking: the budget closed it every time.
- **The games are longer and fuller:** xhigh wrote 1,857 and 1,993 lines (16K medium: 730-766). The cost is time,
  7.3 min per game against ~4 min at 16K medium, still faster than UD-Q4 at 16K (~11 min).
- **The play-test missed a broken game:** medium 32K s2 passed all 8 checks although its fighter never appears;
  enemy motion in the bottom strip passed the "moves" check. The code review caught it.

**Hand play (user, 2026-10-03):** both xhigh games play, but their enemies do not behave like Galaga enemies. Medium
32K s1 has enemies entering the screen the way the arcade does, but its tractor beam kills the fighter instead of
capturing it. The bigger cap buys working code; whether the Galaga details come out right looks like chance recall.

## Conclusion (user's reading, 2026-10-03)

As code, every playable game is decent. **Sonnet 5.5's edge is knowing what Galaga is and how it plays**, which is
what a frontier model should have over a 125B-A6B one. A one-shot prompt with no harness leans on that training
knowledge more than on what the model can reason out and fix. Next: the same test through a coding harness (DeepSeek's,
from a laptop over the network), where the model can run its code and iterate.

## Second local reference: Qwen3.8-27B on NInfer (2026-10-03)

Qwen3.8-27B (dense, Qwen/Qwen3.8-27B as neroued/Qwen3.8-27B-NInfer, 4-6-bit groupwise, 18.2 GB) on the same RTX 4090,
served by NInfer 0.6 (`D:\ninfer-4090`, 262K context, rk4v4-e8 KV, MTP drafting 3 tokens). `gen_ninfer.py` sends the
same 8 runs IQ3_XXS got: the same prompt, sampling, seeds, effort, thinking budgets and output caps. NInfer has no
per-request thinking budget on Chat Completions, so the thinking arms go through its `/v1/messages` (`thinking.budget_tokens`
+ `output_config.effort`); `off` uses Chat Completions with `reasoning_effort: none`. Scored blind (letters R-Y).

| setting | Qwen3.8-27B | Flash-Next IQ3_XXS |
| --- | --- | --- |
| off s1 / s2 | 48 / 46 (neither playable) | 0 / 35 (neither playable) |
| medium 16K s1 / s2 | 50 / **63** | **64** / 36 |
| medium 32K s1 / s2 | **66** / **61** | **70** / 51 |
| xhigh 32K s1 / s2 | **64** / 26 | **67** / **72** |
| **playable** | **4 of 8** | **4 of 8** |
| mean score /76 | 53.0 | 49.4 |
| crashed at load or on start | **0 of 8** | 3 of 8 |
| decode, whole request | 116-129 tok/s | 115-185 tok/s |
| time per game | 1.6-7.1 min | 2.1-7.3 min |

Bold = playable (plays well or playable with flaws).

- **A tie on what matters: 4 of 8 playable each.** IQ3_XXS has the best single game (72 vs 66) and 27B the higher mean
  (53 vs 49), but the mean is pulled by IQ3_XXS's looped 0; neither difference means anything at 8 runs each.
- **27B never crashed: 0 of 8, against 3 of 8 for IQ3_XXS** (a loop, a syntax error, an exception every frame). All 8
  27B games loaded, started and survived the bot. Its failures are all logic: enemies that never enter (R, W), formation
  enemies that cannot be shot (U), a game running 16x too fast (Y), entry paths through the player's row (T).
- **Its thinking ends on its own sometimes:** medium 32K s1 stopped at ~19K of its 32K budget; IQ3_XXS used every
  token of every budget.
- **Same speed class on this card:** both decode at ~115-130 tok/s over a whole request (27B with MTP drafting, IQ3_XXS
  with MTP plus its expert cache), so a game costs about the same time on either.
- **Fence typo:** 27B medium 16K s1 opened its code with "```html>"; the extractor now accepts anything after
  ```html on the fence line (the game itself is complete, 957 lines).
- **The play-test passed games that do not work.** All 8 27B games passed 8/8, including W (no enemy ever appears),
  U (formation unshootable) and Y (game over 1.35 s after Enter, which still changes pixels). It catches crashes, not
  logic; the code review carries the verdict.

**Hand play of the four playable 27B games (user, 2026-10-03):** none has graphics as good as any Strata game.

| game | rubric | hand play |
| --- | ---: | --- |
| medium 32K s2 (S) | 61 | **the best 27B game, closest to how Galaga plays** |
| medium 16K s2 (X) | 63 | playable and OK; you can fire continuously (the 2-shot limit counts only bullets within 2 px of the ship's current x, line 386, so moving bypasses it; the reviewer docked C2) |
| xhigh 32K s1 (V) | 64 | playable but seems incomplete (its centred text is never drawn: high score, prompts, results screen) |
| medium 32K s1 (T) | 66 | runs, but entry paths kill you immediately and the graphics are poor (the reviewer's severe bug: enemies enter through the player's row) |

The rubric ranked these four almost in reverse of hand play, as it did for the Flash-Next games: it scores features
present, not how the game looks or feels. Hand play agrees with each review's *bugs*, not with its *total*.

## Second machine: RTX 5090 / Ryzen 9 9950X3D / 64 GB DDR5, engine 0.1.51 (2026-10-25)

The same 8 IQ3_XXS runs (off, medium 16K, medium 32K, xhigh 32K; seeds 1 and 2; same prompt, sampling and caps),
sent to the server the app was already running (`gen.py --use-running --prefix 5090-`), so the runs are named
`5090-iq3_xxs-*`. Machine and server:

| | |
| --- | --- |
| GPU | NVIDIA GeForce RTX 5090, 32 GB, driver 617.42 |
| CPU / RAM | AMD Ryzen 9 9950X3D (16 cores), 64 GB DDR5 (63.4 GiB usable) |
| Engine | **0.1.51** (the 4090 runs: 0.1.36), MTP drafting, `--prefill auto` (cap 8192) |
| Model | Qwen3.8-Flash-Next GSQ-RCO IQ3_XXS, the same files |
| Context | **131,072** (the 4090 runs: 262,144), KV int8, KV streaming (`--kv-resident 32768`) |
| Expert cache | **13,699 slots / 22.3 GB** (4090: 9,859 / 16.0 GB), 58 MiB VRAM free, 40 GB arena in RAM, 15 pool workers |
| Vision | on (the app's default; it costs 700 MiB of VRAM) |

Play-tested, contact-sheeted and blind-reviewed the same way (letters Z and AB-AJ; `blind.py` now keeps the old
letters and only shuffles new games). The reviewers were a different model generation from the 4090 round
(Claude Fable 5.1 against Claude Opus 5.5), which matters for the verdict column, see below.

| run | score /76 | play checks /8 | severe bugs | verdict | out tokens | time | tok/s | html lines |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| off s1 | 22 | 6 | 7 | not playable (no enemies: the stage builder never stores them; Space does not fire) | 9,353 | 0.7 min | 239 | 407 |
| off s2 | 35 | 6 | 6 | not playable (formation `y` never set; first death freezes the loop; drawn at 1x in a corner) | 10,156 | 0.7 min | 257 | 255 |
| medium 16K s1 | 51 | 8 | 3 | barely playable (stage 1 can never be cleared; aimed fire from entering enemies) | 26,824 | 1.8 min | 244 | 667 |
| medium 16K s2 | 21 | 5 | 1 | not playable (TypeError on the first frame: bezier helper fed an object, not an array) | 29,772 | 2.1 min | 238 | 1,041 |
| medium 32K s1 | **70** | 8 | 1 | barely playable (every formation enemy fires on its own timer: ~8 bullets/s rain) | 49,899 | 3.5 min | 241 | 1,872 |
| medium 32K s2 | 60 | 2 | 2 | not playable (syntax error: an extra `)` in the slot builder; page stays black) | 30,362 | 2.1 min | 239 | 833 |
| xhigh 32K s1 | 61 | 8 | 1 | barely playable (formation positions are NaN: enemies only show mid-dive) | 53,649 | 3.6 min | 248 | 2,096 |
| xhigh 32K s2 | **67** | 8 | 2 | barely playable (challenging stage soft-locks after wave 1; aimed fire at every stage start) | 53,666 | 3.8 min | 239 | 2,080 |

Against the 4090 round of the same 8 runs:

| | 4090, engine 0.1.36 | 5090, engine 0.1.51 |
| --- | --- | --- |
| mean score /76 | 49.4 | 48.4 |
| best run | 72 (xhigh 32K s2) | 70 (medium 32K s1) |
| plays well / playable with flaws | 4 of 8 | **0 of 8** |
| barely playable | 0 of 8 | 4 of 8 |
| crashed at load or on start (syntax error, exception, loop) | 3 of 8 | 3 of 8 (one syntax error, two first-frame exceptions) |
| passed all 8 play checks | 5 of 8 | 4 of 8 |
| decode, whole request | 115-185 tok/s | **238-257 tok/s** |
| time per 32K-thinking game | 5.8-7.3 min | **2.1-3.8 min** |
| time for the 8 runs | ~40 min | **18 min** |

- **Speed is the clear result: 2x.** Every run decodes at 238-257 tok/s over the whole request, against 115-127
  tok/s on the 4090 for the thinking runs; the MTP draft acceptance is 78% (33,001 of 42,285 drafts on xhigh s1) with a
  98% expert-cache hit rate. The 5090's larger cache holds 13,699 of the 24,576 experts (56%) against 40% on the
  4090, so far less goes over PCIe (`pcie_share` 0.002). A 32K-thinking game costs 3.5 min instead of 6-7.
- **Quality looks the same, with the same failure shapes.** The mean is within a point (48.4 vs 49.4), the best game
  within 2 points, and 3 of 8 still fail before gameplay. The bug list is the familiar one: an unassigned field, a
  helper called with the wrong argument type, one extra bracket, a challenging stage that never ends. Thinking budget is
  again the lever: off 22 / 35, 16K 51 / 21, 32K 70 / 60 / 61 / 67. All 32K runs used the whole budget.
- **The verdict column is not comparable across rounds.** The 4090 games were scored "playable with flaws" by Opus
  5.5 reviewers; this round's Fable 5.1 reviewers gave the equivalent games (70, 67, 61 points, 8/8 play checks, 1-2
  severe bugs) "barely playable", mostly for aimed enemy fire during entry and formation bullet rain that kill the bot
  within 30 s. The 4090 reviews never raised fire density as a reason for a verdict, and whether those games shoot as
  much was not checked, so the 4-of-8 to 0-of-8 drop may be reviewer calibration as much as the games. Hand play has
  to settle it, as in the earlier rounds. The 32K games are the ones to play: `out/5090-iq3_xxs-medium32k-s1.html`,
  `out/5090-iq3_xxs-xhigh32k-s2.html`, `out/5090-iq3_xxs-xhigh32k-s1.html`.
- **Not controlled:** engine version (0.1.36 to 0.1.51), context (262K to 131K), vision on, and the seed does not
  reproduce across engine versions, so each run is a fresh sample. With 2 runs per arm this round cannot separate a
  quality change from sampling noise; it shows the quality band did not move while the speed doubled.
- The two `off` games are the shortest of the whole test (255 and 407 lines): without thinking, the model writes a
  skeleton that touches every feature and runs almost none of it.

## IQ3_S on the 5090 (2026-10-25, engine 0.1.51)

The same 8 runs on IQ3_S, the next quant up (ISTA-DASLab, 87.7% top-token match with Q8_0 against IQ3_XXS's 84.5%),
right after the IQ3_XXS round on the same machine. The IQ3_XXS server was stopped and `gen.py --prefix 5090- --quants
IQ3_S` started its own from `strata-iq3_s.json`, rewritten to match the IQ3_XXS config of the day (131K context, KV
int8 with streaming, vision on, CUDA 13.3; the old box's 262K config is kept as `strata-iq3_s-4090.json`). Server up
in 61 s. **11,378 expert slots / 21.6 GB cache**, 389 MiB VRAM free, 47 GB arena in RAM, 15 pool workers. Same
play-test and blind review (letters AA, AC, AH, AK-AO; the IQ3_XXS and IQ3_S reviewers were the same model, Claude Fable
5.1, so the two 5090 rounds are comparable with each other).

| run | score /76 | play checks /8 | severe bugs | verdict | out tokens | time | tok/s | html lines |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| off s1 | 3 | 2 | 6 | not playable (crash at load: a canvas passed where sprite rows are expected) | 11,926 | 0.9 min | 231 | 676 |
| off s2 | 9 | 3 | 8 | not playable (crash on the first title frame: sprite frames collapsed to strings) | 10,220 | 0.7 min | 231 | 353 |
| medium 16K s1 | 50 | 8 | 3 | barely playable (game over never returns to the title; aimed fire during fly-in; challenging stage soft-locks) | 30,555 | 2.0 min | 249 | 935 |
| medium 16K s2 | 2 | 2 | 2 | not playable (syntax error: a stray `[ ]` in an object literal) | 31,188 | 2.0 min | 255 | 1,053 |
| medium 32K s1 | 32 | 8 | 2 | not playable (the player ship is never set alive, so it never appears) | 44,316 | 3.3 min | 222 | 771 |
| medium 32K s2 | 12 | 3 | 3 | not playable (assignment to a `const` on the first update: frozen on the title) | 45,550 | 2.9 min | 260 | 778 |
| xhigh 32K s1 | **69** | 8 | 1 | **playable with flaws** (challenging stage soft-locks on the first hit) | 52,769 | 3.7 min | 240 | 2,109 |
| xhigh 32K s2 | **70** | 8 | 0 | **playable with flaws** (9 minor bugs, no severe one) | 52,050 | 3.7 min | 236 | 2,088 |

| same reviewers, same machine, same day | IQ3_XXS | IQ3_S |
| --- | --- | --- |
| mean score /76 | 48.4 | 30.9 |
| best run | 70 | 70 |
| plays well / playable with flaws | 0 of 8 | **2 of 8** (both xhigh 32K) |
| barely playable | 4 of 8 | 1 of 8 |
| crashed before gameplay | 3 of 8 | **5 of 8** (one syntax error, four exceptions at load or on the first frame) |
| passed all 8 play checks | 4 of 8 | 4 of 8 |
| decode, whole request | 238-257 tok/s | 222-260 tok/s |
| time for the 8 runs | 18 min | 19 min |
| expert slots on the card | 13,699 (56%) | 11,378 (46%) |

- **Same speed as IQ3_XXS on this card.** The 5090's cache holds 46% of IQ3_S's experts instead of 56% of IQ3_XXS's,
  and the whole-request rate is the same ~240 tok/s (the expert-cache hit rate drops from 98% to 97%, `pcie_share`
  from 0.002 to 0.004). On the 4090 IQ3_S was 10-15% slower than IQ3_XXS; here the gap is gone.
- **Two "playable with flaws" games, the first of the 5090 rounds, and both from xhigh 32K.** 69 and 70 points, 8 of 8
  play checks, 0-1 severe bugs. The xhigh 32K s2 game is the only one in either 5090 round with no severe bug at all.
  The IQ3_XXS xhigh games scored 61 and 67 with the same reviewers.
- **Everything below xhigh is worse than IQ3_XXS's.** 5 of 8 crash before gameplay (IQ3_XXS: 3 of 8), and the mean is
  pulled down to 30.9 by four games scored 2-12 for never running. Note that this round's reviewers scored crashed
  games strictly (a syntax error gave 2/76, where the 4090 reviewers gave a comparable game 36 and this round's
  IQ3_XXS reviewer gave one 60 for what the code would have done), so the means of crashed games are not comparable
  across reviewers; count the crashes instead.
- **The play-test again passed a game with no player ship** (medium 32K s1, 8 of 8 checks): the "moves" check sees the
  enemies in the bottom strip. The code review caught it, as it did for IQ3_XXS medium 32K s2 on the 4090.
- **Reading across the two 5090 rounds:** the xhigh 32K arm is 4 of the 16 games and holds 4 of the top 5 scores
  (70, 69, 67, 61; the fifth is IQ3_XXS medium 32K s1 at 70), and every xhigh game ran through the play-test. The
  budget and effort, not the quant, is the lever on this test; with 2 runs per arm the quant difference (2 of 8
  against 0 of 8 playable, 5 against 3 crashes) is inside the noise, as the 4090 round concluded for 4 runs per quant.

Games to hand-play: `out/5090-iq3_s-xhigh32k-s2.html` (70, no severe bug) and `out/5090-iq3_s-xhigh32k-s1.html` (69).

## UD-Q4_K_XL on the 5090 with 64 GB (2026-10-25, engine 0.1.51)

The same 8 runs on Unsloth's 4-bit UD-Q4_K_XL (93.1% top-token match with Q8_0), the quant that had the best mean and
the best Strata game on the 4090 round. On this 64 GB machine it cannot keep its 72 GiB of experts in RAM, so the engine
runs its **mapped mode with a RAM budget**: the hottest experts in RAM, the rest read from the GGUF on the SSD for every
token ([UNSLOTH_Q4.md](../../docs/UNSLOTH_Q4.md)). Config `strata-unsloth-ud-q4_k_xl.json`, rewritten from the 96 GB
box's (kept as `strata-unsloth-ud-q4_k_xl-4090.json`): `--resident-budget-gib 40` (the docs' rule, RAM less 24 GB),
131K context, KV int8 with streaming, vision on, CUDA 13.3, the `STRATA_PARTIAL_PIN` env dropped (the docs measured it
no faster). Server up in 40-51 s; **7,165-7,229 expert slots / 21 GB** on the card (29% of the experts), 15 pool
workers. Same play-test and blind review (letters AP-AW, Claude Fable 5.1 reviewers like the other two 5090 rounds).

**The RAM budget was clamped for the first four runs.** The engine log for the first start:

```
--resident-budget-gib 40.00 exceeds available commit (22.71 GiB minus 4 GiB headroom and a 0.25 GiB margin): 18.46 GiB
```

Windows caps committed memory at RAM plus the pagefile (63.4 + 28 GB, automatically managed), the engine process commits
about 55 GB while touching 23, and the rest of the system had the remainder, so only 22.7 GB of commit was left for the
expert budget. RAM in use was 43.5 of 63.4 GiB the whole time: Task Manager's "In use" is not the limit, "Committed" is.
After the `off` and `medium 16K` runs the user set a fixed 64 GB pagefile (commit limit 127 GB) and rebooted; the
generator resumed from `medium 32K s1` and the engine logged `RAM budget 40.00 GiB: 13704 of the 50.63 GiB of experts the
GPU cache does not hold` (6,316 experts in RAM before). The games are the same test either way (the budget only decides
whether an expert comes from RAM or the SSD); the times are not.

| run | RAM budget | score /76 | play checks /8 | severe bugs | verdict | out tokens | time | tok/s | html lines |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| off s1 | 18.5 GiB | 35 | 8 | 4 | barely playable (formation `y` is NaN: enemies vanish on arrival; no enemy ever dives; corrupt bitmap font) | 14,772 | 7.0 min | 35 | 710 |
| off s2 | 18.5 GiB | 23 | 8 | 5 | not playable (stuck on the STAGE 1 banner: the state never becomes playing, the player is never created) | 12,453 | 5.7 min | 37 | 533 |
| medium 16K s1 | 18.5 GiB | **70** | 8 | **0** | **playable with flaws** (12 minor bugs) | 32,728 | 16.4 min | 33 | 1,083 |
| medium 16K s2 | 18.5 GiB | 7 | 2 | 3 | not playable (crash at load: a leftover placeholder line builds a sprite from `undefined`) | 29,122 | 16.1 min | 30 | 848 |
| medium 32K s1 | 40 GiB | 6 | 2 | 5 | not playable (crash at load: a field set on the game object before it exists) | 47,790 | 14.3 min | 56 | 954 |
| medium 32K s2 | 40 GiB | 3 | 2 | 2 | not playable (crash at load: an undeclared variable in the sprite builder) | 44,844 | 15.0 min | 50 | 760 |
| xhigh 32K s1 | 40 GiB | **65** | 8 | 1 | **playable with flaws** (challenging stage soft-locks after any hit) | 51,089 | 16.3 min | 52 | 2,002 |
| xhigh 32K s2 | 40 GiB | **60** | 8 | 2 | **playable with flaws** (the tractor beam can never capture; the player is frozen in challenging stages) | 52,205 | 16.6 min | 52 | 1,958 |

| same reviewers, same machine, same day | IQ3_XXS | IQ3_S | UD-Q4_K_XL |
| --- | --- | --- | --- |
| mean score /76 | 48.4 | 30.9 | 33.6 |
| best run | 70 | 70 | 70 |
| plays well / playable with flaws | 0 of 8 | 2 of 8 | **3 of 8** |
| barely playable | 4 of 8 | 1 of 8 | 1 of 8 |
| crashed at load or on start | 3 of 8 | 5 of 8 | 3 of 8 (all three at load) |
| passed all 8 play checks | 4 of 8 | 4 of 8 | 5 of 8 |
| decode, whole request | 238-257 tok/s | 222-260 tok/s | 30-37 (18.5 GiB) / 50-56 (40 GiB) tok/s |
| time for the 8 runs | 18 min | 19 min | 107 min |
| expert slots on the card | 13,699 (56%) | 11,378 (46%) | 7,229 (29%) |
| games with no severe bug | 0 | 1 | 1 |

- **Speed: 5x slower than the IQ3 quants here, and no slower than on the 96 GB 4090 box.** With the 40 GiB budget
  UD-Q4_K_XL decodes at 50-56 tok/s over a whole request; the 4090 with every expert in RAM did 45-54. The 5090's larger
  cache (7,229 experts on the card against 5,010 on the 4090 for this file) makes up for the SSD reads. At the
  clamped 18.5 GiB budget it was 30-37 tok/s, so **the pagefile change was worth 1.6x**. Per request the engine read
  780-850 GB of expert data from the SSD (`file_mb` in the run records), which the OS file cache serves in part; the
  SSD is part of the speed here.
- **Quality: the most "playable with flaws" of the three quants, 3 of 8, and again all from thinking runs.** The medium
  16K s1 game is the best-rated of the whole 5090 test together with two 70s from the other quants, and the only one of
  its arm in any 5090 round with no severe bug. Both xhigh 32K games run. The 32K medium runs both crashed at load, as
  did medium 16K s2: three leftover or half-edited lines (`mkSprite(SPR.zako[0]?undefined:undefined)`, `G.stars=[]`
  before `G` exists, a `{c,w,h}` with `h` never declared), the same failure shape as the other quants, one typo away
  from a running game.
- **The quants still cannot be ranked.** 3, 2 and 0 "playable with flaws" out of 8, with 3, 5 and 3 crashes, and the
  same best score (70) for all three. That is what 2 runs per arm looks like: the thinking budget moves the result more
  than the quant does (across the three rounds, 7 games scored above 60: 6 from the 32K-thinking arms and 1 from medium 16K; the best
  `off` game scored 35).
- **The play-test passed two broken games** (off s1 and s2): enemies that vanish on arrival, and a STAGE 1 banner that
  never ends, both still animate the canvas. The code review carries the verdict, as in every round.
- **Not comparable with the 4090 UD-Q4 round** (1 of 4 playable, best 71): different reviewers, 4 runs, all experts in
  RAM there, and the seeds do not reproduce across engine versions.

**Hand play (user, 2026-10-25):**

| game | rubric | hand play |
| --- | ---: | --- |
| medium 16K s1 (AQ) | 70, no severe bug | **Rivals the Sonnet 5.5 game: one of the closest to real Galaga so far, tying Sonnet on similarity.** One bug: after a capture, the respawned fighter appears where the captured one was and dies at once. |
| xhigh 32K s1 (AP) | 65 | Kind of playable, but the movement is odd and it did not really work. |
| xhigh 32K s2 (AU) | 60 | Not playable at all. |

The capture bug the reviewer missed, confirmed in the code: the capture pull moves the fighter's `y` up to the Boss
(lines 775-776), and `respawnCheck` resets only `x` (line 498: `p.alive=true;p.x=112;...`), so the new fighter spawns at
the Boss's altitude inside the formation and is rammed as soon as its 90 frames of invulnerability end. A one-line fix
(`p.y=252` there). Hand play ranks the three the same way the rubric did this time (70 > 65 > 60), but with a far bigger
gap than 10 points: one game is close to the arcade, the other two are not, which the rubric's additive score does not
show. For the first time a Strata game is put level with the Sonnet 5.5 game on faithfulness, by a 4-bit quant with a
16K thinking budget.

## DeepSeek V4.1-Flash on the 5090 with 128 GB (2026-11-04, Strata 0.2.10, DeepSeek engine 0.1.56)

The same 8 runs on a different model: DeepSeek V4.1-Flash-1017 in ISTA-DASLab's IST-DAS 2.25 bpw pack (IQ2_XS shards,
144.6 GB, plus the 111 GB Engram table), on its own engine (`strata-dsv41.exe`). The machine is the same 5090 /
9950X3D box with **128 GB DDR5** now (64 GB in the three rounds above), the model files on a Crucial T710 NVMe. Server:
`strata launch --family deepseek41 --model ist-das-2.25bpw --context 128k --speed faster --set cpu-threads=16`
(131K context, FP4 KV, vision on, `--speed faster` = 5 of 6 routed experts per token, DSpark drafter off), sent to the
running server with `gen.py --use-running`. **2,398 of 15,360 experts on the card (23.7 GB)**, a 104 GB RAM store
of the hottest experts, the rest read from the SSD. Same prompt, the same Qwen sampling as every arm above (DeepSeek's own
recommendation is temperature 1.0, top_p 1.0; not used, to keep the test identical), same caps, seeds and thinking
budgets; DeepSeek's server takes `reasoning_effort` medium / xhigh and `reasoning_budget_tokens` the same way. Same
play-test and blind review (letters AX-BE, Claude Fable 5.1 reviewers like the other 5090 rounds).

| run | score /76 | play checks /8 | severe bugs | verdict | out tokens | time | tok/s | html lines |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| off s1 | 55 | 6 | 2 | not playable (the first Zako or Goei kill freezes the game: a 4-frame index into the 3-frame small explosion) | 14,541 | 6.2 min | 39 | 1,632 |
| off s2 | 41 | 7 | 2 | barely playable (stage 3 stack-overflows: `startChallengingStage` calls itself; a rescue can never clear the stage) | 13,368 | 5.3 min | 42 | 1,505 |
| medium 16K s1 | **70** | 8 | **0** | **playable with flaws** (11 minor bugs: escorts never return, challenge-stage hits never counted) | 32,735 | 13.3 min | 41 | 1,782 |
| medium 16K s2 | 68 | 6 | 2 | barely playable (the first death by an enemy bullet freezes the game; after one capture no enemy dives again) | 32,394 | 13.0 min | 42 | 1,661 |
| medium 32K s1 | 35 | 8 | 1 | not playable (the fighter is never activated at game start: the formation flies in and waits forever) | 50,448 | 20.6 min | 41 | 1,863 |
| medium 32K s2 | **67** | 8 | 1 | **playable with flaws** (escorts stranded off-screen after a Boss dive; dives stop after two) | 47,680 | 19.2 min | 41 | 1,624 |
| xhigh 32K s1 | 62 | 8 | 2 | barely playable (no respawn after the first death or capture: soft-lock after one life) | 50,031 | 19.7 min | 42 | 2,004 |
| xhigh 32K s2 | 53 | 6 | 3 | barely playable (the first bullet death freezes the game; the tractor dive reads a field that does not exist) | 50,411 | 20.1 min | 42 | 2,042 |

| same machine, same reviewers | IQ3_XXS | IQ3_S | UD-Q4_K_XL | DeepSeek V4.1 2.25 bpw |
| --- | --- | --- | --- | --- |
| RAM | 64 GB | 64 GB | 64 GB | 128 GB |
| mean score /76 | 48.4 | 30.9 | 33.6 | **56.4** |
| best run | 70 | 70 | 70 | 70 |
| plays well / playable with flaws | 0 of 8 | 2 of 8 | 3 of 8 | 2 of 8 |
| barely playable | 4 of 8 | 1 of 8 | 1 of 8 | 4 of 8 |
| crashed at load or on start | 3 of 8 | 5 of 8 | 3 of 8 | **0 of 8** |
| passed all 8 play checks | 4 of 8 | 4 of 8 | 5 of 8 | 4 of 8 |
| decode, whole request | 238-257 tok/s | 222-260 tok/s | 30-56 tok/s | 39-42 tok/s |
| time for the 8 runs | 18 min | 19 min | 107 min | 117 min |
| games with no severe bug | 0 | 1 | 1 | 1 |

- **Every DeepSeek game runs.** All 8 finished on their own (`stop`, none at the cap, no loops), all 8 load, draw a
  title and start a game. No other 5090 round got all 8 past the load: the Qwen quants crashed at load or on
  start in 3 to 5 of 8. That is why the mean is 8-26 points higher. DeepSeek's games fail later, in play: 4 of 8 freeze
  on a runtime exception (three of them the same mistake, replacing the enemy-bullet array while a loop walks it), and
  the others soft-lock (no respawn, a fighter never activated, stranded escorts).
- **The best game is no better.** 70 again, the fourth 70 on this machine, from medium 16K s1 with no severe bug, like
  UD-Q4's medium 16K s1. "Playable with flaws" is 2 of 8, inside the Qwen quants' 0-3.
- **Thinking off is closer to the thinking arms here** (55 and 41 against the Qwen quants' 3-35), but neither `off` game
  is playable. The two playable games are medium 16K and medium 32K; xhigh 32K gave 62 and 53, both barely playable.
- **Speed: 6x slower than the IQ3 quants, about the same as UD-Q4 at its 40 GiB budget.** 39-42 tok/s over every
  whole request, flat from 15K to 50K tokens, 2 h for the 8 runs. The server had just been restarted: the first run
  started at 25 tok/s and was at 40 by its end.
- **The play-test passed a broken game again** (medium 32K s1: 8/8 checks, but the fighter is never active; the
  enemies flying in move the bottom of the screen, so `moves` passes). Confirmed in the code: `startGame` sets
  `player.active = false` (line 782), `startStage` never sets it back, and `resetPlayer` is only reached from the
  respawn path (line 1073).
- **Not a quant comparison.** A different model (against Qwen3.8-Flash-Next), a different engine and twice the RAM. Not hand-played yet: the games to play are `out/5090-deepseek41-2.25bpw-medium-s1.html`
  (70) and `out/5090-deepseek41-2.25bpw-medium32k-s2.html` (67).

## Unsloth UD-Q6_K_XL on the 5090 with 128 GB (2026-11-05, Strata 0.2.11, engine 0.1.57)

The same 8 runs on Qwen3.8-Flash-Next again, in Unsloth's 6-bit file (UD-Q6_K_XL at revision `38bb39e`, 169.2 GB;
not touched by Unsloth's 2026-11-04 "Dynamic v3.1" re-release, which changed the 4-bit and smaller sets only). Same
5090 / 9950X3D box with 128 GB. With 128 GB **every routed expert is held in RAM** (101.75 GiB; 43 GB locked, about
59 GiB pinned in slices), **5,223 experts also on the card (21.6 GiB)**, the 54.4 GB Q8_0 PLE table read from the file
on the T710. Server: `strata launch --family unsloth --model UD-Q6_K_XL --context 128k` (131K context, int8 KV, vision
on, DFlash2 drafter, one request at a time), then a quick tune that kept `--prefill auto:32768` (its own decode
measurement, with MTP: 81.4 -> 89.5 tok/s, flagged noisy). Same prompt, sampling, caps, seeds and thinking budgets; same
play-test and blind review (letters BF-BM, Claude Fable 5.1 reviewers).

| run | score /76 | play checks /8 | severe bugs | verdict | out tokens | time | tok/s | html lines |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| off s1 | 34 | 2 | 12 | not playable (the title screen asks for sprites that do not exist; the throw skips `ctx.restore()`, so the screen stays black) | 11,470 | 2.0 min | 94 | 500 |
| off s2 | 21 | 8 | 5 | not playable (the player respawns every tick: GAME OVER in four ticks, no enemy ever appears) | 14,113 | 2.4 min | 99 | 840 |
| medium 16K s1 | 45 | 8 | 2 | not playable (the player object has no `y`: the fighter is never drawn, its shots vanish, it cannot be hit) | 29,940 | 6.3 min | 80 | 998 |
| medium 16K s2 | 8 | 2 | 1 | not playable (`FPS is not defined` in the main loop: nothing is ever drawn) | 29,918 | 6.1 min | 82 | 944 |
| medium 32K s1 | 53 | 8 | 3 | not playable (the fire cooldown is never set, so the player can never shoot) | 34,966 | 7.6 min | 76 | 847 |
| medium 32K s2 | **69** | 6 | 1 | **playable with flaws** (the title screen throws every frame and shows no text, but Enter starts a working game) | 44,931 | 9.6 min | 78 | 796 |
| xhigh 32K s1 | **68** | 8 | 1 | **playable with flaws** (divers leaving the bottom fly back up through the player's row) | 50,108 | 10.4 min | 80 | 2,073 |
| xhigh 32K s2 | 51 | 8 | 4 | barely playable (entering enemies switch to the wrong state and vanish at their slot: no formation, no dives) | 54,513 | 9.8 min | 93 | 2,124 |

| same machine, same reviewers | UD-Q4_K_XL | UD-Q6_K_XL | DeepSeek V4.1 2.25 bpw |
| --- | --- | --- | --- |
| RAM | 64 GB | 128 GB | 128 GB |
| experts | a 40 GiB RAM budget, the rest from the SSD | all in RAM | 16% on the card, a 104 GB store, the rest from the SSD |
| mean score /76 | 33.6 | 43.6 | **56.4** |
| best run | 70 | 69 | 70 |
| plays well / playable with flaws | 3 of 8 | 2 of 8 | 2 of 8 |
| barely playable | 1 of 8 | 1 of 8 | 4 of 8 |
| crashed at load or on start | 3 of 8 | 3 of 8 | **0 of 8** |
| passed all 8 play checks | 5 of 8 | 5 of 8 | 4 of 8 |
| decode, whole request | 30-56 tok/s | **76-99 tok/s** | 39-42 tok/s |
| time for the 8 runs | 107 min | **54 min** | 117 min |
| games with no severe bug | 1 | 0 | 1 |

- **6-bit is not a clear step up from 4-bit here.** The mean is 10 points higher than UD-Q4's (43.6 against 33.6), the
  best game a point lower (69 against 70), and the playable count one lower (2 against 3). The same seed does not give
  the same token stream on two files, and single runs swing widely: UD-Q4's medium 32K pair scored 6 and 3 where Q6's
  scored 53 and 69, and UD-Q4's medium 16K s1 scored 70 where Q6's scored 45. Eight runs cannot separate the two.
- **The failures are the same kind as in every other round:** a name used that was never defined (`FPS`, `SPR.boss`),
  a field never initialised (`player.y`, `fireCd`), a state name that does not match its handler. One such slip is
  enough to make a game unplayable, and every Q6 game has at least one severe bug.
- **The play-test passed three games that do not work** (off s2, medium 16K s1, medium 32K s1: 8/8 checks each, but
  no enemies, no fighter or no shooting), and failed the best game (medium 32K s2, 6/8, because of the title-screen
  exception). Its checks see motion and errors, not gameplay.
- **Entry motion:** the xhigh 32K s1 reviewer notes that each arriving enemy jumps sideways at its slot (the path ends
  at the unswayed slot, the formation sways up to 16 px); the DeepSeek medium 16K s1 game has the same snap (up to
  3.5 px). The same mistake from a 6-bit Qwen file and a 2.25 bpw file of another model points more to what the models
  know about Galaga than to quantization.
- **Speed: the fastest Unsloth round, twice DeepSeek's.** 76-99 tok/s over every whole request, 54 minutes for the 8
  runs, with no expert read from the SSD. Not hand-played yet: the games to play are
  `out/5090-unsloth-ud-q6_k_xl-medium32k-s2.html` (69) and `out/5090-unsloth-ud-q6_k_xl-xhigh32k-s1.html` (68).

## What this does and does not show

- **One-shot, this task is mostly failed by every quant: 2 playable games out of 12.** 7 of 12 never reach gameplay:
  3 syntax errors (one is the truncated loop), 4 runtime exceptions at load or on the first frame. The rest have
  logic bugs that only show up in play: the formation never completes, stage 1 cannot be cleared, the Challenging
  Stage never ends. The model writes plausible, well-structured code with all the spec's systems sketched, then
  leaves a missing bracket, a `const` reassigned, or a state name spelled two ways.
- **Thinking `medium` is the clearest effect**: both playable games came from it, and its mean is 19 points higher.
  6 runs per arm, so it is a direction, not a measurement. All six medium runs used the full 16K thinking budget.
- **The quants cannot be ranked from this.** The spread *within* a quant (IQ3_XXS: 0 to 64) is far larger than the
  gap between quant means (34 / 35 / 43). UD-Q4 has the best mean and the best single game, which agrees in
  direction with the hard suite (52/58 vs 50/58), but 4 runs each cannot separate them. Telling them apart would
  need ~20+ runs per quant, or an agentic setup (let the model run its code and fix errors) that turns most of
  these near-misses into working games.
- **Speed is the solid difference.** IQ3_XXS writes a full game in ~2 min (off) or ~4 min (medium), UD-Q4 in ~5 or
  ~11. For an iterate-and-fix workflow, IQ3_XXS gets 2-3 attempts in the time UD-Q4 takes for one.
- **A repetition loop at temperature 0.7 without thinking** (IQ3_XXS off s1): writing explosion frames as pixel
  strings, it repeated one solid 11x11 frame 346 times to the token cap. One case in 12, on the fastest quant; not
  enough to call it a quant effect. A `presence_penalty` (Qwen suggests 0-2 against endless repetition) was not
  tried.

## Harness caveats

- Playwright's `keyboard.press` sends down+up in the same instant; games that poll a `keys[]` table once per frame
  never see it. Taps are held 80-100 ms (fixed before the final play-test run; the first run under-counted one game).
- A script cut off without `</script>` raises no catchable error, so the looped run shows `loads_clean: true`; it
  fails every other check.
- The bot is crude and dies fast. The play checks prove "starts and survives", not "is good"; the review scores
  carry the judgement.
- Reviewer calibration was spot-checked on the top game: the stage-3 soft-lock it reported (`bonus:0` but the
  tally runs only `if (ch.bonus < 0)`) is real.

## Reproducing

```bash
../../.venv/Scripts/python.exe gen.py                       # ~70 min: 3 server starts, 12 generations
../../.venv/Scripts/python.exe gen.py --use-running --prefix 5090- --quants IQ3_XXS --arms off,medium,medium32k,xhigh32k  # against a running server
../../.venv/Scripts/python.exe gen.py --prefix 5090- --quants IQ3_S --arms off,medium,medium32k,xhigh32k                # starts its own server
../../.venv/Scripts/python.exe gen.py --prefix 5090- --quants unsloth-ud-q4_k_xl --arms off,medium,medium32k,xhigh32k   # ~110 min on 64 GB (SSD-mapped)
../../.venv/Scripts/python.exe gen.py --use-running --prefix 5090- --quants deepseek41-2.25bpw --arms off,medium,medium32k,xhigh32k  # a running DeepSeek server, ~2 h
pw/Scripts/python.exe playtest.py "5090-deepseek41*.html"   # a glob must end in .html: it would also load the .json records
../../.venv/Scripts/python.exe gen.py --use-running --prefix 5090- --quants unsloth-ud-q6_k_xl --arms off,medium,medium32k,xhigh32k  # a running UD-Q6_K_XL server, ~1 h on 128 GB
pw/Scripts/python.exe playtest.py "5090-unsloth-ud-q6*.html"
python -m venv pw && pw/Scripts/pip install playwright pillow
pw/Scripts/python.exe playtest.py && pw/Scripts/python.exe sheet.py
python stats.py && python blind.py                          # then review each review/<letter>/ against rubric.md
python results.py
```

The two playable Strata games: `out/unsloth-ud-q4_k_xl-medium-s2.html` and `out/iq3_xxs-medium-s1.html`; the Sonnet
5.5 baseline game: `out/sonnet-5-5-off-r1.html`. The Sonnet runs: `apivenv/Scripts/python.exe gen_claude.py` with
`ANTHROPIC_API_KEY` set (paid; up to ~$0.50 of output per run at the 49K cap).
