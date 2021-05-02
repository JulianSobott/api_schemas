from api_schemas import *
from .example_schemas import *

import unittest


class TestTransformation(unittest.TestCase):

    def test_constant(self):
        res = parse("x = 10")
        # print(res)

    def test_typedef(self):
        res = parse(typedef_everything)
        # print(res)

    def test_enum(self):
        res = parse("typedef Name\n\tattr1: Week {MONDAY, TUESDAY, WEDNESDAY}")
        # print(res)

    def test_ws(self):
        # res = parse(websockets_1)
        # res = parse(websockets_2)
        res = parse(websockets_3)
        print(res)

    def test_communication(self):
        res = parse(communication_1)
        # print(res)

    def test_all(self):
        parse(everything)

    def test_reference_types(self):
        res = parse(references_schema)
        self.assertTrue(len(res.global_types) == 2)
        self.assertIs(type(res.global_types[0].type), ObjectType)
        self.assertIs(type(res.global_types[1].type), ObjectType)
        self.assertIs(type(res.global_types[0].type.attributes[0].type), ReferenceType)
        self.assertIs(type(res.global_types[1].type.attributes[0].type), ReferenceType)
        self.assertEqual(res.global_types[0].type.attributes[0].type.reference.name, "Y")
        self.assertEqual(res.global_types[1].type.attributes[0].type.reference.name, "X")

    def test_reference_types_not_found(self):
        self.assertRaises(SystemExit, lambda: parse("typedef Y\n\tx: $X\n"))
        self.assertRaises(SystemExit, lambda: parse("typedef Hello\n\tx: int\ntypedef X\n\tx: $hello\n"))

    def test_communication_url(self):
        res = parse(communication_1)
        self.assertEqual(res.communications[0].uri, "/a")
