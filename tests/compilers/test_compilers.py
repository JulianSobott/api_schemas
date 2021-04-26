import unittest
from api_schemas.compilers import python, dart
from tests.example_schemas import everything


class TestCompilers(unittest.TestCase):

    def test_python(self):
        res = python.convert(everything)
        # print(res)

    def test_dart(self):
        res = dart.convert(everything)
        # print(res)
