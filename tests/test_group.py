import unittest


from soundauth import group


class TestGroup(unittest.TestCase):

    def test_create_and_drop(self):
        group.create_group("foo")
        group.drop_group("foo")

    def test_invalid_name_fails(self):
        with self.assertRaises(group.Failure):
            group.create_group("foo:bar")

    def test_add_and_remove_subgroup(self):
        try:
            group.create_group("foo")
            group.add_subgroup("foo", "bar")
            self.assertTrue(group.is_member("foo", "bar"))
            group.drop_subgroup("foo", "bar")
            self.assertFalse(group.is_member("foo", "bar"))
        finally:
            group.drop_group("foo")
            group.drop_subgroup("foo", "bar")

    def test_add_and_remove_account(self):
        try:
            group.create_group("foo")
            group.add_member_account("foo", 1)
            self.assertTrue(group.is_member("foo", "account:1"))
            group.drop_member_account("foo", 1)
            self.assertFalse(group.is_member("foo", "account:1"))
        finally:
            group.drop_group("foo")
            group.drop_member_account("foo", 1)


class TestComplexGroup(unittest.TestCase):

    def setUp(self):
        group.create_group("foo")
        group.create_group("bar")
        group.add_subgroup("foo", "bar")
        group.add_member_account("foo", 1)
        group.add_member_account("bar", 2)

    def tearDown(self):
        group.drop_group("foo")
        group.drop_group("bar")
        group.drop_subgroup("foo", "bar")
        group.drop_member_account("foo", 1)
        group.drop_member_account("bar", 2)

    def test_list_accounts(self):
        self.assertEqual(
            group.list_accounts("foo"),
            set([1,2]),
        )

    def test_is_member_account(self):
        self.assertTrue(group.is_member_account("foo", 1))
        self.assertTrue(group.is_member_account("foo", 2))
        self.assertFalse(group.is_member_account("foo", 3))

    def test_dropping_group_drops_members(self):
        group.drop_group("bar")
        self.assertFalse(group.is_member("foo", "bar"))
        self.assertEqual(group.list_members("bar"), set())

    def test_list_parents(self):
        self.assertEqual(
            group.list_parents("account:2"),
            set(["foo", "bar"]),
        )

    def test_list_account_memberships(self):
        self.assertEqual(
            group.list_account_memberships(1),
            set(["foo"]),
        )
        self.assertEqual(
            group.list_account_memberships(2),
            set(["foo", "bar"]),
        )
