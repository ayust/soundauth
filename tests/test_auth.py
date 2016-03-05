import unittest


from soundauth import account
from soundauth import auth


class TestAuth(unittest.TestCase):

    def setUp(self):
        self.account = account.create_account()

    def tearDown(self):
        account.drop_account(self.account)

    def test_create_and_drop(self):
        # These should just succeed silently.
        auth.create_authenticator("foo", "plaintext:bar", self.account)
        auth.drop_authenticator("foo")

    def test_duplicate_fails(self):
        try:
            auth.create_authenticator("foo", "plaintext:bar", self.account)
            with self.assertRaises(auth.Failure):
                auth.create_authenticator("foo", "plaintext:baz", self.account)
        finally:
            auth.drop_authenticator("foo")

    def test_deleting_account_deletes_auth(self):
        try:
            acc = account.create_account()
            auth.create_authenticator("foo", "plaintext:bar", acc)
            self.assertTrue(auth.verify_authenticator("foo", "bar"))
            account.drop_account(acc)
            self.assertFalse(auth.verify_authenticator("foo", "bar"))
        finally:
            auth.drop_authenticator("foo")
            account.drop_account(acc)


class TestBcrypt(unittest.TestCase):

    def setUp(self):
        self.account = account.create_account()

    def tearDown(self):
        account.drop_account(self.account)

    def test_create_and_verify_works(self):
        try:
            auth.create_bcrypt_authenticator("foo", "bar", self.account)
            self.assertTrue(auth.verify_authenticator("foo", "bar"))
        finally:
            auth.drop_authenticator("foo")

    def test_wrong_password_fails(self):
        try:
            auth.create_bcrypt_authenticator("foo", "bar", self.account)
            self.assertFalse(auth.verify_authenticator("foo", "baz"))
        finally:
            auth.drop_authenticator("foo")

    def test_verify_missing_fails(self):
        self.assertFalse(auth.verify_authenticator("qux", "bar"))
