import unittest

from soundauth import group
from soundauth import rule


class TestRule(unittest.TestCase):

    def setUp(self):
        group.create_group("foo")

    def tearDown(self):
        group.drop_group("foo")

    def test_create_and_drop(self):
        rule_id = rule.create_rule("foo", "deny", "always")
        rule.drop_rule(rule_id)

