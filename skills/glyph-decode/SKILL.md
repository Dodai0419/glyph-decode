---
name: glyph-decode
description: Make an animated SVG where text decodes in through a glyph grid (ASCII, dither, terminal, blueprint or math symbols). No JavaScript, so it plays in a GitHub README, docs site or slide. Use when the user wants an animated README header, a "hacker" text reveal, a loading-style title, or a math-themed title animation.
---

# glyph-decode

Generates a self-contained SVG (CSS keyframes only). Every character scrambles through a ramp of glyphs and lands left to right in one wave, then holds and loops.

## Commands (run from the repo root, Python 3.9+, no installs)
```bash
python glyph_decode.py "Your project name" -o header.svg                 # default 'decode' preset, loops
python glyph_decode.py "Line one\nLine two" --preset math --rest 0.25 -o title.svg
python glyph_decode.py "$ deploy --prod" --preset terminal --once -o cli.svg   # play once, stay on the text
python glyph_decode.py "Loading" --preset dither --theme light -o light.svg
python glyph_decode.py "Hello" --play                                     # preview in the terminal
python glyph_decode.py --demo                                             # writes docs/<preset>.svg for all presets
```

## Options
- `--preset decode|dither|terminal|blueprint|math`
- `--speed cinematic|fast` (fast keeps text readable within ~400 ms)
- `--theme dark|light`, `--size PX`, `--hold MS` (pause before looping), `--once`
- `--rest 0..1` (math preset: share of letters that stay as look-alike symbols, e.g. E -> ∃)
- `--seed N` changes the noise pattern; the same seed gives the same file.

## Put it in a README
```markdown
<p align="center"><img src="header.svg" alt="Your project name"></p>
```
Always keep a real `alt` text. Users with `prefers-reduced-motion` see the final text with no animation.
