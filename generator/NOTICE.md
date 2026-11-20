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
