from api_schemas import *
from example_schemas import *

import unittest


class TestTransformation(unittest.TestCase):

    def test_constant(self):
        res = parse("x = 10")
        print(res)

    def test_typedef(self):
        res = parse(typedef_everything)
        print(res)

    def test_enum(self):
        res = parse("typedef Name\n\tattr1: Week {MONDAY, TUESDAY, WEDNESDAY}")
        print(res)
