import unittest

from api_schemas import *


class TestSyntax(unittest.TestCase):

    def setUp(self) -> None:
        self.i = 0

    def correct(self, content: str):
        with self.subTest(self.i):
            parse(content)
        self.i += 1

    def wrong(self, content: str):
        with self.subTest(self.i):
            self.assertRaises(SystemExit, parse, content)
        self.i += 1

    def test_typedef(self):
        self.correct("""\
typedef Name
    name: str
""")

    def test_indent(self):
        self.correct("typedef Name\n    name: str")
        self.correct("typedef Name\n  name: str")
        self.correct("typedef Name\n\tname: str")

    def test_end(self):
        self.correct("x = 10")
        self.correct("typedef Name\n    name: str")
        self.correct("people\n\tGET\n\t\t->\n\t\t<-\n\t\t\t200")

    def test_common_mistakes(self):
        self.wrong("people\n\tGET\n\t\t->\n\t\t<-\n")

    def test_error_handling(self):
        self.assertRaises(SystemExit, parse, "typedef\n")


if __name__ == '__main__':
    unittest.main()
