import unittest


from soundauth import account


class TestAccount(unittest.TestCase):

    def test_create_and_drop(self):
        acc = account.create_account()
        account.drop_account(acc)
