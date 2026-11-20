# Notice

The artwork code in `templates/` and `lib/` is adapted from
[README Templates](https://github.com/Dr-At0mic/README-Templates) by Anandhu Suresh.
The upstream repository's LICENSE file is the GNU GPL v3 (its README says MIT); this folder
is distributed under the GPL v3, see `LICENSE`.

Changes from upstream (November 2026):
- Import paths given `.js` extensions so the files run directly in Node.
- Singularity telemetry: when `allTime` is set, the stars/followers readouts are replaced with
  all-time contributions and best day; when no public languages exist, the spectral band shows
  the configured `stack` instead.
- Pac-Man scoreboard: same all-time swap in the high-score table, and `stack` as bonus items.
- `build.mjs` and `config.json` are new: they fetch live GitHub data and write the SVGs.
- Pac-Man hero: new endless mode (`endless: true`). The chomper tours every contribution pellet,
  ghosts trail it and turn blue on power pellets, the board flashes CLEAR!, and the round restarts
  forever.
- Singularity hero: a small astronaut developer with a laptop rides a chrome rocket hoverboard around the black hole (in front of
  the disk on the near side, behind the shadow on the far side).
- Singularity hero: a distant space battle in the background (alien saucer, fighters, laser fire,
  an explosion, and a far dogfight).
- Singularity hero: Earth in the far distance (a light on Durban) with a rocket launching every 10s.
