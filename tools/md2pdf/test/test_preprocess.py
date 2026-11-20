"""Run with python3 -m unittest discover -s tools/md2pdf/test."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('preprocess', Path(__file__).parents[1] / 'preprocess.py')
preprocess = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preprocess)


class MermaidTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='md2pdf test ')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    def extract(self, text):
        return preprocess.extract_mermaid(text, self.work)

    def test_nested_fence(self):
        text = '````markdown\n```mermaid\nA-->B\n```\n````\n'
        self.assertEqual(self.extract(text), text)
        self.assertEqual(list(self.work.iterdir()), [])

    def test_unclosed_fence(self):
        source = self.work / 'source.md'
        source.write_text('```mermaid\nA-->B\n')
        result = subprocess.run([sys.executable, spec.origin, str(source),
                                 str(self.work / 'output.md'), str(self.work)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unclosed Mermaid fence at line 1', result.stderr)

    def test_indented_fence(self):
        self.assertIn('![](<', self.extract('   ```mermaid\nA-->B\n   ```\n'))
        text = '    ```mermaid\n    A-->B\n    ```\n'
        self.assertEqual(self.extract(text), text)

    def test_tilde_fence(self):
        self.assertIn('mermaid-1.png>', self.extract('~~~mermaid\nA-->B\n~~~~\n'))

    def test_crlf(self):
        output = self.extract('```mermaid\r\nA-->B\r\n```\r\n')
        self.assertTrue(output.endswith('\r\n'))
        self.assertEqual((self.work / 'mermaid-1.mmd').read_bytes(), b'A-->B\r\n')

    def test_several_blocks(self):
        output = self.extract('```mermaid\nA-->B\n```\ntext\n~~~mermaid\nC-->D\n~~~\n')
        self.assertIn('mermaid-2.png>', output)
        self.assertEqual((self.work / 'mermaid-2.mmd').read_text(), 'C-->D\n')

    def test_no_mermaid(self):
        text = '# Title\n```python\nprint(1)\n```\n'
        self.assertEqual(self.extract(text), text)
        self.assertEqual(list(self.work.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
