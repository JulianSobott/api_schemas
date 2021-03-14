from api_schemas import *

import unittest


class TestTransformation(unittest.TestCase):

    def test_constant(self):
        res = parse("x = 10")
        print(res)

    def test_typedef(self):
        res = parse("typedef object Name\n\tattr1: str\n\tattr2: str")
        print(res)

    def test_enum(self):
        res = parse("typedef object Name\n\tattr1: {MONDAY, TUESDAY, WEDNESDAY}")
        print(res)