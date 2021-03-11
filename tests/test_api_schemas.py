from api_schemas import *
import unittest


class Test(unittest.TestCase):

    def test_types(self):
        ir = parse("""
typedef object my_type
    val1: str
    val2: int
    val3: object AnotherType
        inner: int
    *: str
""")
        self.assertEqual(1, len(ir.global_types))
        t1 = ir.global_types[0]
        self.assertEqual("my_type", t1.name)
        self.assertEqual(ObjectType, t1.type_type)
        self.assertEqual(4, len(t1.data.body.attributes))
        for a in t1.data.body.attributes:
            self.assertIn(a.name, ["val1", "val2", "val3", "*"])
            if a.name == "*":
                self.assertTrue(a.is_wildcard)
            if a.name == "val3":
                self.assertEqual("AnotherType", a.type_definition.name)

    def test_any(self):
        ir = parse("""
typedef object X
    val: any
""")
        self.assertEqual(AnyType, ir.global_types[0].data.body.attributes[0].type_definition.type_type)
