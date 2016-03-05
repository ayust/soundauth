import sqlalchemy
from .db import authenticators


class Failure(Exception): pass


def create_authenticator(name, verifier):
  """Create a new authenticator."""
  query = authenticators.insert().values(
    name=name,
    verifier=verifier,
  )
  try:
    query.execute()
  except sqlalchemy.exc.IntegrityError:
    raise Failure("The name '{}' is already in use.".format(name))


def create_bcrypt_authenticator(name, password):
  """Create a new authenticator using a bcrypt'd password."""
  hashed = bcrypt.hashpw(password, bcrypt.gensalt())
  verifier = "bcrypt:{}".format(hashed)
  create_authenticator(name, verifier)


def verify_authenticator(name, secret):
  """Verify credentials for an authenticator."""
  query = authenticators.select().where(
    authenticators.c.name == name,
  )
  verifier = query.execute().first()
  prefix, _, data = verifier.partition(":")
  if prefix == "bcrypt":
    return verify_bcrypt(secret, data)
  else:
    # If no type prefix, assume this was an unprefixed password.
    return verify_bcrypt(secret, verifier)


def verify_bcrypt(secret, data):
  """Verify a bcrypt-hashed password."""
  return bcrypt.hashpw(secret, data) == data
