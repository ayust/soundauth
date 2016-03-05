import sqlalchemy
# Grab some specific symbols for the table definition DSL
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table


METADATA_SINGLETON = sqlalchemy.MetaData()


authenticators = Table("authenticators", METADATA_SINGLETON,
  # "public" portion of this authenticator, e.g. username
  Column("name", String(100), primary_key=True),
  # "private" portion of this authenticator, e.g. password
  Column("verifier", String(100)),
)


# TODO: Move the database connection string to configuration,
#       and optionally make this only trigger when requested.
ENGINE_SINGLETON = sqlalchemy.create_engine("sqlite:///:memory:")
METADATA_SINGLETON.bind = ENGINE_SINGLETON
METADATA_SINGLETON.create_all()
