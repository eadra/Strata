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
python -m venv pw && pw/Scripts/pip install playwright pillow
pw/Scripts/python.exe playtest.py && pw/Scripts/python.exe sheet.py
python stats.py && python blind.py                          # then review each review/<letter>/ against rubric.md
python results.py
```

The two playable Strata games: `out/unsloth-ud-q4_k_xl-medium-s2.html` and `out/iq3_xxs-medium-s1.html`; the Sonnet
5.5 baseline game: `out/sonnet-5-5-off-r1.html`. The Sonnet runs: `apivenv/Scripts/python.exe gen_claude.py` with
`ANTHROPIC_API_KEY` set (paid; up to ~$0.50 of output per run at the 49K cap).
