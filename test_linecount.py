import os
import tempfile
import unittest

from VDRplayer import lineCount


class LineCountTests(unittest.TestCase):
    def test_linecount_restores_file_pointer(self):
        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as tmp:
            tmp.write('alpha\n')
            tmp.write('beta\n')
            tmp.write('gamma\n')
            tmp.flush()
            tmp.seek(0)

            # Move to a non-zero position before counting.
            tmp.readline()
            original_pos = tmp.tell()

            count = lineCount(tmp)

            self.assertEqual(count, 3)
            self.assertEqual(tmp.tell(), original_pos)

        os.unlink(tmp.name)


if __name__ == '__main__':
    unittest.main()
