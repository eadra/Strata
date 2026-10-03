# Galaga test: review rubric

Score every item **0, 1 or 2** from the code, checked against the play-test screenshots and result:

- **2** = implemented and, as far as the code shows, works as the spec says.
- **1** = partly done, simplified, or present but with a bug that would visibly misbehave.
- **0** = missing, a stub, or broken so it cannot work.

Cite line numbers for every score. Judge what the code *does*, not what its comments or the model's closing
summary claim. If a feature's code exists but is never called or can never trigger, it scores 0. Do not give
credit for effort. Be equally strict with every file.

## A. Deliverable (4 items)
- A1 One complete file; no truncation, placeholders or "rest of code" stubs; no external resources.
- A2 Runs without errors (use the play-test result: `loads_clean`, `survives_play`, and the errors list).
- A3 Fixed-timestep loop on `requestAnimationFrame` (speed does not depend on refresh rate).
- A4 Code structure: state / update / render separated, readable names, sensible comments.

## B. Presentation (6 items)
- B1 3:4 portrait playfield (224x288 proportions), integer or crisp scaling, centred on black.
- B2 Scrolling multi-coloured starfield with twinkle.
- B3 HUD: 1UP score, HIGH SCORE, reserve ships bottom-left, stage badges bottom-right.
- B4 Title/attract screen with the enemy score table and "PRESS ENTER TO START".
- B5 Flow: "STAGE N" before stages, "GAME OVER", return to the title screen.
- B6 High score saved to and loaded from localStorage.

## C. Player (4 items)
- C1 Controls: Left/Right + A/D move (horizontal only), Space fires, Enter starts, P pauses.
- C2 At most two player shots on screen at once.
- C3 3 ships total; extra ship at 20,000 and every 70,000 after.
- C4 Results screen at game over: shots fired, hits, hit-miss ratio %.

## D. Enemies (9 items)
- D1 Zako, Goei and Boss Galaga with distinct sprites and 2-frame wing animation.
- D2 Point values: Zako 50/100, Goei 80/160, Boss 150 formation / 400 / 800 / 1,600 by escorts when diving.
- D3 Boss Galaga takes two hits and changes colour after the first.
- D4 Formation layout: 4 Boss, 16 Goei in two rows, 20 Zako in two rows.
- D5 Enemies fly in along curved entry paths in groups, then take their formation slots.
- D6 Formation sways while filling, then breathes (expand/contract) once complete.
- D7 Dives on curved paths with enemy fire; divers that leave the bottom re-enter from the top and return to their slot.
- D8 Boss Galaga dives with Goei escorts; dive frequency/aggression rises with the stage.
- D9 Collisions: enemy bullet or enemy body kills the player; a rammed enemy dies too.

## E. Tractor beam and dual fighter (6 items)
- E1 Boss stops partway down and projects an animated, widening tractor beam.
- E2 Capture: the ship is pulled up, turns red, is held above the Boss in formation; the player loses that ship (game
  over if it was the last).
- E3 Rescue: shooting the Boss while it dives frees the captive, which flies down and docks beside the player.
- E4 Dual fighter: moves together, fires two shots at once, a hit removes only one half.
- E5 Shooting the Boss in formation destroys the captive (it does not return).
- E6 The captured fighter fires at the player when its Boss dives.

## F. Stages (4 items)
- F1 Clearing a stage advances to the next.
- F2 Challenging stages at 3, 7, 11, ...: 5 waves of 8 looping fly-through enemies that do not fire or stay.
- F3 Challenging-stage scoring: 100 per hit, 1,000 per whole wave, 10,000 PERFECT, "NUMBER OF HITS" + bonus shown.
- F4 Stage badges in the arcade's denominations (1, 5, 10, 20, 30, 50).

## G. Sound (2 items)
- G1 Web Audio sounds for: player shot, enemy hit, enemy destroyed, Boss hit, player explosion, tractor beam, stage
  jingle (2 = all or all but one; 1 = at least three).
- G2 Audio context started on first key press; M mutes.

## H. Polish and fairness (3 items)
- H1 Hitboxes no larger than the sprites.
- H2 Frame-by-frame explosion animations for enemies and the player.
- H3 Respawn after a delay with "READY"; enemies do not dive while the player is respawning.

**Maximum: 38 items x 2 = 76.**

## Also report

- **Bugs:** every defect you find that a player would notice (crash, soft-lock, feature that never triggers, wrong
  rule), with line numbers, each marked *severe* (breaks or blocks play) or *minor*.
- **Playability verdict**, one of: *plays well*, *playable with flaws*, *barely playable*, *not playable*.
- **One paragraph** on overall code quality and how faithful it feels to Galaga.
