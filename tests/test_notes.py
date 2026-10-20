import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('render_notes', ROOT / 'scripts/render_notes.py')
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


def fixture():
    return {'title': '学习页', 'summary': '一句话', 'sections': [
        {'title': '概念', 'table': {'caption': '对照', 'columns': ['名称', '解释'],
                                  'rows': [['A', 'B']]}}],
        'questions': [{'question': '为什么？', 'answer': '条件完整的答案'}]}


class NotesTests(unittest.TestCase):
    def test_material_is_text_not_executable(self):
        data = fixture()
        payload = '<script>alert("x")</script>'
        data['title'] = payload
        data['sections'][0]['table']['rows'][0][1] = payload
        data['questions'][0]['answer'] = payload
        result = notes.render_notes(data)
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)

    def test_table_accessibility_and_answers_hidden(self):
        result = notes.render_notes(fixture())
        self.assertIn('<caption>对照</caption>', result)
        self.assertEqual(result.count('scope="col"'), 2)
        self.assertIn('<details><summary>为什么？', result)
        self.assertNotIn('<details open', result)
        self.assertNotIn('<script src=', result)
        self.assertNotIn('<link ', result)

    def test_invalid_or_missing_table_rejected(self):
        data = fixture()
        data['sections'][0]['table']['rows'] = [['one cell']]
        with self.assertRaises(ValueError):
            notes.render_notes(data)
        data['sections'] = [{'title': '只有段落', 'paragraphs': ['内容']}]
        with self.assertRaises(ValueError):
            notes.render_notes(data)

    def test_links_cannot_run_code(self):
        data = fixture()
        for url in ['javascript:alert(1)', 'file:///tmp/private', 'https://example.com/ bad']:
            data['sources'] = [{'label': '来源', 'url': url}]
            with self.assertRaises(ValueError):
                notes.render_notes(data)
        data['sources'] = [{'label': '来源', 'url': 'https://example.com/?x=1&y=2'}]
        result = notes.render_notes(data)
        self.assertIn('x=1&amp;y=2', result)


if __name__ == '__main__':
    unittest.main()
