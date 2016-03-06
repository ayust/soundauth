from .db import accounts
from .db import authenticators
from .db import transaction


class Failure(Exception): pass


def create_account():
    """Create a new account and return its ID."""
    query = accounts.insert()
    account_id = query.execute().inserted_primary_key[0]
    return account_id


def drop_account(account_id):
    """Remove an account by id."""
    delete_account = accounts.delete().where(accounts.c.id == account_id)
    delete_auths = authenticators.delete().where(
        authenticators.c.account == account_id,
    )
    with transaction() as t:
        t.execute(delete_account)
        t.execute(delete_auths)
