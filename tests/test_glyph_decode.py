import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import glyph_decode as gd  # noqa: E402


class Frames(unittest.TestCase):
    def test_last_frame_is_the_text_and_first_hides_it(self):
        for preset in gd.PRESETS:
            fr = gd.frames(['Hello, world', 'second line'], preset=preset, seed=3)
            self.assertEqual(fr[-1], ['Hello, world', 'second line'], preset)
            self.assertNotIn('Hello', fr[0][0], preset)
            self.assertTrue(all(len(f[0]) == 12 and len(f[1]) == 11 for f in fr), preset)

    def test_deterministic_with_seed(self):
        self.assertEqual(gd.frames(['abc def'], seed=1), gd.frames(['abc def'], seed=1))
        self.assertNotEqual(gd.frames(['abc def ghi jkl'], seed=1), gd.frames(['abc def ghi jkl'], seed=2))

    def test_spaces_stay_spaces_and_wave_runs_left_to_right(self):
        fr = gd.frames(['ab cd efgh ijkl mnop'], seed=5)
        self.assertTrue(all(f[0][2] == ' ' for f in fr))
        text = 'ab cd efgh ijkl mnop'

        def landed(k):
            return min(i for i in range(len(fr)) if all(g[0][k] == text[k] for g in fr[i:]))
        landed = [landed(0), landed(19)]
        self.assertLess(landed[0], landed[1])

    def test_math_rest_swaps_keep_lookalikes(self):
        fr = gd.frames(['EVERY SET'], preset='math', rest=1.0, seed=2)
        last = fr[-1][0]
        self.assertNotEqual(last, 'EVERY SET')
        for a, b in zip('EVERY SET', last):
            self.assertTrue(a == b or b in gd.LOOKALIKE.get(a, ''), (a, b))


class Svg(unittest.TestCase):
    def test_valid_svg_with_escaping_and_one_text_per_frame_line(self):
        svg = gd.render_svg(['a < b & c > d'], seed=1)
        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith('svg'))
        groups = [g for g in root.iter() if g.tag.endswith('}g')]
        self.assertEqual(len(groups), len(gd.frames(['a < b & c > d'], seed=1)))
        last = ''.join(t.text for t in groups[-1] if t.tag.endswith('text'))
        self.assertEqual(last, 'a<b&c>d')
        self.assertIn('&lt;b&amp;c&gt;d', svg)

    def test_strict_grid_x_per_character(self):
        root = ET.fromstring(gd.render_svg(['ab'], size=10, seed=1))
        last = [g for g in root.iter() if g.tag.endswith('}g')][-1]
        self.assertEqual(last[0].get('x'), '10.0 16.0')

    def test_once_mode_freezes_on_last_frame(self):
        svg = gd.render_svg(['hi there'], loop=False, seed=1)
        self.assertIn('forwards', svg)
        self.assertNotIn('infinite', svg)

    def test_cli_writes_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, 'x.svg')
            p = subprocess.run([sys.executable, os.path.join(ROOT, 'glyph_decode.py'), 'Ship it', '-o', out,
                                '--preset', 'terminal'], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            ET.parse(out)


if __name__ == '__main__':
    unittest.main()
