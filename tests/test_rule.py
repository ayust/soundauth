import unittest

from soundauth import group
from soundauth import rule


class TestRule(unittest.TestCase):

    def setUp(self):
        group.create_group("foo")
        group.create_group("bar")

    def tearDown(self):
        group.drop_group("foo")
        group.drop_group("bar")

    def test_create_and_drop(self):
        rule_id = rule.create_rule("foo", "deny", "always")
        rule.drop_rule(rule_id)

    def test_evaluate_rules(self):
        rule_id = rule.create_rule("foo", "deny", "always")
        try:
            self.assertEqual(
                "deny",
                rule.evaluate_rules("foo", {}),
            )
            self.assertEqual(
                "ignore",
                rule.evaluate_rules("bar", {}),
            )
        finally:
            rule.drop_rule(rule_id)
