#!/usr/bin/env python3
"""glyph-decode: turn a line of text into an animated SVG that decodes in through a glyph grid.

The SVG uses CSS keyframes only (no JavaScript), so it plays inside a GitHub README, a docs site or a slide.
Timing and presets follow quanhoangindex/ascii-reveal (MIT); the `math` preset and look-alike swaps follow
8xb300/mathglyph (MIT).
"""
import argparse
import html
import sys

PRESETS = {  # ramp: empty -> dense, scramble: noise glyphs, tick: ms per glyph change
    'decode': {'ramp': ' .:-=+*#%@', 'scramble': 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789#%&*+=?/', 'mode': 'ramp', 'tick': 60},
    'dither': {'ramp': ' ░▒▓█', 'scramble': '░▒▓█', 'mode': 'ramp', 'tick': 85},
    'terminal': {'ramp': ' .-:=+*#', 'scramble': '01<>/\\{}[]|_=+-;:', 'mode': 'random', 'tick': 40, 'cursor': '█'},
    'blueprint': {'ramp': ' ·-+=x#', 'scramble': '+-/\\|x·', 'mode': 'random', 'tick': 95},
    'math': {'ramp': ' ·∘∙∗⊕⊗', 'scramble': '∀∃∄¬∧∨⊢⊨⊤⊥⇒⇔∈∉⊂⊆∪∩∅ℵ⊗⊕⊙∣≡ℤℚℕℝℂ∫∂∑∏√∞', 'mode': 'ramp', 'tick': 60},
}
LOOKALIKE = {
    'A': '∀Λ∆', 'a': '∂α', 'B': 'β', 'b': 'β', 'C': '⊂ℂ∁', 'c': '⊂', 'D': '∂', 'd': '∂', 'E': '∃∈Σ', 'e': '∈ε',
    'F': '∫', 'f': '∫', 'H': 'ℍ', 'h': 'ℏ', 'I': '∣', 'i': 'ι', 'J': '⌋', 'j': '⌋', 'K': 'κ', 'k': 'κ',
    'L': '⌊∟', 'l': 'ℓ∣', 'N': 'ℕ', 'n': '∩η', 'O': '∅Θ⊕○', 'o': '∘σ⊙', 'P': 'ℙρ', 'p': 'ρ', 'Q': 'ℚ',
    'R': 'ℝ', 'S': '∫§', 's': '∫', 'T': '⊤', 't': '†τ', 'U': '∪', 'u': '∪μ', 'V': '∨√', 'v': '∨ν',
    'W': 'ω', 'w': 'ω', 'X': '×χ', 'x': '×χ', 'Y': 'γ', 'y': 'γ', 'Z': 'ℤ', '0': '∅', '1': '∣', '3': '∃',
}
THEMES = {'dark': ('#0d1117', '#e6edf3', '#7d8590', '#58a6ff'), 'light': ('#ffffff', '#1f2328', '#8c959f', '#0969da')}
SPEEDS = {  # spread(n) = ms over which characters start; char = base + random ms per character
    'fast': (lambda n: min(200, 40 + n * 4), (90, 110)),
    'cinematic': (lambda n: min(720, 90 + n * 13), (200, 240)),
}


def _hash(a, b, c):
    """Deterministic integer hash in [0, 1), same mixing as ascii-reveal's util.hash."""
    m = 0xFFFFFFFF
    h = ((a * 0x27D4EB2D) ^ ((b + 0x9E3779B9) * 0x85EBCA6B) ^ ((c + 0x632BE5AB) * 0xC2B2AE35)) & m
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & m
    h ^= h >> 12
    h = (h * 0x297A2D39) & m
    h ^= h >> 15
    return h / 4294967296


def frames(lines, preset='decode', speed='cinematic', seed=1, rest=0.0):
    """Return a list of frames; each frame is a list of strings (one per line). The last frame is the text.

    rest: share of letters that stay as math look-alikes after landing (mathglyph's "readable at rest").
    """
    p = PRESETS[preset]
    spread_fn, (base, rnd) = SPEEDS[speed]
    cells = [(li, k, ch) for li, line in enumerate(lines) for k, ch in enumerate(line)]
    n = max(1, len(cells))
    spread = spread_fn(n)
    s0, s1 = [], []
    for i in range(n):
        start = i / n * spread * 0.72 + _hash(i, seed, 1) * spread * 0.28
        s0.append(start)
        s1.append(start + base + _hash(i, seed, 2) * rnd)
    final = [list(line) for line in lines]
    for i, (li, k, ch) in enumerate(cells):
        if ch in LOOKALIKE and _hash(i, seed, 9) < rest:
            alts = LOOKALIKE[ch]
            final[li][k] = alts[int(_hash(i, seed, 10) * len(alts))]
    ramp, noise, tick = p['ramp'], p['scramble'], p['tick']
    out = []
    t = 0
    while True:
        frame = [[' '] * len(line) for line in lines]
        for i, (li, k, ch) in enumerate(cells):
            if ch == ' ' or t < s0[i]:
                continue
            if t >= s1[i]:
                frame[li][k] = final[li][k]
                continue
            q = (t - s0[i]) / (s1[i] - s0[i])
            step = int(t // tick)
            if p.get('cursor') and q < 0.2:
                g = p['cursor']
            elif p['mode'] == 'ramp' and q < 0.7:
                idx = 1 + int(q / 0.7 * (len(ramp) - 1))
                if _hash(i, step, 5) < 0.35:
                    idx += -1 if _hash(i, step, 6) < 0.5 else 1
                g = ramp[min(max(idx, 1), len(ramp) - 1)]
            else:
                g = noise[int(_hash(i, step, 7) * len(noise))]
            frame[li][k] = g
        out.append([''.join(r) for r in frame])
        if t >= max(s1):
            return out
        t += tick


def render_svg(lines, preset='decode', speed='cinematic', theme='dark', size=28, loop=True, hold=2400,
               seed=1, rest=0.0, title=None):
    fr = frames(lines, preset, speed, seed, rest)
    tick = PRESETS[preset]['tick']
    bg, fg, dim, accent = THEMES[theme]
    cw, lh = size * 0.6, size * 1.35
    cols = max(len(line) for line in lines)
    w, h = int(cols * cw + size * 2), int(len(lines) * lh + size * 1.4)
    n = len(fr)
    total = n * tick + hold if loop else n * tick
    one = 100 * tick / total
    anim = []
    if loop:  # every frame is visible for one tick per cycle; the last one also covers the hold
        anim += ['@keyframes f{0%%{opacity:1}%.4f%%{opacity:0}100%%{opacity:0}}' % one,
                 '@keyframes l{0%%{opacity:1}%.4f%%{opacity:1}%.4f%%{opacity:0}100%%{opacity:0}}' % (100 - one * (n - 1) - 0.0001, 100 - one * (n - 1)),
                 'g{opacity:0;animation:f %dms steps(1,end) infinite}' % total,
                 'g.z{animation-name:l}']
    else:
        anim += ['@keyframes f{0%{opacity:1}100%{opacity:0}}', '@keyframes l{0%,100%{opacity:1}}',
                 'g{opacity:0;animation:f %dms steps(1,end) 1}' % tick,
                 'g.z{animation:l 1ms forwards}']
    anim.append('@media (prefers-reduced-motion:reduce){g{animation:none!important}g.z{opacity:1}}')
    body = []
    for i, f in enumerate(fr):
        group = []
        for li, line in enumerate(f):
            y = size * 0.7 + lh * (li + 0.8)
            # a character has landed when it no longer changes in any later frame
            landed = [ch != ' ' and all(g[li][k] == ch for g in fr[i:]) for k, ch in enumerate(line)]
            for keep, color in ((True, fg), (False, accent if preset == 'blueprint' else dim)):
                idx = [k for k, ch in enumerate(line) if ch != ' ' and landed[k] == keep]
                if idx:  # one x per character keeps a strict grid even for wide math glyphs
                    group.append('<text x="%s" y="%.1f" fill="%s">%s</text>' % (
                        ' '.join('%.1f' % (size + k * cw) for k in idx), y, color,
                        html.escape(''.join(line[k] for k in idx), quote=False)))
        body.append('<g%s style="animation-delay:%dms">%s</g>' % (' class="z"' if i == n - 1 else '', i * tick, ''.join(group)))
    label = html.escape(title or ' / '.join(lines))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" '
            'aria-label="%s" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="%d" '
            'xml:space="preserve">\n<title>%s</title>\n<style>%s</style>\n<rect width="100%%" height="100%%" rx="12" fill="%s"/>\n%s\n</svg>\n'
            % (w, h, w, h, label, size, label, ''.join(anim), bg, '\n'.join(body)))


def play(lines, **kw):
    """Play the animation in a terminal with ANSI cursor moves."""
    import time
    preset = kw.get('preset', 'decode')
    fr = frames(lines, preset, kw.get('speed', 'cinematic'), kw.get('seed', 1), kw.get('rest', 0.0))
    for i, f in enumerate(fr):
        if i:
            sys.stdout.write('\x1b[%dA' % len(lines))
        sys.stdout.write('\n'.join(f) + '\n')
        sys.stdout.flush()
        time.sleep(PRESETS[preset]['tick'] / 1000)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('text', nargs='*', help='text; use \\n or several arguments for more lines')
    ap.add_argument('-o', '--out', help='write SVG here (default: stdout)')
    ap.add_argument('--preset', choices=PRESETS, default='decode')
    ap.add_argument('--speed', choices=SPEEDS, default='cinematic')
    ap.add_argument('--theme', choices=THEMES, default='dark')
    ap.add_argument('--size', type=int, default=28, help='font size in px')
    ap.add_argument('--once', action='store_true', help='play once and stay on the text (default: loop)')
    ap.add_argument('--hold', type=int, default=2400, help='ms to hold the text before looping')
    ap.add_argument('--rest', type=float, default=0.0, help='share of letters left as math look-alikes (0-1)')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--play', action='store_true', help='play in the terminal instead of writing SVG')
    ap.add_argument('--demo', action='store_true', help='write one SVG per preset into docs/')
    a = ap.parse_args(argv)
    if a.demo:
        import os
        docs = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
        os.makedirs(docs, exist_ok=True)
        demos = {'decode': ['glyph-decode', 'text that decodes itself'], 'dither': ['Loading your dashboard'],
                 'terminal': ['$ ship --prod', 'deployed in 4.2s'], 'blueprint': ['SYSTEM DESIGN v2'],
                 'math': ['Every proof starts', 'with a good guess']}
        for preset, lines in demos.items():
            path = os.path.join(docs, preset + '.svg')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(render_svg(lines, preset=preset, rest=0.25 if preset == 'math' else 0.0))
            print('wrote %s (%d frames)' % (os.path.relpath(path), len(frames(lines, preset))))
        return 0
    lines = '\n'.join(a.text).replace('\\n', '\n').split('\n') if a.text else []
    if not any(lines):
        ap.error('give some text, e.g. glyph_decode.py "Hello world" -o hello.svg')
    if a.play:
        play(lines, preset=a.preset, speed=a.speed, seed=a.seed, rest=a.rest)
        return 0
    svg = render_svg(lines, a.preset, a.speed, a.theme, a.size, not a.once, a.hold, a.seed, a.rest)
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(svg)
        print('wrote %s (%d bytes)' % (a.out, len(svg.encode())))
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stdout.write(svg)
    return 0


if __name__ == '__main__':
    sys.exit(main())
