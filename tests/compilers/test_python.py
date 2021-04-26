import unittest
from api_schemas.compilers import python
from tests.example_schemas import everything


class TestPython(unittest.TestCase):

    def test_compile(self):
        res = python.convert(everything)
        print(res)
