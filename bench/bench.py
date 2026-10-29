"""Time SVG generation and report output size. usage: python bench/bench.py [RUNS]"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import glyph_decode as gd  # noqa: E402

runs = int(sys.argv[1]) if len(sys.argv) > 1 else 20
lines = ['glyph-decode', 'text that decodes itself']
for preset in gd.PRESETS:
    t = time.perf_counter()
    for _ in range(runs):
        svg = gd.render_svg(lines, preset=preset)
    ms = (time.perf_counter() - t) / runs * 1000
    print('%-9s %6.1f ms per SVG  %6.1f KB  %d frames' % (preset, ms, len(svg.encode()) / 1024, len(gd.frames(lines, preset))))
