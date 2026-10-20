"""Observable SVG/data integrity tests; no external dependencies."""
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

module_path = Path(__file__).resolve().parents[1] / 'scripts' / 'render_bar_chart.py'
spec = importlib.util.spec_from_file_location('chart', module_path)
chart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chart)
NS = {'s': 'http://www.w3.org/2000/svg'}


def payload(values):
    return {'title': '示例 < & >', 'unit': '个', 'source': '虚构测试数据',
            'items': [{'label': f'项目 {i}', 'value': v} for i, v in enumerate(values)]}


class ChartTests(unittest.TestCase):
    def test_numeric_proportions_and_accessibility(self):
        root = ET.fromstring(chart.render(payload([2, 4])))
        bars = root.findall('s:rect', NS)[1:]
        self.assertAlmostEqual(float(bars[1].get('width')), 2 * float(bars[0].get('width')), places=2)
        self.assertEqual(root.find('s:title', NS).text, '示例 < & >')
        self.assertIn('项目 1: 4', root.find('s:desc', NS).text)

    def test_negative_bar_left_of_positive(self):
        root = ET.fromstring(chart.render(payload([-2, 4])))
        neg, pos = root.findall('s:rect', NS)[1:]
        self.assertLess(float(neg.get('x')), float(pos.get('x')))
        self.assertAlmostEqual(float(neg.get('x')) + float(neg.get('width')), float(pos.get('x')), places=1)

    def test_zero_is_zero_not_invented(self):
        root = ET.fromstring(chart.render(payload([0, 0])))
        self.assertTrue(all(float(b.get('width')) == 0 for b in root.findall('s:rect', NS)[1:]))

    def test_missing_nonfinite_and_bool_rejected(self):
        for value in [None, True, '5', float('nan'), float('inf')]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                chart.render(payload([value]))

    def test_duplicate_empty_and_xml_control_rejected(self):
        data = payload([1, 2])
        data['items'][1]['label'] = data['items'][0]['label']
        with self.assertRaises(ValueError):
            chart.render(data)
        with self.assertRaises(ValueError):
            chart.render(payload([]))
        data = payload([1])
        data['title'] = 'bad\x00title'
        with self.assertRaises(ValueError):
            chart.render(data)

    def test_extreme_finite_values_stay_valid(self):
        root = ET.fromstring(chart.render(payload([-1e308, 1e308])))
        for bar in root.findall('s:rect', NS)[1:]:
            self.assertGreaterEqual(float(bar.get('width')), 0)
            self.assertLessEqual(float(bar.get('width')), 590)


if __name__ == '__main__':
    unittest.main()
