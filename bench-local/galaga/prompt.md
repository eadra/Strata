Build a faithful clone of the 1981 Namco arcade game **Galaga** that runs in a web browser.

## Deliverable

- Exactly **one file**, `galaga.html`, containing all HTML, CSS and JavaScript.
- No external resources of any kind: no libraries, CDNs, fonts, image or audio files. Draw all graphics in code
  (canvas drawing or pixel-art sprites defined as data in the file) and make all sound with the Web Audio API.
- It must run by opening the file directly in a current Chrome or Firefox (`file://`), with no build step and no
  errors in the console.
- Reply with the complete file in a single ```html code block. Do not abbreviate, leave placeholders, or write
  "rest of the code here": the file must be complete and playable as delivered. After the code block, give a short
  list of anything from the spec you did not implement.

## Screen and presentation

- A portrait playfield in the arcade's 224x288 proportions (3:4), scaled up with crisp pixels to fit the browser
  window, centred on a black page.
- A scrolling multi-coloured starfield behind everything, with twinkling stars.
- HUD: `1UP` score and `HIGH SCORE` at the top; remaining reserve ships at the bottom left; stage badges (flags) at
  the bottom right.
- An attract/title screen showing the title, the score table for each enemy type, and "PRESS ENTER TO START".
  Show "STAGE N" before each stage and "GAME OVER" at the end, then return to the title screen.
- Keep the high score in `localStorage`.

## Player

- The fighter moves left and right only, along the bottom of the screen. Controls: Left/Right arrows (also A/D) to
  move, Space to fire, Enter to start, P to pause.
- **At most two of the player's shots on screen at once**, as in the arcade.
- Start with 3 ships (1 in play + 2 in reserve). Award an extra ship at 20,000 points and at every 70,000 after.
- Hit-results screen at game over: shots fired, number of hits, and hit-miss ratio as a percentage.

## Enemies and formation

- Three enemy types with distinct sprites and 2-frame wing-flap animation:
  - **Zako** (blue/yellow bee): 50 points in formation, 100 diving.
  - **Goei** (red butterfly): 80 in formation, 160 diving.
  - **Boss Galaga** (green; turns blue/purple after its first hit): takes **two hits**. 150 in formation; 400 when
    shot diving alone; 800 when diving with one escort and 1,600 with two escorts.
- The standard formation: 4 Boss Galaga in the top row, 16 Goei in the next two rows, 20 Zako in the two bottom
  rows (40 enemies).
- At the start of each stage enemies **fly in along curved entry paths** in groups and take their place in the
  formation. They are not simply spawned in place. Enemies may fire while entering.
- The formation sways side to side while filling, then "breathes" (expands and contracts) once complete.
- Enemies peel off and **dive at the player** along curved paths, firing as they come; a diver that leaves the
  bottom of the screen re-enters from the top and returns to its slot. Boss Galaga can dive with Goei escorts.
  Dives get more frequent and aggressive in later stages.
- Colliding with an enemy or being hit by an enemy bullet destroys the player's ship; the enemy rammed is also
  destroyed.

## Tractor beam and dual fighter (the signature mechanic)

- A Boss Galaga sometimes dives partway down, stops, and projects a **tractor beam** (animated, widening blue
  cone) toward the bottom of the screen.
- If the player's ship is caught in the beam, it is pulled up, turns red, and is held as a **captured fighter**
  above the Boss in the formation. The player loses that ship and continues with the next reserve ship. If that was
  the last ship, the game is over.
- If the player shoots the Boss **while it is diving** with the captured ship, the captured ship is freed, flies
  down, and **docks beside the player's ship to form a dual fighter**: two ships side by side that move together and
  fire two shots at once (twice the width as a target). If either half is hit, only that half is lost.
- Shooting the Boss while it sits **in formation** destroys the captured fighter along with it; the captive turns
  hostile and does not return.
- The captured fighter fires at the player when its Boss dives.

## Stages

- After all enemies of a stage are destroyed, advance to the next stage.
- **Challenging Stage** at stage 3 and every 4th stage after (3, 7, 11, ...): 40 enemies fly through in 5 waves of
  8 along looping patterns without firing or diving, and do not stay. Each hit is 100 points; a bonus of 1,000 for
  each whole wave of 8 destroyed, and a **10,000 PERFECT!** bonus for all 40. Show "NUMBER OF HITS" and the bonus
  afterwards.
- Stage badges at the bottom right follow the arcade's denominations (1, 5, 10, 20, 30, 50).

## Sound (Web Audio, synthesized)

- Distinct sounds for at least: player shot, enemy hit, enemy destroyed, Boss hit, player explosion, tractor beam,
  and a short stage-start jingle. Start the audio context on the first key press (browsers block audio before
  that). Add an M key to mute.

## Engineering requirements

- A fixed-timestep game loop driven by `requestAnimationFrame`, so game speed does not depend on the monitor's
  refresh rate.
- Separate the game state, update logic and rendering. Use readable names and brief comments.
- Collision detection that is fair to the player (hitboxes no larger than the visible sprites).
- Explosions with a short frame-by-frame animation for both enemies and the player.
- Respawn the player with a short delay and the "READY" text, and do not let enemies dive while the player is
  respawning.
