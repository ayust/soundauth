import unittest


from soundauth import group


class TestGroup(unittest.TestCase):

    def test_create_and_drop(self):
        group.create_group("foo")
        group.drop_group("foo")

    def test_add_and_remove_group_member(self):
        try:
            group.create_group("foo")
            group.add_member("foo", "bar")
            self.assertTrue(group.is_member("foo", "bar"))
            group.drop_member("foo", "bar")
            self.assertFalse(group.is_member("foo", "bar"))
        finally:
            group.drop_group("foo")
            group.drop_member("foo", "bar")
