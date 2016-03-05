import bcrypt
import sqlalchemy

from .db import authenticators


class Failure(Exception): pass


def create_authenticator(name, verifier, account):
    """Create a new authenticator.

    Most of the time you don't need to call this directly,
    and instead should call the creator for a specific type
    of authenticator, such as create_bcrypt_authenticator().
    """
    query = authenticators.insert().values(
        name=name,
        verifier=verifier,
        account=account,
    )
    try:
        query.execute()
    except sqlalchemy.exc.IntegrityError:
        raise Failure("The name '{}' is already in use.".format(name))


def drop_authenticator(name):
    """Remove an existing authenticator."""
    query = authenticators.delete().where(
        authenticators.c.name == name,
    )
    query.execute()


def verify_authenticator(name, secret):
    """Verify credentials for an authenticator.

    Returns True if verification is successful, False otherwise.
    """
    query = sqlalchemy.select([authenticators.c.verifier]).where(
        authenticators.c.name == name,
    )
    auth = query.execute().first()
    if not auth:
            return False
    verifier = auth.verifier
    prefix, _, data = verifier.partition(":")
    if prefix == "bcrypt":
        return verify_bcrypt(secret, data)
    elif prefix == "plaintext":
        # ONLY FOR TESTING, DO NOT USE IN PROD
        return secret == data
    else:
        # If no type prefix, assume this was an unprefixed password.
        return verify_bcrypt(secret, verifier)


def create_bcrypt_authenticator(name, password, *args):
    """Create a new authenticator using a bcrypt'd password."""
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    verifier = "bcrypt:{}".format(hashed)
    create_authenticator(name, verifier, *args)


def verify_bcrypt(secret, data):
    """Verify a bcrypt-hashed password."""
    data = data.encode("utf-8")
    try:
        return bcrypt.hashpw(secret, data) == data
    except ValueError:
        raise Failure("Invalid salt: {}".format(data))
